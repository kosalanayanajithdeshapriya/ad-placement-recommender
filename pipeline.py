"""
pipeline.py — Runs full pipeline as functions (no subprocess needed on Render)
"""

import json
import os
import tempfile
import numpy as np
import pandas as pd


# ── Component 1: Candidate Generator ──────────────────────────

def run_component1(video_path):
    """Extract scene changes, silences, transcript boundaries from video."""
    import cv2
    from pydub import AudioSegment
    from pydub.silence import detect_silence

    candidates = []
    total_duration = 0

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    total_duration = frame_count / fps if fps > 0 else 0

    # Scene change detection — sample every 5 frames to save memory
    prev_frame = None
    frame_idx  = 0
    scene_threshold = 30.0
    sample_every = 5

    while True:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if not ret:
            break
        small = cv2.resize(frame, (160, 90))
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        if prev_frame is not None:
            diff = cv2.absdiff(gray, prev_frame)
            score = diff.mean()
            if score > scene_threshold:
                timestamp = frame_idx / fps
                if timestamp > 30:
                    candidates.append({
                        "timestamp": round(timestamp, 2),
                        "type":      "scene_change",
                        "score":     round(float(score), 3)
                    })
        prev_frame = gray
        frame_idx += sample_every
    cap.release()

    # Silence detection
    try:
        audio = AudioSegment.from_file(video_path)
        silences = detect_silence(audio, min_silence_len=800, silence_thresh=-40)
        for start_ms, end_ms in silences:
            mid = (start_ms + end_ms) / 2 / 1000
            if mid > 30 and mid < total_duration - 30:
                candidates.append({
                    "timestamp": round(mid, 2),
                    "type":      "silence",
                    "score":     0.6
                })
    except Exception as e:
        print(f"[Component 1] Audio extraction warning: {e}")

    # Transcript boundary detection
    try:
        import whisper
        print("[Component 1] Running Whisper transcription (base model)...")
        model = whisper.load_model("base")
        result = model.transcribe(video_path)
        segments = result.get("segments", [])
        
        for segment in segments:
            text = segment.get("text", "").strip()
            # If segment ends with terminal punctuation, treat as a break
            if text and text[-1] in ".!?":
                end_time = segment["end"]
                if end_time > 30 and end_time < total_duration - 30:
                    candidates.append({
                        "timestamp": round(end_time, 2),
                        "type":      "transcript_boundary",
                        "score":     0.7
                    })
    except Exception as e:
        print(f"[Component 1] Whisper transcription warning: {e}")

    # Deduplicate — remove candidates within 5s of each other
    candidates = sorted(candidates, key=lambda x: x["timestamp"])
    deduped = []
    for c in candidates:
        if not deduped or abs(c["timestamp"] - deduped[-1]["timestamp"]) > 5:
            deduped.append(c)

    data = {"candidates": deduped, "total_duration": round(total_duration, 2)}
    with open("candidates.json", "w") as f:
        json.dump(data, f, indent=2)

    print(f"[Component 1] {len(deduped)} candidates found, duration: {total_duration:.1f}s")
    return data


# ── Component 2: Feature Extractor (Published Videos) ─────────

def run_component2(video_id, creds):
    """Fetch retention data from YouTube Analytics and extract features."""
    from youtube_analytics import get_retention_curve

    with open("candidates.json") as f:
        data = json.load(f)

    candidates     = data["candidates"]
    total_duration = data["total_duration"]

    curve_df = get_retention_curve(video_id, creds=creds)

    rows = []
    for i, c in enumerate(candidates):
        t = c["timestamp"]

        mask   = (curve_df["second"] >= t - 10) & (curve_df["second"] <= t + 10)
        subset = curve_df[mask]
        if subset.empty:
            ret_at_t, drop_rate, recovery = 0.0, 0.0, 0.0
        else:
            idx      = (subset["second"] - t).abs().idxmin()
            ret_at_t = float(curve_df.loc[idx, "retention_pct"])
            before   = curve_df[curve_df["second"] < t].tail(30)
            after    = curve_df[curve_df["second"] > t].head(30)
            further  = curve_df[curve_df["second"] > t + 30].head(30)
            drop_rate = float(before["retention_pct"].mean() - after["retention_pct"].mean()) if len(before) and len(after) else 0
            recovery  = float(after["retention_pct"].mean() - further["retention_pct"].mean()) if len(after) and len(further) else 0

        time_since_last = t - candidates[i-1]["timestamp"] if i > 0 else t
        rows.append({
            "timestamp":                 round(t, 2),
            "type":                      c["type"],
            "content_score":             c["score"],
            "retention_at_t":            round(ret_at_t, 3),
            "retention_drop_rate":       round(drop_rate, 3),
            "retention_recovery":        round(recovery, 3),
            "relative_position":         round(t / total_duration, 4),
            "time_since_last_candidate": round(time_since_last, 2),
            "label":                     0
        })

    df = pd.DataFrame(rows)
    if len(df) > 1:
        df["label"] = (
            (df["retention_at_t"] > df["retention_at_t"].median()) &
            (df["retention_drop_rate"] < df["retention_drop_rate"].median())
        ).astype(int)

    df.to_csv("features.csv", index=False)
    print(f"[Component 2] features.csv saved — {len(df)} candidates")
    return df


# ── Component 2 Offline: Audio-Based Retention Simulator ──────

def run_component2_offline(video_path):
    """
    Replaces Component 2 for unpublished videos.
    Simulates retention curve using audio energy analysis.
    No YouTube API needed.
    """
    with open("candidates.json") as f:
        data = json.load(f)

    candidates     = data["candidates"]
    total_duration = data["total_duration"]

    # ── Generate simulated retention curve ──
    try:
        import librosa
        audio, sr = librosa.load(video_path, sr=22050, mono=True)
        hop_length = sr  # 1 second per frame
        rms = librosa.feature.rms(y=audio, hop_length=hop_length)[0]
        rms_norm = (rms - rms.min()) / (rms.max() - rms.min() + 1e-6)
        seconds = np.arange(len(rms_norm))
        print(f"[Component 2 Offline] Audio loaded — {len(seconds)} seconds analyzed")
    except Exception as e:
        print(f"[Component 2 Offline] librosa fallback ({e})")
        seconds = np.arange(int(total_duration))
        rms_norm = np.ones(len(seconds))

    n = len(seconds)

    # Base: natural viewer decay over time
    base_decay = np.linspace(1.0, 0.30, n)

    # Audio energy modifier — high energy = viewers stay
    energy_factor = 0.15 * (rms_norm[:n] - 0.5)

    # Intro drop — first 30s many viewers leave quickly
    intro_drop = np.ones(n)
    intro_end = min(30, n)
    intro_drop[:intro_end] = np.linspace(1.0, 0.85, intro_end)

    # Combine & smooth
    retention = base_decay * intro_drop + energy_factor
    retention = np.clip(retention, 0.05, 1.0)
    window = min(30, n // 4)
    if window > 1:
        retention = np.convolve(retention, np.ones(window)/window, mode='same')
    retention = np.clip(retention, 0.05, 1.0)

    curve_df = pd.DataFrame({
        "second":        seconds,
        "retention_pct": (retention * 100).round(2)
    })

    # ── Extract features same as Component 2 ──
    rows = []
    for i, c in enumerate(candidates):
        t = c["timestamp"]

        mask   = (curve_df["second"] >= t - 10) & (curve_df["second"] <= t + 10)
        subset = curve_df[mask]

        if subset.empty:
            ret_at_t, drop_rate, recovery = 50.0, 0.0, 0.0
        else:
            idx      = (subset["second"] - t).abs().idxmin()
            ret_at_t = float(curve_df.loc[idx, "retention_pct"])
            before   = curve_df[curve_df["second"] < t].tail(30)
            after    = curve_df[curve_df["second"] > t].head(30)
            further  = curve_df[curve_df["second"] > t + 30].head(30)
            drop_rate = float(before["retention_pct"].mean() - after["retention_pct"].mean()) if len(before) and len(after) else 0
            recovery  = float(after["retention_pct"].mean() - further["retention_pct"].mean()) if len(after) and len(further) else 0

        time_since_last = t - candidates[i-1]["timestamp"] if i > 0 else t
        rows.append({
            "timestamp":                 round(t, 2),
            "type":                      c["type"],
            "content_score":             c["score"],
            "retention_at_t":            round(ret_at_t, 3),
            "retention_drop_rate":       round(drop_rate, 3),
            "retention_recovery":        round(recovery, 3),
            "relative_position":         round(t / total_duration, 4),
            "time_since_last_candidate": round(time_since_last, 2),
            "label":                     0
        })

    df = pd.DataFrame(rows)
    if len(df) > 1:
        df["label"] = (
            (df["retention_at_t"] > df["retention_at_t"].median()) &
            (df["retention_drop_rate"] < df["retention_drop_rate"].median())
        ).astype(int)

    df.to_csv("features.csv", index=False)
    print(f"[Component 2 Offline] features.csv saved — {len(df)} candidates")
    return df


# ── Component 3: ML Ranker ─────────────────────────────────────

def run_component3():
    """Train LightGBM ranker and score all candidates."""
    import lightgbm as lgb
    from sklearn.preprocessing import LabelEncoder

    df = pd.read_csv("features.csv")

    feature_cols = [
        "retention_at_t", "retention_drop_rate", "retention_recovery",
        "relative_position", "time_since_last_candidate", "content_score"
    ]

    le = LabelEncoder()
    df["type_enc"] = le.fit_transform(df["type"])
    feature_cols.append("type_enc")

    X = df[feature_cols].fillna(0)
    y = df["label"].fillna(0).astype(int)

    n_pos = y.sum()
    print(f"[Component 3] Training LightGBM — {len(df)} samples, {n_pos} positive")

    model = lgb.LGBMClassifier(
        n_estimators=100,
        learning_rate=0.05,
        num_leaves=15,
        random_state=42,
        verbose=-1
    )
    model.fit(X, y)

    scores = model.predict_proba(X)[:, 1]
    df["placement_score"] = scores

    def fmt(t):
        return f"{int(t//60)}m {int(t%60):02d}s"

    placements = []
    for _, row in df.iterrows():
        placements.append({
            "timestamp":           row["timestamp"],
            "timestamp_formatted": fmt(row["timestamp"]),
            "type":                row["type"],
            "placement_score":     float(row["placement_score"]),
            "retention_at_t":      float(row["retention_at_t"]),
            "label":               int(row["label"])
        })

    placements = sorted(placements, key=lambda x: x["placement_score"], reverse=True)
    for i, p in enumerate(placements):
        p["rank"] = i + 1

    result = {"ranked_placements": placements}
    with open("ranked_candidates.json", "w") as f:
        json.dump(result, f, indent=2)

    print(f"[Component 3] Ranked {len(placements)} candidates")
    return placements


# ── Component 4: Recommender ───────────────────────────────────

def run_component4():
    """Apply business rules and generate final recommendations."""

    CONFIG = {
        "min_placement_score":   0.0,
        "min_gap_seconds":       120,
        "skip_intro_pct":        0.20,
        "skip_outro_pct":        0.10,
        "max_placements":        3,
        "short_video_threshold": 480,
    }

    with open("ranked_candidates.json") as f:
        data = json.load(f)

    placements     = data["ranked_placements"]
    total_duration = max(p["timestamp"] for p in placements) / 0.80

    filtered = [p for p in placements if p["placement_score"] >= CONFIG["min_placement_score"]]

    intro_cut = total_duration * CONFIG["skip_intro_pct"]
    filtered  = [p for p in filtered if p["timestamp"] >= intro_cut]

    outro_cut = total_duration * (1 - CONFIG["skip_outro_pct"])
    filtered  = [p for p in filtered if p["timestamp"] <= outro_cut]

    max_allow = 1 if total_duration <= CONFIG["short_video_threshold"] else CONFIG["max_placements"]

    selected = []
    for p in sorted(filtered, key=lambda x: x["placement_score"], reverse=True):
        if len(selected) >= max_allow:
            break
        too_close = any(abs(p["timestamp"] - s["timestamp"]) < CONFIG["min_gap_seconds"] for s in selected)
        if not too_close:
            selected.append(p)

    def fmt(t):
        return f"{int(t//60)}m {int(t%60):02d}s"

    output = {
        "video_duration_seconds":       round(total_duration, 1),
        "video_duration_formatted":     fmt(total_duration),
        "total_placements_recommended": len(selected),
        "config_used":                  CONFIG,
        "recommendations":              []
    }

    for i, p in enumerate(sorted(selected, key=lambda x: x["timestamp"])):
        ret = p["retention_at_t"]
        output["recommendations"].append({
            "placement_number":    i + 1,
            "timestamp_seconds":   p["timestamp"],
            "timestamp_formatted": p["timestamp_formatted"],
            "type":                p["type"],
            "placement_score":     p["placement_score"],
            "retention_at_t":      ret,
            "confidence": (
                "HIGH"   if p["placement_score"] >= 0.75 else
                "MEDIUM" if p["placement_score"] >= 0.50 else
                "LOW"
            ),
            "creator_note": (
                f"Place sponsored segment at {p['timestamp_formatted']} — "
                f"natural {p['type'].replace('_', ' ')} detected, "
                f"{ret:.1f}% viewers still watching."
            )
        })

    with open("final_recommendations.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"[Component 4] {len(selected)} final placements recommended")
    return output


# ── Full Pipeline (Published Videos) ──────────────────────────

def run_full_pipeline(video_path, video_id, creds, progress_callback=None):
    """Run all 4 components for a published YouTube video."""

    def update(msg):
        print(msg)
        if progress_callback:
            progress_callback(msg)

    update("🔍 Step 1/4 — Detecting natural break points in your video...")
    run_component1(video_path)

    update("📊 Step 2/4 — Fetching viewer retention data from YouTube...")
    run_component2(video_id, creds)

    update("🤖 Step 3/4 — Running ML ranking engine...")
    run_component3()

    update("🎯 Step 4/4 — Generating final recommendations...")
    result = run_component4()

    update("✅ Analysis complete!")
    return result


# ── Offline Pipeline (Unpublished Videos — No YouTube API) ────

def run_full_pipeline_offline(video_path, progress_callback=None):
    """
    Run pipeline WITHOUT YouTube Analytics API.
    Uses audio energy analysis to simulate retention curve.
    Perfect for pre-publish ad spot prediction.
    """

    def update(msg):
        print(msg)
        if progress_callback:
            progress_callback(msg)

    update("🔍 Step 1/4 — Detecting natural break points in your video...")
    run_component1(video_path)

    update("🎵 Step 2/4 — Analyzing audio energy to predict viewer retention...")
    run_component2_offline(video_path)

    update("🤖 Step 3/4 — Running ML ranking engine...")
    run_component3()

    update("🎯 Step 4/4 — Generating final predictions...")
    result = run_component4()

    update("✅ Prediction complete!")
    return result
"""
predictor_audio.py — Replaces Component 2 for unpublished videos.
Uses audio energy + pacing to simulate a retention curve.
"""

import numpy as np
import pandas as pd
import json

def generate_simulated_retention(video_path, total_duration):
    """
    Analyzes audio energy to simulate a retention curve.
    Returns a DataFrame matching get_retention_curve() output format.
    """
    try:
        import librosa
        audio, sr = librosa.load(video_path, sr=22050, mono=True)
        
        # Calculate RMS energy per second
        hop_length = sr  # 1 second per frame
        rms = librosa.feature.rms(y=audio, hop_length=hop_length)[0]
        
        # Normalize energy 0 to 1
        rms_norm = (rms - rms.min()) / (rms.max() - rms.min() + 1e-6)
        
        seconds = np.arange(len(rms_norm))
        
    except Exception as e:
        print(f"[Predictor Audio] librosa failed ({e}), using duration-based fallback")
        seconds = np.arange(int(total_duration))
        rms_norm = np.ones(len(seconds))

    # Build simulated retention curve
    # Base: natural decay (viewers always drop over time)
    n = len(seconds)
    base_decay = np.linspace(1.0, 0.30, n)

    # Modify decay based on audio energy
    # Low energy = viewers more likely to leave
    # High energy = viewers stay
    energy_factor = 0.15 * (rms_norm - 0.5)  # range: -0.075 to +0.075
    
    # Add intro spike drop (first 30s many viewers leave)
    intro_drop = np.ones(n)
    intro_end = min(30, n)
    intro_drop[:intro_end] = np.linspace(1.0, 0.85, intro_end)

    # Combine all factors
    retention = base_decay * intro_drop + energy_factor
    retention = np.clip(retention, 0.05, 1.0)

    # Smooth the curve
    window = min(30, n // 4)
    if window > 1:
        retention = np.convolve(retention, np.ones(window)/window, mode='same')
    retention = np.clip(retention, 0.05, 1.0)

    df = pd.DataFrame({
        "second": seconds,
        "retention_pct": (retention * 100).round(2)
    })

    print(f"[Predictor Audio] Simulated retention curve — {len(df)} seconds")
    return df


def run_component2_offline(video_path):
    """
    Drop-in replacement for run_component2() in pipeline.py.
    Uses audio analysis instead of YouTube Analytics API.
    """
    with open("candidates.json") as f:
        data = json.load(f)

    candidates     = data["candidates"]
    total_duration = data["total_duration"]

    # Generate simulated retention curve from audio
    curve_df = generate_simulated_retention(video_path, total_duration)

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
    print(f"[Predictor Audio] features.csv saved — {len(df)} candidates")
    return df
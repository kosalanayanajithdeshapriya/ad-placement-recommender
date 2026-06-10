"""
component2_feature_extractor.py — Updated with real YouTube Analytics support
Simulated : python component2_feature_extractor.py
Real data : python component2_feature_extractor.py --video-id YOUR_VIDEO_ID
"""

import json
import sys
import pandas as pd
import numpy as np


def simulate_retention_curve(total_duration, seed=42):
    np.random.seed(seed)
    t = np.linspace(0, total_duration, int(total_duration))
    base = 100 * np.exp(-0.003 * t)
    noise = np.random.normal(0, 2, len(t))
    spikes = np.zeros(len(t))
    for _ in range(5):
        spike_t = np.random.randint(0, len(t))
        spikes[max(0, spike_t-10):spike_t+10] += np.random.uniform(3, 8)
    return pd.DataFrame({"second": t, "retention_pct": np.clip(base + noise + spikes, 0, 100)})


def get_real_retention_curve(video_id):
    try:
        from youtube_analytics import get_retention_curve
        df = get_retention_curve(video_id)
        return df
    except Exception as e:
        print(f"[Component 2] Warning: {e}")
        print("[Component 2] Falling back to simulated retention curve")
        return None


def get_retention_at(curve_df, t, window=10):
    mask   = (curve_df["second"] >= t - window) & (curve_df["second"] <= t + window)
    subset = curve_df[mask]
    if subset.empty:
        return 0.0, 0.0, 0.0
    at_t_idx       = (subset["second"] - t).abs().idxmin()
    retention_at_t = curve_df.loc[at_t_idx, "retention_pct"]
    before         = curve_df[curve_df["second"] < t].tail(30)
    after          = curve_df[curve_df["second"] > t].head(30)
    further        = curve_df[curve_df["second"] > t + 30].head(30)
    drop_rate      = (before["retention_pct"].mean() - after["retention_pct"].mean()) if len(before) and len(after) else 0
    recovery       = after["retention_pct"].mean() - further["retention_pct"].mean() if len(after) and len(further) else 0
    return round(float(retention_at_t), 3), round(float(drop_rate), 3), round(float(recovery), 3)


def extract_features(candidates_path="candidates.json", video_id=None):
    with open(candidates_path) as f:
        data = json.load(f)

    candidates     = data["candidates"]
    total_duration = data["total_duration"]

    if video_id:
        print(f"[Component 2] Fetching REAL retention for video: {video_id}")
        curve_df = get_real_retention_curve(video_id)
        if curve_df is None:
            curve_df = simulate_retention_curve(total_duration)
    else:
        print("[Component 2] Using SIMULATED retention curve")
        curve_df = simulate_retention_curve(total_duration)

    rows = []
    for i, c in enumerate(candidates):
        t = c["timestamp"]
        ret_at_t, drop_rate, recovery = get_retention_at(curve_df, t)
        time_since_last = t - candidates[i-1]["timestamp"] if i > 0 else t
        rows.append({
            "timestamp":                 t,
            "type":                      c["type"],
            "content_score":             c["score"],
            "retention_at_t":            ret_at_t,
            "retention_drop_rate":       drop_rate,
            "retention_recovery":        recovery,
            "relative_position":         round(t / total_duration, 4),
            "time_since_last_candidate": round(time_since_last, 2),
            "label":                     None
        })

    df = pd.DataFrame(rows)
    df["label"] = (
        (df["retention_at_t"] > df["retention_at_t"].median()) &
        (df["retention_drop_rate"] < df["retention_drop_rate"].median())
    ).astype(int)

    df.to_csv("features.csv", index=False)
    print("[Component 2] features.csv saved ✅")
    print(df[["timestamp", "type", "retention_at_t", "retention_drop_rate", "label"]].to_string(index=False))
    return df


if __name__ == "__main__":
    video_id = None
    if "--video-id" in sys.argv:
        idx      = sys.argv.index("--video-id")
        video_id = sys.argv[idx + 1]
    extract_features(video_id=video_id)
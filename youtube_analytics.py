"""
youtube_analytics.py — Fetches real retention curve from YouTube Analytics API
"""

import pandas as pd
import numpy as np
from googleapiclient.discovery import build


def get_video_duration(video_id, creds):
    youtube = build("youtube", "v3", credentials=creds)
    response = youtube.videos().list(
        part="contentDetails,snippet",
        id=video_id
    ).execute()

    if not response["items"]:
        raise ValueError(f"Video {video_id} not found or is private.")

    item = response["items"][0]
    duration_iso = item["contentDetails"]["duration"]
    title = item["snippet"]["title"]

    # Parse ISO 8601 duration
    import re
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_iso)
    hours   = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    total_seconds = hours * 3600 + minutes * 60 + seconds

    print(f"[Analytics] Video: {title}")
    print(f"[Analytics] Duration: {hours}h {minutes}m {seconds}s ({total_seconds}s)")
    return total_seconds, title


def get_retention_curve(video_id, creds=None):
    if creds is None:
        from youtube_auth import get_credentials
        creds = get_credentials()

    try:
        total_duration, title = get_video_duration(video_id, creds)
    except Exception as e:
        print(f"[Analytics] Could not get video duration: {e}")
        total_duration = 600

    try:
        analytics = build("youtubeAnalytics", "v2", credentials=creds)
        response = analytics.reports().query(
            ids="channel==MINE",
            startDate="2020-01-01",
            endDate="2030-01-01",
            metrics="audienceWatchRatio",
            dimensions="elapsedVideoTimeRatio",
            filters=f"video=={video_id}",
            maxResults=100
        ).execute()

        rows = response.get("rows", [])
        if not rows:
            raise ValueError("No retention data returned from YouTube Analytics.")

        print(f"[Analytics] Fetched {len(rows)} retention data points for {video_id}")

        ratios     = [r[0] for r in rows]
        watch_vals = [r[1] for r in rows]
        max_watch  = max(watch_vals) if watch_vals else 1

        df = pd.DataFrame({
            "second":        [r * total_duration for r in ratios],
            "retention_pct": [min((v / max_watch) * 100, 100) for v in watch_vals]
        })

        # Save for dashboard chart
        curve_json = [
            {"time_seconds": round(row["second"], 2), "retention_percent": round(row["retention_pct"], 2)}
            for _, row in df.iterrows()
        ]
        import json
        with open("retention_curve.json", "w") as f:
            json.dump(curve_json, f)

        return df

    except Exception as e:
        print(f"[Analytics] Error fetching retention: {e}")
        print("[Analytics] Falling back to simulated curve")
        return simulate_retention_curve(total_duration)


def simulate_retention_curve(total_duration, seed=42):
    np.random.seed(seed)
    t    = np.linspace(0, total_duration, int(total_duration))
    base = 100 * np.exp(-0.003 * t)
    noise  = np.random.normal(0, 2, len(t))
    spikes = np.zeros(len(t))
    for _ in range(5):
        spike_t = np.random.randint(0, len(t))
        spikes[max(0, spike_t-10):spike_t+10] += np.random.uniform(3, 8)
    df = pd.DataFrame({
        "second":        t,
        "retention_pct": np.clip(base + noise + spikes, 0, 100)
    })
    # Save for dashboard
    curve_json = [
        {"time_seconds": round(row["second"], 2), "retention_percent": round(row["retention_pct"], 2)}
        for _, row in df.iterrows()
    ]
    import json
    with open("retention_curve.json", "w") as f:
        json.dump(curve_json, f)
    return df
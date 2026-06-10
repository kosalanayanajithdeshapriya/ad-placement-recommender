from youtube_analytics import get_retention_curve

video_ids = [
    "USVNGTw2pKM",  # Dijkstra is Dead
    "okPBQ0Ekafw",
    "FU78qBHeQf0",
    "4Rq-LY16WxM",  # FlashGuard
    "LpihkA9KWqo",
]

for vid in video_ids:
    print(f"\nTrying: {vid}")
    df = get_retention_curve(vid)
    if df is not None:
        print(f"  ✅ Has retention data! ({len(df)} points)")
        print(df.head(5).to_string(index=False))
    else:
        print(f"  ⚠️  No data yet")
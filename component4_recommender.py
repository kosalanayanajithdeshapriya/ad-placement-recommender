"""
Component 4: Smart Recommender
- Loads ranked_candidates.json from Component 3
- Applies business rules to filter and finalize ad placement timestamps
- Outputs final_recommendations.json — the creator-ready result
"""

import json
import os

# ── Business Rule Config (tweak these per creator/video) ──
CONFIG = {
    "min_placement_score":    0.0,   # minimum ML score to consider
    "min_gap_seconds":        120,   # minimum 3 min between placements
    "skip_intro_pct":         0.20,  # skip first 20% of video
    "skip_outro_pct":         0.10,  # skip last 10% of video
    "max_placements":         3,     # max sponsored segments per video
    "short_video_threshold":  480,   # videos <= 8 min → max 1 placement
    "post_peak_bonus":        0.05,  # future: boost score if after sentiment peak
}

def load_ranked(path="ranked_candidates.json"):
    with open(path) as f:
        data = json.load(f)
    placements = data["ranked_placements"]
    # find total duration from highest timestamp as fallback
    total_duration = max(p["timestamp"] for p in placements) / 0.80
    print(f"[Component 4] Loaded {len(placements)} ranked candidates")
    print(f"  Estimated video duration: {int(total_duration//60)}m {int(total_duration%60)}s")
    return placements, total_duration

def apply_rules(placements, total_duration, config=CONFIG):
    print("\n[Applying Business Rules]")

    # Rule 1: Score threshold
    filtered = [p for p in placements if p["placement_score"] >= config["min_placement_score"]]
    print(f"  Rule 1 — Score >= {config['min_placement_score']}: {len(filtered)} passed")

    # Rule 2: Skip intro
    intro_cut = total_duration * config["skip_intro_pct"]
    filtered = [p for p in filtered if p["timestamp"] >= intro_cut]
    print(f"  Rule 2 — Skip intro ({int(config['skip_intro_pct']*100)}%, < {int(intro_cut)}s removed): {len(filtered)} remain")

    # Rule 3: Skip outro
    outro_cut = total_duration * (1 - config["skip_outro_pct"])
    filtered = [p for p in filtered if p["timestamp"] <= outro_cut]
    print(f"  Rule 3 — Skip outro ({int(config['skip_outro_pct']*100)}%, > {int(outro_cut)}s removed): {len(filtered)} remain")

    # Rule 4: Max placements for short videos
    max_allow = 1 if total_duration <= config["short_video_threshold"] else config["max_placements"]
    print(f"  Rule 4 — Max placements allowed: {max_allow}")

    # Rule 5: Minimum gap enforcement (greedy selection by score)
    selected = []
    for p in sorted(filtered, key=lambda x: x["placement_score"], reverse=True):
        if len(selected) >= max_allow:
            break
        too_close = any(abs(p["timestamp"] - s["timestamp"]) < config["min_gap_seconds"] for s in selected)
        if not too_close:
            selected.append(p)

    print(f"  Rule 5 — Min gap {config['min_gap_seconds']}s enforced: {len(selected)} final placements")
    return selected

def format_output(selected, total_duration, config=CONFIG):
    output = {
        "video_duration_seconds": round(total_duration, 1),
        "video_duration_formatted": f"{int(total_duration//60)}m {int(total_duration%60)}s",
        "total_placements_recommended": len(selected),
        "config_used": config,
        "recommendations": []
    }

    for i, p in enumerate(sorted(selected, key=lambda x: x["timestamp"])):
        output["recommendations"].append({
            "placement_number": i + 1,
            "timestamp_seconds": p["timestamp"],
            "timestamp_formatted": p["timestamp_formatted"],
            "type": p["type"],
            "placement_score": p["placement_score"],
            "retention_at_t": p["retention_at_t"],
            "confidence": (
                "HIGH"   if p["placement_score"] >= 0.75 else
                "MEDIUM" if p["placement_score"] >= 0.50 else
                "LOW"
            ),
            "creator_note": (
                f"Place sponsored segment at {p['timestamp_formatted']} — "
                f"natural {p['type'].replace('_', ' ')} detected, "
                f"{p['retention_at_t']:.1f}% viewers still watching."
            )
        })
    return output

def print_summary(output):
    print("\n" + "=" * 55)
    print("  FINAL RECOMMENDATIONS FOR CREATOR")
    print("=" * 55)
    print(f"  Video Duration : {output['video_duration_formatted']}")
    print(f"  Placements     : {output['total_placements_recommended']}")
    print()
    if not output["recommendations"]:
        print("  ⚠️  No suitable placement found.")
        print("  Suggestion: Lower min_placement_score in CONFIG")
        print("              or collect more video data for better ML labels.")
    else:
        for r in output["recommendations"]:
            print(f"  📍 Placement {r['placement_number']}")
            print(f"     Timestamp  : {r['timestamp_formatted']}")
            print(f"     Type       : {r['type']}")
            print(f"     Score      : {r['placement_score']} ({r['confidence']})")
            print(f"     Retention  : {r['retention_at_t']}% viewers watching")
            print(f"     Note       : {r['creator_note']}")
            print()

def run(ranked_path="ranked_candidates.json", output_path="final_recommendations.json"):
    print("=" * 55)
    print("  COMPONENT 4: SMART RECOMMENDER")
    print("=" * 55)
    placements, total_duration = load_ranked(ranked_path)
    selected = apply_rules(placements, total_duration)
    output = format_output(selected, total_duration)
    print_summary(output)
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"✅ Component 4 Complete!")
    print(f"   → {output_path}")
    print(f"   Next: python dashboard.py  (Streamlit visualization)")

if __name__ == "__main__":
    run()

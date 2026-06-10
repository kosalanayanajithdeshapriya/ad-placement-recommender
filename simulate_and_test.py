"""
Quick test: simulates candidates.json then runs Component 2
No real video or API needed — run this first to verify the pipeline.
"""
import json, numpy as np

total_duration = 600  # 10-minute video

# Simulate Component 1 output
np.random.seed(0)
candidates = []
for t in range(120, 540, 70):
    t += np.random.randint(-10, 10)
    candidates.append({
        "timestamp": float(t),
        "type": np.random.choice(["silence", "scene_change", "transcript_boundary"]),
        "score": round(np.random.uniform(0.5, 5.0), 3)
    })

with open("candidates.json", "w") as f:
    json.dump({"total_duration": total_duration, "candidates": candidates}, f, indent=2)

print("candidates.json created with", len(candidates), "candidates")
print("Now run: python component2_feature_extractor.py")

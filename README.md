---
title: Ad Placement Recommender
emoji: ??
colorFrom: indigo
colorTo: blue
sdk: streamlit
sdk_version: "1.30.0"
app_file: dashboard.py
pinned: false
---

# Retention-Aware Mid-Roll Ad Placement System

## Project Structure
`
project/
+-- requirements.txt
├── simulate_and_test.py       ← Start here (no video needed)
├── component1_candidate_generator.py
├── component2_feature_extractor.py
├── candidates.json            ← Output of Component 1
├── features.csv               ← Output of Component 2
└── README.md
```

## Quick Start
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Test the pipeline (no video or API needed)
python simulate_and_test.py
python component2_feature_extractor.py

# 3. Run on a real video
python component1_candidate_generator.py your_video.mp4
python component2_feature_extractor.py
```

## Phases
- [x] Phase 1 — Environment Setup
- [x] Phase 2 — Component 1: Candidate Generator
- [x] Phase 3 — Component 2: Feature Extractor (simulated retention)
- [ ] Phase 4 — Component 3: ML Ranker (LightGBM)
- [ ] Phase 5 — Component 4: Ad Placement Recommender
- [ ] Phase 6 — FastAPI + Dashboard
- [ ] Phase 7 — Evaluation + Research Paper

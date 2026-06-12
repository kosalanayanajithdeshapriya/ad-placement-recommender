# 📺 Ad Placement Recommender

> **AI-powered YouTube ad timestamp optimizer** — uses real viewer retention data and audio/video analysis to recommend the best moments to place ads, maximizing revenue while minimizing viewer drop-off.

***

## 🌟 Overview

The **Ad Placement Recommender** is a full-stack ML web application that helps YouTube content creators identify optimal timestamps to place advertisements in their videos.

Unlike conventional fixed-interval ad placement, this system analyzes **real viewer behavior data** and **video content signals** to recommend ad spots that maximize revenue while minimizing viewer disruption.

### Two Operating Modes

| Mode | Input | How It Works |
|------|-------|-------------|
| **Published Video Mode** | YouTube URL + Login | Fetches real retention curves from YouTube Analytics API |
| **Pre-Publish Prediction Mode** | Local video file | Simulates retention via Librosa audio energy analysis |

The **Pre-Publish Prediction Mode** is a first-of-its-kind capability — no existing YouTube creator tool lets you plan ad placement *before* a video goes live.

***

## 🚀 Live Demo

**[→ Try it at kosala2002-addplace.hf.space](https://kosala2002-addplace.hf.space)**

#Available for public ASAP !!!!!!!!!!

Log in with your Google account and paste any YouTube video URL to get instant recommendations.

***

## ✨ Key Features

- 🔐 **Google OAuth 2.0 + PKCE** — industry-standard secure authentication
- 📊 **Real-time retention analysis** — fetches actual viewer drop-off data from YouTube Analytics API v2
- 🎥 **Scene change detection** — OpenCV frame comparison (1 in every 5 frames for memory efficiency)
- 🔇 **Silence gap detection** — PyDub finds natural speech pauses (>800ms, <-40dB)
- 🤖 **LightGBM ML ranking** — trained on-the-fly per video, no pre-training needed
- 🎙️ **Whisper transcription** — speech-to-text for topic change boundary detection
- 🔮 **Pre-publish prediction** — Librosa audio energy simulation for unpublished videos
- 📈 **Interactive Plotly charts** — retention curve with ad spot markers overlaid
- 🎯 **Confidence scoring** — HIGH / MEDIUM / LOW rating per recommendation
- ⚙️ **Business rules engine** — configurable gap, intro/outro skipping, max placements
- 🌑 **Premium dark UI** — glassmorphism design with animated ambient effects
- ☁️ **Cloud deployed** — Hugging Face Spaces (16GB RAM, globally accessible)

***

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Streamlit Frontend                    │
│              (dashboard.py — Dark UI)                    │
└───────────────────────┬─────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
  ┌──────────┐   ┌──────────┐   ┌──────────────┐
  │YouTube   │   │YouTube   │   │  Local Video  │
  │Auth API  │   │Analytics │   │  (offline)    │
  │(OAuth2)  │   │API v2    │   │               │
  └──────────┘   └──────────┘   └──────────────┘
                        │
         ┌──────────────▼──────────────────┐
         │         ML Pipeline             │
         │                                 │
         │  Component 1: Candidate Gen     │
         │  (OpenCV scene + PyDub silence) │
         │              ↓                  │
         │  Component 2: Feature Extract   │
         │  (Retention curve + audio RMS)  │
         │              ↓                  │
         │  Component 3: LightGBM Ranking  │
         │  (placement_score per spot)     │
         │              ↓                  │
         │  Component 4: Business Rules    │
         │  (gap, intro/outro, max ads)    │
         └─────────────────────────────────┘
                        │
                        ▼
            Final Ad Spot Recommendations
         (timestamp, confidence, score, label)
```

***

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Streamlit + Custom CSS | Premium dark glassmorphism web UI |
| **ML Engine** | LightGBM | Candidate timestamp ranking & scoring |
| **Computer Vision** | OpenCV | Frame-level scene change detection |
| **Audio Analysis** | PyDub + Librosa | Silence detection & energy simulation |
| **NLP / Speech** | OpenAI Whisper | Speech transcription for topic boundaries |
| **Data API** | YouTube Analytics API v2 | Real viewer retention curve data |
| **Authentication** | Google OAuth 2.0 + PKCE | Secure user login & token management |
| **Visualization** | Plotly | Interactive retention charts with markers |
| **Deployment** | Hugging Face Spaces | Cloud hosting (16GB RAM, Docker) |

***

## ⚙️ Core Algorithm

### Step 1 — Candidate Generation
```
Video file → OpenCV samples every 5th frame
           → Compares frame brightness differences
           → Diff > threshold = scene change candidate
           → PyDub finds audio silence gaps (>800ms, <-40dB)
           → Deduplicates candidates within 5-second windows
```

### Step 2 — Feature Extraction
```
For each candidate timestamp:
  retention_at_t        ← % viewers still watching at t
  retention_drop_rate   ← rate of viewer loss before t
  retention_recovery    ← viewer stability after t
  relative_position     ← where in video (0.0–1.0)
  content_score         ← scene change magnitude
  time_since_last_ad    ← gap from previous candidate
```

### Step 3 — LightGBM Ranking
```
Features → LightGBM Classifier (100 estimators, max_depth=4)
         → Outputs placement_score (0.0–1.0)
         → Higher score = better ad placement moment
```

### Step 4 — Business Rules Engine
```
Rules applied in order:
  1. Score ≥ minimum threshold
  2. Skip first 20% of video (intro zone)
  3. Skip last 10% of video (outro zone)
  4. Minimum 120 seconds gap between ads
  5. Max 3 ads for videos > 8 minutes
  6. Max 1 ad for videos ≤ 8 minutes
```

### Pre-Publish Prediction (Offline Mode)
```python
# Load audio from local video file
audio, sr = librosa.load(video_path, sr=22050, mono=True)

# Calculate RMS energy per second
rms = librosa.feature.rms(y=audio, hop_length=sr)[0]

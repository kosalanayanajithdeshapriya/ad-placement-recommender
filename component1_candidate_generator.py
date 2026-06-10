import librosa
import cv2
import numpy as np
import whisper
import json
from pathlib import Path

SILENCE_THRESHOLD = 0.01
SILENCE_MIN_DURATION = 1.5   # seconds
SCENE_THRESHOLD = 30.0        # frame diff threshold
MIN_GAP_SECONDS = 60          # min gap between candidates

def detect_silence(audio_path):
    y, sr = librosa.load(audio_path, sr=None, mono=True)
    frame_length = int(sr * 0.1)
    hop_length = frame_length // 2
    rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
    times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop_length)
    candidates = []
    in_silence = False
    silence_start = 0
    for t, r in zip(times, rms):
        if r < SILENCE_THRESHOLD and not in_silence:
            in_silence = True
            silence_start = t
        elif r >= SILENCE_THRESHOLD and in_silence:
            duration = t - silence_start
            if duration >= SILENCE_MIN_DURATION:
                candidates.append({"timestamp": round(silence_start + duration / 2, 2),
                                   "type": "silence", "score": round(float(duration), 3)})
            in_silence = False
    return candidates

def detect_scene_changes(video_path):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    candidates = []
    prev_frame = None
    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if prev_frame is not None:
            diff = np.mean(np.abs(gray.astype(float) - prev_frame.astype(float)))
            if diff > SCENE_THRESHOLD:
                t = round(frame_idx / fps, 2)
                candidates.append({"timestamp": t, "type": "scene_change", "score": round(float(diff), 3)})
        prev_frame = gray
        frame_idx += 1
    cap.release()
    return candidates

def detect_transcript_boundaries(audio_path):
    model = whisper.load_model("base")
    result = model.transcribe(audio_path, word_timestamps=True)
    candidates = []
    segments = result.get("segments", [])
    for i in range(1, len(segments)):
        gap = segments[i]["start"] - segments[i-1]["end"]
        if gap > 1.0:
            t = round((segments[i-1]["end"] + segments[i]["start"]) / 2, 2)
            candidates.append({"timestamp": t, "type": "transcript_boundary", "score": round(gap, 3)})
    return candidates

def merge_candidates(all_candidates, total_duration, min_gap=MIN_GAP_SECONDS):
    all_candidates.sort(key=lambda x: x["timestamp"])
    # Remove candidates in first 20% and last 10%
    start_cut = total_duration * 0.20
    end_cut = total_duration * 0.90
    filtered = [c for c in all_candidates if start_cut <= c["timestamp"] <= end_cut]
    merged = []
    last_t = -min_gap
    for c in filtered:
        if c["timestamp"] - last_t >= min_gap:
            merged.append(c)
            last_t = c["timestamp"]
    return merged

def run(video_path, output_path="candidates.json"):
    print(f"[Component 1] Processing: {video_path}")
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    total_duration = frame_count / fps
    cap.release()
    silence = detect_silence(video_path)
    print(f"  Silence candidates: {len(silence)}")
    scene = detect_scene_changes(video_path)
    print(f"  Scene change candidates: {len(scene)}")
    transcript = detect_transcript_boundaries(video_path)
    print(f"  Transcript boundary candidates: {len(transcript)}")
    all_c = silence + scene + transcript
    merged = merge_candidates(all_c, total_duration)
    print(f"  Final merged candidates: {len(merged)}")
    with open(output_path, "w") as f:
        json.dump({"total_duration": total_duration, "candidates": merged}, f, indent=2)
    print(f"  Saved to {output_path}")
    return merged

if __name__ == "__main__":
    import sys
    video_path = sys.argv[1] if len(sys.argv) > 1 else "test_video.mp4"
    run(video_path)

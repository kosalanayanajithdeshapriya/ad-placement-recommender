"""
Dashboard — Creator-Friendly Ad Placement Recommender (Premium UI)
"""

import os
# Must be set BEFORE any other imports
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
import streamlit as st
import json
import math
import pandas as pd
import plotly.graph_objects as go
import base64
from PIL import Image
from youtube_auth import get_credentials, show_login_button, logout

# ── Page Config ──
st.set_page_config(
    page_title="Ad Placement Recommender",
    page_icon="🔮",
    layout="wide"
)

# ═══════════════════════════════════════════════════════════════
#  DESIGN SYSTEM — CSS
# ═══════════════════════════════════════════════════════════════
st.markdown("""
<style>
    /* ── Google Fonts ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    /* ── CSS Custom Properties ── */
    :root {
        --bg-primary: #0a0e1a;
        --bg-secondary: #0f1425;
        --bg-card: rgba(22, 28, 45, 0.65);
        --bg-card-solid: #161c2d;
        --border-glass: rgba(99, 102, 241, 0.15);
        --border-subtle: rgba(255, 255, 255, 0.06);
        --accent-indigo: #6366f1;
        --accent-purple: #8b5cf6;
        --accent-cyan: #22d3ee;
        --accent-pink: #ec4899;
        --success: #10b981;
        --success-glow: rgba(16, 185, 129, 0.25);
        --warning: #f59e0b;
        --warning-glow: rgba(245, 158, 11, 0.25);
        --danger: #ef4444;
        --danger-glow: rgba(239, 68, 68, 0.25);
        --text-primary: #f1f5f9;
        --text-secondary: #94a3b8;
        --text-muted: #64748b;
        --radius-sm: 8px;
        --radius-md: 14px;
        --radius-lg: 20px;
        --radius-xl: 28px;
        --glass-blur: 16px;
        --transition-fast: 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        --transition-smooth: 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    }

    /* ── Base ── */
    html, body, .stApp, [data-testid="stAppViewContainer"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        background: var(--bg-primary) !important;
        color: var(--text-primary) !important;
    }
    .stApp > header { background: transparent !important; }
    .main .block-container {
        padding-top: 2rem !important;
        max-width: 1200px;
    }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: var(--bg-primary); }
    ::-webkit-scrollbar-thumb { background: #2d3555; border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: #3d4570; }

    /* ── Fade-in Animation ── */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(18px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    @keyframes shimmer {
        0%   { background-position: -200% center; }
        100% { background-position: 200% center; }
    }
    @keyframes pulseGlow {
        0%, 100% { box-shadow: 0 0 20px rgba(99,102,241,0.15); }
        50%      { box-shadow: 0 0 35px rgba(99,102,241,0.3); }
    }
    @keyframes gradientShift {
        0%   { background-position: 0% 50%; }
        50%  { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    @keyframes float {
        0%, 100% { transform: translateY(0); }
        50%      { transform: translateY(-6px); }
    }
    @keyframes ringPulse {
        0%, 100% { filter: drop-shadow(0 0 3px rgba(99,102,241,0.3)); }
        50%      { filter: drop-shadow(0 0 8px rgba(99,102,241,0.6)); }
    }
    @keyframes orbFloat1 {
        0%   { transform: translate(0, 0) scale(1); }
        50%  { transform: translate(5vw, 10vh) scale(1.2); }
        100% { transform: translate(-5vw, 5vh) scale(0.9); }
    }
    @keyframes orbFloat2 {
        0%   { transform: translate(0, 0) scale(1); }
        50%  { transform: translate(-10vw, -5vh) scale(1.1); }
        100% { transform: translate(5vw, -10vh) scale(1); }
    }
    @keyframes progressPulse {
        0% { opacity: 0.6; box-shadow: 0 0 10px rgba(99,102,241,0.2); }
        50% { opacity: 1; box-shadow: 0 0 25px rgba(99,102,241,0.6); }
        100% { opacity: 0.6; box-shadow: 0 0 10px rgba(99,102,241,0.2); }
    }

    /* ── Ambient Background Orbs & Grid ── */
    [data-testid="stAppViewContainer"] {
        background-color: var(--bg-primary);
        background-image: 
            radial-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
            radial-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px);
        background-position: 0 0, 20px 20px;
        background-size: 40px 40px;
    }
    [data-testid="stAppViewContainer"]::before {
        content: ''; position: fixed; top: -10%; left: -10%; width: 50vw; height: 50vw;
        background: radial-gradient(circle, rgba(99,102,241,0.25) 0%, rgba(10,14,26,0) 60%);
        border-radius: 50%; filter: blur(80px); z-index: 0; pointer-events: none;
        animation: orbFloat1 20s infinite ease-in-out alternate;
    }
    [data-testid="stAppViewContainer"]::after {
        content: ''; position: fixed; bottom: -10%; right: -10%; width: 60vw; height: 60vw;
        background: radial-gradient(circle, rgba(34,211,238,0.2) 0%, rgba(10,14,26,0) 60%);
        border-radius: 50%; filter: blur(100px); z-index: 0; pointer-events: none;
        animation: orbFloat2 25s infinite ease-in-out alternate-reverse;
    }
    .main .block-container { z-index: 1; position: relative; }

    /* ── Hero Title ── */
    .hero-title {
        font-size: 2.6rem; font-weight: 900;
        background: linear-gradient(135deg, #6366f1, #8b5cf6, #22d3ee, #6366f1);
        background-size: 300% 300%;
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text;
        animation: gradientShift 6s ease infinite;
        letter-spacing: -0.03em;
        line-height: 1.2;
        margin-bottom: 0.3rem;
    }
    .hero-subtitle {
        font-size: 1.05rem; color: var(--text-secondary);
        font-weight: 400; line-height: 1.6;
        margin-bottom: 0.5rem;
    }
    .hero-accent-line {
        width: 60px; height: 3px; border-radius: 3px;
        background: linear-gradient(90deg, var(--accent-indigo), var(--accent-cyan));
        margin-bottom: 2rem;
    }

    /* ── Glass Card Base ── */
    .glass-card {
        background: rgba(22, 28, 45, 0.5); /* More transparent to show background */
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: var(--radius-lg);
        padding: 1.8rem;
        animation: fadeInUp 0.5s ease-out both;
        transition: transform var(--transition-fast), box-shadow var(--transition-fast);
    }
    .glass-card:hover {
        transform: translateY(-4px) scale(1.01);
        box-shadow: 0 15px 40px rgba(99,102,241,0.15), 0 0 20px rgba(99,102,241,0.05) inset;
        border-color: rgba(99,102,241,0.3);
    }

    /* ── Metric Cards ── */
    .metric-card {
        background: var(--bg-card);
        backdrop-filter: blur(var(--glass-blur));
        -webkit-backdrop-filter: blur(var(--glass-blur));
        border: 1px solid var(--border-glass);
        border-radius: var(--radius-md);
        padding: 1.4rem 1.2rem;
        text-align: center;
        position: relative;
        overflow: hidden;
        animation: fadeInUp 0.5s ease-out both;
        transition: transform var(--transition-fast), box-shadow var(--transition-fast);
    }
    .metric-card::before {
        content: '';
        position: absolute; top: 0; left: 0; right: 0;
        height: 3px;
        background: linear-gradient(90deg, var(--accent-indigo), var(--accent-purple));
    }
    .metric-card:hover {
        transform: translateY(-5px) scale(1.02);
        box-shadow: 0 15px 45px rgba(139,92,246,0.15), 0 0 15px rgba(139,92,246,0.05) inset;
        border-color: rgba(139,92,246,0.3);
    }
    .metric-icon {
        width: 42px; height: 42px; border-radius: 12px;
        display: inline-flex; align-items: center; justify-content: center;
        font-size: 1.3rem; margin-bottom: 0.7rem;
    }
    .metric-label {
        font-size: 0.78rem; font-weight: 500;
        color: var(--text-muted);
        text-transform: uppercase; letter-spacing: 0.06em;
        margin-bottom: 0.4rem;
    }
    .metric-value {
        font-size: 1.9rem; font-weight: 800;
        letter-spacing: -0.02em;
        line-height: 1.1;
    }

    /* ── Section Headers ── */
    .section-header {
        font-size: 1.35rem; font-weight: 700;
        color: var(--text-primary);
        margin: 2.5rem 0 0.6rem 0;
        display: flex; align-items: center; gap: 0.5rem;
    }
    .section-header::after {
        content: '';
        flex: 1; height: 1px;
        background: linear-gradient(90deg, var(--border-glass), transparent);
        margin-left: 1rem;
    }

    /* ── Placement Cards ── */
    .placement-card {
        background: var(--bg-card);
        backdrop-filter: blur(var(--glass-blur));
        -webkit-backdrop-filter: blur(var(--glass-blur));
        border: 1px solid rgba(16, 185, 129, 0.2);
        border-left: 4px solid var(--success);
        border-radius: var(--radius-md);
        padding: 1.6rem;
        margin-bottom: 1rem;
        animation: fadeInUp 0.5s ease-out both;
        transition: transform var(--transition-fast), box-shadow var(--transition-fast);
    }
    .placement-card:hover {
        transform: translateY(-4px) scale(1.01);
        box-shadow: 0 12px 35px var(--success-glow), 0 0 15px rgba(16,185,129,0.05) inset;
        border-color: rgba(16,185,129,0.4);
    }
    .placement-card-warn {
        background: var(--bg-card);
        backdrop-filter: blur(var(--glass-blur));
        -webkit-backdrop-filter: blur(var(--glass-blur));
        border: 1px solid rgba(245, 158, 11, 0.2);
        border-left: 4px solid var(--warning);
        border-radius: var(--radius-md);
        padding: 1.6rem;
        margin-bottom: 1rem;
        animation: fadeInUp 0.5s ease-out both;
        transition: all var(--transition-smooth);
    }
    .placement-card-warn:hover {
        transform: translateY(-4px) scale(1.01);
        box-shadow: 0 12px 35px var(--warning-glow), 0 0 15px rgba(245,158,11,0.05) inset;
        border-color: rgba(245,158,11,0.4);
    }
    .placement-card-bad {
        background: var(--bg-card);
        backdrop-filter: blur(var(--glass-blur));
        -webkit-backdrop-filter: blur(var(--glass-blur));
        border: 1px solid rgba(239, 68, 68, 0.2);
        border-left: 4px solid var(--danger);
        border-radius: var(--radius-md);
        padding: 1.6rem;
        margin-bottom: 1rem;
        animation: fadeInUp 0.5s ease-out both;
        transition: all var(--transition-smooth);
    }
    .placement-card-bad:hover {
        transform: translateY(-4px) scale(1.01);
        box-shadow: 0 12px 35px var(--danger-glow), 0 0 15px rgba(239,68,68,0.05) inset;
        border-color: rgba(239,68,68,0.4);
    }
    .placement-header {
        display: flex; justify-content: space-between;
        align-items: center; margin-bottom: 1rem;
    }
    .placement-title {
        font-size: 1.15rem; font-weight: 700; color: var(--text-primary);
    }
    .placement-timestamp {
        font-family: 'JetBrains Mono', 'Fira Code', monospace;
        background: rgba(99, 102, 241, 0.15);
        color: var(--accent-indigo);
        padding: 2px 10px; border-radius: 6px;
        font-size: 0.85rem; font-weight: 600;
    }
    .placement-body {
        display: flex; gap: 1.5rem; align-items: center;
        flex-wrap: wrap;
    }
    .placement-stats {
        flex: 1; display: flex; gap: 2rem; flex-wrap: wrap;
    }
    .stat-block .stat-label {
        font-size: 0.7rem; font-weight: 600;
        color: var(--text-muted);
        text-transform: uppercase; letter-spacing: 0.08em;
        margin-bottom: 0.2rem;
    }
    .stat-block .stat-value {
        font-size: 1.4rem; font-weight: 700; color: var(--text-primary);
    }
    .stat-block .stat-value-sm {
        font-size: 0.95rem; font-weight: 600; color: #cbd5e1;
    }

    /* ── SVG Retention Ring ── */
    .retention-ring-container {
        display: flex; align-items: center; justify-content: center;
        width: 80px; height: 80px;
        flex-shrink: 0;
        animation: ringPulse 3s ease-in-out infinite;
    }

    /* ── Badges ── */
    .badge {
        display: inline-flex; align-items: center; gap: 4px;
        padding: 4px 12px; border-radius: 20px;
        font-size: 0.75rem; font-weight: 600;
        letter-spacing: 0.03em;
    }
    .badge-green {
        background: rgba(16,185,129,0.15); color: #6ee7b7;
        border: 1px solid rgba(16,185,129,0.3);
    }
    .badge-yellow {
        background: rgba(245,158,11,0.15); color: #fde68a;
        border: 1px solid rgba(245,158,11,0.3);
    }
    .badge-red {
        background: rgba(239,68,68,0.15); color: #fca5a5;
        border: 1px solid rgba(239,68,68,0.3);
    }

    /* ── Tip Box ── */
    .tip-box {
        background: rgba(99,102,241,0.06);
        border: 1px solid rgba(99,102,241,0.12);
        border-radius: var(--radius-sm);
        padding: 1rem 1.2rem;
        margin-top: 1rem;
        font-size: 0.88rem; color: #cbd5e1;
        line-height: 1.65;
    }
    .tip-box b { color: var(--text-primary); }

    /* ── Insight Alert Cards ── */
    .insight-card {
        background: var(--bg-card);
        backdrop-filter: blur(var(--glass-blur));
        border: 1px solid var(--border-glass);
        border-radius: var(--radius-sm);
        padding: 0.9rem 1.1rem;
        margin-bottom: 0.6rem;
        display: flex; align-items: flex-start; gap: 0.7rem;
        font-size: 0.9rem; line-height: 1.55;
        animation: fadeInUp 0.4s ease-out both;
    }
    .insight-icon {
        font-size: 1.1rem; flex-shrink: 0; margin-top: 1px;
    }
    .insight-text { color: #cbd5e1; }
    .insight-text strong { color: var(--text-primary); }

    /* ── Login Page ── */
    .login-card {
        background: var(--bg-card);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid var(--border-glass);
        border-radius: var(--radius-xl);
        padding: 3rem 2.5rem;
        text-align: center;
        max-width: 500px; margin: 2rem auto;
        animation: fadeInUp 0.6s ease-out both;
        position: relative;
        overflow: hidden;
    }
    .login-card::before {
        content: '';
        position: absolute; top: -1px; left: 20%; right: 20%;
        height: 2px;
        background: linear-gradient(90deg, transparent, var(--accent-indigo), var(--accent-cyan), transparent);
    }
    .login-icon {
        width: 72px; height: 72px;
        background: linear-gradient(135deg, rgba(99,102,241,0.2), rgba(139,92,246,0.2));
        border: 1px solid rgba(99,102,241,0.3);
        border-radius: 20px; margin: 0 auto 1.5rem auto;
        display: flex; align-items: center; justify-content: center;
        font-size: 2rem;
        animation: float 3s ease-in-out infinite;
    }
    .login-title {
        font-size: 1.4rem; font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 0.6rem;
    }
    .login-desc {
        color: var(--text-secondary); font-size: 0.92rem;
        line-height: 1.6; margin-bottom: 1.5rem;
    }
    .trust-badges {
        display: flex; justify-content: center; gap: 0.6rem;
        flex-wrap: wrap; margin-bottom: 1.8rem;
    }
    .trust-badge {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 20px; padding: 5px 14px;
        font-size: 0.75rem; color: var(--text-secondary);
        font-weight: 500;
    }
    .login-btn {
        display: block;
        background: linear-gradient(135deg, #ef4444, #dc2626);
        color: white !important; border-radius: var(--radius-md);
        padding: 1rem 2rem;
        font-size: 1.05rem; font-weight: 700;
        text-align: center; text-decoration: none !important;
        transition: transform var(--transition-fast), box-shadow var(--transition-fast);
        box-shadow: 0 4px 20px rgba(239,68,68,0.25);
    }
    .login-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(239,68,68,0.35);
    }
    .login-trust-line {
        margin-top: 1.2rem;
        font-size: 0.82rem; color: var(--success);
        font-weight: 500;
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d1220 0%, #0a0e1a 100%) !important;
        border-right: 1px solid var(--border-subtle) !important;
    }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        font-family: 'Inter', sans-serif !important;
    }
    .sidebar-status {
        background: rgba(16,185,129,0.1);
        border: 1px solid rgba(16,185,129,0.25);
        border-radius: var(--radius-sm);
        padding: 0.7rem 1rem;
        display: flex; align-items: center; gap: 0.6rem;
        font-size: 0.88rem; color: #6ee7b7; font-weight: 600;
        margin-bottom: 1rem;
    }
    .sidebar-status-dot {
        width: 8px; height: 8px; border-radius: 50%;
        background: var(--success);
        box-shadow: 0 0 6px var(--success);
    }
    .sidebar-step {
        display: flex; align-items: flex-start; gap: 0.7rem;
        margin-bottom: 0.8rem;
    }
    .sidebar-step-num {
        width: 24px; height: 24px; border-radius: 50%;
        background: rgba(99,102,241,0.15);
        border: 1px solid rgba(99,102,241,0.3);
        display: flex; align-items: center; justify-content: center;
        font-size: 0.72rem; font-weight: 700; color: var(--accent-indigo);
        flex-shrink: 0; margin-top: 1px;
    }
    .sidebar-step-text {
        font-size: 0.88rem; color: var(--text-secondary); line-height: 1.4;
    }

    /* ── Streamlit Overrides ── */
    .stButton > button {
        font-family: 'Inter', sans-serif !important;
        background: linear-gradient(135deg, var(--accent-indigo), var(--accent-purple)) !important;
        color: white !important;
        border: none !important;
        border-radius: var(--radius-md) !important;
        padding: 0.7rem 2rem !important;
        font-size: 1rem !important; font-weight: 600 !important;
        letter-spacing: 0.01em;
        transition: transform var(--transition-fast), box-shadow var(--transition-fast) !important;
        box-shadow: 0 4px 15px rgba(99,102,241,0.25);
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(99,102,241,0.35) !important;
    }
    .stTextInput > div > div > input {
        font-family: 'Inter', sans-serif !important;
        background: var(--bg-card-solid) !important;
        border: 1px solid var(--border-glass) !important;
        border-radius: var(--radius-sm) !important;
        color: var(--text-primary) !important;
        padding: 0.7rem 1rem !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: var(--accent-indigo) !important;
        box-shadow: 0 0 0 2px rgba(99,102,241,0.2) !important;
    }
    [data-testid="stFileUploader"] {
        font-family: 'Inter', sans-serif !important;
    }
    [data-testid="stFileUploader"] section {
        background: var(--bg-card-solid) !important;
        border: 1px dashed var(--border-glass) !important;
        border-radius: var(--radius-sm) !important;
        padding: 1rem !important;
    }
    .stProgress > div > div > div {
        background: linear-gradient(90deg, var(--accent-indigo), var(--accent-cyan)) !important;
        border-radius: 10px !important;
    }
    [data-testid="stExpander"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-glass) !important;
        border-radius: var(--radius-md) !important;
    }
    [data-testid="stExpander"] summary {
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
    }
    .stDataFrame {
        border-radius: var(--radius-sm) !important;
        overflow: hidden;
    }

    /* ── Divider ── */
    .gradient-divider {
        height: 1px; border: none;
        background: linear-gradient(90deg, transparent, var(--border-glass), transparent);
        margin: 2rem 0;
    }

    /* ── Footer ── */
    .footer {
        text-align: center; padding: 2rem 0 1rem 0;
        color: var(--text-muted); font-size: 0.8rem;
    }
    .footer-brand {
        font-weight: 600;
        background: linear-gradient(90deg, var(--accent-indigo), var(--accent-cyan));
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text;
    }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════
def get_spot_quality(retention):
    if retention >= 50:
        return "✦", "Great Spot",  "placement-card",      "badge-green"
    elif retention >= 30:
        return "◆", "Decent Spot", "placement-card-warn", "badge-yellow"
    else:
        return "▼", "Weak Spot",   "placement-card-bad",  "badge-red"

def get_type_label(t):
    return {
        "scene_change":        "🎬 Scene Break",
        "silence":             "🔇 Quiet Moment",
        "transcript_boundary": "🗣️ Topic Change"
    }.get(t, t)

def get_type_tip(t):
    return {
        "scene_change":        "The video visually transitions here — viewers naturally expect a brief pause. Perfect for a sponsorship read.",
        "silence":             "There's a quiet gap in audio here — inserting an ad won't feel jarring or cut off speech.",
        "transcript_boundary": "The speaker shifts to a new topic — a natural mental break for the viewer."
    }.get(t, "Natural break detected in the video.")

def extract_video_id(url):
    import re
    for pattern in [r"youtu\.be/([^?&]+)", r"youtube\.com/watch\?v=([^&]+)"]:
        m = re.search(pattern, url)
        if m:
            return m.group(1)
    if re.match(r'^[A-Za-z0-9_-]{11}$', url.strip()):
        return url.strip()
    return None

def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)

def build_retention_ring(percent, color, size=76):
    """Generate an SVG donut ring for retention percentage."""
    radius = 30
    circumference = 2 * math.pi * radius
    offset = circumference - (percent / 100) * circumference
    return f"""
    <svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">
        <circle cx="{size//2}" cy="{size//2}" r="{radius}"
                fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="6"/>
        <circle cx="{size//2}" cy="{size//2}" r="{radius}"
                fill="none" stroke="{color}" stroke-width="6"
                stroke-linecap="round"
                stroke-dasharray="{circumference}"
                stroke-dashoffset="{offset}"
                transform="rotate(-90 {size//2} {size//2})"
                style="transition: stroke-dashoffset 1s ease-out;"/>
        <text x="{size//2}" y="{size//2 + 1}" text-anchor="middle"
              dominant-baseline="middle" fill="{color}"
              font-size="14" font-weight="800"
              font-family="Inter, sans-serif">{percent:.0f}%</text>
    </svg>"""

def get_favicon_base64():
    return "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EREREREREREREREREREREREREREREREREREREREREREREZGsAPwHz0lJrfIIp0sAAAAASUVORK5CYII="


# ═══════════════════════════════════════════════════════════════
#  HERO HEADER
# ═══════════════════════════════════════════════════════════════
favicon_b64 = get_favicon_base64()
icon_html = f'<img src="data:image/png;base64,{favicon_b64}" style="height:1.2em; vertical-align:middle; margin-right:0.3rem;" />' if favicon_b64 else "🔮"

st.markdown(f"""
<div style="animation: fadeInUp 0.5s ease-out both;">
    <div class="hero-title">{icon_html} Ad Placement Recommender</div>
    <div class="hero-subtitle">
        Find the perfect moments in your video to place ads — so viewers stay happy and you earn more.
    </div>
    <div class="hero-accent-line"></div>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
#  AUTH GATE
# ═══════════════════════════════════════════════════════════════
creds = get_credentials()

if creds is None:
    st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        auth_url = show_login_button()
        st.markdown(f"""
        <div class="login-card">
            <div class="login-icon">🔗</div>
            <div class="login-title">Connect Your YouTube Account</div>
            <div class="login-desc">
                We need read-only access to your YouTube Analytics
                to see where viewers drop off in your videos.
            </div>
            <div class="trust-badges">
                <span class="trust-badge">🔒 Read-Only Access</span>
                <span class="trust-badge">🛡️ 256-bit Encrypted</span>
                <span class="trust-badge">🚫 No Data Stored</span>
            </div>
            <a href="{auth_url}" target="_self" class="login-btn">
                ▶ &nbsp; Sign in with YouTube
            </a>
            <div class="login-trust-line">
                ✓ &nbsp; We never post, modify, or delete anything
            </div>
        </div>
        """, unsafe_allow_html=True)
    st.stop()


# ═══════════════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### 👤 Account")
    st.markdown("""
    <div class="sidebar-status">
        <div class="sidebar-status-dot"></div>
        YouTube Connected
    </div>
    """, unsafe_allow_html=True)
    if st.button("🚪 Logout"):
        logout()
        st.rerun()
    st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)
    st.markdown("### ℹ️ How It Works")
    steps = [
        ("1", "🔗 Paste your YouTube video URL"),
        ("2", "🎬 Upload the same video as <code>.mp4</code>"),
        ("3", "🚀 Click <strong>Analyze</strong>"),
        ("4", "📍 See exactly where to place ads"),
    ]
    for num, text in steps:
        st.markdown(f"""
        <div class="sidebar-step">
            <div class="sidebar-step-num">{num}</div>
            <div class="sidebar-step-text">{text}</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        '<div style="text-align:center;color:var(--text-muted);font-size:0.75rem;">'
        'Ad Placement Recommender<br>Built for YouTube Creators</div>',
        unsafe_allow_html=True
    )


# ═══════════════════════════════════════════════════════════════
#  INPUT FORM
# ═══════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">📥 Analyze Your Video</div>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 1])
with col1:
    yt_input = st.text_input(
        "🔗 YouTube Video URL",
        placeholder="https://youtu.be/4Rq-LY16WxM",
        help="Must be YOUR video — we need access to its analytics"
    )
with col2:
    uploaded_file = st.file_uploader(
        "🎬 Upload Your Video File (.mp4)",
        type=["mp4"],
        help="Upload the same video you posted on YouTube"
    )

analyze_btn = st.button("🚀 Analyze My Video & Find Best Ad Spots")

if analyze_btn:
    if not yt_input or not uploaded_file:
        st.warning("⚠️ Please provide both your YouTube URL and upload your video file.")
    else:
        video_id = extract_video_id(yt_input)
        if not video_id:
            st.error("❌ Could not extract video ID. Please check your YouTube URL.")
        else:
            os.makedirs("test_video", exist_ok=True)
            save_path = os.path.join("test_video", uploaded_file.name)
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            from pipeline import run_full_pipeline

            # Custom loading UI
            loading_container = st.empty()
            
            # Use columns to center the animation
            with loading_container.container():
                st.markdown("""
                <div class="glass-card" style="text-align:center; padding:3rem; margin:2rem 0; animation: progressPulse 2s infinite;">
                    <div style="font-size:2.5rem; animation: float 3s infinite ease-in-out; margin-bottom:1rem;">🔮</div>
                    <div style="font-size:1.3rem; font-weight:700; color:var(--text-primary); margin-bottom:0.5rem;">
                        Analyzing Video Content...
                    </div>
                    <div style="color:var(--accent-cyan); font-size:0.95rem; font-weight:600;" id="loading-msg">
                        Processing frames and audio
                    </div>
                </div>
                """, unsafe_allow_html=True)
                progress_bar = st.progress(0)

            steps_done   = [0]

            def on_progress(msg):
                steps_done[0] += 1
                progress_bar.progress(min(steps_done[0] / 4, 1.0))

            try:
                run_full_pipeline(save_path, video_id, creds, progress_callback=on_progress)
                progress_bar.progress(1.0)
                loading_container.empty()
                st.session_state["analysis_done"] = True
                st.rerun()
            except Exception as e:
                st.error(f"❌ Pipeline error: {str(e)}")
                st.info("💡 Make sure your video is public or unlisted and belongs to your connected YouTube channel.")

st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
#  LOAD RESULTS
# ═══════════════════════════════════════════════════════════════
# Only show results if the user has analyzed a video in this session
if not st.session_state.get("analysis_done", False):
    data = None
else:
    data = load_json("final_recommendations.json")
candidates = load_json("ranked_candidates.json") if st.session_state.get("analysis_done") else None
retention  = load_json("retention_curve.json") if st.session_state.get("analysis_done") else None

if not data:
    st.markdown("""
    <div class="glass-card" style="text-align:center;padding:3rem;">
        <div style="font-size:2.5rem;margin-bottom:0.8rem;">📹</div>
        <div style="font-size:1.1rem;font-weight:600;color:var(--text-primary);margin-bottom:0.4rem;">
            Ready to analyze your video
        </div>
        <div style="color:var(--text-secondary);font-size:0.92rem;">
            Enter your YouTube URL and upload your video above to get started.
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

recs         = data.get("recommendations", [])
duration     = data.get("video_duration_formatted", "N/A")
total_placed = data.get("total_placements_recommended", 0)
cands_list   = candidates.get("ranked_placements", []) if candidates else []
top_ret      = max((c["retention_at_t"] for c in cands_list), default=0)


# ═══════════════════════════════════════════════════════════════
#  METRICS
# ═══════════════════════════════════════════════════════════════
metrics_data = [
    ("🎬", "Video Duration",      duration,         "#e2e8f0",  "rgba(99,102,241,0.15)"),
    ("📍", "Ad Spots Found",      str(total_placed), "#10b981" if total_placed > 0 else "#ef4444", "rgba(16,185,129,0.15)" if total_placed > 0 else "rgba(239,68,68,0.15)"),
    ("🔬", "Moments Analyzed",    str(len(cands_list)), "#e2e8f0", "rgba(99,102,241,0.15)"),
    ("👀", "Best Retention",      f"{top_ret:.0f}%", "#10b981" if top_ret >= 50 else "#f59e0b", "rgba(16,185,129,0.15)" if top_ret >= 50 else "rgba(245,158,11,0.15)"),
]

m1, m2, m3, m4 = st.columns(4)
for i, (col, (icon, label, value, color, icon_bg)) in enumerate(zip([m1, m2, m3, m4], metrics_data)):
    with col:
        st.markdown(f"""
        <div class="metric-card" style="animation-delay:{i*0.1}s;">
            <div class="metric-icon" style="background:{icon_bg};">{icon}</div>
            <div class="metric-label">{label}</div>
            <div class="metric-value" style="color:{color};">{value}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
#  RETENTION CURVE
# ═══════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">📈 Viewer Retention Curve</div>', unsafe_allow_html=True)
st.caption("How many viewers are still watching at each moment. Markers show recommended ad spots.")

if retention:
    times  = [p["time_seconds"]      for p in retention]
    values = [p["retention_percent"] for p in retention]

    fig = go.Figure()

    # Main retention line
    fig.add_trace(go.Scatter(
        x=times, y=values, mode="lines",
        name="Viewer Retention",
        line=dict(color="#6366f1", width=3, shape="spline", smoothing=1.2),
        fill="tozeroy",
        fillgradient=dict(
            type="vertical",
            colorscale=[
                [0.0, "rgba(99,102,241,0.0)"],
                [1.0, "rgba(99,102,241,0.2)"]
            ]
        ),
        hovertemplate="<b>%{x:.0f}s</b><br>Retention: %{y:.1f}%<extra></extra>"
    ))

    # Ad spot markers
    spot_colors = ["#10b981", "#f59e0b", "#ef4444"]
    for i, r in enumerate(recs):
        color = spot_colors[i % len(spot_colors)]
        ts = r["timestamp_seconds"]
        # Find approximate retention at this timestamp
        ret_val = r.get("retention_at_t", 50)

        fig.add_trace(go.Scatter(
            x=[ts], y=[ret_val],
            mode="markers+text",
            marker=dict(
                symbol="diamond", size=14, color=color,
                line=dict(width=2, color="white")
            ),
            text=[f"Ad {r['placement_number']}"],
            textposition="top center",
            textfont=dict(color=color, size=12, family="Inter"),
            hovertemplate=f"<b>Ad Spot {r['placement_number']}</b><br>{r['timestamp_formatted']}<br>Retention: {ret_val:.1f}%<extra></extra>",
            showlegend=False
        ))

        fig.add_vline(
            x=ts, line_dash="dot",
            line_color=color, line_width=1.5,
            opacity=0.5
        )

    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94a3b8", family="Inter"),
        height=400,
        xaxis=dict(
            title="Time (seconds)",
            gridcolor="rgba(255,255,255,0.04)",
            zeroline=False,
            tickfont=dict(size=11)
        ),
        yaxis=dict(
            title="Viewers Still Watching (%)",
            gridcolor="rgba(255,255,255,0.04)",
            range=[0, 105],
            zeroline=False,
            tickfont=dict(size=11)
        ),
        margin=dict(l=10, r=10, t=20, b=40),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02,
            xanchor="right", x=1,
            bgcolor="rgba(0,0,0,0)"
        ),
        hoverlabel=dict(
            bgcolor="#161c2d",
            bordercolor="#6366f1",
            font_size=13,
            font_family="Inter"
        )
    )
    st.plotly_chart(fig, use_container_width=True)

st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
#  RECOMMENDATIONS
# ═══════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">🎯 Where to Place Your Ads</div>', unsafe_allow_html=True)

if not recs:
    st.markdown("""
    <div class="glass-card" style="text-align:center;">
        <div style="font-size:2.2rem;margin-bottom:0.5rem;">😕</div>
        <div style="font-size:1.1rem;color:#f87171;font-weight:600;margin-bottom:0.4rem;">
            No strong ad spots found for this video
        </div>
        <div style="color:var(--text-secondary);font-size:0.9rem;">
            This usually means viewer retention dropped too quickly.<br>
            Try a video where viewers watch past the halfway point.
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    for idx, r in enumerate(recs):
        emoji, quality, card_class, badge_class = get_spot_quality(r["retention_at_t"])
        type_label = get_type_label(r["type"])
        type_tip   = get_type_tip(r["type"])
        ret        = r["retention_at_t"]
        conf       = r["confidence"]
        conf_color = "#10b981" if conf == "HIGH" else "#f59e0b" if conf == "MEDIUM" else "#94a3b8"

        # Ring color based on retention quality
        ring_color = "#10b981" if ret >= 50 else "#f59e0b" if ret >= 30 else "#ef4444"
        ring_svg   = build_retention_ring(ret, ring_color)

        st.markdown(f"""
        <div class="{card_class}" style="animation-delay:{idx*0.12}s;">
            <div class="placement-header">
                <div>
                    <span class="placement-title">📍 Ad Spot {r['placement_number']}</span>
                    &nbsp;&nbsp;
                    <span class="placement-timestamp">{r['timestamp_formatted']}</span>
                </div>
                <span class="badge {badge_class}">{emoji} {quality}</span>
            </div>
            <div class="placement-body">
                <div class="placement-stats">
                    <div class="stat-block">
                        <div class="stat-label">VIEWERS WATCHING</div>
                        <div class="stat-value" style="color:{ring_color};">{ret:.0f}%</div>
                    </div>
                    <div class="stat-block">
                        <div class="stat-label">BREAK TYPE</div>
                        <div class="stat-value-sm">{type_label}</div>
                    </div>
                    <div class="stat-block">
                        <div class="stat-label">CONFIDENCE</div>
                        <div class="stat-value-sm" style="color:{conf_color};">{conf}</div>
                    </div>
                </div>
                <div class="retention-ring-container">
                    {ring_svg}
                </div>
            </div>
            <div class="tip-box">
                💡 <b>Why this spot?</b> {type_tip}<br><br>
                🎬 <b>What to do:</b> Place your sponsorship or enable mid-roll at <b>{r['timestamp_formatted']}</b>.
                At this moment, <b>{ret:.0f}% of your audience</b> is still watching.
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
#  INSIGHTS FOR NEXT VIDEO
# ═══════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">📊 Insights for Your Next Video</div>', unsafe_allow_html=True)

if cands_list:
    df         = pd.DataFrame(cands_list)
    best_ret   = df["retention_at_t"].max()
    worst_ret  = df["retention_at_t"].min()
    avg_ret    = df["retention_at_t"].mean()
    drop_time  = df.loc[df["retention_at_t"].idxmin(), "timestamp_formatted"]

    insight_metrics = [
        ("🏆", "Peak Retention",    f"{best_ret:.0f}%", "#10b981", "rgba(16,185,129,0.15)", "viewers at best moment"),
        ("📉", "Biggest Drop-Off",  drop_time,          "#ef4444", "rgba(239,68,68,0.15)",  "most viewers left here"),
        ("📊", "Avg Retention",     f"{avg_ret:.0f}%",  "#f59e0b", "rgba(245,158,11,0.15)", "across all break points"),
    ]

    i1, i2, i3 = st.columns(3)
    for i, (col, (icon, label, value, color, icon_bg, sub)) in enumerate(zip([i1, i2, i3], insight_metrics)):
        with col:
            st.markdown(f"""
            <div class="metric-card" style="animation-delay:{i*0.1}s;">
                <div class="metric-icon" style="background:{icon_bg};">{icon}</div>
                <div class="metric-label">{label}</div>
                <div class="metric-value" style="color:{color};">{value}</div>
                <div style="color:var(--text-muted);font-size:0.78rem;margin-top:0.3rem;">{sub}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-header" style="font-size:1.1rem;">💡 What This Means for Your Next Video</div>', unsafe_allow_html=True)

    tips = []
    if best_ret >= 60:
        tips.append(("✅", "Strong early retention — your intro hooks viewers well. Keep doing what you did in the first 2 minutes."))
    if worst_ret < 25:
        tips.append(("⚠️", f"Viewers drop off near <strong>{drop_time}</strong> — tighten that section or add a re-engagement hook."))
    if avg_ret < 35:
        tips.append(("📉", "Overall retention is low — try shorter videos or stronger pacing."))
    if avg_ret >= 50:
        tips.append(("🎉", "Great overall retention — you can confidently place ads and expect good visibility."))
    if total_placed == 0:
        tips.append(("🔴", "No strong ad spots this time — aim to keep 40%+ viewers watching past the 2-minute mark."))

    for icon, text in tips:
        st.markdown(f"""
        <div class="insight-card">
            <div class="insight-icon">{icon}</div>
            <div class="insight-text">{text}</div>
        </div>
        """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
#  ADVANCED TABLE
# ═══════════════════════════════════════════════════════════════
st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)
with st.expander("🔬 View All Analyzed Moments (Advanced)"):
    if cands_list:
        df_show = pd.DataFrame(cands_list)[["timestamp_formatted", "type", "retention_at_t", "placement_score"]]
        df_show.columns = ["Timestamp", "Break Type", "Viewers Watching (%)", "ML Score"]
        df_show["Break Type"]           = df_show["Break Type"].map(get_type_label)
        df_show["Viewers Watching (%)"] = df_show["Viewers Watching (%)"].map(lambda x: f"{x:.1f}%")
        df_show["ML Score"]             = df_show["ML Score"].map(lambda x: f"{x:.4f}")
        st.dataframe(df_show, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════
#  FOOTER
# ═══════════════════════════════════════════════════════════════
st.markdown("""
<div class="gradient-divider"></div>
<div class="footer">
    <span class="footer-brand">Ad Placement Recommender</span>
    &nbsp;·&nbsp; Built with ❤️ for YouTube Creators
</div>
""", unsafe_allow_html=True)
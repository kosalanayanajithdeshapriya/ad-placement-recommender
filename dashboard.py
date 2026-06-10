"""
Dashboard — Creator-Friendly Ad Placement Recommender
Full OAuth login + integrated pipeline (no subprocess)
"""

import streamlit as st
import json
import os
import pandas as pd
import plotly.graph_objects as go
from youtube_auth import get_credentials, show_login_button, logout

# ── Page Config ──
st.set_page_config(
    page_title="Ad Placement Recommender",
    page_icon="🎯",
    layout="wide"
)

# ── Custom CSS ──
st.markdown("""
<style>
    .main { background-color: #0e1117; }
    .big-title { font-size:2.2rem; font-weight:800; color:#ffffff; }
    .subtitle  { font-size:1rem; color:#aaaaaa; margin-bottom:2rem; }
    .metric-box {
        background:#1c1f26; border-radius:12px;
        padding:1.2rem; text-align:center;
    }
    .metric-label { font-size:0.85rem; color:#888; margin-bottom:4px; }
    .metric-value { font-size:2rem; font-weight:700; color:#ffffff; }
    .placement-card {
        background:#1a2a1a; border:1px solid #2a5a2a;
        border-radius:12px; padding:1.4rem; margin-bottom:1rem;
    }
    .placement-card-warn {
        background:#2a2a1a; border:1px solid #5a5a2a;
        border-radius:12px; padding:1.4rem; margin-bottom:1rem;
    }
    .placement-card-bad {
        background:#2a1a1a; border:1px solid #5a2a2a;
        border-radius:12px; padding:1.4rem; margin-bottom:1rem;
    }
    .tip-box {
        background:#111827; border-left:4px solid #3b82f6;
        border-radius:8px; padding:1rem; margin-top:0.5rem;
        font-size:0.9rem; color:#cbd5e1;
    }
    .section-header {
        font-size:1.3rem; font-weight:700;
        color:#ffffff; margin:2rem 0 1rem 0;
    }
    .badge-green  { background:#166534; color:#86efac; padding:3px 10px; border-radius:20px; font-size:0.8rem; }
    .badge-yellow { background:#713f12; color:#fde68a; padding:3px 10px; border-radius:20px; font-size:0.8rem; }
    .badge-red    { background:#7f1d1d; color:#fca5a5; padding:3px 10px; border-radius:20px; font-size:0.8rem; }
    .stButton>button {
        background:linear-gradient(135deg,#3b82f6,#8b5cf6);
        color:white; border:none; border-radius:10px;
        padding:0.7rem 2rem; font-size:1rem; font-weight:600;
        width:100%; cursor:pointer;
    }
    .login-card {
        background:#1c1f26; border-radius:16px;
        padding:2.5rem; text-align:center; max-width:480px; margin:auto;
    }
</style>
""", unsafe_allow_html=True)

# ── Handle post-login rerun FIRST (before anything else) ──
if "just_logged_in" in st.session_state:
    del st.session_state["just_logged_in"]
    st.rerun()

# ── Helpers ──
def get_spot_quality(retention):
    if retention >= 50:
        return "🟢", "Great Spot",  "placement-card",      "badge-green"
    elif retention >= 30:
        return "🟡", "Decent Spot", "placement-card-warn", "badge-yellow"
    else:
        return "🔴", "Weak Spot",   "placement-card-bad",  "badge-red"

def get_type_label(t):
    return {
        "scene_change":        "🎬 Natural scene break",
        "silence":             "🔇 Quiet moment",
        "transcript_boundary": "🗣️ Topic change"
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

# ══════════════════════════════════════════════
#  HEADER
# ══════════════════════════════════════════════
st.markdown('<div class="big-title">🎯 Ad Placement Recommender</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Find the perfect moments in your video to place ads — so viewers stay happy and you earn more.</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════
#  AUTH GATE
# ══════════════════════════════════════════════
creds = get_credentials()

if creds is None:
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div class="login-card">
            <div style="font-size:3rem;">🔐</div>
            <div style="font-size:1.3rem;font-weight:700;color:#fff;margin:1rem 0;">
                Connect Your YouTube Account
            </div>
            <div style="color:#9ca3af;font-size:0.9rem;margin-bottom:1.5rem;">
                We need read-only access to your YouTube Analytics<br>
                to see where viewers drop off in your videos.<br><br>
                <b style="color:#6ee7b7;">We never post, modify or delete anything.</b>
            </div>
        </div>
        """, unsafe_allow_html=True)

        auth_url = show_login_button()
        st.markdown(f"""
        <a href="{auth_url}" target="_self" style="text-decoration:none;">
            <div style="
                background:linear-gradient(135deg,#ff0000,#cc0000);
                color:white; border-radius:12px; padding:1rem 2rem;
                font-size:1.1rem; font-weight:700; text-align:center;
                margin-top:1.5rem; cursor:pointer;
            ">
                🎬 Login with YouTube
            </div>
        </a>
        """, unsafe_allow_html=True)
    st.stop()

# ── Sidebar (logged in) ──
with st.sidebar:
    st.markdown("### 👤 Account")
    st.success("✅ YouTube Connected")
    if st.button("🚪 Logout"):
        logout()
        st.rerun()
    st.markdown("---")
    st.markdown("### ℹ️ How It Works")
    st.markdown("""
    1. 🔗 Paste your YouTube video URL
    2. 🎬 Upload the same video as `.mp4`
    3. 🚀 Click Analyze
    4. 📍 See exactly where to place ads
    """)

# ══════════════════════════════════════════════
#  INPUT FORM
# ══════════════════════════════════════════════
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

            progress_box = st.empty()
            progress_bar = st.progress(0)
            steps_done   = [0]

            def on_progress(msg):
                progress_box.info(msg)
                steps_done[0] += 1
                progress_bar.progress(min(steps_done[0] / 4, 1.0))

            try:
                with st.spinner("Analyzing your video... this takes 2–4 minutes ⏳"):
                    run_full_pipeline(save_path, video_id, creds, progress_callback=on_progress)
                progress_bar.progress(1.0)
                progress_box.success("✅ Analysis complete!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Pipeline error: {str(e)}")
                st.info("💡 Make sure your video is public or unlisted and belongs to your connected YouTube channel.")

st.markdown("---")

# ══════════════════════════════════════════════
#  LOAD RESULTS
# ══════════════════════════════════════════════
data       = load_json("final_recommendations.json")
candidates = load_json("ranked_candidates.json")
retention  = load_json("retention_curve.json")

if not data:
    st.info("👆 Enter your YouTube URL and upload your video above to get started.")
    st.stop()

recs         = data.get("recommendations", [])
duration     = data.get("video_duration_formatted", "N/A")
total_placed = data.get("total_placements_recommended", 0)
cands_list   = candidates.get("ranked_placements", []) if candidates else []
top_ret      = max((c["retention_at_t"] for c in cands_list), default=0)

# ══════════════════════════════════════════════
#  METRICS
# ══════════════════════════════════════════════
m1, m2, m3, m4 = st.columns(4)
for col, label, value, color in [
    (m1, "🎬 Video Duration",      duration,           "#ffffff"),
    (m2, "📍 Best Ad Spots Found", total_placed,       "#22c55e" if total_placed > 0 else "#ef4444"),
    (m3, "🔬 Moments Analyzed",    len(cands_list),    "#ffffff"),
    (m4, "👀 Best Spot Retention", f"{top_ret:.0f}%",  "#22c55e" if top_ret >= 50 else "#f59e0b"),
]:
    with col:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">{label}</div>
            <div class="metric-value" style="color:{color};">{value}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ══════════════════════════════════════════════
#  RETENTION CURVE
# ══════════════════════════════════════════════
st.markdown('<div class="section-header">📈 Your Viewer Retention Curve</div>', unsafe_allow_html=True)
st.caption("This shows how many viewers are still watching at each moment. Markers show recommended ad spots.")

if retention:
    times  = [p["time_seconds"]      for p in retention]
    values = [p["retention_percent"] for p in retention]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=times, y=values, mode="lines",
        name="Viewer Retention",
        line=dict(color="#6366f1", width=2),
        fill="tozeroy", fillcolor="rgba(99,102,241,0.15)"
    ))

    colors = ["#22c55e", "#f59e0b", "#ef4444"]
    for i, r in enumerate(recs):
        color = colors[i % len(colors)]
        fig.add_vline(
            x=r["timestamp_seconds"], line_dash="dash",
            line_color=color, line_width=2,
            annotation_text=f"📍 Ad {r['placement_number']} ({r['timestamp_formatted']})",
            annotation_font_color=color
        )

    fig.update_layout(
        plot_bgcolor="#0e1117", paper_bgcolor="#0e1117",
        font_color="white", height=380,
        xaxis=dict(title="Time (seconds)", gridcolor="#1f2937"),
        yaxis=dict(title="Viewers Still Watching (%)", gridcolor="#1f2937", range=[0, 105]),
        margin=dict(l=20, r=20, t=30, b=40)
    )
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ══════════════════════════════════════════════
#  RECOMMENDATIONS
# ══════════════════════════════════════════════
st.markdown('<div class="section-header">🎯 Where to Place Your Ad</div>', unsafe_allow_html=True)

if not recs:
    st.markdown("""
    <div style="background:#1c1f26;border-radius:12px;padding:1.5rem;text-align:center;">
        <div style="font-size:2rem;">😕</div>
        <div style="font-size:1.1rem;color:#f87171;font-weight:600;margin:0.5rem 0;">
            No strong ad spots found for this video
        </div>
        <div style="color:#9ca3af;font-size:0.9rem;">
            This usually means viewer retention dropped too quickly.<br>
            Try a video where viewers watch past the halfway point.
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    for r in recs:
        emoji, quality, card_class, badge_class = get_spot_quality(r["retention_at_t"])
        type_label = get_type_label(r["type"])
        type_tip   = get_type_tip(r["type"])
        ret        = r["retention_at_t"]
        conf_color = "#22c55e" if r["confidence"] == "HIGH" else "#f59e0b" if r["confidence"] == "MEDIUM" else "#94a3b8"

        st.markdown(f"""
        <div class="{card_class}">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.8rem;">
                <div style="font-size:1.2rem;font-weight:700;color:#ffffff;">
                    📍 Ad Spot {r['placement_number']} &nbsp;—&nbsp; {r['timestamp_formatted']}
                </div>
                <span class="{badge_class}">{emoji} {quality}</span>
            </div>
            <div style="display:flex;gap:2rem;margin-bottom:0.8rem;flex-wrap:wrap;">
                <div>
                    <div style="color:#888;font-size:0.8rem;">VIEWERS WATCHING</div>
                    <div style="font-size:1.5rem;font-weight:700;color:#ffffff;">{ret:.0f}%</div>
                </div>
                <div>
                    <div style="color:#888;font-size:0.8rem;">BREAK TYPE</div>
                    <div style="font-size:1rem;font-weight:600;color:#e2e8f0;">{type_label}</div>
                </div>
                <div>
                    <div style="color:#888;font-size:0.8rem;">CONFIDENCE</div>
                    <div style="font-size:1rem;font-weight:600;color:{conf_color};">{r['confidence']}</div>
                </div>
            </div>
            <div class="tip-box">
                💡 <b>Why this spot?</b> {type_tip}<br><br>
                🎬 <b>What to do:</b> Place your sponsorship or enable mid-roll at <b>{r['timestamp_formatted']}</b>.
                At this moment, <b>{ret:.0f}% of your audience</b> is still watching.
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# ══════════════════════════════════════════════
#  INSIGHTS FOR NEXT VIDEO
# ══════════════════════════════════════════════
st.markdown('<div class="section-header">📊 Insights for Your Next Video</div>', unsafe_allow_html=True)

if cands_list:
    df = pd.DataFrame(cands_list)
    best_ret  = df["retention_at_t"].max()
    worst_ret = df["retention_at_t"].min()
    avg_ret   = df["retention_at_t"].mean()
    drop_time = df.loc[df["retention_at_t"].idxmin(), "timestamp_formatted"]

    i1, i2, i3 = st.columns(3)
    for col, label, value, color, sub in [
        (i1, "🏆 Peak Retention Spot",     f"{best_ret:.0f}%", "#22c55e", "viewers at best moment"),
        (i2, "📉 Biggest Drop-Off At",     drop_time,          "#ef4444", "most viewers left here"),
        (i3, "📊 Avg Retention at Breaks", f"{avg_ret:.0f}%",  "#f59e0b", "across all detected moments"),
    ]:
        with col:
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-label">{label}</div>
                <div class="metric-value" style="color:{color};">{value}</div>
                <div style="color:#888;font-size:0.8rem;">{sub}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 💡 What This Means for Your Next Video")

    tips = []
    if best_ret >= 60:
        tips.append("✅ **Strong early retention** — your intro hooks viewers well. Keep doing what you did in the first 2 minutes.")
    if worst_ret < 25:
        tips.append(f"⚠️ **Viewers drop off near {drop_time}** — tighten that section or add a re-engagement hook.")
    if avg_ret < 35:
        tips.append("📉 **Overall retention is low** — try shorter videos or stronger pacing.")
    if avg_ret >= 50:
        tips.append("🎉 **Great overall retention** — you can confidently place ads and expect good visibility.")
    if total_placed == 0:
        tips.append("🔴 **No strong ad spots this time** — aim to keep 40%+ viewers watching past the 2-minute mark.")

    for tip in tips:
        st.markdown(f"- {tip}")

# ══════════════════════════════════════════════
#  ADVANCED TABLE
# ══════════════════════════════════════════════
st.markdown("---")
with st.expander("🔬 View All Analyzed Moments (Advanced)"):
    if cands_list:
        df_show = pd.DataFrame(cands_list)[["timestamp_formatted", "type", "retention_at_t", "placement_score"]]
        df_show.columns = ["Timestamp", "Break Type", "Viewers Watching (%)", "ML Score"]
        df_show["Break Type"]           = df_show["Break Type"].map(get_type_label)
        df_show["Viewers Watching (%)"] = df_show["Viewers Watching (%)"].map(lambda x: f"{x:.1f}%")
        df_show["ML Score"]             = df_show["ML Score"].map(lambda x: f"{x:.4f}")
        st.dataframe(df_show, use_container_width=True, hide_index=True)

# ── Footer ──
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    '<div style="text-align:center;color:#4b5563;font-size:0.8rem;">Ad Placement Recommender • Built for YouTube Creators</div>',
    unsafe_allow_html=True
)
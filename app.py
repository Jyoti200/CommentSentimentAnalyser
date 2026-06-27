import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from utils import extract_video_id, get_video_info
from fetch_comments import get_comments
from analyze_comments import analyze_sentiment
from database import save_analysis, get_history, get_trend

# ─── Page Config ───────────────────────────────────────────────
st.set_page_config(
    page_title="CommentPulse — YouTube Sentiment Analyzer",
    page_icon="📊",
    layout="wide"
)

# ─── Custom CSS ────────────────────────────────────────────────
st.markdown("""
<style>
    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* App background */
    .stApp { background-color: #0f0f0f; }

    /* Header */
    .hero-title {
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(135deg, #ff0000, #ff6b6b);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }
    .hero-sub {
        color: #aaaaaa;
        font-size: 1.1rem;
        margin-top: 0.2rem;
        margin-bottom: 2rem;
    }

    /* Metric cards */
    .metric-card {
        background: #1a1a1a;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        border: 1px solid #2a2a2a;
        text-align: center;
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        margin: 0;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #888;
        margin: 0;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .positive { color: #4ade80; }
    .neutral  { color: #60a5fa; }
    .negative { color: #f87171; }

    /* Video info card */
    .video-card {
        background: #1a1a1a;
        border-radius: 12px;
        padding: 1rem 1.5rem;
        border: 1px solid #2a2a2a;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        gap: 1rem;
    }

    /* Input styling */
    .stTextInput input {
        background: #1a1a1a !important;
        border: 1px solid #333 !important;
        color: white !important;
        border-radius: 8px !important;
        font-size: 1rem !important;
        padding: 0.7rem 1rem !important;
    }

    /* Button */
    .stButton button {
        background: linear-gradient(135deg, #ff0000, #cc0000) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 0.6rem 2rem !important;
        font-size: 1rem !important;
        width: 100%;
    }
    .stButton button:hover {
        opacity: 0.9 !important;
    }

    /* History table */
    .history-row {
        background: #1a1a1a;
        border-radius: 8px;
        padding: 0.8rem 1rem;
        margin-bottom: 0.5rem;
        border: 1px solid #2a2a2a;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab"] {
        color: #888 !important;
    }
    .stTabs [aria-selected="true"] {
        color: #ff4444 !important;
        border-bottom-color: #ff4444 !important;
    }

    /* Warning/info */
    .stAlert { border-radius: 8px !important; }
</style>
""", unsafe_allow_html=True)

COLOR_MAP = {
    'positive': '#4ade80',
    'negative': '#f87171',
    'neutral':  '#60a5fa'
}

# ─── Header ────────────────────────────────────────────────────
st.markdown('<p class="hero-title">CommentPulse</p>', unsafe_allow_html=True)
st.markdown('<p class="hero-sub">Instant sentiment analysis for any YouTube video</p>', unsafe_allow_html=True)

# ─── Input ─────────────────────────────────────────────────────
col_input, col_btn = st.columns([5, 1])
with col_input:
    url_input = st.text_input(
        label="video_url",
        placeholder="Paste any YouTube URL — e.g. https://youtube.com/watch?v=...",
        label_visibility="collapsed"
    )
with col_btn:
    analyze_clicked = st.button("Analyze", use_container_width=True)

# ─── Analysis ──────────────────────────────────────────────────
if analyze_clicked:
    if not url_input.strip():
        st.warning("Paste a YouTube URL above to get started.")
    else:
        video_id = extract_video_id(url_input)

        if not video_id:
            st.error("Couldn't find a video ID in that URL. Try: https://youtube.com/watch?v=VIDEO_ID")
        else:
            with st.spinner("Fetching comments and analyzing sentiment..."):
                # Get video metadata
                video_info = get_video_info(video_id)

                # Fetch and analyze
                comments = get_comments(video_id)

                if not comments:
                    st.error("No comments found. The video may have comments disabled or is private.")
                else:
                    results = analyze_sentiment(comments)

                    # Save to DB
                    save_analysis(
                        video_id=video_id,
                        video_title=video_info.get("title", "Unknown"),
                        sentiment_summary=results["summary"],
                        comments=results["comments"]
                    )

                    # Store in session for display
                    st.session_state["last_results"] = {
                        "video_info": video_info,
                        "summary": results["summary"],
                        "comments": results["comments"],
                        "video_id": video_id
                    }

# ─── Results Display ───────────────────────────────────────────
if "last_results" in st.session_state:
    r = st.session_state["last_results"]
    summary = r["summary"]
    video_info = r["video_info"]
    comments = r["comments"]

    total = sum(summary.values()) or 1

    # Video info
    if video_info.get("title"):
        st.markdown(f"""
        <div class="video-card">
            <div>
                <div style="font-weight:600; font-size:1.05rem; color:white">▶ {video_info['title']}</div>
                <div style="color:#888; font-size:0.85rem">{video_info.get('channel', '')} · {len(comments):,} comments analyzed</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Metrics
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <p class="metric-value positive">{summary.get('positive', 0):,}</p>
            <p class="metric-label">😊 Positive</p>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="metric-card">
            <p class="metric-value neutral">{summary.get('neutral', 0):,}</p>
            <p class="metric-label">😐 Neutral</p>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="metric-card">
            <p class="metric-value negative">{summary.get('negative', 0):,}</p>
            <p class="metric-label">😞 Negative</p>
        </div>""", unsafe_allow_html=True)
    with c4:
        score = round((summary.get('positive', 0) / total) * 100)
        color = "#4ade80" if score >= 60 else "#f87171" if score < 40 else "#60a5fa"
        st.markdown(f"""
        <div class="metric-card">
            <p class="metric-value" style="color:{color}">{score}%</p>
            <p class="metric-label">🎯 Positivity Score</p>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Charts + Comments
    tab1, tab2, tab3 = st.tabs(["📊 Breakdown", "💬 Sample Comments", "📈 Trend"])

    with tab1:
        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            summary_df = pd.DataFrame([
                {"Sentiment": k, "Count": v} for k, v in summary.items()
            ])
            fig = px.pie(
                summary_df,
                values="Count",
                names="Sentiment",
                color="Sentiment",
                color_discrete_map=COLOR_MAP,
                hole=0.5
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#ffffff",
                legend=dict(font=dict(color="#aaaaaa")),
                margin=dict(t=20, b=20)
            )
            st.plotly_chart(fig, use_container_width=True)

        with chart_col2:
            fig2 = go.Figure(go.Bar(
                x=list(summary.keys()),
                y=list(summary.values()),
                marker_color=[COLOR_MAP.get(k, '#888') for k in summary.keys()],
                text=[f"{(v/total*100):.1f}%" for v in summary.values()],
                textposition="outside"
            ))
            fig2.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#ffffff",
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=False, color="#aaa"),
                margin=dict(t=20, b=20)
            )
            st.plotly_chart(fig2, use_container_width=True)

    with tab2:
        if comments:
            comments_df = pd.DataFrame(comments)
            for sentiment_type, emoji in [("positive", "😊"), ("negative", "😞"), ("neutral", "😐")]:
                filtered = comments_df[comments_df["sentiment"] == sentiment_type].head(3)
                if not filtered.empty:
                    st.markdown(f"**{emoji} {sentiment_type.capitalize()} comments**")
                    for _, row in filtered.iterrows():
                        st.markdown(f"""
                        <div style="background:#1a1a1a; border-left: 3px solid {COLOR_MAP[sentiment_type]};
                             padding: 0.7rem 1rem; border-radius: 0 8px 8px 0; margin-bottom: 0.5rem; color: #ddd;">
                            {row['text'][:200]}{'...' if len(row['text']) > 200 else ''}
                        </div>""", unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)

    with tab3:
        trend_data = get_trend(r["video_id"])
        if trend_data and len(trend_data) > 1:
            trend_df = pd.DataFrame(trend_data)
            fig3 = px.line(
                trend_df,
                x="date",
                y="count",
                color="sentiment",
                color_discrete_map=COLOR_MAP,
                markers=True,
                labels={"count": "Comments", "date": "Date"}
            )
            fig3.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#ffffff",
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=False),
            )
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("Analyze this video multiple times over different days to see the sentiment trend.")

# ─── Recent Analyses History ───────────────────────────────────
st.markdown("---")
st.markdown("### 🕘 Recently Analyzed")

history = get_history(limit=8)
if history:
    for row in history:
        total_h = (row["positive"] + row["neutral"] + row["negative"]) or 1
        score_h = round((row["positive"] / total_h) * 100)
        color_h = "#4ade80" if score_h >= 60 else "#f87171" if score_h < 40 else "#60a5fa"
        st.markdown(f"""
        <div class="history-row">
            <div>
                <span style="color:white; font-weight:500">{row['video_title'][:55]}{'...' if len(row['video_title']) > 55 else ''}</span>
                <br><span style="color:#666; font-size:0.8rem">{row['analyzed_at'][:10]}</span>
            </div>
            <div style="text-align:right">
                <span style="color:{color_h}; font-weight:700; font-size:1.1rem">{score_h}%</span>
                <br><span style="color:#666; font-size:0.8rem">positive</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.markdown('<p style="color:#555">No analyses yet — paste a YouTube URL above!</p>', unsafe_allow_html=True)

# Footer
st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<p style="color:#333; text-align:center; font-size:0.8rem">CommentPulse · Free · No login required</p>', unsafe_allow_html=True)

import os
from datetime import datetime
from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

if not (SUPABASE_URL and SUPABASE_KEY):
    raise RuntimeError(
        "SUPABASE_URL and SUPABASE_KEY must be set (Streamlit Cloud secrets) "
        "for persistent storage."
    )

_sb = create_client(SUPABASE_URL, SUPABASE_KEY)

def save_analysis(video_id: str, video_title: str, sentiment_summary: dict):
    """Save one sentiment snapshot for a video (call this each time you analyze it)."""
    positive = sentiment_summary.get("positive", 0)
    neutral  = sentiment_summary.get("neutral", 0)
    negative = sentiment_summary.get("negative", 0)
    total    = positive + neutral + negative

    _sb.table("analyses").insert({
        "video_id":    video_id,
        "video_title": video_title,
        "positive":    positive,
        "neutral":     neutral,
        "negative":    negative,
        "total":       total,
        "analyzed_at": datetime.utcnow().isoformat()
    }).execute()

def get_video_history(video_id: str) -> list[dict]:
    """Get all past sentiment snapshots for one specific video, oldest first."""
    result = _sb.table("analyses")\
        .select("video_title, positive, neutral, negative, total, analyzed_at")\
        .eq("video_id", video_id)\
        .order("analyzed_at")\
        .execute()
    return result.data or []

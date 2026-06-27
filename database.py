import os
import sqlite3
from datetime import datetime

# ─── Config ────────────────────────────────────────────────────
# Set SUPABASE_URL and SUPABASE_KEY in Streamlit Cloud secrets for production.
# Falls back to local SQLite for local development automatically.
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
USE_SUPABASE  = bool(SUPABASE_URL and SUPABASE_KEY)

LOCAL_DB = "comments_analysis.db"

# ─── Local SQLite Setup ────────────────────────────────────────
def _init_local_db():
    with sqlite3.connect(LOCAL_DB) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT,
                video_title TEXT,
                positive INTEGER,
                neutral INTEGER,
                negative INTEGER,
                total INTEGER,
                analyzed_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT,
                text TEXT,
                sentiment TEXT,
                score REAL,
                analyzed_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

_init_local_db()

# ─── Supabase Setup ────────────────────────────────────────────
def _get_supabase():
    from supabase import create_client
    return create_client(SUPABASE_URL, SUPABASE_KEY)

# ─── Public API ────────────────────────────────────────────────
def save_analysis(video_id: str, video_title: str, sentiment_summary: dict, comments: list):
    """Save analysis results. Uses Supabase in production, SQLite locally."""
    positive = sentiment_summary.get("positive", 0)
    neutral  = sentiment_summary.get("neutral", 0)
    negative = sentiment_summary.get("negative", 0)
    total    = positive + neutral + negative

    if USE_SUPABASE:
        try:
            sb = _get_supabase()
            # Save summary
            result = sb.table("analyses").insert({
                "video_id":    video_id,
                "video_title": video_title,
                "positive":    positive,
                "neutral":     neutral,
                "negative":    negative,
                "total":       total,
                "analyzed_at": datetime.utcnow().isoformat()
            }).execute()

            # Save individual comments (up to 50)
            rows = [{
                "video_id":    video_id,
                "text":        c["text"][:500],
                "sentiment":   c["sentiment"],
                "score":       c["score"],
                "analyzed_at": datetime.utcnow().isoformat()
            } for c in comments[:50]]
            if rows:
                sb.table("comments").insert(rows).execute()
            return
        except Exception as e:
            print(f"Supabase error, falling back to SQLite: {e}")

    # Local SQLite fallback
    with sqlite3.connect(LOCAL_DB) as conn:
        conn.execute("""
            INSERT INTO analyses (video_id, video_title, positive, neutral, negative, total)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (video_id, video_title, positive, neutral, negative, total))

        rows = [(video_id, c["text"][:500], c["sentiment"], c["score"]) for c in comments[:50]]
        conn.executemany("""
            INSERT INTO comments (video_id, text, sentiment, score)
            VALUES (?, ?, ?, ?)
        """, rows)


def get_history(limit: int = 8) -> list[dict]:
    """Get recent analyses for the history panel."""
    if USE_SUPABASE:
        try:
            sb = _get_supabase()
            result = sb.table("analyses")\
                .select("video_title, positive, neutral, negative, analyzed_at")\
                .order("analyzed_at", desc=True)\
                .limit(limit)\
                .execute()
            return result.data or []
        except Exception as e:
            print(f"Supabase error: {e}")

    # Local SQLite
    with sqlite3.connect(LOCAL_DB) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""
            SELECT video_title, positive, neutral, negative, analyzed_at
            FROM analyses
            ORDER BY analyzed_at DESC
            LIMIT ?
        """, (limit,)).fetchall()
        return [dict(r) for r in rows]


def get_trend(video_id: str) -> list[dict]:
    """Get sentiment trend over time for a specific video."""
    if USE_SUPABASE:
        try:
            sb = _get_supabase()
            result = sb.table("analyses")\
                .select("positive, neutral, negative, analyzed_at")\
                .eq("video_id", video_id)\
                .order("analyzed_at")\
                .execute()

            rows = []
            for r in (result.data or []):
                date = r["analyzed_at"][:10]
                rows.append({"date": date, "count": r["positive"],  "sentiment": "positive"})
                rows.append({"date": date, "count": r["neutral"],   "sentiment": "neutral"})
                rows.append({"date": date, "count": r["negative"],  "sentiment": "negative"})
            return rows
        except Exception as e:
            print(f"Supabase error: {e}")

    # Local SQLite
    with sqlite3.connect(LOCAL_DB) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""
            SELECT date(analyzed_at) as date, positive, neutral, negative
            FROM analyses
            WHERE video_id = ?
            ORDER BY analyzed_at
        """, (video_id,)).fetchall()

        result = []
        for r in rows:
            result.append({"date": r["date"], "count": r["positive"],  "sentiment": "positive"})
            result.append({"date": r["date"], "count": r["neutral"],   "sentiment": "neutral"})
            result.append({"date": r["date"], "count": r["negative"],  "sentiment": "negative"})
        return result

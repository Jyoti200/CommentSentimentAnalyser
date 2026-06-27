# CommentPulse 📊
Instant sentiment analysis for any YouTube video — free to use, free to deploy.

## Local Setup

```bash
pip install -r requirements.txt
streamlit run app.py
```

For local dev, no API keys needed — it uses mock comments and SQLite automatically.

## Deploy to Streamlit Cloud (Free)

1. Push this folder to a GitHub repo
2. Go to share.streamlit.io → New app → select your repo → set `app.py` as main file
3. Add these secrets in Streamlit Cloud dashboard (Settings → Secrets):

```toml
YOUTUBE_API_KEY = "your_youtube_api_key_here"
SUPABASE_URL    = "https://xxxx.supabase.co"
SUPABASE_KEY    = "your_supabase_anon_key_here"
```

## Get Free API Keys

### YouTube Data API v3 (free — 10,000 units/day)
1. Go to console.cloud.google.com
2. Create project → Enable "YouTube Data API v3"
3. Credentials → Create API Key → copy it

### Supabase (free — 500MB, unlimited requests)
1. Go to supabase.com → New project
2. Go to SQL Editor → run this to create tables:

```sql
CREATE TABLE analyses (
    id BIGSERIAL PRIMARY KEY,
    video_id TEXT,
    video_title TEXT,
    positive INTEGER,
    neutral INTEGER,
    negative INTEGER,
    total INTEGER,
    analyzed_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE comments (
    id BIGSERIAL PRIMARY KEY,
    video_id TEXT,
    text TEXT,
    sentiment TEXT,
    score REAL,
    analyzed_at TIMESTAMPTZ DEFAULT NOW()
);
```

3. Go to Settings → API → copy "Project URL" and "anon public" key

## File Structure

```
├── app.py              # Main Streamlit dashboard
├── utils.py            # URL parsing + video metadata
├── fetch_comments.py   # YouTube API comment fetching
├── analyze_comments.py # Hugging Face sentiment model (free, no API cost)
├── database.py         # Supabase (prod) + SQLite (local) storage
└── requirements.txt    # Dependencies
```

## How it works

```
User pastes URL → extract video ID → fetch comments (YouTube API)
                                           ↓
                              analyze sentiment (Hugging Face, free)
                                           ↓
                              save to Supabase → show results
```

## Free Tier Limits

| Service | Free Limit | This app uses |
|---|---|---|
| YouTube API | 10,000 units/day | ~2 units per analysis |
| Hugging Face model | Unlimited (runs locally) | 0 API calls |
| Supabase | 500MB storage | ~1KB per analysis |
| Streamlit Cloud | Unlimited | — |

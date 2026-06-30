import os
from dotenv import load_dotenv
from googleapiclient.discovery import build
load_dotenv()
MAX_COMMENTS = 200

def get_comments(video_id: str) -> list[dict]:
    YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")  # read at call time
    if not YOUTUBE_API_KEY:
        print("Warning: No YOUTUBE_API_KEY set. Using mock data.")
        return _mock_comments()
    try:
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        comments = []
        next_page_token = None
        while len(comments) < MAX_COMMENTS:
            response = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=min(100, MAX_COMMENTS - len(comments)),
                pageToken=next_page_token,
                textFormat="plainText",
                order="relevance"
            ).execute()
            for item in response.get("items", []):
                snippet = item["snippet"]["topLevelComment"]["snippet"]
                comments.append({
                    "text": snippet["textDisplay"],
                    "published_at": snippet["publishedAt"],   # e.g. "2024-05-12T14:23:01Z"
                    "updated_at": snippet.get("updatedAt"),   # in case it was edited
                })
            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break
        return comments
    except Exception as e:
        error_msg = str(e)
        if "commentsDisabled" in error_msg:
            return []
        if "quotaExceeded" in error_msg:
            raise RuntimeError("YouTube API quota exceeded. Try again tomorrow (resets at midnight PT).")
        raise RuntimeError(f"Failed to fetch comments: {error_msg}")

def _mock_comments() -> list[dict]:
    from datetime import datetime, timedelta, timezone
    base = datetime.now(timezone.utc)
    texts = [
        "This video is absolutely amazing, learned so much!",
        "Not really what I expected, kind of disappointed.",
        "Great explanation, very clear and well structured.",
        "I have watched this 3 times already, so good!",
        "Meh, nothing special here.",
        "This changed how I think about this topic completely.",
        "The editing could be better but content is solid.",
        "Terrible, waste of time.",
        "One of the best videos on this topic, highly recommend.",
        "Pretty average, seen better.",
    ] * 10
    return [
        {"text": t, "published_at": (base - timedelta(hours=i)).isoformat(), "updated_at": None}
        for i, t in enumerate(texts)
    ]

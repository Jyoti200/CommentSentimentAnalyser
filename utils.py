import re
import os
from dotenv import load_dotenv
from googleapiclient.discovery import build

load_dotenv()

def extract_video_id(url: str) -> str | None:
    """Extract video ID from any YouTube URL format."""
    patterns = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",
        r"(?:embed\/)([0-9A-Za-z_-]{11})",
        r"(?:youtu\.be\/)([0-9A-Za-z_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_video_info(video_id: str) -> dict:
    """Fetch video title and channel name from YouTube API."""
    YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")  # now read at call time
    if not YOUTUBE_API_KEY:
        return {"title": f"Video ({video_id})", "channel": ""}
    try:
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        response = youtube.videos().list(
            part="snippet",
            id=video_id
        ).execute()

        if response["items"]:
            snippet = response["items"][0]["snippet"]
            return {
                "title": snippet.get("title", "Unknown"),
                "channel": snippet.get("channelTitle", "")
            }
    except Exception as e:
        print(f"Error fetching video info: {e}")
    return {"title": f"Video ({video_id})", "channel": ""}
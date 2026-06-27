from textblob import TextBlob

def analyze_sentiment(comments: list[str]) -> dict:
    """
    Analyze sentiment using TextBlob.
    Lightweight — no torch, no API, works everywhere.
    TextBlob polarity: -1.0 (negative) to +1.0 (positive)
    """
    if not comments:
        return {"summary": {"positive": 0, "neutral": 0, "negative": 0}, "comments": []}

    summary = {"positive": 0, "neutral": 0, "negative": 0}
    analyzed_comments = []

    for comment in comments:
        polarity = TextBlob(comment).sentiment.polarity

        if polarity > 0.1:
            sentiment = "positive"
        elif polarity < -0.1:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        summary[sentiment] += 1
        analyzed_comments.append({
            "text": comment,
            "sentiment": sentiment,
            "score": round(polarity, 3)
        })

    return {
        "summary": summary,
        "comments": analyzed_comments
    }

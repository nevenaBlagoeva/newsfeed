from datetime import datetime, timezone

# --------------------------
# Predefined keyword sets
# --------------------------
HIGH_PRIORITY_KEYWORDS = {
    "cybersecurity", "security", "data breach", "vulnerability", "exploit",
    "malware", "ransomware", "phishing", "ddos", "incident", "threat"
}

MEDIUM_PRIORITY_KEYWORDS = {
    "server", "network", "cloud", "aws", "azure", "gcp", "downtime", "outage",
    "patch", "update", "application", "api"
}

LOW_PRIORITY_KEYWORDS = {
    "python", "ai", "machine learning", "ml", "docker", "kubernetes", "software"
}

# Priority points
PRIORITY_POINTS = {"high": 10, "medium": 6, "low": 3}
TITLE_MULTIPLIER = 3


# --------------------------
# Recency scoring function
# --------------------------
def recency_points(published_at: str, max_points: int = 10) -> int:
    """
    Assign points 1-10 based on how recent the item is.
    Most recent items get max_points, oldest get 1.
    """
    try:
        dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        age_hours = (datetime.now(timezone.utc) - dt).total_seconds() / 3600
        max_hours = 30 * 24  # 30 days
        points = max(1, min(max_points, int(round(max_points * (1 - age_hours / max_hours)))))
        return points
    except Exception:
        return 1

# --------------------------
# Keyword scoring function
# --------------------------
def calculate_keyword_relevance_score(item: dict) -> float:
    """
    Calculate a relevance score (0-1) for a news item based on:
    - Keyword matches (high/medium/low priority)
    - Title multiplier
    - Recency points

    Args:
        item (dict): Must contain 'title', 'body', 'published_at'

    Returns:
        float: Normalized relevance score (0.0 - 1.0)
    """
    title = item.get("title", "").lower().split()
    body = item.get("body", "").lower().split()

    # Title keyword points
    kw_title_points = sum(PRIORITY_POINTS["high"] for w in title if w in HIGH_PRIORITY_KEYWORDS) * TITLE_MULTIPLIER
    kw_title_points += sum(PRIORITY_POINTS["medium"] for w in title if w in MEDIUM_PRIORITY_KEYWORDS) * TITLE_MULTIPLIER
    kw_title_points += sum(PRIORITY_POINTS["low"] for w in title if w in LOW_PRIORITY_KEYWORDS) * TITLE_MULTIPLIER

    # Body keyword points
    kw_body_points = sum(PRIORITY_POINTS["high"] for w in body if w in HIGH_PRIORITY_KEYWORDS)
    kw_body_points += sum(PRIORITY_POINTS["medium"] for w in body if w in MEDIUM_PRIORITY_KEYWORDS)
    kw_body_points += sum(PRIORITY_POINTS["low"] for w in body if w in LOW_PRIORITY_KEYWORDS)

    # Recency points
    rec_pts = recency_points(item.get("published_at", ""))

    total_points = kw_title_points + kw_body_points + rec_pts

    # Normalize to 0-1 (rough estimate)
    max_possible_points = 200  # adjust based on keyword set size
    score = min(total_points / max_possible_points, 1.0)
    return score

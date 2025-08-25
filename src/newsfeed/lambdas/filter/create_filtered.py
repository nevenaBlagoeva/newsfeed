from datetime import datetime, timezone
from decimal import Decimal

def create_filtered_item(raw_item: dict, relevance_score: float) -> dict:
    """
    Transform raw news item into filtered item with sort key and relevance score.
    """
    published_at = raw_item.get("published_at", datetime.now(timezone.utc).isoformat())
    sort_key = f"{relevance_score:.2f}#{published_at}"

    return {
        "PK": "news",
        "SK": sort_key,
        "id": raw_item["id"],
        "source": raw_item["source"],
        "title": raw_item["title"],
        "body": raw_item.get("body", ""),
        "published_at": published_at,
        "url": raw_item.get("url", ""),
        "relevance_score": Decimal(str(relevance_score)),
        "filtered_at": datetime.now(timezone.utc).isoformat(),
        "ttl_epoch": int(datetime.now(timezone.utc).timestamp()) + (30 * 24 * 60 * 60),
    }

import logging
from datetime import datetime, timedelta, timezone
from newsfeed.lambdas.filter.ranker import calculate_keyword_relevance_score

# Set up logging
logger = logging.getLogger(__name__)

def make_item(source='reddit', hours_ago=0, title='', body=''):
    """Helper to create a test item"""
    published_at = (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat()
    return {
        'source': source,
        'published_at': published_at,
        'title': title,
        'body': body
    }

def test_calculate_keyword_relevance_score_basic():
    text = 'AI, Blockchain, Cloud Computing'
    item = make_item(source='reddit', hours_ago=2, title=text)
    score = calculate_keyword_relevance_score(item)
    logger.info(f"Basic keyword test score: {score}")
    assert 0.0 <= score <= 1.0

def test_calculate_keyword_relevance_score_other_source():
    item = make_item(source='unknown', hours_ago=2, title='AI trends')
    score = calculate_keyword_relevance_score(item)
    logger.info(f"Other source test score: {score}")
    # recency + keyword score
    assert score >= 0.01
    assert score <= 1.0

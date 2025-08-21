from fetchers.reddit import RedditFetcher
from fetchers.rss import RSSFetcher

# Configuration for all news sources
SOURCES = [
    {
        "name": "reddit_technology",
        "class": RedditFetcher,
        "config": {
            "subreddit": "technology",
            "limit": 5
        }
    },
    {
        "name": "reddit_programming", 
        "class": RedditFetcher,
        "config": {
            "subreddit": "programming",
            "limit": 5
        }
    },
    {
        "name": "ars_technica",
        "class": RSSFetcher,
        "config": {
            "feed_url": "https://feeds.arstechnica.com/arstechnica/technology-lab",
            "source_name": "ars_technica"
        }
    },
    {
        "name": "hacker_news",
        "class": RSSFetcher,
        "config": {
            "feed_url": "https://hnrss.org/frontpage",
            "source_name": "hacker_news"
        }
    }
]

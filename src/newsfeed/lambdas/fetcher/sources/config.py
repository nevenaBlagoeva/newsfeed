from newsfeed.lambdas.fetcher.fetchers.reddit import RedditFetcher
from newsfeed.lambdas.fetcher.fetchers.rss import RSSFetcher

# Configuration for all news sources
SOURCES = [
    {
        "name": "reddit_technology",
        "class": RedditFetcher,
        "config": {
            "subreddit": "technology",
            "limit": 100
        }
    },
    {
        "name": "reddit_programming", 
        "class": RedditFetcher,
        "config": {
            "subreddit": "programming",
            "limit": 100
        }
    },
        {
        "name": "reddit_managers", 
        "class": RedditFetcher,
        "config": {
            "subreddit": "managers",
            "limit": 100
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

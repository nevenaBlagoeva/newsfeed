import feedparser
import requests
from datetime import datetime
from .base import BaseFetcher

class RSSFetcher(BaseFetcher):
    def __init__(self, feed_url: str, source_name: str = "rss"):
        self.feed_url = feed_url
        self.source_name = source_name

    def fetch(self):
        try:
            print(f"Fetching RSS from {self.feed_url}")
            
            response = requests.get(self.feed_url, timeout=30)
            response.raise_for_status()
            
            feed = feedparser.parse(response.content)
            
            events = []
            for entry in feed.entries[:10]:
                events.append({
                    'source': self.source_name,
                    'id': getattr(entry, 'guid', entry.link),
                    'title': entry.title,
                    'body': getattr(entry, 'summary', ''),
                    'url': entry.link,
                    'published_at': getattr(entry, 'published', datetime.utcnow().isoformat())
                })
            
            print(f"RSS fetcher returned {len(events)} events")
            return events
            
        except Exception as e:
            print(f"Error fetching RSS feed: {e}")
            return []
        
        # TODO: Implement logging or retry mechanism
        # for better error handling
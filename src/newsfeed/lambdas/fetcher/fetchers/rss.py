import feedparser
import requests
import re
from datetime import datetime
from .base import BaseFetcher
from html.parser import HTMLParser


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
            for entry in feed.entries[:200]:
                matches = re.findall(r'href="([^"]+)"', entry.summary)
                if matches:
                    url = matches[0]
                else:
                    url = self.feed_url
                events.append({
                    'source': self.source_name,
                    'id': getattr(entry, 'guid', entry.link),
                    'title': entry.title,
                    'body': getattr(entry, 'summary', ''),
                    'url': getattr(entry, 'url', url),
                    'published_at': getattr(entry, 'published', datetime.now().isoformat())
                })
            
            print(f"RSS fetcher returned {len(events)} events")
            return events
            
        except Exception as e:
            print(f"Error fetching RSS feed: {e}")
            return []
        
        # TODO: Implement logging or retry mechanism
        # for better error handling
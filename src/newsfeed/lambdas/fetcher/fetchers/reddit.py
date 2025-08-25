import praw
import os
from datetime import datetime
from .base import BaseFetcher

class RedditFetcher(BaseFetcher):
    def __init__(self, subreddit: str = "technology", limit: int = 10):
        self.subreddit = subreddit
        self.limit = limit
        self.reddit = None

    def _get_reddit_client(self):
        """Initialize Reddit client with PRAW"""
        client_id = os.getenv('REDDIT_CLIENT_ID')
        client_secret = os.getenv('REDDIT_CLIENT_SECRET')
        
        if not client_id or not client_secret:
            raise ValueError("Reddit credentials not found in environment variables")
        
        return praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent="newsfeed-bot/1.0 (Educational Project)",
            check_for_async=False,
            timeout=10  # Add timeout
        )

    def fetch(self):
        try:
            print(f"Fetching from r/{self.subreddit}")
            
            # Initialize Reddit client
            if not self.reddit:
                self.reddit = self._get_reddit_client()
            
            subreddit = self.reddit.subreddit(self.subreddit)
            
            events = []
            # Add timeout and reduce limit for faster response
            for submission in subreddit.hot(limit=min(self.limit, 3)):
                    
                event = {
                    "source": "reddit",
                    "id": submission.id,
                    "title": submission.title,
                    "body": submission.selftext,
                    "url": submission.url,
                    "score": submission.score,
                    "subreddit": submission.subreddit.display_name,
                    "published_at": datetime.fromtimestamp(submission.created_utc).isoformat()
                }
                events.append(event)
            
            print(f"Reddit fetcher returned {len(events)} events from r/{self.subreddit}")
            return events
            
        except Exception as e:
            print(f"Reddit fetch error: {e}")
            return []

        # TODO: Implement logging or retry mechanism
        # for better error handling
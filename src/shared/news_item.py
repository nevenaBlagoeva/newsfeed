from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timezone
import json
import hashlib

@dataclass
class NewsItem:
    """Common schema for news items across the system"""
    id: str
    source: str
    title: str
    url: Optional[str] = ""
    body: Optional[str] = ""
    published_at: Optional[str] = None
    ingested_at: Optional[str] = None
    fingerprint: Optional[str] = None
    raw_payload: Optional[str] = None
    ttl_epoch: Optional[int] = None

    @classmethod
    def from_raw_event(cls, raw_event: dict) -> 'NewsItem':
        """Create NewsItem from raw fetcher event"""
        now = datetime.now(timezone.utc).isoformat()
        fingerprint = cls._generate_fingerprint(raw_event)
        
        # Calculate TTL (10 days from now).
        ttl_epoch = int(datetime.now(timezone.utc).timestamp()) + (10 * 24 * 60 * 60)
        
        return cls(
            id=fingerprint,  # Use fingerprint as primary key
            source=raw_event['source'],
            title=raw_event['title'],
            url=raw_event.get('url', ''),  # Make sure URL is preserved
            body=raw_event.get('body', ''),
            published_at=raw_event.get('published_at', now),
            ingested_at=now,
            fingerprint=fingerprint,
            raw_payload=json.dumps(raw_event),
            ttl_epoch=ttl_epoch
        )
    
    @staticmethod
    def _generate_fingerprint(event: dict) -> str:
        """Generate unique fingerprint for deduplication"""
        content = f"{event['title']}{event.get('published_at', '')}{event['source']}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def to_dynamodb_item(self) -> dict:
        """Convert to DynamoDB item format"""
        return {
            'id': self.id,
            'source': self.source,
            'title': self.title,
            'body': self.body,
            'url': self.url,
            'published_at': self.published_at,
            'ingested_at': self.ingested_at,
            'fingerprint': self.fingerprint,
            'raw_payload': self.raw_payload,
            'ttl_epoch': self.ttl_epoch
        }
    
    def validate(self) -> bool:
        """Validate required fields"""
        required_fields = [self.id, self.source, self.title, self.url]
        return all(field for field in required_fields)

from dataclasses import dataclass
from typing import Optional, List, Dict

@dataclass
class FilteredNewsItem:
    """Schema for filtered news items in FilteredEvents table"""
    id: str
    source: str
    title: str
    body: str
    published_at: str
    relevance_score: float
    recency_score: float
    rank_score: float
    categories: List[str]
    decisions: Dict[str, str]
    gsi_pk: str = "ALL"
    rank_sort: Optional[str] = None

    def __post_init__(self):
        if self.rank_sort is None:
            # Create deterministic sort key: rank_score + published_at + id
            self.rank_sort = f"{self.rank_score:012.6f}#{self.published_at}#{self.id}"
    
    def to_dynamodb_item(self) -> dict:
        """Convert to DynamoDB item format"""
        return {
            'id': self.id,
            'source': self.source,
            'title': self.title,
            'body': self.body,
            'published_at': self.published_at,
            'relevance_score': self.relevance_score,
            'recency_score': self.recency_score,
            'rank_score': self.rank_score,
            'categories': self.categories,
            'decisions': self.decisions,
            'gsi_pk': self.gsi_pk,
            'rank_sort': self.rank_sort
        }

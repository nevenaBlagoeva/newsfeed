from abc import ABC, abstractmethod

class BaseFetcher(ABC):
    """Base class for all news fetchers"""
    
    @abstractmethod
    def fetch(self):
        """
        Fetch news items from the source.
        
        Returns:
            list: List of news event dictionaries
        """
        pass

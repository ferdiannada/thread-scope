from abc import ABC, abstractmethod
from typing import List
from app.schemas.post import PostCreate


class BaseScraper(ABC):
    @abstractmethod
    async def search_posts(self, keyword: str, limit: int = 30) -> List[PostCreate]:
        """
        Search public posts on Threads by keyword.
        Returns a list of normalized PostCreate objects.
        """
        pass

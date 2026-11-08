import logging
from datetime import datetime, timezone
from typing import List, Optional
import httpx
from app.scraper.base import BaseScraper
from app.schemas.post import PostCreate
from app.core.config import settings

logger = logging.getLogger(__name__)


class OfficialThreadsClient(BaseScraper):
    """
    Official Meta Threads API Client.
    Requires Meta for Developers App with 'threads_keyword_search' permission scope.
    """

    BASE_URL = "https://graph.threads.net/v1.0"

    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token or settings.THREADS_ACCESS_TOKEN

    async def search_posts(self, keyword: str, limit: int = 30) -> List[PostCreate]:
        if not self.access_token:
            logger.warning("Threads Official API access token is not set.")
            raise ValueError(
                "THREADS_ACCESS_TOKEN is required to use the Official Threads API."
            )

        posts: List[PostCreate] = []
        url = f"{self.BASE_URL}/keyword_search"
        params = {
            "q": keyword,
            "fields": "id,text,timestamp,username,permalink,like_count,reply_count",
            "limit": min(limit, 100),
            "access_token": self.access_token,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                raw_items = data.get("data", [])
                for item in raw_items:
                    # Parse timestamp (e.g., "2024-10-12T07:12:00+0000")
                    raw_ts = item.get("timestamp")
                    if raw_ts:
                        try:
                            posted_at = datetime.fromisoformat(raw_ts)
                        except Exception:
                            posted_at = datetime.now(timezone.utc)
                    else:
                        posted_at = datetime.now(timezone.utc)

                    post = PostCreate(
                        id=str(item.get("id")),
                        author_username=item.get("username", "anonymous"),
                        author_name=item.get("username"),
                        content=item.get("text", ""),
                        post_url=item.get("permalink"),
                        likes_count=item.get("like_count", 0) or 0,
                        replies_count=item.get("reply_count", 0) or 0,
                        reposts_count=0,
                        posted_at=posted_at,
                        raw_metadata=item,
                    )
                    posts.append(post)

            except httpx.HTTPStatusError as e:
                logger.error(f"Threads API HTTP error {e.response.status_code}: {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"Failed to query Threads API: {str(e)}")
                raise

        return posts

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from app.schemas.sentiment import SentimentResponse


class PostBase(BaseModel):
    id: str
    author_username: str
    author_name: Optional[str] = None
    author_profile_pic: Optional[str] = None
    content: str
    post_url: Optional[str] = None
    likes_count: int = 0
    replies_count: int = 0
    reposts_count: int = 0
    posted_at: datetime
    media_urls: List[str] = []


class PostCreate(PostBase):
    raw_metadata: Optional[dict] = None


class PostResponse(PostBase):
    created_at: datetime
    sentiment: Optional[SentimentResponse] = None

    model_config = ConfigDict(from_attributes=True)


class PaginatedPostsResponse(BaseModel):
    items: List[PostResponse]
    total: int
    page: int
    limit: int
    total_pages: int

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Text, Integer, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.sentiment import Sentiment


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[str] = mapped_column(String(128), primary_key=True, index=True)
    author_username: Mapped[str] = mapped_column(String(128), index=True)
    author_name: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    author_profile_pic: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    content: Mapped[str] = mapped_column(Text)
    post_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    
    likes_count: Mapped[int] = mapped_column(Integer, default=0)
    replies_count: Mapped[int] = mapped_column(Integer, default=0)
    reposts_count: Mapped[int] = mapped_column(Integer, default=0)
    
    posted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    media_urls: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    raw_metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationship to sentiment analysis
    sentiment: Mapped[Optional["Sentiment"]] = relationship(
        "Sentiment", back_populates="post", uselist=False, cascade="all, delete-orphan"
    )

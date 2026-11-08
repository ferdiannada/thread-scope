import uuid
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Text, Float, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.post import Post


class Sentiment(Base):
    __tablename__ = "sentiments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    post_id: Mapped[str] = mapped_column(
        String(128), ForeignKey("posts.id", ondelete="CASCADE"), unique=True, index=True
    )
    sentiment_label: Mapped[str] = mapped_column(
        String(32), index=True
    )  # 'positive', 'neutral', 'negative'
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    primary_emotion: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, index=True
    )  # 'anger', 'anxiety', 'sadness', 'hope', 'neutral'
    summary_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    locations: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    entities: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    
    analyzed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    post: Mapped["Post"] = relationship("Post", back_populates="sentiment")

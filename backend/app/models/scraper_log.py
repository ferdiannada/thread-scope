import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Text, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class ScraperLog(Base):
    __tablename__ = "scraper_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    keyword: Mapped[str] = mapped_column(String(128), index=True)
    method: Mapped[str] = mapped_column(String(32), default="playwright")  # 'playwright', 'official_api'
    status: Mapped[str] = mapped_column(String(32), default="running")     # 'running', 'success', 'failed'
    posts_found: Mapped[int] = mapped_column(Integer, default=0)
    posts_inserted: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

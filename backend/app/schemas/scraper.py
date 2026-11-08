from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class ScraperTriggerRequest(BaseModel):
    keywords: Optional[List[str]] = Field(default=None, description="Daftar kata kunci opsional. Jika kosong, memakai default")
    max_posts: int = Field(default=50, ge=5, le=300, description="Target jumlah post per pencarian (hingga 200+)")
    method: str = Field(default="playwright", description="'playwright' atau 'official_api'")
    clear_existing: bool = Field(default=False, description="Hapus semua data lama dan gantikan dengan data baru (timpa)")


class ScraperTriggerResponse(BaseModel):
    message: str
    task_id: str
    keywords: List[str]
    method: str
    clear_existing: bool = False


class ScraperLogResponse(BaseModel):
    id: UUID
    keyword: str
    method: str
    status: str
    posts_found: int
    posts_inserted: int
    error_message: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

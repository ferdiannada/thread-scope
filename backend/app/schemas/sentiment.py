from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class SentimentBase(BaseModel):
    sentiment_label: str = Field(description="positive, neutral, or negative")
    confidence_score: float = Field(ge=0.0, le=1.0, default=0.8)
    primary_emotion: Optional[str] = Field(default="neutral", description="anger, anxiety, sadness, hope, neutral")
    summary_reason: Optional[str] = Field(default=None, description="Ringkasan penjelasan sentimen")
    locations: List[str] = Field(default_factory=list, description="Wilayah/kota/provinsi Indonesia yang disebut")
    entities: List[str] = Field(default_factory=list, description="Instansi/topik/sektor terkait (BMKG, KLHK, ISPA, dsb)")


class SentimentResponse(SentimentBase):
    id: UUID
    post_id: str
    analyzed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ThreadSentimentExtraction(BaseModel):
    post_id: str = Field(description="ID unik post Threads yang dianalisis")
    sentiment: str = Field(description="Salah satu dari: 'positive', 'neutral', 'negative'")
    confidence: float = Field(ge=0.0, le=1.0, description="Skor kepercayaan 0.0 sampai 1.0")
    emotion: str = Field(description="Emosi dominan: 'anger', 'anxiety', 'sadness', 'hope', atau 'neutral'")
    locations: List[str] = Field(default_factory=list, description="Nama wilayah Indonesia: Riau, Kalteng, Pontianak, Palangkaraya, Jambi, dll")
    entities: List[str] = Field(default_factory=list, description="Entitas penting: KLHK, BMKG, BNPB, ISPA, Sawit, Pemda, Sekolah Libur, dll")
    summary_reason: str = Field(description="Alasan singkat penentuan sentimen dalam bahasa Indonesia")


class GeminiBatchSentimentOutput(BaseModel):
    results: List[ThreadSentimentExtraction] = Field(description="Daftar hasil analisis sentimen per postingan")

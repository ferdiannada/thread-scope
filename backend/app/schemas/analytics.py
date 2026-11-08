from typing import List, Dict, Optional
from pydantic import BaseModel


class SentimentSummary(BaseModel):
    positive: int = 0
    neutral: int = 0
    negative: int = 0
    total: int = 0
    positive_percentage: float = 0.0
    neutral_percentage: float = 0.0
    negative_percentage: float = 0.0
    net_sentiment_index: float = 0.0  # (positive - negative) / total * 100


class EmotionSummary(BaseModel):
    anger: int = 0
    anxiety: int = 0
    sadness: int = 0
    hope: int = 0
    neutral: int = 0


class EntityMetric(BaseModel):
    name: str
    count: int
    negative_ratio: float = 0.0


class RegionalFactReport(BaseModel):
    region_name: str
    status: str  # 'Kritis' | 'Waspada' | 'Terkendali'
    total_reports: int
    negative_percentage: float
    key_issues: List[str]
    sample_citizen_voice: str
    affected_cities: List[str]


class OverviewMetrics(BaseModel):
    total_posts: int
    sentiment: SentimentSummary
    emotions: EmotionSummary
    top_locations: List[EntityMetric]
    top_entities: List[EntityMetric]
    regional_reports: List[RegionalFactReport] = []
    total_likes: int
    total_replies: int
    last_updated: Optional[str] = None


class TimelinePoint(BaseModel):
    timestamp: str  # YYYY-MM-DD or YYYY-MM-DD HH:00
    display_label: str = ""
    positive: int
    neutral: int
    negative: int
    total: int
    net_score: float = 0.0  # Net Sentiment: (+ - -) / total

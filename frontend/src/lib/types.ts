export interface SentimentData {
  id: string;
  post_id: string;
  sentiment_label: 'positive' | 'neutral' | 'negative';
  confidence_score: number;
  primary_emotion: string;
  summary_reason?: string;
  locations: string[];
  entities: string[];
  analyzed_at: string;
}

export interface ThreadPost {
  id: string;
  author_username: string;
  author_name?: string;
  author_profile_pic?: string;
  content: string;
  post_url?: string;
  likes_count: number;
  replies_count: number;
  reposts_count: number;
  posted_at: string;
  created_at: string;
  media_urls?: string[];
  raw_metadata?: Record<string, any>;
  sentiment?: SentimentData;
}

export interface PaginatedPosts {
  items: ThreadPost[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export interface SentimentSummary {
  positive: number;
  neutral: number;
  negative: number;
  total: number;
  positive_percentage: number;
  neutral_percentage: number;
  negative_percentage: number;
}

export interface EmotionSummary {
  anger: number;
  anxiety: number;
  sadness: number;
  hope: number;
  neutral: number;
}

export interface EntityMetric {
  name: string;
  count: number;
  negative_ratio: number;
}

export interface RegionalFactReport {
  region_name: string;
  status: 'Kritis' | 'Waspada' | 'Terkendali';
  total_reports: number;
  negative_percentage: number;
  key_issues: string[];
  sample_citizen_voice: string;
  affected_cities: string[];
}

export interface OverviewMetrics {
  total_posts: number;
  sentiment: SentimentSummary;
  emotions: EmotionSummary;
  top_locations: EntityMetric[];
  top_entities: EntityMetric[];
  regional_reports?: RegionalFactReport[];
  total_likes: number;
  total_replies: number;
  last_updated?: string;
}

export interface TimelinePoint {
  timestamp: string;
  display_label?: string;
  positive: number;
  neutral: number;
  negative: number;
  total: number;
  net_score?: number;
}

export interface ScraperLog {
  id: string;
  keyword: string;
  method: string;
  status: 'running' | 'queued' | 'success' | 'failed';
  posts_found: number;
  posts_inserted: number;
  error_message?: string;
  started_at: string;
  completed_at?: string;
}

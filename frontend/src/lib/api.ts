import type { OverviewMetrics, TimelinePoint, PaginatedPosts, ScraperLog } from './types';

const API_BASE = '/api/v1';

export function getProxyImageUrl(url?: string | null): string {
  if (!url) return '';
  // Route Meta/Instagram CDN links through backend proxy to bypass ERR_BLOCKED_BY_RESPONSE.NotSameOrigin
  if (url.includes('fbcdn.net') || url.includes('cdninstagram.com')) {
    return `${API_BASE}/posts/proxy-image?url=${encodeURIComponent(url)}`;
  }
  return url;
}

export async function fetchOverview(): Promise<OverviewMetrics> {
  const res = await fetch(`${API_BASE}/analytics/overview`);
  if (!res.ok) throw new Error(`Failed to fetch overview: ${res.statusText}`);
  return res.json();
}

export async function fetchTimeline(days: number = 7, granularity: 'hour' | 'day' = 'hour'): Promise<TimelinePoint[]> {
  const res = await fetch(`${API_BASE}/analytics/timeline?days=${days}&granularity=${granularity}`);
  if (!res.ok) throw new Error(`Failed to fetch timeline: ${res.statusText}`);
  return res.json();
}

export interface PostFilterParams {
  page?: number;
  limit?: number;
  sentiment?: string;
  keyword?: string;
  emotion?: string;
  location?: string;
}

export async function fetchPosts(params: PostFilterParams = {}): Promise<PaginatedPosts> {
  const searchParams = new URLSearchParams();
  if (params.page) searchParams.set('page', params.page.toString());
  if (params.limit) searchParams.set('limit', params.limit.toString());
  if (params.sentiment) searchParams.set('sentiment', params.sentiment);
  if (params.keyword) searchParams.set('keyword', params.keyword);
  if (params.emotion) searchParams.set('emotion', params.emotion);
  if (params.location) searchParams.set('location', params.location);

  const res = await fetch(`${API_BASE}/posts?${searchParams.toString()}`);
  if (!res.ok) throw new Error(`Failed to fetch posts: ${res.statusText}`);
  return res.json();
}

export async function triggerScraperJob(
  keywords?: string[],
  method: string = 'playwright',
  maxPosts: number = 20,
  clearExisting: boolean = false
) {
  const res = await fetch(`${API_BASE}/scraper/trigger`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      keywords,
      method,
      max_posts: maxPosts,
      clear_existing: clearExisting,
    }),
  });
  if (!res.ok) throw new Error(`Failed to trigger scraper: ${res.statusText}`);
  return res.json();
}

export async function fetchScraperLogs(limit: number = 10): Promise<ScraperLog[]> {
  const res = await fetch(`${API_BASE}/scraper/status?limit=${limit}`);
  if (!res.ok) throw new Error(`Failed to fetch scraper logs: ${res.statusText}`);
  return res.json();
}

export async function resetStuckJobs() {
  const res = await fetch(`${API_BASE}/scraper/reset-stuck`, { method: 'POST' });
  if (!res.ok) throw new Error(`Failed to reset scraper jobs: ${res.statusText}`);
  return res.json();
}

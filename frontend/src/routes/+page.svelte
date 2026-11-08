<script lang="ts">
  import { onMount } from 'svelte';
  import Header from '#lib/components/Header.svelte';
  import KpiCard from '#lib/components/KpiCard.svelte';
  import SentimentTimeline from '#lib/components/SentimentTimeline.svelte';
  import GeoTopicMatrix from '#lib/components/GeoTopicMatrix.svelte';
  import PostFeed from '#lib/components/PostFeed.svelte';
  import { fetchOverview, fetchTimeline, fetchPosts } from '#lib/api';
  import type { OverviewMetrics, TimelinePoint, PaginatedPosts } from '#lib/types';

  let overview = $state<OverviewMetrics | null>(null);
  let timeline = $state<TimelinePoint[]>([]);
  let postsData = $state<PaginatedPosts>({
    items: [],
    total: 0,
    page: 1,
    limit: 10,
    total_pages: 1,
  });

  let isRefreshing = $state(false);
  let isLoadingPosts = $state(false);

  // Filters state
  let currentSentiment = $state('');
  let currentKeyword = $state('');
  let currentLocation = $state('');
  let currentPage = $state(1);
  let currentLimit = $state(10);

  // Timeline config
  let currentGranularity = $state<'hour' | 'day'>('hour');
  let currentDays = $state(3);

  async function loadAllData() {
    isRefreshing = true;
    try {
      const [ov, tl] = await Promise.all([
        fetchOverview(),
        fetchTimeline(currentDays, currentGranularity),
      ]);
      overview = ov;
      timeline = tl;
      await loadFilteredPosts();
    } catch (e) {
      console.error('Error loading dashboard metrics:', e);
    } finally {
      isRefreshing = false;
    }
  }

  async function handleTimelineConfigChange(granularity: 'hour' | 'day', days: number) {
    currentGranularity = granularity;
    currentDays = days;
    try {
      timeline = await fetchTimeline(currentDays, currentGranularity);
    } catch (e) {
      console.error('Failed to update timeline:', e);
    }
  }

  function handleTimeSelect(timestamp: string) {
    const datePart = timestamp.split(' ')[0];
    if (datePart) {
      currentKeyword = datePart;
      currentPage = 1;
      loadFilteredPosts();
    }
  }

  async function loadFilteredPosts() {
    isLoadingPosts = true;
    try {
      postsData = await fetchPosts({
        sentiment: currentSentiment || undefined,
        keyword: currentKeyword || undefined,
        location: currentLocation || undefined,
        page: currentPage,
        limit: currentLimit,
      });
    } catch (e) {
      console.error('Error fetching posts:', e);
    } finally {
      isLoadingPosts = false;
    }
  }

  function handleFilterChange(filters: { sentiment?: string; keyword?: string; location?: string; page: number; limit?: number }) {
    currentSentiment = filters.sentiment ?? '';
    currentKeyword = filters.keyword ?? '';
    currentLocation = filters.location ?? '';
    currentPage = filters.page;
    if (filters.limit) currentLimit = filters.limit;
    loadFilteredPosts();
  }

  function handleMatrixFilterSelect(type: 'location' | 'keyword', val: string) {
    if (type === 'location') {
      currentLocation = val;
    } else {
      currentKeyword = val;
    }
    currentPage = 1;
    loadFilteredPosts();
  }

  onMount(() => {
    loadAllData();
  });
</script>

<svelte:head>
  <title>ThreadScope: Analisis Sentimen Threads</title>
  <meta name="description" content="Pantau sentimen dan topik percakapan publik di Threads." />
</svelte:head>

<div class="min-h-screen bg-slate-50 flex flex-col font-sans">
  <Header
    onRefresh={loadAllData}
    lastUpdated={overview?.last_updated}
    {isRefreshing}
  />

  <main class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-6 space-y-6">
    <!-- Top KPI Grid -->
    <section class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <KpiCard
        title="Total Postingan"
        value={overview ? overview.total_posts : '...'}
        subtitle="Jumlah postingan yang tersimpan"
        trendLabel="Total"
        barPercent={100}
        barColor="bg-slate-900"
      />

      <KpiCard
        title="Sentimen Negatif"
        value={overview ? `${overview.sentiment.negative_percentage}%` : '...'}
        subtitle="{overview?.sentiment.negative || 0} postingan bernada negatif"
        trendLabel="Porsi Negatif"
        barPercent={overview?.sentiment.negative_percentage || 0}
        barColor="bg-red-600"
      />

      <KpiCard
        title="Sentimen Netral"
        value={overview ? `${overview.sentiment.neutral_percentage}%` : '...'}
        subtitle="{overview?.sentiment.neutral || 0} postingan berita atau fakta"
        trendLabel="Porsi Netral"
        barPercent={overview?.sentiment.neutral_percentage || 0}
        barColor="bg-slate-400"
      />

      <KpiCard
        title="Sentimen Positif"
        value={overview ? `${overview.sentiment.positive_percentage}%` : '...'}
        subtitle="{overview?.sentiment.positive || 0} postingan bernada positif"
        trendLabel="Porsi Positif"
        barPercent={overview?.sentiment.positive_percentage || 0}
        barColor="bg-emerald-600"
      />
    </section>

    <!-- Sentiment Timeline Chart & Emotion Breakdown -->
    <section>
      <SentimentTimeline
        {timeline}
        emotions={overview?.emotions}
        {currentGranularity}
        {currentDays}
        onTimelineConfigChange={handleTimelineConfigChange}
        onTimeSelect={handleTimeSelect}
      />
    </section>

    <!-- Geo & Topic Entity Breakdown -->
    <section>
      <GeoTopicMatrix
        regionalReports={overview?.regional_reports || []}
        locations={overview?.top_locations || []}
        entities={overview?.top_entities || []}
        onFilterSelect={handleMatrixFilterSelect}
      />
    </section>

    <!-- Post Feed Explorer -->
    <section>
      <PostFeed
        {postsData}
        {currentSentiment}
        {currentKeyword}
        {currentLocation}
        {currentPage}
        {currentLimit}
        isLoading={isLoadingPosts}
        onFilterChange={handleFilterChange}
      />
    </section>
  </main>

  <!-- Clean Footer -->
  <footer class="border-t border-slate-200 bg-white py-5 px-6 text-xs text-slate-500 font-mono mt-12">
    <div class="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3">
      <div class="flex items-center gap-2">
        <span class="w-2 h-2 rounded-full bg-emerald-600"></span>
        <span class="font-medium text-slate-700">ThreadScope</span>
      </div>
      <div class="flex flex-wrap items-center gap-4 text-[11px] text-slate-500">
        <span>FastAPI &amp; PostgreSQL 16</span>
        <span>IndoBERT Transformer</span>
        <span>SvelteKit</span>
      </div>
    </div>
  </footer>
</div>

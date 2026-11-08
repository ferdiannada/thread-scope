<script lang="ts">
  import type { ThreadPost, PaginatedPosts } from '#lib/types';
  import { getProxyImageUrl } from '#lib/api';
  import {
    Search,
    ExternalLink,
    Heart,
    MessageCircle,
    Repeat2,
    X,
    ChevronLeft,
    ChevronRight,
    Copy,
    Check,
    Image as ImageIcon,
    FileCode,
    Clock,
    Maximize2,
    AlertCircle,
  } from 'lucide-svelte';

  interface Props {
    postsData: PaginatedPosts;
    currentSentiment?: string;
    currentKeyword?: string;
    currentLocation?: string;
    currentPage: number;
    currentLimit?: number;
    isLoading?: boolean;
    onFilterChange: (filters: { sentiment?: string; keyword?: string; location?: string; page: number; limit?: number }) => void;
  }

  let {
    postsData,
    currentSentiment = '',
    currentKeyword = '',
    currentLocation = '',
    currentPage = 1,
    currentLimit = 10,
    isLoading = false,
    onFilterChange,
  }: Props = $props();

  let searchInput = $state('');
  let copiedPostId = $state<string | null>(null);
  let selectedPostForDetail = $state<ThreadPost | null>(null);
  let lightboxImageUrl = $state<string | null>(null);
  let avatarErrors = $state<Record<string, boolean>>({});
  let mediaErrors = $state<Record<string, boolean>>({});

  $effect(() => {
    searchInput = currentKeyword;
  });

  function handleSearchSubmit(e: SubmitEvent) {
    e.preventDefault();
    onFilterChange({
      sentiment: currentSentiment,
      keyword: searchInput.trim(),
      location: currentLocation,
      page: 1,
      limit: currentLimit,
    });
  }

  function handleSentimentTab(sentiment: string) {
    onFilterChange({
      sentiment: sentiment === currentSentiment ? '' : sentiment,
      keyword: currentKeyword,
      location: currentLocation,
      page: 1,
      limit: currentLimit,
    });
  }

  function handleLimitChange(e: Event) {
    const val = Number((e.target as HTMLSelectElement).value);
    onFilterChange({
      sentiment: currentSentiment,
      keyword: currentKeyword,
      location: currentLocation,
      page: 1,
      limit: val,
    });
  }

  function handleLocationClick(loc: string) {
    onFilterChange({
      sentiment: currentSentiment,
      keyword: currentKeyword,
      location: loc,
      page: 1,
      limit: currentLimit,
    });
  }

  function clearLocation() {
    onFilterChange({
      sentiment: currentSentiment,
      keyword: currentKeyword,
      location: '',
      page: 1,
      limit: currentLimit,
    });
  }

  function clearKeyword() {
    searchInput = '';
    onFilterChange({
      sentiment: currentSentiment,
      keyword: '',
      location: currentLocation,
      page: 1,
      limit: currentLimit,
    });
  }

  function changePage(newPage: number) {
    if (newPage < 1 || newPage > postsData.total_pages) return;
    onFilterChange({
      sentiment: currentSentiment,
      keyword: currentKeyword,
      location: currentLocation,
      page: newPage,
      limit: currentLimit,
    });
  }

  async function copyToClipboard(url?: string, postId?: string) {
    if (!url) return;
    try {
      await navigator.clipboard.writeText(url);
      copiedPostId = postId || url;
      setTimeout(() => {
        copiedPostId = null;
      }, 2000);
    } catch (e) {
      console.error('Failed to copy', e);
    }
  }

  interface FormattedDate {
    relative: string;
    dateStr: string;
    timeStr: string;
    fullStr: string;
    iso: string;
  }

  function decodeMetaSnowflake(code: string): Date | null {
    const raw = code.replace(/^th_/, '');
    if (!/^[A-Za-z0-9_-]{11}$/.test(raw)) return null;
    if (/(?:AugLive|Aman|Kawal|Peduli|Kalteng|Sebangau|Gambut|Haze|Hotspot|Asap|Ketapang|Darurat|Ampera|Evaluasi|Restorasi|Oksigen|Waterbomb|Kukar|Savana|Tips|Sekat|TNK|Gerimis|PKU|BPK|Nostalgia|Kehutanan|Tersangka|Wildlife|Hero|TNKS|Barito)/i.test(raw)) return null;

    const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_';
    try {
      let val = 0n;
      for (let i = 0; i < raw.length; i++) {
        const idx = BigInt(alphabet.indexOf(raw[i]));
        if (idx < 0n) return null;
        val = val * 64n + idx;
      }
      const epoch = 1314220021721n;
      const tsMs = Number((val >> 23n) + epoch);
      const decodedDate = new Date(tsMs);
      if (decodedDate.getFullYear() >= 2023 && decodedDate.getFullYear() <= 2030) {
        return decodedDate;
      }
    } catch {
      return null;
    }
    return null;
  }

  function formatPostDate(isoString: string, postId?: string): FormattedDate {
    try {
      let d: Date;
      if (postId) {
        const snowflakeDate = decodeMetaSnowflake(postId);
        d = snowflakeDate || new Date(isoString);
      } else {
        d = new Date(isoString);
      }

      if (isNaN(d.getTime())) {
        return {
          relative: 'Waktu tidak tersedia',
          dateStr: '-',
          timeStr: '-',
          fullStr: '-',
          iso: isoString || '',
        };
      }

      const now = new Date();
      const diffMs = now.getTime() - d.getTime();
      const diffSec = Math.floor(diffMs / 1000);
      const diffMin = Math.floor(diffSec / 60);
      const diffHour = Math.floor(diffMin / 60);
      const diffDay = Math.floor(diffHour / 24);

      // Format Jam (WIB)
      const timeStr =
        d.toLocaleTimeString('id-ID', {
          hour: '2-digit',
          minute: '2-digit',
          hour12: false,
          timeZone: 'Asia/Jakarta',
        }) + ' WIB';

      // Format Tanggal (WIB)
      const dateStr = d.toLocaleDateString('id-ID', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
        timeZone: 'Asia/Jakarta',
      });

      let relative = '';
      if (diffSec < 60) {
        relative = 'Baru saja';
      } else if (diffMin < 60) {
        relative = `${diffMin} menit lalu`;
      } else if (diffHour < 24) {
        const todayWib = now.toLocaleDateString('id-ID', { timeZone: 'Asia/Jakarta' });
        const postWib = d.toLocaleDateString('id-ID', { timeZone: 'Asia/Jakarta' });
        if (todayWib === postWib) {
          relative = `${diffHour} jam lalu`;
        } else {
          relative = `Kemarin, ${timeStr}`;
        }
      } else if (diffDay === 1) {
        relative = `Kemarin, ${timeStr}`;
      } else if (diffDay < 7) {
        relative = `${diffDay} hari lalu`;
      } else if (diffDay < 30) {
        const weeks = Math.floor(diffDay / 7);
        relative = `${weeks} minggu lalu`;
      } else {
        const months = Math.floor(diffDay / 30);
        relative = `${months} bulan lalu`;
      }

      const fullStr =
        d.toLocaleDateString('id-ID', {
          weekday: 'long',
          day: 'numeric',
          month: 'long',
          year: 'numeric',
          timeZone: 'Asia/Jakarta',
        }) +
        ', ' +
        timeStr;

      return {
        relative,
        dateStr,
        timeStr,
        fullStr,
        iso: d.toISOString(),
      };
    } catch {
      return {
        relative: '-',
        dateStr: '-',
        timeStr: '-',
        fullStr: '-',
        iso: isoString || '',
      };
    }
  }

  function cleanThreadsContent(text: string): string {
    if (!text) return '';
    let cleaned = text.trim();
    cleaned = cleaned.replace(/^(\d+\s*(?:hari|jam|menit|mnt|detik|dtk|minggu|d|h|m|w)\s+)/i, '');
    cleaned = cleaned.replace(/\s+(?:\d+(?:[.,]\d+)?\s*(?:rb|jt|k|m)?\s*){2,6}$/i, '');
    cleaned = cleaned.replace(/\b(Lihat terjemahan|Translate)\b/gi, '').trim();
    return cleaned;
  }

  interface ThreadsLinkInfo {
    url: string;
    isDirectPost: boolean;
    label: string;
    authorUrl: string;
    isRealAuthor: boolean;
  }

  function getThreadsLinkInfo(post: ThreadPost): ThreadsLinkInfo {
    const rawUrl = (post.post_url || '').trim();
    const author = (post.author_username || 'threads').trim();

    // Jika URL adalah link langsung ke postingan spesifik Threads (/@user/post/code atau /t/code)
    if (rawUrl && (rawUrl.includes('/post/') || rawUrl.includes('/t/'))) {
      return {
        url: rawUrl,
        isDirectPost: true,
        label: 'Buka di Threads',
        authorUrl: `https://www.threads.net/@${author}`,
        isRealAuthor: true,
      };
    }

    // Untuk topik hasil pencarian baru di mana akses tamu Threads dibatasi (guest limit),
    // tautkan langsung ke halaman pencarian resmi Threads agar membuka feed percakapan asli
    // di peramban pengguna dan mencegah munculnya error 404 (Not Found).
    const kw = (post.raw_metadata?.keyword || currentKeyword || 'threads').trim();
    const searchUrl = rawUrl.startsWith('http')
      ? rawUrl
      : `https://www.threads.net/search?q=${encodeURIComponent(kw)}&serp_type=default`;

    return {
      url: searchUrl,
      isDirectPost: false,
      label: 'Cari di Threads',
      authorUrl: `https://www.threads.net/search?q=${encodeURIComponent(author.replace(/_/g, ' '))}&serp_type=default`,
      isRealAuthor: false,
    };
  }

  function getSentimentBadge(sentiment?: string) {
    switch (sentiment) {
      case 'negative':
        return {
          label: 'Negatif',
          bg: 'bg-red-50',
          text: 'text-red-700',
          border: 'border-red-200',
          dot: 'bg-red-600',
        };
      case 'positive':
        return {
          label: 'Positif',
          bg: 'bg-emerald-50',
          text: 'text-emerald-700',
          border: 'border-emerald-200',
          dot: 'bg-emerald-600',
        };
      default:
        return {
          label: 'Netral',
          bg: 'bg-slate-100',
          text: 'text-slate-700',
          border: 'border-slate-200',
          dot: 'bg-slate-500',
        };
    }
  }

  function getEmotionBadge(emotion?: string) {
    switch (emotion) {
      case 'anger':
        return { label: 'Marah', text: 'text-red-800', bg: 'bg-red-50', border: 'border-red-200' };
      case 'anxiety':
        return { label: 'Cemas', text: 'text-amber-800', bg: 'bg-amber-50', border: 'border-amber-200' };
      case 'sadness':
        return { label: 'Sedih', text: 'text-sky-800', bg: 'bg-sky-50', border: 'border-sky-200' };
      case 'hope':
        return { label: 'Harapan', text: 'text-emerald-800', bg: 'bg-emerald-50', border: 'border-emerald-200' };
      default:
        return { label: 'Netral', text: 'text-slate-700', bg: 'bg-slate-100', border: 'border-slate-200' };
    }
  }
</script>

<div class="bg-white border border-slate-200 rounded-lg p-6 shadow-2xs">
  <!-- Feed Header & Controls -->
  <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-200">
    <div>
      <div class="flex items-center gap-2">
        <h2 class="text-sm font-bold text-slate-900 uppercase tracking-wider">
          Daftar Postingan
        </h2>
        <span class="text-[11px] px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200 font-mono font-medium">
          {postsData.total} Postingan
        </span>
      </div>
      <p class="text-xs text-slate-500 mt-0.5">
        Kumpulan postingan Threads terbaru sesuai kata kunci yang dicari
      </p>
    </div>

    <!-- Search input & limit selector -->
    <div class="flex items-center gap-2.5 flex-wrap">
      <form onsubmit={handleSearchSubmit} class="flex items-center gap-2 max-w-xs w-full">
        <div class="relative w-full">
          <Search class="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            bind:value={searchInput}
            placeholder="Cari kata, lokasi, @user..."
            class="w-full bg-white border border-slate-300 rounded pl-8 pr-8 py-1.5 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-slate-800 font-mono shadow-2xs"
          />
          {#if searchInput}
            <button
              type="button"
              onclick={clearKeyword}
              class="absolute right-2.5 top-2 text-slate-400 hover:text-slate-600"
              title="Hapus pencarian"
            >
              <X class="w-3.5 h-3.5" />
            </button>
          {/if}
        </div>
        <button
          type="submit"
          class="px-3 py-1.5 text-xs font-medium rounded bg-slate-900 hover:bg-slate-800 text-white transition-colors shadow-2xs"
        >
          Cari
        </button>
      </form>

      <div class="flex items-center gap-1.5 text-xs font-mono text-slate-500">
        <span>Tampil:</span>
        <select
          value={currentLimit}
          onchange={handleLimitChange}
          class="bg-white border border-slate-300 text-slate-900 rounded px-2 py-1 text-xs focus:outline-none focus:border-slate-800 font-mono shadow-2xs"
        >
          <option value={10}>10</option>
          <option value={20}>20</option>
          <option value={35}>35</option>
          <option value={50}>50</option>
        </select>
      </div>
    </div>
  </div>

  <!-- Filters Row -->
  <div class="flex flex-wrap items-center justify-between gap-3 py-3 border-b border-slate-200">
    <!-- Sentiment Tabs -->
    <div class="flex items-center gap-1 bg-slate-100 p-0.5 rounded-md border border-slate-200">
      <button
        type="button"
        onclick={() => handleSentimentTab('')}
        class="px-3 py-1 text-xs rounded font-medium transition-colors {currentSentiment === '' ? 'bg-white text-slate-900 font-semibold shadow-2xs' : 'text-slate-600 hover:text-slate-900'}"
      >
        Semua
      </button>
      <button
        type="button"
        onclick={() => handleSentimentTab('negative')}
        class="px-3 py-1 text-xs rounded font-medium transition-colors flex items-center gap-1.5 {currentSentiment === 'negative' ? 'bg-white text-red-700 font-semibold shadow-2xs' : 'text-slate-600 hover:text-red-700'}"
      >
        <span class="w-2 h-2 rounded-full bg-red-600"></span>
        Negatif
      </button>
      <button
        type="button"
        onclick={() => handleSentimentTab('neutral')}
        class="px-3 py-1 text-xs rounded font-medium transition-colors flex items-center gap-1.5 {currentSentiment === 'neutral' ? 'bg-white text-slate-800 font-semibold shadow-2xs' : 'text-slate-600 hover:text-slate-900'}"
      >
        <span class="w-2 h-2 rounded-full bg-slate-400"></span>
        Netral
      </button>
      <button
        type="button"
        onclick={() => handleSentimentTab('positive')}
        class="px-3 py-1 text-xs rounded font-medium transition-colors flex items-center gap-1.5 {currentSentiment === 'positive' ? 'bg-white text-emerald-700 font-semibold shadow-2xs' : 'text-slate-600 hover:text-emerald-700'}"
      >
        <span class="w-2 h-2 rounded-full bg-emerald-600"></span>
        Positif
      </button>
    </div>

    <!-- Active filter tags -->
    <div class="flex flex-wrap items-center gap-2">
      {#if currentLocation}
        <span class="inline-flex items-center gap-1.5 text-xs bg-slate-100 border border-slate-200 text-slate-800 px-2.5 py-1 rounded font-mono">
          <span>Lokasi: {currentLocation}</span>
          <button type="button" onclick={clearLocation} class="hover:text-slate-900" title="Hapus filter lokasi">
            <X class="w-3 h-3" />
          </button>
        </span>
      {/if}
      {#if currentKeyword}
        <span class="inline-flex items-center gap-1.5 text-xs bg-slate-100 border border-slate-200 text-slate-800 px-2.5 py-1 rounded font-mono">
          <span>Kata kunci: "{currentKeyword}"</span>
          <button type="button" onclick={clearKeyword} class="hover:text-slate-900" title="Hapus filter">
            <X class="w-3 h-3" />
          </button>
        </span>
      {/if}
    </div>
  </div>

  <!-- Post List Cards -->
  <div class="mt-5 space-y-4">
    {#if isLoading}
      <div class="py-16 text-center text-xs text-slate-500 font-mono flex flex-col items-center justify-center gap-2">
        <div class="w-6 h-6 border-2 border-slate-800 border-t-transparent rounded-full animate-spin"></div>
        <span>Memuat postingan...</span>
      </div>
    {:else if postsData.items.length === 0}
      <div class="py-16 text-center text-xs text-slate-500 font-mono bg-slate-50 rounded border border-slate-200 p-6">
        <AlertCircle class="w-6 h-6 text-slate-400 mx-auto mb-2" />
        <p class="text-slate-800 font-medium">Tidak ada postingan yang sesuai.</p>
        <p class="text-[11px] text-slate-500 mt-1">Coba ubah kata kunci atau pilih filter sentimen lainnya.</p>
      </div>
    {:else}
      {#each postsData.items as post (post.id)}
        {@const sentBadge = getSentimentBadge(post.sentiment?.sentiment_label)}
        {@const emotBadge = getEmotionBadge(post.sentiment?.primary_emotion)}
        {@const dateInfo = formatPostDate(post.posted_at, post.id)}
        {@const cleanText = cleanThreadsContent(post.content)}
        {@const linkInfo = getThreadsLinkInfo(post)}
        {@const directUrl = linkInfo.url}
        {@const authorUrl = linkInfo.authorUrl}

        <article class="bg-white border border-slate-200 hover:border-slate-300 rounded-lg p-6 transition-all duration-150 flex flex-col justify-between shadow-2xs">
          <div>
            <!-- Header Bar: Author Info, Time Created & Sentiment Badges -->
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
              <!-- Left: Author profile & identity -->
              <div class="flex items-center gap-3">
                <a
                  href={authorUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  class="w-10 h-10 rounded-full bg-slate-100 border border-slate-200 flex items-center justify-center text-xs font-mono font-bold text-slate-600 overflow-hidden shrink-0 hover:ring-2 hover:ring-slate-400 transition-all shadow-2xs"
                  title="Buka profil @{post.author_username} di Threads"
                >
                  {#if post.author_profile_pic && !avatarErrors[post.id]}
                    <img
                      src={getProxyImageUrl(post.author_profile_pic)}
                      alt={post.author_username}
                      class="w-full h-full object-cover"
                      referrerpolicy="no-referrer"
                      onerror={() => { avatarErrors[post.id] = true; }}
                    />
                  {:else}
                    {post.author_username.slice(0, 2).toUpperCase()}
                  {/if}
                </a>

                <div>
                  <div class="flex items-center gap-2 flex-wrap">
                    <a
                      href={authorUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      class="text-sm font-bold text-slate-900 hover:text-slate-700 transition-colors"
                      title="Buka profil @{post.author_username}"
                    >
                      {post.author_name || post.author_username}
                    </a>
                    <a
                      href={authorUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      class="text-xs font-mono text-slate-500 hover:text-slate-700 transition-colors"
                      title="Buka profil @{post.author_username}"
                    >
                      @{post.author_username}
                    </a>
                    <span class="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 border border-slate-200 text-slate-600 font-mono">
                      Threads
                    </span>
                  </div>

                  <!-- Date & Time -->
                  <div class="flex items-center gap-1.5 text-xs text-slate-500 font-mono mt-0.5" title={dateInfo.fullStr}>
                    <Clock class="w-3 h-3 text-slate-400 shrink-0" />
                    <span class="text-slate-700 font-medium">{dateInfo.relative}</span>
                    <span class="text-slate-300">•</span>
                    <span class="text-slate-500">{dateInfo.dateStr}, {dateInfo.timeStr}</span>
                  </div>
                </div>
              </div>

              <!-- Right: Sentiment & Emotion Badges -->
              <div class="flex items-center gap-2 self-start sm:self-center shrink-0">
                {#if post.sentiment?.primary_emotion}
                  <span class="text-[11px] px-2 py-0.5 rounded border {emotBadge.border} {emotBadge.text} {emotBadge.bg} font-mono hidden md:inline-flex items-center gap-1 font-medium">
                    <span>{emotBadge.label}</span>
                  </span>
                {/if}
                <span class="inline-flex items-center gap-1.5 text-xs px-2.5 py-0.5 rounded font-medium border {sentBadge.bg} {sentBadge.text} {sentBadge.border}">
                  <span class="w-1.5 h-1.5 rounded-full {sentBadge.dot}"></span>
                  <span>{sentBadge.label}</span>
                  {#if post.sentiment?.confidence_score}
                    <span class="text-[10px] font-mono opacity-80">
                      {Math.round(post.sentiment.confidence_score * 100)}%
                    </span>
                  {/if}
                </span>
              </div>
            </div>

            <!-- Post Content Text -->
            <p class="text-sm text-slate-900 mt-3.5 leading-relaxed font-sans whitespace-pre-line selection:bg-slate-200">
              {cleanText}
            </p>

            <!-- Media Attachments Preview Gallery -->
            {#if post.media_urls && post.media_urls.length > 0}
              <div class="mt-3.5">
                <div class="flex flex-wrap gap-2.5">
                  {#each post.media_urls as imgUrl}
                    {#if !mediaErrors[imgUrl]}
                      <button
                        type="button"
                        onclick={() => (lightboxImageUrl = imgUrl)}
                        class="group relative block rounded-md overflow-hidden border border-slate-200 hover:border-slate-400 transition-all bg-slate-50 text-left focus:outline-none focus:ring-1 focus:ring-slate-800 max-w-[280px] max-h-[180px] shadow-2xs"
                        title="Klik untuk melihat foto"
                      >
                        <img
                          src={getProxyImageUrl(imgUrl)}
                          alt="Foto postingan Threads"
                          class="w-full h-full object-cover group-hover:scale-102 transition-transform duration-200"
                          loading="lazy"
                          referrerpolicy="no-referrer"
                          onerror={() => { mediaErrors[imgUrl] = true; }}
                        />
                        <div class="absolute inset-0 bg-slate-900/30 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                          <span class="px-2 py-1 rounded bg-slate-900/90 text-[10px] font-mono text-white flex items-center gap-1 shadow-xs">
                            <Maximize2 class="w-3 h-3 text-slate-200" />
                            <span>Lihat Foto</span>
                          </span>
                        </div>
                      </button>
                    {/if}
                  {/each}
                </div>
              </div>
            {/if}

            <!-- AI Intelligence Fact Box -->
            <div class="mt-4 bg-slate-50 rounded-md border border-slate-200 p-3.5 space-y-2">
              <div class="flex flex-wrap items-center justify-between gap-2">
                <!-- Location & Entity Badges -->
                <div class="flex flex-wrap items-center gap-1.5">
                  <span class="text-[10px] font-mono text-slate-500 uppercase tracking-wider mr-1">
                    Topik &amp; Lokasi:
                  </span>

                  {#if post.sentiment?.locations && post.sentiment.locations.length > 0}
                    {#each post.sentiment.locations as loc}
                      <button
                        type="button"
                        onclick={() => handleLocationClick(loc)}
                        class="text-[11px] px-2 py-0.5 rounded bg-white hover:bg-slate-100 text-slate-800 border border-slate-200 font-mono inline-flex items-center gap-1 transition-colors shadow-2xs"
                        title="Filter postingan di {loc}"
                      >
                        <span>{loc}</span>
                      </button>
                    {/each}
                  {:else}
                    <span class="text-[11px] text-slate-400 font-mono italic">Umum</span>
                  {/if}

                  {#if post.sentiment?.entities && post.sentiment.entities.length > 0}
                    {#each post.sentiment.entities as ent}
                      <span class="text-[11px] px-2 py-0.5 rounded bg-white text-slate-700 border border-slate-200 font-mono inline-flex items-center gap-1 shadow-2xs">
                        <span>{ent}</span>
                      </span>
                    {/each}
                  {/if}
                </div>

                <!-- Post Unique ID -->
                <span class="text-[10px] font-mono text-slate-400">
                  ID: <span class="text-slate-600">{post.id}</span>
                </span>
              </div>

              <!-- Rationale Briefing -->
              {#if post.sentiment?.summary_reason}
                <div class="text-xs text-slate-700 leading-relaxed border-l-2 border-slate-700 pl-2.5 py-0.5 mt-1 font-sans">
                  <span class="text-slate-900 font-semibold">Alasan Sentimen:</span>
                  <span> {post.sentiment.summary_reason}</span>
                </div>
              {/if}
            </div>
          </div>

          <!-- Bottom Action Bar -->
          <div class="mt-4 pt-3 border-t border-slate-100 flex flex-wrap items-center justify-between gap-3 text-xs">
            <!-- Left: Engagement Counts -->
            <div class="flex items-center gap-4 text-slate-500 font-mono text-xs">
              <span class="flex items-center gap-1.5" title="{post.likes_count} suka">
                <Heart class="w-3.5 h-3.5 text-slate-400" />
                <span>{post.likes_count.toLocaleString('id-ID')}</span>
                <span class="hidden sm:inline text-slate-400">suka</span>
              </span>
              <span class="flex items-center gap-1.5" title="{post.replies_count} balasan">
                <MessageCircle class="w-3.5 h-3.5 text-slate-400" />
                <span>{post.replies_count.toLocaleString('id-ID')}</span>
                <span class="hidden sm:inline text-slate-400">balasan</span>
              </span>
              <span class="flex items-center gap-1.5" title="{post.reposts_count} repost">
                <Repeat2 class="w-3.5 h-3.5 text-slate-400" />
                <span>{post.reposts_count.toLocaleString('id-ID')}</span>
                <span class="hidden sm:inline text-slate-400">repost</span>
              </span>
            </div>

            <!-- Right: Action Buttons -->
            <div class="flex items-center gap-2 flex-wrap">
              <!-- Button: Copy Link -->
              <button
                type="button"
                onclick={() => copyToClipboard(directUrl, post.id)}
                class="px-2.5 py-1 text-xs rounded bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 font-mono inline-flex items-center gap-1.5 transition-colors shadow-2xs"
                title="Salin tautan postingan"
              >
                {#if copiedPostId === post.id}
                  <Check class="w-3 h-3 text-emerald-600" />
                  <span class="text-emerald-700">Tersalin</span>
                {:else}
                  <Copy class="w-3 h-3 text-slate-500" />
                  <span>Salin Link</span>
                {/if}
              </button>

              <!-- Button: Metadata -->
              <button
                type="button"
                onclick={() => (selectedPostForDetail = post)}
                class="px-2.5 py-1 text-xs rounded bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 font-mono inline-flex items-center gap-1.5 transition-colors shadow-2xs"
                title="Lihat detail metadata"
              >
                <FileCode class="w-3 h-3 text-slate-500" />
                <span>Metadata</span>
              </button>

              <!-- Button: Open on Threads Platform -->
              <a
                href={linkInfo.url}
                target="_blank"
                rel="noopener noreferrer"
                class="px-3 py-1 text-xs font-medium rounded bg-slate-900 hover:bg-slate-800 text-white shadow-xs inline-flex items-center gap-1.5 transition-colors"
                title="Buka postingan di Threads"
              >
                <span>{linkInfo.label}</span>
                <ExternalLink class="w-3.5 h-3.5" />
              </a>
            </div>
          </div>
        </article>
      {/each}
    {/if}
  </div>

  <!-- Pagination Controls -->
  {#if postsData.total_pages > 1}
    <div class="mt-6 pt-4 border-t border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs font-mono">
      <span class="text-slate-500">
        Halaman <strong class="text-slate-900">{postsData.page}</strong> dari <strong class="text-slate-900">{postsData.total_pages}</strong> ({postsData.total} total post)
      </span>
      <div class="flex items-center gap-1.5">
        <button
          type="button"
          disabled={currentPage <= 1 || isLoading}
          onclick={() => changePage(currentPage - 1)}
          class="p-1.5 rounded bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 disabled:opacity-40 transition-colors shadow-2xs"
          title="Halaman sebelumnya"
        >
          <ChevronLeft class="w-4 h-4" />
        </button>
        <span class="px-3 py-1 rounded bg-slate-100 border border-slate-200 text-slate-800 font-semibold">
          {currentPage} / {postsData.total_pages}
        </span>
        <button
          type="button"
          disabled={currentPage >= postsData.total_pages || isLoading}
          onclick={() => changePage(currentPage + 1)}
          class="p-1.5 rounded bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 disabled:opacity-40 transition-colors shadow-2xs"
          title="Halaman berikutnya"
        >
          <ChevronRight class="w-4 h-4" />
        </button>
      </div>
    </div>
  {/if}
</div>

<!-- Modal: Lightbox Image Preview -->
{#if lightboxImageUrl}
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-2xs p-4">
    <div class="relative max-w-4xl max-h-[90vh] bg-white border border-slate-200 rounded-lg overflow-hidden flex flex-col shadow-xl">
      <div class="flex items-center justify-between px-4 py-2.5 border-b border-slate-200 bg-slate-50">
        <span class="text-xs font-mono text-slate-700 flex items-center gap-1.5 font-medium">
          <ImageIcon class="w-3.5 h-3.5 text-slate-500" />
          <span>Foto Postingan</span>
        </span>
        <button
          type="button"
          onclick={() => (lightboxImageUrl = null)}
          class="text-slate-400 hover:text-slate-600 transition-colors"
          title="Tutup foto"
        >
          <X class="w-4 h-4" />
        </button>
      </div>
      <div class="p-3 flex items-center justify-center bg-slate-100 overflow-auto">
        <img
          src={getProxyImageUrl(lightboxImageUrl)}
          alt="Foto Threads"
          class="max-h-[75vh] w-auto object-contain rounded border border-slate-200"
          referrerpolicy="no-referrer"
        />
      </div>
    </div>
  </div>
{/if}

<!-- Modal: Raw Public Data Inspection -->
{#if selectedPostForDetail}
  {@const modalDate = formatPostDate(selectedPostForDetail.posted_at, selectedPostForDetail.id)}
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-2xs p-4">
    <div class="bg-white border border-slate-200 rounded-lg max-w-2xl w-full p-6 shadow-xl relative max-h-[90vh] flex flex-col">
      <div class="flex items-center justify-between pb-3 border-b border-slate-200">
        <div class="flex items-center gap-2">
          <FileCode class="w-4 h-4 text-slate-600" />
          <h3 class="text-sm font-bold text-slate-900">
            Detail Metadata Postingan
          </h3>
        </div>
        <button
          type="button"
          onclick={() => (selectedPostForDetail = null)}
          class="text-slate-400 hover:text-slate-600"
          title="Tutup dialog"
        >
          <X class="w-4 h-4" />
        </button>
      </div>

      <div class="overflow-y-auto my-4 space-y-4 text-xs font-mono text-slate-700 pr-1">
        <div class="grid grid-cols-2 gap-3 bg-slate-50 p-3.5 rounded border border-slate-200">
          <div>
            <span class="text-slate-400 block text-[10px] uppercase">ID POSTINGAN</span>
            <span class="text-slate-900 font-bold">{selectedPostForDetail.id}</span>
          </div>
          <div>
            <span class="text-slate-400 block text-[10px] uppercase">AKUN PENULIS</span>
            <span class="text-slate-900 font-bold">@{selectedPostForDetail.author_username}</span>
          </div>
          <div>
            <span class="text-slate-400 block text-[10px] uppercase">WAKTU POSTING</span>
            <span class="text-slate-800 font-medium">{modalDate.fullStr}</span>
          </div>
          <div>
            <span class="text-slate-400 block text-[10px] uppercase">INTERAKSI</span>
            <span class="text-slate-800">
              {selectedPostForDetail.likes_count} suka, {selectedPostForDetail.replies_count} balasan, {selectedPostForDetail.reposts_count} repost
            </span>
          </div>
        </div>

        <div>
          <span class="text-slate-700 block text-[11px] mb-1 font-bold uppercase">LINK THREADS</span>
          <div class="flex items-center gap-2 bg-slate-50 p-2.5 rounded border border-slate-200">
            <span class="truncate flex-1 text-slate-700">{selectedPostForDetail.post_url}</span>
            <a
              href={selectedPostForDetail.post_url}
              target="_blank"
              rel="noopener noreferrer"
              class="px-2.5 py-1 rounded bg-slate-900 text-white font-sans text-xs hover:bg-slate-800 shrink-0 inline-flex items-center gap-1 shadow-2xs"
            >
              <span>Buka Link</span>
              <ExternalLink class="w-3 h-3" />
            </a>
          </div>
        </div>

        <div>
          <span class="text-slate-700 block text-[11px] mb-1 font-bold uppercase">ISI POSTINGAN</span>
          <div class="p-3 bg-slate-50 rounded border border-slate-200 text-slate-900 font-sans leading-relaxed whitespace-pre-wrap">
            {selectedPostForDetail.content}
          </div>
        </div>

        <div>
          <span class="text-slate-700 block text-[11px] mb-1 font-bold uppercase">ANALISIS SENTIMEN</span>
          <div class="p-3 bg-slate-50 rounded border border-slate-200 space-y-2">
            <div class="flex items-center gap-4 flex-wrap">
              <span>Sentimen: <strong class="text-slate-900 uppercase">{selectedPostForDetail.sentiment?.sentiment_label}</strong></span>
              <span>Keyakinan: <strong>{((selectedPostForDetail.sentiment?.confidence_score || 0) * 100).toFixed(1)}%</strong></span>
              <span>Emosi: <strong>{selectedPostForDetail.sentiment?.primary_emotion}</strong></span>
            </div>
            <div>Lokasi: <span class="text-slate-800 font-medium">{selectedPostForDetail.sentiment?.locations?.join(', ') || '-'}</span></div>
            <div>Topik/Entitas: <span class="text-slate-800 font-medium">{selectedPostForDetail.sentiment?.entities?.join(', ') || '-'}</span></div>
            <div class="text-slate-600 italic">Alasan: {selectedPostForDetail.sentiment?.summary_reason}</div>
          </div>
        </div>

        {#if selectedPostForDetail.raw_metadata}
          <div>
            <span class="text-slate-700 block text-[11px] mb-1 font-bold uppercase">DATA MENTAH (JSON)</span>
            <pre class="p-3 bg-slate-50 rounded border border-slate-200 overflow-x-auto text-[11px] text-slate-700">
{JSON.stringify(selectedPostForDetail.raw_metadata, null, 2)}
            </pre>
          </div>
        {/if}
      </div>

      <div class="pt-3 border-t border-slate-200 flex justify-end">
        <button
          type="button"
          onclick={() => (selectedPostForDetail = null)}
          class="px-4 py-1.5 text-xs font-medium rounded bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 transition-colors shadow-2xs"
        >
          Tutup
        </button>
      </div>
    </div>
  </div>
{/if}

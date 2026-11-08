<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { RefreshCw, Play, CheckCircle2, Clock, Loader2, X } from 'lucide-svelte';
  import { triggerScraperJob, fetchScraperLogs, resetStuckJobs } from '#lib/api';
  import type { ScraperLog } from '#lib/types';

  interface Props {
    onRefresh: () => void;
    lastUpdated?: string;
    isRefreshing?: boolean;
  }

  let { onRefresh, lastUpdated = '', isRefreshing = false }: Props = $props();

  let isModalOpen = $state(false);
  let customKeyword = $state('');
  let selectedMethod = $state('playwright');
  let maxPosts = $state(25);
  let clearExisting = $state(false);
  let isTriggering = $state(false);
  let triggerNotice = $state<string | null>(null);

  // Background scraper job tracking
  let activeJob = $state<ScraperLog | null>(null);
  let pollInterval: ReturnType<typeof setInterval> | null = null;
  let elapsedSeconds = $state(0);
  let timerInterval: ReturnType<typeof setInterval> | null = null;
  let completionNotification = $state<string | null>(null);
  let isResetting = $state(false);

  const presetKeywords = [
    'Karhutla',
    'Timnas Indonesia',
    'Kecerdasan Buatan',
    'Kuliner',
    'Cuaca Ekstrem',
    'Kebijakan Publik'
  ];

  function startTimer() {
    if (timerInterval) return;
    elapsedSeconds = 0;
    timerInterval = setInterval(() => {
      elapsedSeconds += 1;
    }, 1000);
  }

  function stopTimer() {
    if (timerInterval) {
      clearInterval(timerInterval);
      timerInterval = null;
    }
    elapsedSeconds = 0;
  }

  async function checkScraperStatus() {
    try {
      const logs = await fetchScraperLogs(3);
      if (!logs || logs.length === 0) return;
      const latest = logs[0];
      if (latest.status === 'running' || latest.status === 'queued') {
        activeJob = latest;
        startPolling();
        startTimer();
      } else {
        if (activeJob && (latest.status === 'success' || latest.status === 'failed')) {
          activeJob = null;
          stopPolling();
          stopTimer();
          if (latest.status === 'success') {
            completionNotification = `Selesai: ${latest.posts_found} post ditemukan, ${latest.posts_inserted} data baru disimpan.`;
          } else {
            completionNotification = `Gagal: ${latest.error_message || 'Terjadi gangguan koneksi'}`;
          }
          onRefresh();
          setTimeout(() => {
            completionNotification = null;
          }, 6000);
        } else {
          activeJob = null;
          stopTimer();
        }
      }
    } catch {
      // Ignore polling errors
    }
  }

  function startPolling() {
    if (pollInterval) return;
    pollInterval = setInterval(checkScraperStatus, 3000);
  }

  function stopPolling() {
    if (pollInterval) {
      clearInterval(pollInterval);
      pollInterval = null;
    }
  }

  async function handleResetStuck() {
    isResetting = true;
    try {
      await resetStuckJobs();
      activeJob = null;
      stopPolling();
      stopTimer();
      completionNotification = 'Proses berhasil dibatalkan.';
      onRefresh();
      setTimeout(() => {
        completionNotification = null;
      }, 4000);
    } catch (e: any) {
      console.error('Reset scraper error:', e);
    } finally {
      isResetting = false;
    }
  }

  onMount(() => {
    checkScraperStatus();
  });

  onDestroy(() => {
    stopPolling();
    stopTimer();
  });

  async function handleTrigger() {
    isTriggering = true;
    triggerNotice = null;
    try {
      const kw = customKeyword.trim() || presetKeywords[0];
      const kws = [kw];
      await triggerScraperJob(kws, selectedMethod, maxPosts, clearExisting);
      triggerNotice = clearExisting
        ? `Memulai pencarian "${kw}" (${maxPosts} post, data lama dihapus)...`
        : `Memulai pencarian "${kw}" (${maxPosts} post) di latar belakang...`;
      setTimeout(() => {
        isModalOpen = false;
        triggerNotice = null;
        clearExisting = false;
        checkScraperStatus();
      }, 1200);
    } catch (e: any) {
      triggerNotice = `Gagal: ${e.message}`;
    } finally {
      isTriggering = false;
    }
  }
</script>

<header class="border-b border-slate-200 bg-white px-6 py-4 sticky top-0 z-30 shadow-xs">
  <div class="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center md:justify-between gap-4">
    <!-- Brand Identity & Topic Scope -->
    <div>
      <div class="flex items-center gap-2.5">
        <h1 class="text-base font-bold tracking-tight text-slate-900">
          ThreadScope
        </h1>
        <span class="flex items-center gap-1.5 text-[11px] text-emerald-700 font-mono bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
          <span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
          Aktif
        </span>
      </div>
      <p class="text-xs text-slate-500 mt-0.5">
        Pantau sentimen dan percakapan publik di Threads
      </p>
    </div>

    <!-- Actions & Job Feedback Status -->
    <div class="flex items-center flex-wrap gap-2.5">
      {#if activeJob}
        <div class="flex items-center gap-2 px-3 py-1.5 rounded bg-amber-50 border border-amber-200 text-xs font-mono text-amber-900">
          <Loader2 class="w-3.5 h-3.5 animate-spin text-amber-600 shrink-0" />
          <div class="flex items-center gap-1.5">
            <span>Mencari "{activeJob.keyword}"...</span>
            <span class="text-amber-700 font-bold">({elapsedSeconds}s)</span>
          </div>
          {#if elapsedSeconds >= 30}
            <button
              type="button"
              onclick={handleResetStuck}
              disabled={isResetting}
              class="ml-2 text-[11px] text-red-600 hover:text-red-700 underline font-sans"
              title="Batalkan proses"
            >
              {isResetting ? 'Membatalkan...' : 'Batal'}
            </button>
          {/if}
        </div>
      {:else if completionNotification}
        <div class="flex items-center gap-2 px-3 py-1.5 rounded bg-emerald-50 border border-emerald-200 text-xs font-mono text-emerald-800">
          <CheckCircle2 class="w-3.5 h-3.5 text-emerald-600 shrink-0" />
          <span>{completionNotification}</span>
        </div>
      {/if}

      {#if lastUpdated}
        <div class="hidden sm:flex items-center gap-1.5 text-xs text-slate-500 font-mono bg-slate-50 px-3 py-1.5 rounded border border-slate-200">
          <Clock class="w-3.5 h-3.5 text-slate-400" />
          <span>Update: {new Date(lastUpdated).toLocaleTimeString('id-ID')}</span>
        </div>
      {/if}

      <button
        type="button"
        onclick={onRefresh}
        disabled={isRefreshing}
        class="inline-flex items-center gap-2 px-3 py-1.5 text-xs font-medium rounded bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 transition-colors disabled:opacity-50 shadow-2xs"
        title="Muat ulang data"
      >
        <RefreshCw class="w-3.5 h-3.5 {isRefreshing ? 'animate-spin text-slate-800' : 'text-slate-500'}" />
        <span>Segarkan</span>
      </button>

      <button
        type="button"
        onclick={() => { isModalOpen = true; clearExisting = false; }}
        class="inline-flex items-center gap-2 px-3.5 py-1.5 text-xs font-medium rounded bg-slate-900 hover:bg-slate-800 text-white shadow-xs transition-colors"
      >
        <Play class="w-3 h-3 fill-white" />
        <span>Cari Topik Baru</span>
      </button>
    </div>
  </div>
</header>

<!-- Modal Trigger Scraper -->
{#if isModalOpen}
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-2xs p-4">
    <div class="bg-white border border-slate-200 rounded-lg max-w-md w-full p-6 shadow-xl relative">
      <div class="flex items-start justify-between pb-3 border-b border-slate-100">
        <div>
          <h3 class="text-sm font-bold text-slate-900">
            Cari &amp; Ambil Data Threads
          </h3>
          <p class="text-xs text-slate-500 mt-0.5">
            Cari postingan publik di Threads dan analisis sentimennya.
          </p>
        </div>
        <button
          type="button"
          onclick={() => (isModalOpen = false)}
          class="text-slate-400 hover:text-slate-600 transition-colors p-1"
          title="Tutup dialog"
        >
          <X class="w-4 h-4" />
        </button>
      </div>

      <div class="mt-4 space-y-4">
        <div>
          <label for="kw-input" class="block text-xs font-medium text-slate-700 mb-1">
            Kata Kunci / Topik
          </label>
          <input
            id="kw-input"
            type="text"
            bind:value={customKeyword}
            placeholder="Ketik topik apa saja... (misal: AI, Timnas, Karhutla, Kuliner, IKN)"
            class="w-full bg-white border border-slate-300 rounded px-3 py-2 text-xs text-slate-900 focus:outline-none focus:border-slate-800 font-mono shadow-2xs"
          />
          <div class="flex flex-wrap gap-1.5 mt-2">
            {#each presetKeywords as kw}
              <button
                type="button"
                onclick={() => (customKeyword = kw)}
                class="text-[11px] px-2 py-0.5 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 font-mono transition-colors border border-slate-200"
              >
                #{kw}
              </button>
            {/each}
          </div>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label for="method-select" class="block text-xs font-medium text-slate-700 mb-1">
              Metode
            </label>
            <select
              id="method-select"
              bind:value={selectedMethod}
              class="w-full bg-white border border-slate-300 rounded px-2.5 py-1.5 text-xs text-slate-900 focus:outline-none focus:border-slate-800 shadow-2xs"
            >
              <option value="playwright">Playwright</option>
              <option value="official_api">Official API</option>
            </select>
          </div>

          <div>
            <label for="limit-select" class="block text-xs font-medium text-slate-700 mb-1">
              Jumlah Postingan
            </label>
            <select
              id="limit-select"
              bind:value={maxPosts}
              class="w-full bg-white border border-slate-300 rounded px-2.5 py-1.5 text-xs text-slate-900 focus:outline-none focus:border-slate-800 font-mono shadow-2xs"
            >
              <option value={25}>25 Post (Cepat)</option>
              <option value={50}>50 Post (Sedang)</option>
              <option value={100}>100 Post (Banyak)</option>
              <option value={150}>150 Post (Lengkap)</option>
              <option value={200}>200 Post (Maksimal)</option>
            </select>
          </div>
        </div>

        <div class="rounded-md border p-3 transition-colors {clearExisting ? 'bg-red-50 border-red-200' : 'bg-slate-50 border-slate-200'}">
          <label class="flex items-start gap-3 cursor-pointer select-none">
            <input
              type="checkbox"
              bind:checked={clearExisting}
              class="mt-0.5 w-4 h-4 rounded border-slate-300 bg-white text-red-600 focus:ring-red-500/20 cursor-pointer accent-red-600"
            />
            <div class="space-y-0.5">
              <span class="text-xs font-medium text-slate-900 block">
                Hapus data sebelumnya
              </span>
              <p class="text-[11px] {clearExisting ? 'text-red-700' : 'text-slate-500'} leading-relaxed">
                {#if clearExisting}
                  Data lama akan dihapus dan diganti dengan hasil pencarian baru.
                {:else}
                  Data baru akan ditambahkan tanpa menghapus data yang sudah ada.
                {/if}
              </p>
            </div>
          </label>
        </div>

        {#if triggerNotice}
          <div class="p-2.5 rounded bg-slate-50 border border-slate-200 text-xs flex items-start gap-2 text-slate-800 font-mono">
            <CheckCircle2 class="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
            <span>{triggerNotice}</span>
          </div>
        {/if}
      </div>

      <div class="mt-6 flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
        <button
          type="button"
          disabled={isTriggering}
          onclick={() => (isModalOpen = false)}
          class="px-3.5 py-1.5 text-xs font-medium rounded bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 transition-colors shadow-2xs"
        >
          Batal
        </button>
        <button
          type="button"
          disabled={isTriggering}
          onclick={handleTrigger}
          class="px-4 py-1.5 text-xs font-medium rounded text-white transition-colors flex items-center gap-1.5 shadow-xs {clearExisting ? 'bg-red-600 hover:bg-red-700' : 'bg-slate-900 hover:bg-slate-800'}"
        >
          {#if isTriggering}
            <RefreshCw class="w-3.5 h-3.5 animate-spin" />
            <span>Memproses...</span>
          {:else}
            <span>Mulai Cari</span>
          {/if}
        </button>
      </div>
    </div>
  </div>
{/if}

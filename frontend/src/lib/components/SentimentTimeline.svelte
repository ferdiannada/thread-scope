<script lang="ts">
  import type { TimelinePoint, EmotionSummary } from '#lib/types';
  import { Clock, Calendar } from 'lucide-svelte';

  interface Props {
    timeline: TimelinePoint[];
    emotions?: EmotionSummary;
    currentGranularity?: 'hour' | 'day';
    currentDays?: number;
    onTimelineConfigChange?: (granularity: 'hour' | 'day', days: number) => void;
    onTimeSelect?: (timestamp: string) => void;
  }

  let {
    timeline = [],
    emotions,
    currentGranularity = 'hour',
    currentDays = 3,
    onTimelineConfigChange,
    onTimeSelect,
  }: Props = $props();

  let hoveredPoint = $state<TimelinePoint | null>(null);

  // Computed metrics
  const totalVol = $derived(timeline.reduce((acc, p) => acc + p.total, 0));
  const totalNeg = $derived(timeline.reduce((acc, p) => acc + p.negative, 0));
  const totalNeu = $derived(timeline.reduce((acc, p) => acc + p.neutral, 0));
  const totalPos = $derived(timeline.reduce((acc, p) => acc + p.positive, 0));

  const maxTotal = $derived(Math.max(1, ...timeline.map((p) => p.total)));

  // Peak activity point
  const peakPoint = $derived(
    timeline.length > 0
      ? [...timeline].sort((a, b) => b.total - a.total)[0]
      : null
  );

  // Net Sentiment Index (-100 to +100)
  const netSentimentScore = $derived(
    totalVol > 0 ? Math.round(((totalPos - totalNeg) / totalVol) * 100) : 0
  );

  function handleGranularity(gran: 'hour' | 'day') {
    onTimelineConfigChange?.(gran, currentDays);
  }

  function handleDays(days: number) {
    onTimelineConfigChange?.(currentGranularity, days);
  }
</script>

<div class="bg-white border border-slate-200 rounded-lg p-6 shadow-2xs">
  <!-- Chart Top Header -->
  <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-slate-200">
    <div>
      <div class="flex items-center gap-2">
        <h2 class="text-sm font-bold text-slate-900 uppercase tracking-wider">
          Tren Sentimen
        </h2>
        <span class="text-[11px] px-2 py-0.5 rounded bg-slate-100 border border-slate-200 font-mono text-slate-700">
          {totalVol} Postingan
        </span>
      </div>
      <p class="text-xs text-slate-500 mt-0.5">
        Perkembangan sentimen dan volume postingan dari waktu ke waktu
      </p>
    </div>

    <!-- Controls: Granularity & Days Filter -->
    <div class="flex items-center gap-2.5 flex-wrap text-xs font-mono">
      <!-- Hourly / Daily Toggle -->
      <div class="flex items-center bg-slate-100 p-0.5 rounded-md border border-slate-200">
        <button
          type="button"
          onclick={() => handleGranularity('hour')}
          class="px-2.5 py-1 rounded text-xs transition-colors flex items-center gap-1.5 {currentGranularity === 'hour' ? 'bg-white text-slate-900 font-semibold shadow-2xs' : 'text-slate-600 hover:text-slate-900'}"
        >
          <Clock class="w-3 h-3 text-slate-500" />
          <span>Per Jam</span>
        </button>
        <button
          type="button"
          onclick={() => handleGranularity('day')}
          class="px-2.5 py-1 rounded text-xs transition-colors flex items-center gap-1.5 {currentGranularity === 'day' ? 'bg-white text-slate-900 font-semibold shadow-2xs' : 'text-slate-600 hover:text-slate-900'}"
        >
          <Calendar class="w-3 h-3 text-slate-500" />
          <span>Per Hari</span>
        </button>
      </div>

      <!-- Time range buttons -->
      <div class="flex items-center bg-slate-100 p-0.5 rounded-md border border-slate-200">
        <button
          type="button"
          onclick={() => handleDays(1)}
          class="px-2.5 py-1 rounded text-xs transition-colors {currentDays === 1 ? 'bg-white text-slate-900 font-semibold shadow-2xs' : 'text-slate-600 hover:text-slate-900'}"
        >
          24 Jam
        </button>
        <button
          type="button"
          onclick={() => handleDays(3)}
          class="px-2.5 py-1 rounded text-xs transition-colors {currentDays === 3 ? 'bg-white text-slate-900 font-semibold shadow-2xs' : 'text-slate-600 hover:text-slate-900'}"
        >
          3 Hari
        </button>
        <button
          type="button"
          onclick={() => handleDays(7)}
          class="px-2.5 py-1 rounded text-xs transition-colors {currentDays === 7 ? 'bg-white text-slate-900 font-semibold shadow-2xs' : 'text-slate-600 hover:text-slate-900'}"
        >
          7 Hari
        </button>
      </div>
    </div>
  </div>

  <!-- Real-Time Analytical Insight Bar -->
  <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 my-4 bg-slate-50 p-3.5 rounded-lg border border-slate-200 text-xs font-mono">
    <div>
      <span class="text-slate-500 text-[10px] block uppercase tracking-wider">INDEKS SENTIMEN</span>
      <span class="text-base font-bold {netSentimentScore < 0 ? 'text-red-700' : 'text-emerald-700'}">
        {netSentimentScore > 0 ? `+${netSentimentScore}` : netSentimentScore}%
        <span class="text-[11px] font-normal text-slate-500 font-sans ml-1">
          ({netSentimentScore < -20 ? 'Cenderung Negatif' : netSentimentScore > 20 ? 'Cenderung Positif' : 'Seimbang'})
        </span>
      </span>
    </div>

    <div>
      <span class="text-slate-500 text-[10px] block uppercase tracking-wider">WAKTU TERBANYAK</span>
      <span class="text-sm font-bold text-slate-800">
        {peakPoint ? `${peakPoint.display_label || peakPoint.timestamp} (${peakPoint.total} post)` : '-'}
      </span>
    </div>

    <div class="flex items-center justify-between sm:justify-end gap-3 text-[11px]">
      <div class="flex items-center gap-1.5">
        <span class="w-2.5 h-2.5 rounded-xs bg-red-600"></span>
        <span class="text-slate-700 font-medium">Negatif: {totalNeg}</span>
      </div>
      <div class="flex items-center gap-1.5">
        <span class="w-2.5 h-2.5 rounded-xs bg-slate-400"></span>
        <span class="text-slate-700 font-medium">Netral: {totalNeu}</span>
      </div>
      <div class="flex items-center gap-1.5">
        <span class="w-2.5 h-2.5 rounded-xs bg-emerald-600"></span>
        <span class="text-slate-700 font-medium">Positif: {totalPos}</span>
      </div>
    </div>
  </div>

  <!-- Dynamic Chart Display -->
  <div class="mt-4">
    {#if timeline.length === 0}
      <div class="h-52 flex items-center justify-center text-xs text-slate-500 font-mono">
        Belum ada data untuk rentang waktu ini.
      </div>
    {:else}
      <!-- Chart Container with Y Axis Gridlines -->
      <div class="relative pt-6 pb-2 border-b border-slate-200">
        <!-- Floating Hover Tooltip -->
        {#if hoveredPoint}
          <div class="absolute -top-1 left-1/2 -translate-x-1/2 bg-white border border-slate-300 px-4 py-2 rounded shadow-lg text-xs font-mono flex items-center gap-4 z-20 pointer-events-none transition-all">
            <div>
              <span class="text-[10px] text-slate-400 block uppercase">WAKTU</span>
              <span class="text-slate-900 font-bold">{hoveredPoint.display_label || hoveredPoint.timestamp}</span>
            </div>
            <div>
              <span class="text-[10px] text-slate-400 block uppercase">JUMLAH</span>
              <div class="flex items-center gap-2">
                <span class="text-red-700">Neg: {hoveredPoint.negative}</span>
                <span class="text-slate-600">Neu: {hoveredPoint.neutral}</span>
                <span class="text-emerald-700">Pos: {hoveredPoint.positive}</span>
              </div>
            </div>
            <div class="border-l border-slate-200 pl-3">
              <span class="text-[10px] text-slate-400 block uppercase">SKOR</span>
              <span class="font-bold {hoveredPoint.net_score && hoveredPoint.net_score < 0 ? 'text-red-700' : 'text-emerald-700'}">
                {hoveredPoint.net_score}%
              </span>
            </div>
          </div>
        {/if}

        <!-- Bar Series -->
        <div class="h-44 flex items-end gap-1.5 sm:gap-2 px-2 overflow-x-auto">
          {#each timeline as point}
            {@const negHeight = (point.negative / maxTotal) * 120}
            {@const neuHeight = (point.neutral / maxTotal) * 120}
            {@const posHeight = (point.positive / maxTotal) * 120}
            {@const isPeak = peakPoint && point.timestamp === peakPoint.timestamp}
            
            <button
              type="button"
              onclick={() => onTimeSelect?.(point.timestamp)}
              onmouseenter={() => (hoveredPoint = point)}
              onmouseleave={() => (hoveredPoint = null)}
              class="flex-1 min-w-[28px] max-w-[50px] flex flex-col items-center justify-end h-full group relative focus:outline-none"
              title="Klik untuk filter postingan waktu ini"
            >
              <!-- Total count marker above bar -->
              <span class="text-[10px] font-mono text-slate-400 mb-1 group-hover:text-slate-900 font-bold transition-colors">
                {point.total}
              </span>

              <!-- Stacked Color Bar -->
              <div class="w-full rounded-t overflow-hidden bg-slate-100 border {isPeak ? 'border-slate-800 ring-1 ring-slate-800' : 'border-slate-200'} group-hover:border-slate-400 transition-colors flex flex-col-reverse">
                {#if point.negative > 0}
                  <div class="w-full bg-red-600 hover:bg-red-500 transition-colors" style="height: {Math.max(4, negHeight)}px"></div>
                {/if}
                {#if point.neutral > 0}
                  <div class="w-full bg-slate-400 hover:bg-slate-300 transition-colors" style="height: {Math.max(4, neuHeight)}px"></div>
                {/if}
                {#if point.positive > 0}
                  <div class="w-full bg-emerald-600 hover:bg-emerald-500 transition-colors" style="height: {Math.max(4, posHeight)}px"></div>
                {/if}
              </div>

              <!-- Time Axis Label -->
              <span class="text-[10px] font-mono text-slate-500 mt-2 truncate w-full text-center group-hover:text-slate-900">
                {point.display_label ? point.display_label.split(' ')[1] || point.display_label : point.timestamp.slice(5)}
              </span>
            </button>
          {/each}
        </div>
      </div>
    {/if}
  </div>

  <!-- Emotion Spectrum Breakdown -->
  {#if emotions}
    <div class="mt-5 pt-4 border-t border-slate-200">
      <div class="flex items-center justify-between mb-2">
        <span class="text-[11px] font-semibold text-slate-600 uppercase tracking-wider">
          Rincian Emosi
        </span>
        <span class="text-[10px] font-mono text-slate-500">Total: {totalVol} post</span>
      </div>
      <div class="grid grid-cols-2 sm:grid-cols-5 gap-2.5">
        <div class="bg-red-50/70 border border-red-200 rounded p-2.5 flex items-center justify-between text-xs">
          <div>
            <span class="text-red-800 block text-[11px] font-semibold">Marah</span>
            <span class="text-[10px] text-red-600 font-mono">Kritik atau protes</span>
          </div>
          <span class="font-bold num-mono text-red-700 text-sm">{emotions.anger}</span>
        </div>
        <div class="bg-amber-50/70 border border-amber-200 rounded p-2.5 flex items-center justify-between text-xs">
          <div>
            <span class="text-amber-800 block text-[11px] font-semibold">Cemas</span>
            <span class="text-[10px] text-amber-600 font-mono">Khawatir atau resah</span>
          </div>
          <span class="font-bold num-mono text-amber-700 text-sm">{emotions.anxiety}</span>
        </div>
        <div class="bg-sky-50/70 border border-sky-200 rounded p-2.5 flex items-center justify-between text-xs">
          <div>
            <span class="text-sky-800 block text-[11px] font-semibold">Sedih</span>
            <span class="text-[10px] text-sky-600 font-mono">Kecewa atau prihatin</span>
          </div>
          <span class="font-bold num-mono text-sky-700 text-sm">{emotions.sadness}</span>
        </div>
        <div class="bg-emerald-50/70 border border-emerald-200 rounded p-2.5 flex items-center justify-between text-xs">
          <div>
            <span class="text-emerald-800 block text-[11px] font-semibold">Harapan</span>
            <span class="text-[10px] text-emerald-600 font-mono">Dukungan atau doa</span>
          </div>
          <span class="font-bold num-mono text-emerald-700 text-sm">{emotions.hope}</span>
        </div>
        <div class="bg-slate-50 border border-slate-200 rounded p-2.5 flex items-center justify-between text-xs">
          <div>
            <span class="text-slate-800 block text-[11px] font-semibold">Netral</span>
            <span class="text-[10px] text-slate-500 font-mono">Berita atau info umum</span>
          </div>
          <span class="font-bold num-mono text-slate-700 text-sm">{emotions.neutral}</span>
        </div>
      </div>
    </div>
  {/if}
</div>

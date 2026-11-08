<script lang="ts">
  import type { RegionalFactReport, EntityMetric } from '#lib/types';
  import { ArrowRight } from 'lucide-svelte';

  interface Props {
    regionalReports?: RegionalFactReport[];
    locations?: EntityMetric[];
    entities?: EntityMetric[];
    onFilterSelect: (filterType: 'location' | 'keyword', val: string) => void;
  }

  let { regionalReports = [], locations = [], entities = [], onFilterSelect }: Props = $props();

  function getStatusStyle(status: string) {
    switch (status) {
      case 'Kritis':
        return {
          bg: 'bg-red-50',
          text: 'text-red-700',
          border: 'border-red-200',
          indicator: 'bg-red-600',
        };
      case 'Waspada':
        return {
          bg: 'bg-amber-50',
          text: 'text-amber-700',
          border: 'border-amber-200',
          indicator: 'bg-amber-500',
        };
      default:
        return {
          bg: 'bg-emerald-50',
          text: 'text-emerald-700',
          border: 'border-emerald-200',
          indicator: 'bg-emerald-500',
        };
    }
  }
</script>

<div class="space-y-4">
  <!-- Section Title -->
  <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 bg-white border border-slate-200 rounded-lg p-4 shadow-2xs">
    <div>
      <h2 class="text-sm font-bold uppercase tracking-wider text-slate-900">
        Wilayah &amp; Lokasi Terkait
      </h2>
      <p class="text-xs text-slate-500 mt-0.5">
        Daerah yang paling sering disebut dalam postingan warganet
      </p>
    </div>
    <span class="text-[11px] font-mono px-2.5 py-1 rounded bg-slate-50 text-slate-700 border border-slate-200 shrink-0">
      {regionalReports.length} Daerah
    </span>
  </div>

  <!-- Regional Grid -->
  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
    {#if regionalReports.length === 0}
      <div class="col-span-full bg-white border border-slate-200 rounded-lg p-8 text-center text-xs text-slate-500 font-mono shadow-2xs">
        Belum ada data wilayah. Silakan cari topik baru untuk melihat lokasi terkait.
      </div>
    {:else}
      {#each regionalReports as reg}
        {@const style = getStatusStyle(reg.status)}
        <div class="bg-white border border-slate-200 hover:border-slate-300 rounded-lg p-5 flex flex-col justify-between transition-all shadow-2xs">
          <div>
            <!-- Region Header & Status Badge -->
            <div class="flex items-start justify-between gap-3 pb-3 border-b border-slate-100">
              <div>
                <h3 class="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <span class="w-2 h-2 rounded-full {style.indicator}"></span>
                  {reg.region_name}
                </h3>
                <span class="text-[11px] font-mono text-slate-500">
                  {reg.total_reports} postingan
                </span>
              </div>

              <span class="text-[11px] px-2 py-0.5 rounded font-mono font-semibold border {style.bg} {style.text} {style.border}">
                {reg.status.toUpperCase()}
              </span>
            </div>

            <!-- Negative percentage progress bar -->
            <div class="my-3 bg-slate-50 p-2.5 rounded border border-slate-200">
              <div class="flex items-center justify-between text-xs font-mono mb-1.5">
                <span class="text-slate-600 text-[11px]">Porsi Negatif:</span>
                <span class="font-bold {reg.negative_percentage > 50 ? 'text-red-700' : 'text-slate-700'}">
                  {reg.negative_percentage}%
                </span>
              </div>
              <div class="w-full bg-slate-200 rounded-full h-1.5 overflow-hidden">
                <div
                  class="h-full rounded-full transition-all duration-300 {reg.negative_percentage > 50 ? 'bg-red-600' : 'bg-amber-500'}"
                  style="width: {reg.negative_percentage}%"
                ></div>
              </div>
            </div>

            <!-- Key Issues -->
            <div class="mb-3">
              <span class="text-[10px] font-mono text-slate-500 uppercase tracking-wider block mb-1.5">
                Topik Terkait:
              </span>
              <div class="flex flex-wrap gap-1.5">
                {#each reg.key_issues as issue}
                  <span class="text-[11px] px-2 py-0.5 rounded bg-slate-50 text-slate-700 border border-slate-200 font-sans flex items-center gap-1.5">
                    <span class="w-1 h-1 rounded-full bg-slate-400"></span>
                    {issue}
                  </span>
                {/each}
              </div>
            </div>

            <!-- Direct Citizen Quote -->
            {#if reg.sample_citizen_voice}
              <div class="mb-3 bg-slate-50 border-l-2 border-slate-400 p-2.5 rounded-r text-xs text-slate-700 italic leading-relaxed">
                "{reg.sample_citizen_voice}"
              </div>
            {/if}

            <!-- Affected Cities / Districts -->
            {#if reg.affected_cities && reg.affected_cities.length > 0}
              <div class="text-[11px] text-slate-500 font-mono flex items-center gap-1 flex-wrap">
                <span>Daerah:</span>
                {#each reg.affected_cities as city}
                  <span class="px-1.5 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
                    {city}
                  </span>
                {/each}
              </div>
            {/if}
          </div>

          <!-- Click to filter action button -->
          <div class="mt-4 pt-3 border-t border-slate-100">
            <button
              type="button"
              onclick={() => onFilterSelect('location', reg.region_name.split(' ')[0])}
              class="w-full py-1.5 px-3 rounded bg-slate-50 hover:bg-slate-100 text-slate-800 border border-slate-200 text-xs font-mono font-medium flex items-center justify-center gap-2 group transition-colors shadow-2xs"
            >
              <span>Lihat Postingan {reg.region_name}</span>
              <ArrowRight class="w-3.5 h-3.5 text-slate-500 group-hover:translate-x-1 transition-transform" />
            </button>
          </div>
        </div>
      {/each}
    {/if}
  </div>

  <!-- Key Entities Bar -->
  <div class="bg-white border border-slate-200 rounded-lg p-5 shadow-2xs">
    <div class="flex items-center justify-between pb-2.5 border-b border-slate-100">
      <div>
        <h3 class="text-xs font-bold uppercase tracking-wider text-slate-900">
          Kata Kunci &amp; Topik Terpopuler
        </h3>
        <p class="text-[11px] text-slate-500 mt-0.5">
          Klik kata kunci untuk menyaring postingan terkait
        </p>
      </div>
      <span class="text-[11px] font-mono text-slate-500">{entities.length} Topik</span>
    </div>

    <div class="flex flex-wrap gap-2 mt-3.5">
      {#if entities.length === 0}
        <span class="text-xs text-slate-400 font-mono">Belum ada data topik.</span>
      {:else}
        {#each entities as ent}
          <button
            type="button"
            onclick={() => onFilterSelect('keyword', ent.name)}
            class="flex items-center gap-2 px-3 py-1.5 rounded bg-slate-50 border border-slate-200 hover:border-slate-400 hover:bg-slate-100 transition-colors text-xs text-slate-800 shadow-2xs"
          >
            <span class="font-mono font-semibold text-slate-900">#{ent.name}</span>
            <span class="px-1.5 py-0.2 rounded bg-slate-200 text-slate-700 text-[10px] font-mono">
              {ent.count} post
            </span>
            {#if ent.negative_ratio > 0}
              <span class="text-[10px] font-mono text-red-700 font-medium">
                ({(ent.negative_ratio * 100).toFixed(0)}% negatif)
              </span>
            {/if}
          </button>
        {/each}
      {/if}
    </div>
  </div>
</div>

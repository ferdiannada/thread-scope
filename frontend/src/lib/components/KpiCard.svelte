<script lang="ts">
  interface Props {
    title: string;
    value: string | number;
    subtitle?: string;
    trendLabel?: string;
    trendPositive?: boolean;
    barPercent?: number;
    barColor?: string;
    accentColor?: string;
  }

  let {
    title,
    value,
    subtitle = '',
    trendLabel = '',
    trendPositive = false,
    barPercent = 0,
    barColor = 'bg-slate-400',
    accentColor = 'text-slate-600',
  }: Props = $props();
</script>

<div class="bg-white border border-slate-200 rounded-lg p-5 flex flex-col justify-between shadow-2xs hover:border-slate-300 transition-colors">
  <div>
    <div class="flex items-center justify-between">
      <span class="font-medium uppercase tracking-wider text-[11px] text-slate-500">
        {title}
      </span>
      {#if trendLabel && barPercent > 0}
        <span class="text-[11px] font-mono font-semibold px-1.5 py-0.2 rounded bg-slate-100 text-slate-700 border border-slate-200">
          {barPercent.toFixed(1)}%
        </span>
      {/if}
    </div>

    <div class="my-3">
      <div class="text-3xl font-bold num-mono text-slate-900 tracking-tight">
        {value}
      </div>
      {#if subtitle}
        <div class="text-xs text-slate-500 mt-1">
          {subtitle}
        </div>
      {/if}
    </div>
  </div>

  {#if barPercent > 0}
    <div class="mt-2">
      <div class="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
        <div
          class="h-full rounded-full transition-all duration-300 {barColor}"
          style="width: {Math.min(barPercent, 100)}%"
        ></div>
      </div>
      {#if trendLabel}
        <div class="text-[11px] font-mono mt-1.5 flex items-center justify-between text-slate-400">
          <span>{trendLabel}</span>
        </div>
      {/if}
    </div>
  {/if}
</div>

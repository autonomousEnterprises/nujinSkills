<template>
  <div class="w-full flex flex-col gap-2 font-mono">
    <!-- Header -->
    <div class="flex items-center justify-between pb-1 border-b border-base-content/10 text-xs">
      <span class="font-bold uppercase tracking-wider text-[11px] text-base-content">{{ title || 'Trade Return Distribution' }}</span>
      <span class="text-[10px] text-base-content/60">{{ totalCount }} Closed Trades Simulated</span>
    </div>

    <!-- Bars Container -->
    <div class="rounded-box bg-base-200/40 p-3 border border-base-content/10 flex flex-col gap-2">
      <div class="flex items-end justify-between gap-2 h-24 pt-2 px-1 border-b border-base-content/10">
        <div 
          v-for="(bin, idx) in formattedBins" 
          :key="idx"
          class="flex-1 flex flex-col items-center gap-1 h-full justify-end group relative cursor-pointer"
        >
          <!-- Count label above bar -->
          <span class="text-[10px] font-bold text-base-content/70 group-hover:text-base-content transition-colors">
            {{ bin.count }}
          </span>

          <!-- Bar with gradient and smooth height transition -->
          <div
            :style="{ height: `${Math.max(bin.heightPct, 6)}%` }"
            class="w-full rounded-t transition-all duration-300"
            :class="bin.win ? 'bg-success/80 hover:bg-success group-hover:shadow-[0_0_8px_rgba(16,185,129,0.5)]' : 'bg-error/80 hover:bg-error group-hover:shadow-[0_0_8px_rgba(244,63,94,0.5)]'"
          />

          <!-- Tooltip on hover -->
          <div class="absolute -top-9 opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity bg-base-300 px-2 py-1 rounded shadow text-[10px] font-mono whitespace-nowrap z-20 border border-base-content/10">
            <span class="font-bold">{{ bin.label }}:</span> {{ bin.count }} ({{ bin.percent }}%)
          </div>
        </div>
      </div>

      <!-- X-Axis Labels -->
      <div class="grid grid-cols-6 text-[8px] text-center text-base-content/60 font-mono">
        <span v-for="(bin, idx) in formattedBins" :key="idx" class="truncate px-0.5">
          {{ bin.label.replace(' to ', '~') }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

interface Bin {
  bin_label?: string;
  label?: string;
  count: number;
  win?: boolean;
}

const props = withDefaults(
  defineProps<{
    data?: Bin[];
    title?: string;
  }>(),
  {
    data: () => [
      { bin_label: "<-3.0%", count: 1, win: false },
      { bin_label: "-3.0% to -1.5%", count: 3, win: false },
      { bin_label: "-1.5% to 0%", count: 5, win: false },
      { bin_label: "0% to +1.5%", count: 8, win: true },
      { bin_label: "+1.5% to +3.0%", count: 7, win: true },
      { bin_label: ">+3.0%", count: 5, win: true }
    ]
  }
);

const totalCount = computed(() => {
  return props.data.reduce((sum, b) => sum + (b.count || 0), 0);
});

const maxCount = computed(() => {
  const max = Math.max(...props.data.map((b) => b.count || 0));
  return max > 0 ? max : 1;
});

const formattedBins = computed(() => {
  const total = totalCount.value || 1;
  const max = maxCount.value;
  return props.data.map((b) => {
    const label = b.bin_label || b.label || '';
    const isWin = b.win !== undefined ? b.win : (!label.includes('-') && !label.startsWith('<'));
    const heightPct = (b.count / max) * 100;
    const percent = Math.round((b.count / total) * 100);
    return {
      label,
      count: b.count,
      win: isWin,
      heightPct,
      percent
    };
  });
});
</script>

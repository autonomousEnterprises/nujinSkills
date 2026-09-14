<template>
  <div class="w-full flex flex-col gap-2 font-mono">
    <!-- Header with quick summary metrics -->
    <div v-if="showHeader" class="flex flex-wrap items-center justify-between text-xs gap-2 pb-1 border-b border-base-content/10">
      <div class="flex items-center gap-2">
        <span class="font-bold text-base-content uppercase tracking-wider text-[11px]">{{ title || 'Equity Growth Curve' }}</span>
        <span v-if="regimeLabel" class="badge badge-sm badge-outline font-semibold">{{ regimeLabel }}</span>
      </div>
      <div class="flex items-center gap-3 text-[11px]">
        <span>Peak: <strong class="text-success font-bold">+{{ peakGainPct.toFixed(2) }}%</strong></span>
        <span>Net PnL: <strong :class="finalNetPct >= 0 ? 'text-success' : 'text-error'" class="font-bold">
          {{ finalNetPct >= 0 ? '+' : '' }}{{ finalNetPct.toFixed(2) }}%
        </strong></span>
        <span>Worst DD: <strong class="text-error font-bold">-{{ maxDd.toFixed(2) }}%</strong></span>
      </div>
    </div>

    <!-- Chart container with interactive hover tooltip -->
    <div 
      class="relative w-full rounded-box overflow-hidden bg-base-200/40 p-2 border border-base-content/10"
      @mousemove="onMouseMove"
      @mouseleave="hoverIdx = null"
      ref="containerRef"
    >
      <svg 
        :viewBox="`0 0 ${width} ${height}`" 
        class="w-full overflow-visible select-none"
        :style="{ height: `${chartHeight}px` }"
        preserveAspectRatio="none"
      >
        <defs>
          <linearGradient :id="gradId" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" :stop-color="strokeColor" stop-opacity="0.35" />
            <stop offset="100%" :stop-color="strokeColor" stop-opacity="0.0" />
          </linearGradient>
        </defs>

        <!-- 100% baseline -->
        <line 
          x1="0" 
          :y1="baselineY" 
          :x2="width" 
          :y2="baselineY" 
          class="stroke-base-content/20" 
          stroke-dasharray="3 3" 
          stroke-width="1"
        />

        <!-- Area fill -->
        <path :d="areaD" :fill="`url(#${gradId})`" />

        <!-- Line stroke -->
        <path 
          :d="pathD" 
          fill="none" 
          :stroke="strokeColor" 
          stroke-width="2.2" 
          stroke-linecap="round" 
          stroke-linejoin="round" 
        />

        <!-- Hover vertical crosshair & point -->
        <g v-if="hoverPoint">
          <line 
            :x1="hoverPoint.x" 
            y1="0" 
            :x2="hoverPoint.x" 
            :y2="height" 
            class="stroke-base-content/40" 
            stroke-dasharray="2 2"
            stroke-width="1"
          />
          <circle 
            :cx="hoverPoint.x" 
            :cy="hoverPoint.y" 
            r="4.5" 
            :fill="strokeColor" 
            class="stroke-base-100" 
            stroke-width="2"
          />
        </g>
      </svg>

      <!-- Hover tooltip floating badge -->
      <div 
        v-if="hoverPoint" 
        class="absolute pointer-events-none px-2 py-1 bg-base-300/95 backdrop-blur-sm border border-base-content/10 shadow-lg rounded-box text-[10px] flex items-center gap-2 z-20"
        :style="{
          left: `${Math.min(Math.max(hoverTooltipLeft, 10), containerWidth - 110)}px`,
          top: '8px'
        }"
      >
        <span class="text-base-content/70">Point #{{ hoverIdx! + 1 }}</span>
        <span :class="hoverPoint.val >= 100 ? 'text-success' : 'text-error'" class="font-bold">
          {{ (hoverPoint.val - 100) >= 0 ? '+' : '' }}{{ (hoverPoint.val - 100).toFixed(2) }}%
        </span>
        <span v-if="hoverPoint.dd > 0" class="text-error">DD: -{{ hoverPoint.dd.toFixed(2) }}%</span>
        <span v-if="hoverPoint.timeFormatted" class="text-base-content/50 border-l border-base-content/10 pl-1.5">{{ hoverPoint.timeFormatted }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue';

interface Point {
  time?: number;
  equity_pct: number;
  drawdown_pct?: number;
}

const props = withDefaults(
  defineProps<{
    data?: Point[];
    title?: string;
    regimeLabel?: string;
    chartHeight?: number;
    showHeader?: boolean;
    idPrefix?: string;
  }>(),
  {
    data: () => [
      { equity_pct: 100.0, drawdown_pct: 0.0 },
      { equity_pct: 102.5, drawdown_pct: 0.0 },
      { equity_pct: 101.8, drawdown_pct: 0.68 },
      { equity_pct: 104.2, drawdown_pct: 0.0 },
      { equity_pct: 107.1, drawdown_pct: 0.0 }
    ],
    chartHeight: 140,
    showHeader: true,
    idPrefix: 'eq'
  }
);

const width = 800;
const height = 140;
const containerRef = ref<HTMLDivElement | null>(null);
const containerWidth = ref(800);
const hoverIdx = ref<number | null>(null);

const uid = Math.random().toString(36).substring(2, 7);
const gradId = computed(() => `${props.idPrefix}_grad_${uid}`);

const points = computed(() => {
  if (!props.data || props.data.length < 2) {
    return [
      { equity_pct: 100.0, drawdown_pct: 0.0 },
      { equity_pct: 100.0, drawdown_pct: 0.0 }
    ];
  }
  return props.data;
});

const rawMinEq = computed(() => Math.min(...points.value.map((d) => d.equity_pct)));
const rawMaxEq = computed(() => Math.max(...points.value.map((d) => d.equity_pct)));
const minEq = computed(() => Math.min(rawMinEq.value, 100.0));
const maxEq = computed(() => Math.max(rawMaxEq.value, 100.0));
const rangeEq = computed(() => Math.max(maxEq.value - minEq.value, 0.4));

const finalEq = computed(() => points.value[points.value.length - 1]?.equity_pct ?? 100.0);
const finalNetPct = computed(() => finalEq.value - 100.0);
const peakGainPct = computed(() => Math.max(rawMaxEq.value - 100.0, 0.0));
const maxDd = computed(() => Math.max(...points.value.map((d) => d.drawdown_pct || 0.0), 0.0));

const isProfitable = computed(() => finalNetPct.value >= 0);
const strokeColor = computed(() => (isProfitable.value ? '#10b981' : '#f43f5e'));

const baselineY = computed(() => {
  return height - ((100.0 - minEq.value) / rangeEq.value) * (height - 24) - 12;
});

const pathD = computed(() => {
  const pts = points.value;
  const count = pts.length;
  return pts
    .map((d, idx) => {
      const x = (idx / Math.max(count - 1, 1)) * width;
      const y = height - ((d.equity_pct - minEq.value) / rangeEq.value) * (height - 24) - 12;
      return `${idx === 0 ? 'M' : 'L'} ${x.toFixed(1)} ${y.toFixed(1)}`;
    })
    .join(' ');
});

const areaD = computed(() => {
  return `${pathD.value} L ${width} ${height} L 0 ${height} Z`;
});

const formatPointTime = (ts?: number) => {
  if (!ts) return null;
  const ms = ts < 1e11 ? ts * 1000 : ts;
  const d = new Date(ms);
  if (isNaN(d.getTime())) return null;
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
};

const hoverPoint = computed(() => {
  if (hoverIdx.value === null || hoverIdx.value < 0 || hoverIdx.value >= points.value.length) {
    return null;
  }
  const idx = hoverIdx.value;
  const pt = points.value[idx];
  const count = points.value.length;
  const x = (idx / Math.max(count - 1, 1)) * width;
  const y = height - ((pt.equity_pct - minEq.value) / rangeEq.value) * (height - 24) - 12;
  return { 
    x, 
    y, 
    val: pt.equity_pct, 
    dd: pt.drawdown_pct || 0,
    timeFormatted: formatPointTime(pt.time)
  };
});

const hoverTooltipLeft = computed(() => {
  if (!hoverPoint.value || !containerRef.value) return 0;
  return (hoverPoint.value.x / width) * containerWidth.value - 40;
});

const onMouseMove = (e: MouseEvent) => {
  if (!containerRef.value) return;
  const rect = containerRef.value.getBoundingClientRect();
  containerWidth.value = rect.width;
  const relX = Math.max(0, Math.min(e.clientX - rect.left, rect.width));
  const ratio = relX / rect.width;
  const total = points.value.length;
  hoverIdx.value = Math.min(Math.round(ratio * (total - 1)), total - 1);
};

const updateContainerWidth = () => {
  if (containerRef.value) {
    containerWidth.value = containerRef.value.getBoundingClientRect().width;
  }
};

onMounted(() => {
  updateContainerWidth();
  window.addEventListener('resize', updateContainerWidth);
});

onUnmounted(() => {
  window.removeEventListener('resize', updateContainerWidth);
});
</script>

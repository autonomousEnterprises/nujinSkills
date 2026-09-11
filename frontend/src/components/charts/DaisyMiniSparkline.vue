<template>
  <div class="w-full select-none">
    <svg :viewBox="`0 0 ${width} ${height}`" class="w-full overflow-visible" :style="{ height: `${height}px` }">
      <defs>
        <linearGradient :id="gradId" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" :stop-color="strokeColor" stop-opacity="0.4" />
          <stop offset="100%" :stop-color="strokeColor" stop-opacity="0.0" />
        </linearGradient>
      </defs>
      <!-- Baseline -->
      <line :x1="0" :y1="baseY" :x2="width" :y2="baseY" class="stroke-base-content/15" stroke-dasharray="2 2" />
      <!-- Area fill -->
      <path :d="areaD" :fill="`url(#${gradId})`" />
      <!-- Line -->
      <path :d="pathD" fill="none" :stroke="strokeColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" />
      <!-- End dot -->
      <circle :cx="lastX" :cy="lastY" r="2.5" :fill="strokeColor" />
    </svg>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = withDefaults(
  defineProps<{
    data: Array<{ equity_pct: number }>;
    width?: number;
    height?: number;
    idPrefix?: string;
  }>(),
  {
    width: 300,
    height: 55,
    idPrefix: 'spark'
  }
);

const gradId = computed(() => `${props.idPrefix}_grad_${Math.random().toString(36).substring(2, 7)}`);

const pts = computed(() => {
  if (!props.data || props.data.length === 0) return [{ equity_pct: 100 }, { equity_pct: 100 }];
  return props.data;
});

const rawMin = computed(() => Math.min(...pts.value.map((p) => p.equity_pct)));
const rawMax = computed(() => Math.max(...pts.value.map((p) => p.equity_pct)));
const minVal = computed(() => Math.min(rawMin.value, 100.0));
const maxVal = computed(() => Math.max(rawMax.value, 100.0));
const rangeVal = computed(() => Math.max(maxVal.value - minVal.value, 0.3));

const lastPt = computed(() => pts.value[pts.value.length - 1] || { equity_pct: 100 });
const isProf = computed(() => (lastPt.value.equity_pct - 100.0) >= 0);
const strokeColor = computed(() => (isProf.value ? '#10b981' : '#f43f5e'));

const baseY = computed(() => props.height - ((100.0 - minVal.value) / rangeVal.value) * (props.height - 16) - 8);

const pathD = computed(() => {
  const count = pts.value.length;
  return pts.value
    .map((p, idx) => {
      const x = (idx / Math.max(count - 1, 1)) * props.width;
      const y = props.height - ((p.equity_pct - minVal.value) / rangeVal.value) * (props.height - 16) - 8;
      return `${idx === 0 ? 'M' : 'L'} ${x.toFixed(1)} ${y.toFixed(1)}`;
    })
    .join(' ');
});

const areaD = computed(() => `${pathD.value} L ${props.width} ${props.height} L 0 ${props.height} Z`);

const lastX = computed(() => props.width);
const lastY = computed(() => props.height - ((lastPt.value.equity_pct - minVal.value) / rangeVal.value) * (props.height - 16) - 8);
</script>

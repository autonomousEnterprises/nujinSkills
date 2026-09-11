<template>
  <div class="w-full select-none font-mono">
    <div class="flex items-center justify-between text-[10px] text-base-content/60 mb-1">
      <span v-if="startLabel">{{ startLabel }}</span>
      <span v-else class="text-[9px] text-base-content/40">Baseline: {{ formattedFirst }}</span>
      <span class="font-bold" :style="{ color: strokeColor }">
        Latest: {{ formattedLast }}
      </span>
    </div>

    <svg :viewBox="`0 0 ${width} ${height}`" class="w-full overflow-visible" :style="{ height: `${height}px` }">
      <defs>
        <linearGradient :id="gradId" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" :stop-color="strokeColor" stop-opacity="0.35" />
          <stop offset="100%" :stop-color="strokeColor" stop-opacity="0.0" />
        </linearGradient>
      </defs>

      <!-- Hurdle line if provided -->
      <line
        v-if="hurdleY !== null"
        :x1="paddingX"
        :y1="hurdleY"
        :x2="width - paddingX"
        :y2="hurdleY"
        class="stroke-base-content/20"
        stroke-dasharray="3 3"
        stroke-width="1"
      />
      <text
        v-if="hurdleY !== null && hurdleLabel"
        :x="width - paddingX"
        :y="Math.max(10, hurdleY - 3)"
        text-anchor="end"
        class="fill-base-content/40 text-[8px]"
      >
        {{ hurdleLabel }}
      </text>

      <!-- Shaded area -->
      <path :d="areaD" :fill="`url(#${gradId})`" />

      <!-- Main sparkline stroke -->
      <path
        :d="lineD"
        fill="none"
        :stroke="strokeColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      />

      <!-- Dots for each point -->
      <circle
        v-for="(pt, idx) in coords"
        :key="idx"
        :cx="pt.x"
        :cy="pt.y"
        :r="idx === coords.length - 1 ? 3 : 2"
        :fill="idx === coords.length - 1 ? strokeColor : 'currentColor'"
        class="text-base-content/40 transition-all"
      />

      <!-- Pulsing halo on latest point -->
      <circle
        v-if="coords.length > 0"
        :cx="coords[coords.length - 1].x"
        :cy="coords[coords.length - 1].y"
        r="5"
        fill="none"
        :stroke="strokeColor"
        stroke-width="1"
        stroke-opacity="0.6"
      />
    </svg>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = withDefaults(
  defineProps<{
    values: number[];
    color?: string;
    hurdle?: number;
    hurdleLabel?: string;
    suffix?: string;
    startLabel?: string;
    width?: number;
    height?: number;
    idPrefix?: string;
  }>(),
  {
    values: () => [],
    color: '#10b981',
    suffix: '',
    width: 240,
    height: 48,
    idPrefix: 'drift_spark',
  }
);

const paddingX = 8;
const paddingTop = 6;
const paddingBottom = 8;

const gradId = computed(() => `${props.idPrefix}_grad_${Math.random().toString(36).substring(2, 8)}`);

const pts = computed(() => {
  if (!props.values || props.values.length === 0) return [0, 0];
  if (props.values.length === 1) return [props.values[0], props.values[0]];
  return props.values;
});

const formattedFirst = computed(() => {
  const v = pts.value[0];
  return `${v.toFixed(2)}${props.suffix}`;
});

const formattedLast = computed(() => {
  const v = pts.value[pts.value.length - 1];
  return `${v.toFixed(2)}${props.suffix}`;
});

const minVal = computed(() => {
  let m = Math.min(...pts.value);
  if (props.hurdle !== undefined) m = Math.min(m, props.hurdle);
  return m;
});

const maxVal = computed(() => {
  let m = Math.max(...pts.value);
  if (props.hurdle !== undefined) m = Math.max(m, props.hurdle);
  return m;
});

const rangeVal = computed(() => Math.max(maxVal.value - minVal.value, 0.1));

const strokeColor = computed(() => {
  if (props.color) return props.color;
  const first = pts.value[0];
  const last = pts.value[pts.value.length - 1];
  return last >= first ? '#10b981' : '#f43f5e';
});

const availableWidth = computed(() => props.width - paddingX * 2);
const availableHeight = computed(() => props.height - paddingTop - paddingBottom);

const coords = computed(() => {
  const count = pts.value.length;
  return pts.value.map((v, i) => {
    const x = paddingX + (count > 1 ? (i / (count - 1)) * availableWidth.value : availableWidth.value / 2);
    const normalizedY = (v - minVal.value) / rangeVal.value;
    const y = props.height - paddingBottom - normalizedY * availableHeight.value;
    return { x, y, val: v };
  });
});

const hurdleY = computed(() => {
  if (props.hurdle === undefined) return null;
  const normalizedY = (props.hurdle - minVal.value) / rangeVal.value;
  return props.height - paddingBottom - normalizedY * availableHeight.value;
});

const lineD = computed(() => {
  if (coords.value.length === 0) return '';
  return coords.value
    .map((pt, i) => `${i === 0 ? 'M' : 'L'} ${pt.x.toFixed(1)} ${pt.y.toFixed(1)}`)
    .join(' ');
});

const areaD = computed(() => {
  if (coords.value.length === 0) return '';
  const first = coords.value[0];
  const last = coords.value[coords.value.length - 1];
  const bottomY = props.height - paddingBottom;
  return `${lineD.value} L ${last.x.toFixed(1)} ${bottomY} L ${first.x.toFixed(1)} ${bottomY} Z`;
});
</script>

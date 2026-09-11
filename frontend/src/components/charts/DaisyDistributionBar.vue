<template>
  <div class="w-full flex flex-col gap-2 font-mono">
    <div class="flex items-center justify-between text-xs pb-1 border-b border-base-content/10">
      <span class="font-bold uppercase tracking-wider text-[11px] text-base-content">{{ title }}</span>
      <span class="text-[10px] text-base-content/60">{{ total }} Total</span>
    </div>

    <div class="space-y-2 p-3 bg-base-200/40 rounded-box border border-base-content/10">
      <div v-for="(item, idx) in items" :key="idx" class="space-y-1">
        <div class="flex items-center justify-between text-[11px]">
          <span class="text-base-content/80 font-medium">{{ item.label }}</span>
          <div class="flex items-center gap-1.5 font-bold">
            <span :class="item.colorText || 'text-primary'">{{ item.count }}</span>
            <span class="text-[9px] text-base-content/50">({{ item.pct }}%)</span>
          </div>
        </div>
        <!-- Progress bar -->
        <div class="w-full h-2 rounded-full bg-base-300 overflow-hidden">
          <div 
            class="h-full rounded-full transition-all duration-500" 
            :class="item.colorBg || 'bg-primary'"
            :style="{ width: `${item.pct}%` }"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{
  title: string;
  data: Record<string, number>;
  colorTheme?: 'primary' | 'success' | 'warning' | 'info' | 'rainbow';
}>();

const colorMap: Record<string, { text: string; bg: string }> = {
  'S-Tier': { text: 'text-amber-400', bg: 'bg-amber-400' },
  'A-Tier': { text: 'text-primary', bg: 'bg-primary' },
  'B-Tier': { text: 'text-info', bg: 'bg-info' },
  'C-Tier': { text: 'text-base-content/60', bg: 'bg-base-content/40' },
  '> 2.5': { text: 'text-success', bg: 'bg-success' },
  '1.5 - 2.5': { text: 'text-primary', bg: 'bg-primary' },
  '1.0 - 1.5': { text: 'text-warning', bg: 'bg-warning' },
  '< 1.0': { text: 'text-error', bg: 'bg-error' },
};

const total = computed(() => {
  if (!props.data) return 0;
  return Object.values(props.data).reduce((a, b) => a + b, 0);
});

const items = computed(() => {
  if (!props.data) return [];
  const tot = total.value || 1;
  return Object.entries(props.data).map(([key, val]) => {
    const pct = Math.round((val / tot) * 100);
    const colors = colorMap[key] || { text: 'text-primary', bg: 'bg-primary' };
    return {
      label: key,
      count: val,
      pct,
      colorText: colors.text,
      colorBg: colors.bg
    };
  });
});
</script>

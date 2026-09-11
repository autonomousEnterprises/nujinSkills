<template>
  <div class="card bg-base-200 border border-base-content/10 p-3 flex flex-wrap items-center justify-between gap-3">
    <div class="flex items-center gap-2 flex-wrap">
      <span class="text-[11px] font-bold text-base-content/50 uppercase flex items-center gap-1 mr-1">
        <Filter class="w-3.5 h-3.5" /> Scope:
      </span>

      <button
        @click="emit('update:selectedStratTab', 'ALL')"
        class="btn btn-xs font-mono font-bold gap-1.5"
        :class="selectedStratTab === 'ALL' ? 'btn-secondary text-secondary-content shadow' : 'btn-ghost text-base-content/70 border border-base-content/10'"
      >
        <Layers class="w-3.5 h-3.5" />
        <span>ALL ACTIVE STRATEGIES</span>
        <span class="badge badge-xs badge-neutral">{{ stratOptions.length }}</span>
      </button>

      <button
        v-for="strat in stratOptions"
        :key="strat.name"
        @click="emit('update:selectedStratTab', strat.name)"
        class="btn btn-xs font-mono font-bold gap-1.5"
        :class="selectedStratTab === strat.name ? 'btn-primary text-primary-content shadow' : 'btn-ghost text-base-content/70 border border-base-content/10'"
      >
        <span class="w-2 h-2 rounded-full" :class="strat.isActive ? 'bg-success animate-pulse' : 'bg-base-content/30'" />
        <span>{{ strat.name }}</span>
        <span class="badge badge-xs" :class="strat.symbol.includes('XAU') ? 'badge-warning' : 'badge-info'">
          {{ strat.symbol }}
        </span>
      </button>
    </div>

    <!-- Scope-specific quick action -->
    <div v-if="selectedStratTab !== 'ALL'" class="flex items-center gap-2">
      <button
        v-if="activeBots.includes(selectedStratTab)"
        @click="emit('stopBot', selectedStratTab)"
        :disabled="actionLoading"
        class="btn btn-xs btn-outline btn-error gap-1 font-bold"
      >
        <XCircle class="w-3 h-3" /> Stop {{ selectedStratTab }}
      </button>
      <button
        v-else
        @click="emit('deployBot', selectedStratTab)"
        :disabled="actionLoading"
        class="btn btn-xs btn-outline btn-success gap-1 font-bold"
      >
        <Play class="w-3 h-3 fill-current" /> Deploy {{ selectedStratTab }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Filter, Layers, XCircle, Play } from 'lucide-vue-next';

defineProps<{
  selectedStratTab: string;
  stratOptions: Array<{ name: string; symbol: string; isActive: boolean }>;
  activeBots: string[];
  actionLoading?: boolean;
}>();

const emit = defineEmits<{
  (e: 'update:selectedStratTab', value: string): void;
  (e: 'deployBot', stratName: string): void;
  (e: 'stopBot', stratName: string): void;
}>();
</script>

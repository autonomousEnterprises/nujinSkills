<template>
  <div class="card bg-base-200 border border-base-content/10 p-4 md:p-5 space-y-3">
    <div class="flex items-center justify-between border-b border-base-content/10 pb-2">
      <h3 class="text-xs font-bold flex items-center gap-2 text-base-content">
        <Globe class="w-4 h-4 text-accent" />
        MARKET REGIME SURVIVAL BREAKDOWN (BULL / BEAR / RANGING)
      </h3>
      <span class="text-[10px] text-base-content/50">Click regime card to isolate trajectory</span>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
      <div
        v-for="r in regimeCards"
        :key="r.key"
        @click="emit('selectRegime', r.key)"
        class="card bg-base-300/60 border p-3 cursor-pointer transition-all hover:border-primary/50"
        :class="selectedRegime === r.key ? 'border-primary ring-1 ring-primary/40 bg-primary/5' : 'border-base-content/10'"
      >
        <div class="flex items-center justify-between">
          <span class="text-xs font-bold flex items-center gap-1.5 text-base-content">
            <span>{{ r.icon }}</span>
            <span>{{ r.label }}</span>
            <span v-if="selectedRegime === r.key" class="badge badge-xs badge-primary font-bold">ISOLATED</span>
          </span>
          <span class="text-[10px] text-base-content/60">{{ r.data?.trade_count ?? 0 }} Trades</span>
        </div>

        <!-- Sparkline -->
        <div class="my-2">
          <DaisyMiniSparkline :data="r.curve" :height="50" :idPrefix="`spark_${r.key}`" />
        </div>

        <!-- 3-Col Stats -->
        <div class="grid grid-cols-3 gap-1 text-center pt-2 border-t border-base-content/10 text-xs">
          <div>
            <div class="text-[9px] text-base-content/50">WIN RATE</div>
            <div class="font-bold" :class="getValColor(r.data?.win_rate)">
              {{ ((r.data?.win_rate || 0) * 100).toFixed(1) }}%
            </div>
          </div>
          <div>
            <div class="text-[9px] text-base-content/50">PROFIT FACTOR</div>
            <div class="font-bold" :class="getValColor((Number(r.data?.profit_factor) || 1) - 1.0)">
              {{ r.data?.profit_factor != null ? (typeof r.data.profit_factor === 'number' ? r.data.profit_factor.toFixed(2) : r.data.profit_factor) : '—' }}
            </div>
          </div>
          <div>
            <div class="text-[9px] text-base-content/50">NET PnL</div>
            <div class="font-bold" :class="(r.data?.net_pnl_pct || 0) >= 0 ? 'text-success' : 'text-error'">
              {{ (r.data?.net_pnl_pct || 0) > 0 ? '+' : '' }}{{ r.data?.net_pnl_pct ?? 0 }}%
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Globe } from 'lucide-vue-next';
import DaisyMiniSparkline from '../charts/DaisyMiniSparkline.vue';
import type { RegimeData } from '../../types';
import { getValColor } from '../../utils/formatters';

defineProps<{
  regimeCards: RegimeData[];
  selectedRegime: string;
}>();

const emit = defineEmits<{
  (e: 'selectRegime', regimeKey: string): void;
}>();
</script>

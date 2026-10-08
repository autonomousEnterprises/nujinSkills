<template>
  <div class="space-y-3">
    <!-- Top Account Growth Tier Callout (if account model available) -->
    <div v-if="accountSummary" class="flex flex-wrap items-center justify-between bg-primary/10 border border-primary/20 rounded-box px-4 py-2 text-xs font-mono">
      <div class="flex items-center gap-2">
        <span class="badge badge-primary badge-sm font-bold uppercase tracking-wider">Account Mode</span>
        <span class="text-base-content font-semibold">Tier ${{ (selectedTier || accountSummary.benchmark_tier || 5000).toLocaleString() }} Base</span>
      </div>
      <div class="flex items-center gap-4 text-xs">
        <span>Account Growth: <strong class="text-success font-bold">+{{ currentTierData?.net_growth_pct || accountSummary.net_growth_pct }}%</strong></span>
        <span>Dollar Profit: <strong class="text-success font-bold">+${{ (currentTierData?.net_profit_dollars || accountSummary.net_profit_dollars)?.toLocaleString() }}</strong></span>
        <span>Account DD: <strong class="text-error font-bold">-{{ currentTierData?.max_drawdown_pct || accountSummary.max_drawdown_pct }}%</strong></span>
      </div>
    </div>

    <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
      <!-- Net Sharpe -->
      <div class="stat bg-base-200 border border-base-content/10 rounded-box p-3">
        <div class="stat-title text-[10px] uppercase font-bold flex items-center gap-1 text-base-content/60">
          <BarChart3 class="w-3.5 h-3.5 text-primary" /> NET SHARPE
        </div>
        <div class="stat-value text-xl font-mono mt-0.5" :class="getValColor(summary?.sharpe)">
          {{ summary?.sharpe != null ? summary.sharpe : '–' }}
        </div>
        <div class="stat-desc text-[10px] text-base-content/50">Threshold: &gt;= 1.8</div>
      </div>

      <!-- Max Drawdown -->
      <div class="stat bg-base-200 border border-base-content/10 rounded-box p-3">
        <div class="stat-title text-[10px] uppercase font-bold flex items-center gap-1 text-base-content/60">
          <ShieldCheck class="w-3.5 h-3.5 text-error" /> {{ chartMode === 'account' ? 'ACCOUNT MAX DD' : 'MAX DRAWDOWN' }}
        </div>
        <div class="stat-value text-xl font-mono mt-0.5" :class="displayDrawdown != null ? getValColor(-displayDrawdown) : ''">
          {{ displayDrawdown != null ? `${displayDrawdown.toFixed(2)}%` : '–' }}
        </div>
        <div class="stat-desc text-[10px] text-base-content/50">Cap Limit: &lt;= 3.0%</div>
      </div>

      <!-- Expectancy -->
      <div class="stat bg-base-200 border border-base-content/10 rounded-box p-3">
        <div class="stat-title text-[10px] uppercase font-bold flex items-center gap-1 text-base-content/60">
          <Layers class="w-3.5 h-3.5 text-accent" /> EXPECTANCY
        </div>
        <div class="stat-value text-xl font-mono mt-0.5" :class="getValColor(summary?.expectancy_bps)">
          {{ summary?.expectancy_bps != null ? `${summary.expectancy_bps} bps` : '–' }}
        </div>
        <div class="stat-desc text-[10px] text-base-content/50">Min: &gt;= 12.0 bps</div>
      </div>

      <!-- Profit Factor -->
      <div class="stat bg-base-200 border border-base-content/10 rounded-box p-3">
        <div class="stat-title text-[10px] uppercase font-bold flex items-center gap-1 text-base-content/60">
          <CheckCircle2 class="w-3.5 h-3.5 text-secondary" /> PROFIT FACTOR
        </div>
        <div class="stat-value text-xl font-mono mt-0.5" :class="summary?.profit_factor ? getValColor(summary.profit_factor - 1.0) : ''">
          {{ summary?.profit_factor != null ? summary.profit_factor : '–' }}
        </div>
        <div class="stat-desc text-[10px] text-base-content/50">Target: &gt;= 1.50</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { BarChart3, ShieldCheck, Layers, CheckCircle2 } from 'lucide-vue-next';
import type { BacktestSummary } from '../../types';
import { getValColor } from '../../utils/formatters';

const props = withDefaults(
  defineProps<{
    summary?: BacktestSummary | null;
    accountSummary?: any;
    selectedTier?: number;
    chartMode?: 'account' | 'spot';
  }>(),
  {
    chartMode: 'account'
  }
);

const currentTierData = computed(() => {
  if (!props.accountSummary?.account_tiers) return null;
  const tierKey = String(props.selectedTier || props.accountSummary.benchmark_tier || 5000);
  return props.accountSummary.account_tiers[tierKey] || null;
});

const displayDrawdown = computed(() => {
  if (props.chartMode === 'account') {
    const accDd = currentTierData.value?.max_drawdown_pct ?? props.accountSummary?.max_drawdown_pct;
    if (accDd != null) return accDd;
  }
  return props.summary?.max_drawdown != null ? props.summary.max_drawdown * 100 : null;
});
</script>

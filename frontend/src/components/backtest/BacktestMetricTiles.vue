<template>
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
        <ShieldCheck class="w-3.5 h-3.5 text-error" /> MAX DRAWDOWN
      </div>
      <div class="stat-value text-xl font-mono mt-0.5" :class="summary?.max_drawdown != null ? getValColor(-summary.max_drawdown) : ''">
        {{ summary?.max_drawdown != null ? `${(summary.max_drawdown * 100).toFixed(2)}%` : '–' }}
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
</template>

<script setup lang="ts">
import { BarChart3, ShieldCheck, Layers, CheckCircle2 } from 'lucide-vue-next';
import type { BacktestSummary } from '../../types';
import { getValColor } from '../../utils/formatters';

defineProps<{
  summary?: BacktestSummary | null;
}>();
</script>

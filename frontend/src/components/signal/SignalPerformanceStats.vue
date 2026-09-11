<template>
  <div class="card bg-base-200 border border-base-content/10 p-5 space-y-4">
    <div class="flex items-center justify-between border-b border-base-content/10 pb-3">
      <span class="font-bold text-sm flex items-center gap-2 text-primary">
        <Award class="w-4 h-4" />
        LIVE TELEMETRY PERFORMANCE — {{ selectedStratTab === 'ALL' ? 'COMBINED MULTI-STRATEGY PORTFOLIO' : selectedStratTab }}
      </span>
      <span class="text-[10px] text-base-content/60 font-mono">
        {{ liveStats?.total_trades ?? 0 }} closed signals evaluated
      </span>
    </div>

    <!-- 4 Primary KPI Cards -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
      <!-- Win Rate -->
      <div class="stat bg-base-300/50 rounded-box border border-base-content/10 p-3">
        <div class="stat-title text-[10px] uppercase font-bold flex items-center gap-1 text-base-content/60">
          <Percent class="w-3 h-3 text-primary" /> WIN RATE (LIVE)
        </div>
        <div class="stat-value text-xl font-mono mt-0.5" :class="liveStats && liveStats.win_rate >= 0.5 ? 'text-success' : 'text-warning'">
          {{ liveStats ? `${(liveStats.win_rate * 100).toFixed(1)}%` : '—' }}
        </div>
        <div class="stat-desc text-[10px] text-base-content/50">
          {{ liveStats?.wins ?? 0 }}W / {{ liveStats?.losses ?? 0 }}L
        </div>
      </div>

      <!-- Profit Factor -->
      <div class="stat bg-base-300/50 rounded-box border border-base-content/10 p-3">
        <div class="stat-title text-[10px] uppercase font-bold flex items-center gap-1 text-base-content/60">
          <BarChart3 class="w-3 h-3 text-secondary" /> PROFIT FACTOR
        </div>
        <div 
          class="stat-value text-xl font-mono mt-0.5"
          :class="liveStats && liveStats.profit_factor > 1.5 ? 'text-success' : liveStats && liveStats.profit_factor > 1.0 ? 'text-warning' : 'text-error'"
        >
          {{ liveStats?.profit_factor ?? '—' }}
        </div>
        <div class="stat-desc text-[10px] text-base-content/50">Gross profit / loss</div>
      </div>

      <!-- Sharpe Live -->
      <div class="stat bg-base-300/50 rounded-box border border-base-content/10 p-3">
        <div class="stat-title text-[10px] uppercase font-bold flex items-center gap-1 text-base-content/60">
          <TrendingUp class="w-3 h-3 text-accent" /> SHARPE (LIVE)
        </div>
        <div class="stat-value text-xl font-mono mt-0.5" :class="liveStats && liveStats.sharpe_live > 1.5 ? 'text-success' : 'text-warning'">
          {{ liveStats?.sharpe_live ?? '—' }}
        </div>
        <div class="stat-desc text-[10px] text-base-content/50">Annualized return / risk</div>
      </div>

      <!-- Total Net PnL -->
      <div class="stat bg-base-300/50 rounded-box border border-base-content/10 p-3">
        <div class="stat-title text-[10px] uppercase font-bold flex items-center gap-1 text-base-content/60">
          <DollarSign class="w-3 h-3 text-success" /> TOTAL NET PnL
        </div>
        <div 
          class="stat-value text-xl font-mono mt-0.5"
          :class="liveStats ? (liveStats.total_pnl_pct >= 0 ? 'text-success' : 'text-error') : ''"
        >
          {{ liveStats ? `${liveStats.total_pnl_pct > 0 ? '+' : ''}${liveStats.total_pnl_pct}%` : '—' }}
        </div>
        <div class="stat-desc text-[10px] text-base-content/50">Realized closed trades</div>
      </div>
    </div>

    <!-- Secondary Stats -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
      <div class="p-2.5 rounded-box bg-base-300/40 border border-base-content/10 flex flex-col">
        <span class="text-[9px] text-base-content/50 uppercase">Avg Win</span>
        <span class="text-sm font-bold text-success mt-0.5">+{{ liveStats?.avg_win_pct ?? 0 }}%</span>
      </div>
      <div class="p-2.5 rounded-box bg-base-300/40 border border-base-content/10 flex flex-col">
        <span class="text-[9px] text-base-content/50 uppercase">Avg Loss</span>
        <span class="text-sm font-bold text-error mt-0.5">-{{ liveStats?.avg_loss_pct ?? 0 }}%</span>
      </div>
      <div class="p-2.5 rounded-box bg-base-300/40 border border-base-content/10 flex flex-col">
        <span class="text-[9px] text-base-content/50 uppercase">Active Open Positions</span>
        <span class="text-sm font-bold text-info mt-0.5">{{ openPositionsCount }} In Flight</span>
      </div>
      <div class="p-2.5 rounded-box bg-base-300/40 border border-base-content/10 flex flex-col">
        <span class="text-[9px] text-base-content/50 uppercase">Max Consec. Loss</span>
        <span class="text-sm font-bold mt-0.5" :class="(liveStats?.max_consecutive_losses ?? 0) >= 3 ? 'text-error' : 'text-warning'">
          {{ liveStats?.max_consecutive_losses ?? 0 }}
        </span>
      </div>
    </div>

    <!-- Gross Profit/Loss Visual Ratio Bar -->
    <div v-if="liveStats && (liveStats.gross_profit_pct > 0 || liveStats.gross_loss_pct > 0)" class="pt-2">
      <div class="flex items-center justify-between text-[10px] text-base-content/70 mb-1">
        <span>Gross Profit: <strong class="text-success font-bold">+{{ liveStats.gross_profit_pct }}%</strong></span>
        <span>Gross Loss: <strong class="text-error font-bold">-{{ liveStats.gross_loss_pct }}%</strong></span>
      </div>
      <div class="h-2 w-full rounded-full overflow-hidden flex bg-error/30">
        <div class="h-full bg-success rounded-l-full transition-all" :style="{ width: `${profitRatioPct}%` }" />
        <div class="h-full bg-error flex-1 rounded-r-full" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { Award, Percent, BarChart3, TrendingUp, DollarSign } from 'lucide-vue-next';

const props = defineProps<{
  selectedStratTab: string;
  liveStats?: any;
  openPositionsCount: number;
}>();

const profitRatioPct = computed(() => {
  if (!props.liveStats) return 50;
  const gp = props.liveStats.gross_profit_pct || 0;
  const gl = props.liveStats.gross_loss_pct || 0;
  const total = gp + gl;
  if (total === 0) return 50;
  return Math.round((gp / total) * 100);
});
</script>

<template>
  <!-- ── TOP HEADER: LIFECYCLE CONTROLS ── -->
  <div class="card bg-base-200 border border-base-content/10 shadow-sm p-4">
    <div class="flex flex-wrap items-center justify-between gap-4">
      <div class="flex items-center gap-3">
        <div class="p-2.5 rounded-box bg-primary/10 border border-primary/30 text-primary">
          <Layers class="w-5 h-5" />
        </div>
        <div>
          <div class="flex items-center gap-2 flex-wrap">
            <span class="font-bold text-sm text-base-content">
              STRATEGY LIFECYCLE &amp; PORTFOLIO MANAGER
            </span>
            <span class="badge badge-sm badge-success font-bold">
              {{ activeCount }} ACTIVE IN BOT
            </span>
            <span class="badge badge-sm badge-warning font-bold">
              {{ cronCount }} CRON MONITORED
            </span>
            <span class="badge badge-sm badge-info font-bold">
              REAL-TIME QUANT DECK
            </span>
          </div>
          <div class="text-[11px] text-base-content/60 mt-0.5">
            Automated drift detection, cron re-evaluations, Sharpe ranking &amp; single-click deployment to live broker bot
          </div>
        </div>
      </div>

      <!-- Actions: Run All Backtests & Trigger Cron -->
      <div class="flex items-center gap-2 flex-wrap">
        <button
          @click="emit('runAllBacktests')"
          :disabled="runningAll"
          class="btn btn-xs sm:btn-sm btn-primary gap-1 shadow font-bold"
          title="Run quantitative backtests for all registered strategies"
        >
          <Play class="w-3.5 h-3.5 fill-current" />
          <span>{{ runningAll ? 'Evaluating...' : 'Run All Evaluations' }}</span>
        </button>

        <button
          @click="emit('triggerCron')"
          :disabled="runningCron"
          class="btn btn-xs sm:btn-sm btn-warning gap-1 shadow font-bold"
          title="Trigger immediate cron re-evaluation and drift check"
        >
          <RefreshCw class="w-3.5 h-3.5" :class="runningCron ? 'animate-spin' : ''" />
          <span>Trigger Cron Cycle</span>
        </button>
      </div>
    </div>
  </div>

  <!-- ── PORTFOLIO KPI STATS RIBBON ── -->
  <div class="grid grid-cols-2 sm:grid-cols-4 xl:grid-cols-7 gap-3">
    <!-- Active Bots -->
    <div class="stat bg-base-200 border border-base-content/10 rounded-box p-3">
      <div class="stat-title text-[10px] uppercase font-bold text-base-content/60">ACTIVE LIVE BOTS</div>
      <div class="stat-value text-xl font-mono mt-0.5 text-success">
        {{ portfolio.active_count }} <span class="text-xs font-normal text-base-content/50">/ {{ strategies.length }}</span>
      </div>
      <div class="stat-desc text-[10px] text-base-content/60 mt-0.5 truncate">
        {{ portfolio.active_strategies.map(s => s.replace('.py','')).join(', ') || 'No active bots' }}
      </div>
    </div>

    <!-- Total Net PnL -->
    <div class="stat bg-base-200 border border-base-content/10 rounded-box p-3">
      <div class="stat-title text-[10px] uppercase font-bold text-base-content/60">TOTAL NET PnL</div>
      <div 
        class="stat-value text-xl font-mono mt-0.5" 
        :class="(portfolio.total_net_pnl ?? portfolio.total_realized_pnl ?? 0) >= 0 ? 'text-success' : 'text-error'"
      >
        {{ (portfolio.total_net_pnl ?? portfolio.total_realized_pnl) != null ? `${(portfolio.total_net_pnl ?? portfolio.total_realized_pnl) > 0 ? '+' : ''}${(portfolio.total_net_pnl ?? portfolio.total_realized_pnl).toFixed(2)}%` : '–' }}
      </div>
      <div class="stat-desc text-[10px] text-base-content/50 mt-0.5">Across active strategies</div>
    </div>

    <!-- Blended Sharpe -->
    <div class="stat bg-base-200 border border-base-content/10 rounded-box p-3">
      <div class="stat-title text-[10px] uppercase font-bold text-base-content/60">BLENDED SHARPE</div>
      <div class="stat-value text-xl font-mono mt-0.5" :class="getValColor(portfolio.blended_sharpe)">
        {{ portfolio.blended_sharpe != null && portfolio.blended_sharpe > 0 ? portfolio.blended_sharpe.toFixed(2) : '–' }}
      </div>
      <div class="stat-desc text-[10px] text-base-content/50 mt-0.5">Target: &gt;= 1.80</div>
    </div>

    <!-- Blended Win Rate -->
    <div class="stat bg-base-200 border border-base-content/10 rounded-box p-3">
      <div class="stat-title text-[10px] uppercase font-bold text-base-content/60">BLENDED WIN RATE</div>
      <div class="stat-value text-xl font-mono mt-0.5" :class="getValColor((portfolio.blended_win_rate ?? 0) - 50)">
        {{ portfolio.blended_win_rate != null && portfolio.blended_win_rate >= 0 ? `${portfolio.blended_win_rate.toFixed(1)}%` : '–' }}
      </div>
      <div class="stat-desc text-[10px] text-base-content/50 mt-0.5">Across active positions</div>
    </div>

    <!-- Combined Profit Factor -->
    <div class="stat bg-base-200 border border-base-content/10 rounded-box p-3">
      <div class="stat-title text-[10px] uppercase font-bold text-base-content/60">PROFIT FACTOR</div>
      <div class="stat-value text-xl font-mono mt-0.5" :class="getValColor(((portfolio.combined_profit_factor ?? 1.0)) - 1.0)">
        {{ portfolio.combined_profit_factor != null && portfolio.combined_profit_factor >= 0 ? portfolio.combined_profit_factor.toFixed(2) : '–' }}
      </div>
      <div class="stat-desc text-[10px] text-base-content/50 mt-0.5">Hurdle: &gt;= 1.50</div>
    </div>

    <!-- Total Simulated Trades -->
    <div class="stat bg-base-200 border border-base-content/10 rounded-box p-3">
      <div class="stat-title text-[10px] uppercase font-bold text-base-content/60">TOTAL TRADES</div>
      <div class="stat-value text-xl font-mono mt-0.5 text-base-content">
        {{ portfolio.total_trades != null && portfolio.total_trades >= 0 ? portfolio.total_trades.toLocaleString() : '–' }}
      </div>
      <div class="stat-desc text-[10px] text-base-content/50 mt-0.5">Statistical significance</div>
    </div>

    <!-- Asset Scope -->
    <div class="stat bg-base-200 border border-base-content/10 rounded-box p-3">
      <div class="stat-title text-[10px] uppercase font-bold text-base-content/60">ACTIVE ASSETS</div>
      <div class="stat-value text-base font-mono mt-1 text-primary truncate">
        {{ portfolio.symbols.join(', ') || 'XAU/USD' }}
      </div>
      <div class="stat-desc text-[10px] text-base-content/50 mt-0.5">Diversified risk universe</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Layers, Play, RefreshCw } from 'lucide-vue-next';
import type { ManagedStrategy, PortfolioSummary } from '../../types';
import { getValColor } from '../../utils/formatters';

defineProps<{
  strategies: ManagedStrategy[];
  portfolio: PortfolioSummary;
  activeCount: number;
  cronCount: number;
  runningCron?: boolean;
  runningAll?: boolean;
}>();

const emit = defineEmits<{
  (e: 'runAllBacktests'): void;
  (e: 'triggerCron'): void;
}>();
</script>

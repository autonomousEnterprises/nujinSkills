<template>
  <div class="w-full h-full overflow-y-auto font-mono select-none bg-base-100 text-base-content transition-colors">
    <div class="w-full px-3 md:px-6 py-4 space-y-4">

      <!-- ── TOP STATS & LIFECYCLE ACTIONS RIBBON ── -->
      <StrategyKpiRibbon
        :strategies="strategies"
        :portfolio="portfolio"
        :activeCount="activeCount"
        :cronCount="cronCount"
        :runningCron="runningCron"
        :runningAll="runningAll"
        @runAllBacktests="handleRunAllBacktests"
        @triggerCron="handleTriggerCron"
      />

      <!-- ── STRATEGY LEADERBOARD TABLE (WITH DRIFT METRICS & SNAPSHOTS) ── -->
      <StrategyLeaderboard
        :strategies="strategies"
        :activeCount="activeCount"
        :cronCount="cronCount"
        :actionLoading="actionLoading"
        @navigateToBacktest="emit('navigateToBacktest', $event)"
        @runBacktest="handleRunBacktest"
        @updateStatus="handleUpdateStatus"
      />

      <!-- ── PORTFOLIO RISK, CORRELATION MATRIX & ALLOCATION SCOPE ── -->
      <StrategyAlphaRiskDeck
        :strategies="strategies"
        :portfolio="portfolio"
        :portfolioSummary="portfolioSummary"
        :distribution="distribution"
        :runningCron="runningCron"
        :actionLoading="actionLoading"
        @navigateToBacktest="emit('navigateToBacktest', $event)"
        @runBacktest="handleRunBacktest"
        @updateStatus="handleUpdateStatus"
        @triggerCron="handleTriggerCron"
      />

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import StrategyKpiRibbon from './strategy/StrategyKpiRibbon.vue';
import StrategyLeaderboard from './strategy/StrategyLeaderboard.vue';
import StrategyAlphaRiskDeck from './strategy/StrategyAlphaRiskDeck.vue';
import type { ManagedStrategy, PortfolioSummary, DistributionAnalytics } from '../types';

const props = withDefaults(
  defineProps<{
    theme?: 'dark' | 'light';
    strategies?: ManagedStrategy[];
    signals?: any[];
    activeStrategy?: string;
    portfolioSummary?: PortfolioSummary | null;
    distributionAnalytics?: DistributionAnalytics | null;
  }>(),
  {
    theme: 'dark',
    strategies: () => [],
    signals: () => [],
    activeStrategy: 'GoatFundedTraderXauusdScalper.py',
  }
);

const emit = defineEmits<{
  (e: 'selectStrategy', stratName: string): void;
  (e: 'activateStrategy', stratName: string): void;
  (e: 'updateStatus', stratName: string, newStatus: string): void;
  (e: 'runBacktest', stratName: string): void;
  (e: 'triggerCron'): void;
  (e: 'navigateToBacktest', stratName: string): void;
}>();

const runningCron = ref(false);
const runningAll = ref(false);
const actionLoading = ref<Record<string, boolean>>({});

const activeCount = computed(() => props.strategies.filter((s) => s.status === 'ACTIVE_LIVE').length);
const cronCount = computed(() => props.strategies.filter((s) => s.status === 'CRON_BACKTEST').length);

const portfolio = computed<PortfolioSummary>(() => {
  if (
    props.portfolioSummary &&
    props.portfolioSummary.active_count !== undefined &&
    props.portfolioSummary.blended_win_rate !== undefined &&
    props.portfolioSummary.blended_win_rate > 0
  ) {
    return props.portfolioSummary;
  }
  const activeStrats = props.strategies.filter((s) => s.status === 'ACTIVE_LIVE');
  let totalTrades = 0;
  let totalWins = 0;
  let weightedSharpeSum = 0;
  let netPnlSum = 0;
  const pfs: number[] = [];
  const syms: string[] = [];
  const names: string[] = [];

  activeStrats.forEach((s) => {
    names.push(s.name);
    if (s.symbol && !syms.includes(s.symbol)) syms.push(s.symbol);
    const bt = s.latest_backtest || {};
    const trades = bt.trades || 0;
    const rawWr = bt.win_rate || 0;
    const normWr = rawWr <= 1.0 ? rawWr : rawWr / 100;
    const sh = bt.sharpe || 0;
    const pf = bt.profit_factor || 0;

    const eq = s.backtest_equity_curve || [];
    if (eq && eq.length >= 2) {
      netPnlSum += (eq[eq.length - 1].equity_pct || 100) - (eq[0].equity_pct || 100);
    }

    totalTrades += trades;
    totalWins += Math.round(trades * normWr);
    weightedSharpeSum += sh * Math.max(1, trades);
    if (pf > 0) pfs.push(pf);
  });

  const btWr = totalTrades > 0 ? (totalWins / totalTrades) * 100 : 0;
  const blendedSh = totalTrades > 0 ? weightedSharpeSum / totalTrades : (activeStrats.length > 0 ? activeStrats.reduce((a, b) => a + (b.latest_backtest?.sharpe || 0), 0) / activeStrats.length : 0);
  const combinedPf = pfs.length > 0 ? pfs.reduce((a, b) => a + b, 0) / pfs.length : 0;

  return {
    active_count: activeStrats.length,
    active_strategies: names,
    blended_win_rate: Number(btWr.toFixed(1)),
    blended_sharpe: Number(blendedSh.toFixed(2)),
    total_trades: totalTrades,
    combined_profit_factor: Number(combinedPf.toFixed(2)),
    total_realized_pnl: Number(netPnlSum.toFixed(2)),
    total_net_pnl: Number(netPnlSum.toFixed(2)),
    symbols: syms,
    best_performer: activeStrats[0]?.name || null,
  };
});

const distribution = computed<DistributionAnalytics>(() => {
  if (props.distributionAnalytics && props.distributionAnalytics.total_evaluated !== undefined) {
    return props.distributionAnalytics;
  }

  const improving: any[] = [];
  const decaying: any[] = [];
  const stable: any[] = [];
  const sharpeBins: Record<string, number> = { '< 1.0': 0, '1.0 - 1.5': 0, '1.5 - 2.5': 0, '> 2.5': 0 };
  const tierCounts: Record<string, number> = { 'S-Tier': 0, 'A-Tier': 0, 'B-Tier': 0, 'C-Tier': 0 };
  const assetCounts: Record<string, number> = {};

  props.strategies.forEach((s) => {
    const tier = s.tier || 'C-Tier';
    if (tier.includes('S-Tier')) tierCounts['S-Tier']++;
    else if (tier.includes('A-Tier')) tierCounts['A-Tier']++;
    else if (tier.includes('B-Tier')) tierCounts['B-Tier']++;
    else tierCounts['C-Tier']++;

    const sym = s.symbol || 'Other';
    assetCounts[sym] = (assetCounts[sym] || 0) + 1;

    const sh = s.latest_backtest?.sharpe || 0;
    if (sh < 1.0) sharpeBins['< 1.0']++;
    else if (sh <= 1.5) sharpeBins['1.0 - 1.5']++;
    else if (sh <= 2.5) sharpeBins['1.5 - 2.5']++;
    else sharpeBins['> 2.5']++;

    const hist = s.cron_config?.drift_history || [];
    let deltaSh = 0;
    let deltaWr = 0;
    if (hist.length >= 2) {
      const last = hist[hist.length - 1];
      const prev = hist[hist.length - 2];
      deltaSh = Number(((last.sharpe || 0) - (prev.sharpe || 0)).toFixed(2));
      deltaWr = Number((((last.win_rate || 0) - (prev.win_rate || 0)) * 100).toFixed(1));
    }

    const entry = {
      name: s.name,
      display_name: s.display_name,
      status: s.status,
      sharpe: sh,
      win_rate: s.latest_backtest?.win_rate || 0,
      delta_sharpe: deltaSh,
      delta_win_rate: deltaWr,
      snapshots_count: hist.length,
      trajectory: 'STABLE',
    };

    if (deltaSh > 0.05 || deltaWr > 1.0) {
      entry.trajectory = 'GAINING_EDGE';
      improving.push(entry);
    } else if (deltaSh < -0.05 || deltaWr < -1.0) {
      entry.trajectory = 'DECAYING_EDGE';
      decaying.push(entry);
    } else {
      stable.push(entry);
    }
  });

  return {
    improving,
    decaying,
    stable,
    sharpe_distribution: sharpeBins,
    tier_distribution: tierCounts,
    asset_distribution: assetCounts,
    total_evaluated: props.strategies.length,
  };
});

const handleRunBacktest = async (stratName: string) => {
  try {
    actionLoading.value[stratName] = true;
    emit('runBacktest', stratName);
  } finally {
    actionLoading.value[stratName] = false;
  }
};

const handleUpdateStatus = (stratName: string, newStatus: string) => {
  emit('updateStatus', stratName, newStatus);
};

const handleTriggerCron = async () => {
  try {
    runningCron.value = true;
    emit('triggerCron');
  } finally {
    runningCron.value = false;
  }
};

const handleRunAllBacktests = async () => {
  try {
    runningAll.value = true;
    for (const strat of props.strategies) {
      emit('runBacktest', strat.name);
    }
  } finally {
    runningAll.value = false;
  }
};
</script>

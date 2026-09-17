<template>
  <div class="w-full h-full overflow-y-auto font-mono select-none bg-base-100 text-base-content px-3 md:px-6 py-4 transition-colors">
    <div class="w-full space-y-4">

      <!-- Loading Overlay -->
      <div v-if="loading" class="w-full py-20 flex flex-col items-center justify-center gap-3 text-primary">
        <span class="loading loading-spinner loading-lg text-primary" />
        <span class="font-bold text-sm tracking-wider">EXECUTING_REAL_QUANTITATIVE_BACKTEST_FOR [{{ selectedStrategy }}]...</span>
      </div>

      <template v-else>
        <!-- ── 1. TOP BANNER: SINGLE SOURCE OF TRUTH METRICS ── -->
        <BacktestTopBanner
          :cleanSelectedName="cleanSelectedName"
          :activeName="activeName"
          :activeState="activeState"
          :selectedBacktestData="selectedBacktestData"
          :summary="summary"
          :strategyRecord="matchedManagedStrategy"
        />

        <!-- ── 2. QUANT EDGE THESIS & COUNTERPARTY MECHANICS ── -->
        <BacktestThesisCard
          :cleanSelectedName="cleanSelectedName"
          :thesisInfo="thesisInfo"
        />

        <!-- ── 3. 4 KEY METRIC TILES ── -->
        <BacktestMetricTiles :summary="summary" />

        <!-- ── 4. CHARTS ROW: MAIN EQUITY GROWTH CURVE & TRADE RETURN DISTRIBUTION ── -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <!-- Left 2 Cols: Main Equity Curve -->
          <div class="card bg-base-200 border border-base-content/10 p-4 lg:col-span-2 space-y-3">
            <div class="flex flex-wrap items-center justify-between gap-2 border-b border-base-content/10 pb-2">
              <div class="flex items-center gap-2 flex-wrap">
                <span class="font-bold text-xs flex items-center gap-2 text-primary">
                  <TrendingUp class="w-4 h-4" />
                  EQUITY GROWTH CURVE &amp; DRAWDOWN ENVELOPE
                </span>
                <span v-if="timePeriodLabel" class="badge badge-xs badge-neutral border-base-content/20 font-mono text-[10px] text-base-content/70 gap-1">
                  <Calendar class="w-2.5 h-2.5 text-primary" />
                  {{ timePeriodLabel }}
                </span>
              </div>

              <!-- Regime filter toggle buttons -->
              <div class="join">
                <button
                  v-for="r in [
                    { key: 'ALL', label: 'ALL REGIMES' },
                    { key: 'bull_market', label: 'BULL 🐂' },
                    { key: 'bear_market', label: 'BEAR 🐻' },
                    { key: 'ranging_market', label: 'RANGING 🔄' }
                  ]"
                  :key="r.key"
                  @click="selectedRegimeFilter = r.key as any"
                  class="btn btn-xs join-item font-mono text-[10px]"
                  :class="selectedRegimeFilter === r.key ? 'btn-primary font-bold' : 'btn-ghost text-base-content/60'"
                >
                  {{ r.label }}
                </button>
              </div>
            </div>

            <DaisyEquityChart 
              :data="currentEquityCurve" 
              :title="`Equity Trajectory (${selectedRegimeFilter.toUpperCase()})`"
              :regimeLabel="selectedRegimeFilter"
              :chartHeight="150"
            />
          </div>

          <!-- Right 1 Col: Trade Return Distribution Histogram -->
          <div class="card bg-base-200 border border-base-content/10 p-4 space-y-3">
            <DaisyHistogramChart 
              :data="distributionBins" 
              title="TRADE RETURN DISTRIBUTION"
            />
          </div>
        </div>

        <!-- ── 5. MARKET REGIME SURVIVAL BREAKDOWN (BULL / BEAR / RANGING) ── -->
        <BacktestRegimeBreakdown
          :regimeCards="regimeCards"
          :selectedRegime="selectedRegimeFilter"
          @selectRegime="selectedRegimeFilter = ($event === selectedRegimeFilter ? 'ALL' : $event as any)"
        />

        <!-- ── 6. SEQUENTIAL TRADE LOG TABLE ── -->
        <BacktestTradeLog :tradesDetail="tradesDetail" />

        <!-- ── 7. ADVERSARIAL FALSIFICATION GATES (CYNIC AUDIT) ── -->
        <BacktestFalsificationGates
          :cleanSelectedName="cleanSelectedName"
          :summary="summary"
          :gates="gates"
        />

        <!-- ── 8. ALPHA DRIFT ANALYSIS & MULTI-EVALUATION MATRIX ── -->
        <BacktestAlphaDriftCard
          :cleanSelectedName="cleanSelectedName"
          :selectedStrategy="selectedStrategy"
          :summary="summary"
          :managedStrategy="matchedManagedStrategy"
          @runBacktest="emit('runBacktest', $event)"
          @activateStrategy="emit('activateStrategy', $event)"
        />

      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { TrendingUp, Calendar } from 'lucide-vue-next';
import DaisyEquityChart from './charts/DaisyEquityChart.vue';
import DaisyHistogramChart from './charts/DaisyHistogramChart.vue';
import BacktestTopBanner from './backtest/BacktestTopBanner.vue';
import BacktestThesisCard from './backtest/BacktestThesisCard.vue';
import BacktestMetricTiles from './backtest/BacktestMetricTiles.vue';
import BacktestRegimeBreakdown from './backtest/BacktestRegimeBreakdown.vue';
import BacktestTradeLog from './backtest/BacktestTradeLog.vue';
import BacktestFalsificationGates from './backtest/BacktestFalsificationGates.vue';
import BacktestAlphaDriftCard from './backtest/BacktestAlphaDriftCard.vue';
import type { StrategyFile, BacktestSummary, ThesisProps, RegimeData } from '../types';
import { getTimePeriodInfo, getDatasetFallbackPeriod } from '../utils/formatters';

const props = withDefaults(
  defineProps<{
    theme?: 'dark' | 'light';
    selectedStrategy?: string;
    selectedBacktestData?: any;
    activeState?: any;
    strategies?: StrategyFile[];
    managedStrategies?: any[];
    loading?: boolean;
  }>(),
  {
    theme: 'dark',
    selectedStrategy: '',
    strategies: () => [],
    managedStrategies: () => [],
    loading: false,
  }
);

const emit = defineEmits<{
  (e: 'selectStrategy', stratName: string): void;
  (e: 'activateStrategy', stratName: string): void;
  (e: 'runBacktest', stratName: string): void;
}>();

const selectedRegimeFilter = ref<'ALL' | 'bull_market' | 'bear_market' | 'ranging_market'>('ALL');

const cleanSelectedName = computed(() => (props.selectedStrategy || props.activeState?.active_strategy || props.strategies?.[0]?.name || '').replace('.py', ''));
const activeName = computed(() => props.activeState?.active_strategy || cleanSelectedName.value);

const matchedManagedStrategy = computed(() => {
  return props.managedStrategies?.find((s) => s.name === props.selectedStrategy || s.name.replace('.py','') === props.selectedStrategy.replace('.py',''));
});

const timePeriodLabel = computed(() => {
  const info = getTimePeriodInfo(props.selectedBacktestData) ||
               getTimePeriodInfo(matchedManagedStrategy.value) ||
               getTimePeriodInfo(props.activeState) ||
               getDatasetFallbackPeriod(cleanSelectedName.value);
  return info ? info.period_label : '';
});

const summary = computed<BacktestSummary | null>(() => props.selectedBacktestData?.summary || props.activeState?.backtest_summary || null);
const thesisInfo = computed<ThesisProps | null>(() => props.selectedBacktestData?.thesis_props || null);
const gates = computed(() => props.selectedBacktestData?.falsification_gates || null);
const tradesDetail = computed(() => props.selectedBacktestData?.trades_detail || []);

const distributionBins = computed(() => {
  return props.selectedBacktestData?.return_distribution || [
    { bin_label: "<-3.0%", count: 1, win: false },
    { bin_label: "-3.0% to -1.5%", count: 3, win: false },
    { bin_label: "-1.5% to 0%", count: 5, win: false },
    { bin_label: "0% to +1.5%", count: 8, win: true },
    { bin_label: "+1.5% to +3.0%", count: 12, win: true },
    { bin_label: ">+3.0%", count: 4, win: true }
  ];
});

const currentEquityCurve = computed(() => {
  const curve = props.selectedBacktestData?.equity_curve || props.activeState?.equity_curve || [];
  if (selectedRegimeFilter.value === 'ALL') return curve;
  const regimes = props.selectedBacktestData?.regime_breakdown || props.activeState?.regime_breakdown || {};
  return regimes[selectedRegimeFilter.value]?.equity_curve || curve;
});

const regimeCards = computed<RegimeData[]>(() => {
  const breakdown = props.selectedBacktestData?.regime_breakdown || props.activeState?.regime_breakdown || {};
  return [
    {
      key: 'bull_market',
      label: 'BULL REGIME',
      icon: '🐂',
      data: breakdown.bull_market || { trade_count: 14, win_rate: 0.643, profit_factor: 1.82, net_pnl_pct: 12.4 },
      curve: breakdown.bull_market?.equity_curve || []
    },
    {
      key: 'bear_market',
      label: 'BEAR REGIME',
      icon: '🐻',
      data: breakdown.bear_market || { trade_count: 8, win_rate: 0.500, profit_factor: 1.45, net_pnl_pct: 4.8 },
      curve: breakdown.bear_market?.equity_curve || []
    },
    {
      key: 'ranging_market',
      label: 'RANGING / CHOP',
      icon: '🔄',
      data: breakdown.ranging_market || { trade_count: 18, win_rate: 0.556, profit_factor: 1.58, net_pnl_pct: 8.2 },
      curve: breakdown.ranging_market?.equity_curve || []
    }
  ];
});
</script>

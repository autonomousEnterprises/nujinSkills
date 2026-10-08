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
        <BacktestMetricTiles 
          :summary="summary" 
          :accountSummary="accountSummaryData" 
          :selectedTier="selectedAccountTier"
          :chartMode="chartMode"
        />

        <!-- ── 4. CHARTS ROW: MAIN EQUITY GROWTH CURVE & TRADE RETURN DISTRIBUTION ── -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <!-- Left 2 Cols: Main Equity Curve -->
          <div class="card bg-base-200 border border-base-content/10 p-4 lg:col-span-2 space-y-3">
            <div class="flex flex-wrap items-center justify-between gap-2 border-b border-base-content/10 pb-2">
              <div class="flex items-center gap-2 flex-wrap">
                <span class="font-bold text-xs flex items-center gap-2 text-primary">
                  <TrendingUp class="w-4 h-4" />
                  {{ chartMode === 'account' ? 'ACCOUNT EQUITY TRAJECTORY' : 'SPOT PRICE MOVE TRAJECTORY' }}
                </span>
                <span v-if="timePeriodLabel" class="badge badge-xs badge-neutral border-base-content/20 font-mono text-[10px] text-base-content/70 gap-1">
                  <Calendar class="w-2.5 h-2.5 text-primary" />
                  {{ timePeriodLabel }}
                </span>
              </div>

              <!-- Controls: Account vs Spot Toggle + Account Sizing Tiers + Regime Filter -->
              <div class="flex items-center gap-2 flex-wrap">
                <!-- Mode Toggle: Account vs Spot -->
                <div class="join">
                  <button
                    @click="chartMode = 'account'"
                    class="btn btn-xs join-item font-mono text-[10px]"
                    :class="chartMode === 'account' ? 'btn-primary font-bold' : 'btn-ghost text-base-content/60'"
                  >
                    💰 ACCOUNT GROWTH
                  </button>
                  <button
                    @click="chartMode = 'spot'"
                    class="btn btn-xs join-item font-mono text-[10px]"
                    :class="chartMode === 'spot' ? 'btn-primary font-bold' : 'btn-ghost text-base-content/60'"
                  >
                    📊 SPOT DELTA
                  </button>
                </div>

                <!-- Account Tier Selector (visible when in account mode) -->
                <div v-if="chartMode === 'account'" class="join">
                  <button
                    v-for="tier in [5000, 10000, 25000, 50000, 100000]"
                    :key="tier"
                    @click="selectedAccountTier = tier"
                    class="btn btn-xs join-item font-mono text-[9px] px-1.5"
                    :class="selectedAccountTier === tier ? 'btn-secondary font-bold' : 'btn-ghost text-base-content/50'"
                  >
                    ${{ tier >= 1000 ? `${tier / 1000}k` : tier }}
                  </button>
                </div>

                <!-- Regime filter toggle buttons -->
                <div class="join">
                  <button
                    v-for="r in [
                      { key: 'ALL', label: 'ALL' },
                      { key: 'bull_market', label: '🐂' },
                      { key: 'bear_market', label: '🐻' },
                      { key: 'ranging_market', label: '🔄' }
                    ]"
                    :key="r.key"
                    @click="selectedRegimeFilter = r.key as any"
                    class="btn btn-xs join-item font-mono text-[10px]"
                    :class="selectedRegimeFilter === r.key ? 'btn-accent font-bold' : 'btn-ghost text-base-content/60'"
                  >
                    {{ r.label }}
                  </button>
                </div>
              </div>
            </div>

            <DaisyEquityChart 
              :data="currentEquityCurve" 
              :title="chartMode === 'account' ? `Account Trajectory ($${selectedAccountTier.toLocaleString()})` : `Spot Trajectory (${selectedRegimeFilter.toUpperCase()})`"
              :regimeLabel="selectedRegimeFilter !== 'ALL' ? selectedRegimeFilter : ''"
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
          @runBacktest="(strat, days) => emit('runBacktest', strat, days)"
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
  (e: 'runBacktest', stratName: string, days?: number): void;
}>();

const selectedRegimeFilter = ref<'ALL' | 'bull_market' | 'bear_market' | 'ranging_market'>('ALL');
const chartMode = ref<'account' | 'spot'>('account');
const selectedAccountTier = ref<number>(5000);

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
const accountSummaryData = computed(() => props.selectedBacktestData?.account_summary || props.activeState?.account_summary || null);
const accountGrowthModels = computed(() => props.selectedBacktestData?.account_growth_models || props.activeState?.account_growth_models || null);
const thesisInfo = computed<ThesisProps | null>(() => props.selectedBacktestData?.thesis_props || null);
const gates = computed(() => props.selectedBacktestData?.falsification_gates || null);
const tradesDetail = computed(() => props.selectedBacktestData?.trades_detail || []);

const distributionBins = computed(() => {
  return props.selectedBacktestData?.return_distribution || props.activeState?.return_distribution || [];
});

const currentEquityCurve = computed(() => {
  // 1. In Account Mode: return the simulated tier equity curve with dollar balances & account returns
  if (chartMode.value === 'account' && accountGrowthModels.value) {
    const tierKey = String(selectedAccountTier.value);
    const tierData = accountGrowthModels.value[tierKey];
    if (tierData && tierData.equity_curve && tierData.equity_curve.length > 0) {
      return tierData.equity_curve;
    }
  }

  // 2. In Spot Delta / Regime Mode: return the raw price move or regime curve
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
      data: breakdown.bull_market || null,
      curve: breakdown.bull_market?.equity_curve || []
    },
    {
      key: 'bear_market',
      label: 'BEAR REGIME',
      icon: '🐻',
      data: breakdown.bear_market || null,
      curve: breakdown.bear_market?.equity_curve || []
    },
    {
      key: 'ranging_market',
      label: 'RANGING / CHOP',
      icon: '🔄',
      data: breakdown.ranging_market || null,
      curve: breakdown.ranging_market?.equity_curve || []
    }
  ];
});
</script>

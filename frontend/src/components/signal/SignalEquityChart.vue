<template>
  <div class="card bg-base-200 border border-base-content/10 p-4 md:p-5 space-y-3 font-mono">
    <!-- Top Header & Scope Controls -->
    <div class="flex flex-wrap items-center justify-between border-b border-base-content/10 pb-3 gap-3">
      <div class="flex flex-wrap items-center gap-2.5">
        <span class="font-bold text-sm flex items-center gap-2 text-primary">
          <LineChart class="w-4 h-4" />
          REALIZED EQUITY TRAJECTORY
        </span>
        <span class="badge badge-sm badge-neutral font-semibold text-[11px]">
          {{ selectedStratTab === 'ALL' ? 'PORTFOLIO (ALL STRATEGIES)' : selectedStratTab }}
        </span>
        <span 
          v-if="effectiveMode === 'LIVE'"
          class="badge badge-sm badge-success badge-outline font-bold gap-1 text-[10px]"
        >
          <span class="w-1.5 h-1.5 rounded-full bg-success animate-pulse" />
          LIVE TELEMETRY
        </span>
        <span 
          v-else
          class="badge badge-sm badge-outline badge-info font-bold text-[10px]"
        >
          {{ selectedStratTab === 'ALL' ? 'BLENDED PORTFOLIO BENCHMARK' : 'STRATEGY BENCHMARK' }}
        </span>
      </div>

      <!-- Live Telemetry vs Benchmark Backtest Toggle -->
      <div class="flex items-center gap-2">
        <div class="join border border-base-content/10 rounded-box bg-base-300/60 p-0.5">
          <button
            @click="activeMode = 'LIVE'"
            class="btn btn-xs join-item font-mono text-[10px] transition-all"
            :class="effectiveMode === 'LIVE' ? 'btn-primary font-bold shadow-sm' : 'btn-ghost text-base-content/60'"
          >
            <span class="w-1.5 h-1.5 rounded-full mr-1" :class="effectiveMode === 'LIVE' ? 'bg-primary-content' : 'bg-success'" />
            LIVE SIGNALS ({{ closedTradesCount }})
          </button>
          <button
            v-if="hasBenchmarkData"
            @click="activeMode = 'BENCHMARK'"
            class="btn btn-xs join-item font-mono text-[10px] transition-all"
            :class="effectiveMode === 'BENCHMARK' ? 'btn-primary font-bold shadow-sm' : 'btn-ghost text-base-content/60'"
          >
            {{ selectedStratTab === 'ALL' ? 'PORTFOLIO BENCHMARK' : 'BENCHMARK BACKTEST' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Quick Metric Strip -->
    <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5 pt-1">
      <div class="p-2 rounded-box bg-base-300/40 border border-base-content/10 flex flex-col">
        <span class="text-[9px] text-base-content/50 uppercase font-bold">Baseline Capital</span>
        <span class="text-xs font-bold font-mono mt-0.5 text-base-content/80">100.00%</span>
      </div>

      <div class="p-2 rounded-box bg-base-300/40 border border-base-content/10 flex flex-col">
        <span class="text-[9px] text-base-content/50 uppercase font-bold">Current Equity</span>
        <span 
          class="text-xs font-bold font-mono mt-0.5"
          :class="netChangePct >= 0 ? 'text-success' : 'text-error'"
        >
          {{ currentEquity.toFixed(2) }}%
          <span class="text-[10px] ml-0.5 font-normal">({{ netChangePct >= 0 ? '+' : '' }}{{ netChangePct.toFixed(2) }}%)</span>
        </span>
      </div>

      <div class="p-2 rounded-box bg-base-300/40 border border-base-content/10 flex flex-col">
        <span class="text-[9px] text-base-content/50 uppercase font-bold">Peak Trajectory</span>
        <span class="text-xs font-bold text-success font-mono mt-0.5">
          +{{ peakGainPct.toFixed(2) }}%
        </span>
      </div>

      <div class="p-2 rounded-box bg-base-300/40 border border-base-content/10 flex flex-col">
        <span class="text-[9px] text-base-content/50 uppercase font-bold">Max Drawdown</span>
        <span 
          class="text-xs font-bold font-mono mt-0.5"
          :class="maxDrawdown > 0 ? 'text-error' : 'text-base-content/60'"
        >
          {{ maxDrawdown > 0 ? `-${maxDrawdown.toFixed(2)}%` : '0.00%' }}
        </span>
      </div>

      <div class="p-2 rounded-box bg-base-300/40 border border-base-content/10 flex flex-col">
        <span class="text-[9px] text-base-content/50 uppercase font-bold">Sample Points</span>
        <span class="text-xs font-bold text-base-content font-mono mt-0.5">
          {{ effectiveMode === 'LIVE' ? `${closedTradesCount} Closed Trades` : `${displayedCurve.length} Points` }}
        </span>
      </div>

      <div class="p-2 rounded-box bg-base-300/40 border border-base-content/10 flex flex-col">
        <span class="text-[9px] text-base-content/50 uppercase font-bold">Win Rate (Scope)</span>
        <span 
          class="text-xs font-bold font-mono mt-0.5"
          :class="scopeWinRate >= 0.5 ? 'text-success' : 'text-warning'"
        >
          {{ (scopeWinRate * 100).toFixed(1) }}%
        </span>
      </div>
    </div>

    <!-- Equity Curve SVG Container -->
    <div class="pt-1">
      <DaisyEquityChart
        v-if="displayedCurve && displayedCurve.length > 0"
        :data="displayedCurve"
        :chartHeight="165"
        :showHeader="false"
        :idPrefix="chartIdPrefix"
      />

      <!-- Empty State when in LIVE mode and no trades yet -->
      <div 
        v-else 
        class="h-36 rounded-box border border-dashed border-base-content/20 flex flex-col items-center justify-center text-center p-4 bg-base-300/20"
      >
        <TrendingUp class="w-7 h-7 text-base-content/30 mb-2" />
        <div class="text-xs font-bold text-base-content/70">
          No Closed Trades Yet for {{ selectedStratTab === 'ALL' ? 'Active Strategies' : selectedStratTab }}
        </div>
        <p class="text-[11px] text-base-content/50 mt-1 max-w-md">
          Live equity trajectory starts at 100.00% baseline and dynamically compounds each realized trade return in real-time.
        </p>
        <button
          v-if="hasBenchmarkData"
          @click="activeMode = 'BENCHMARK'"
          class="btn btn-xs btn-outline btn-primary mt-2 font-mono text-[10px]"
        >
          View Theoretical Benchmark Curve
        </button>
      </div>
    </div>

    <!-- Chart Footer Note -->
    <div class="flex flex-wrap items-center justify-between text-[10px] text-base-content/50 pt-1 border-t border-base-content/5">
      <div class="flex items-center gap-1.5">
        <span class="w-1.5 h-1.5 rounded-full" :class="netChangePct >= 0 ? 'bg-success' : 'bg-error'" />
        <span>Compounded capital trajectory net of 5 bps taker fee & 2 bps slippage model.</span>
      </div>
      <div class="flex items-center gap-3">
        <span v-if="timeRangeText">{{ timeRangeText }}</span>
        <span class="font-mono text-base-content/40">DSR Audit Gate: $\ge 0.95$</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { LineChart, TrendingUp } from 'lucide-vue-next';
import DaisyEquityChart from '../charts/DaisyEquityChart.vue';
import type { SignalData, ManagedStrategy } from '../../types';

interface Point {
  time?: number;
  equity_pct: number;
  drawdown_pct?: number;
}

const props = withDefaults(
  defineProps<{
    signals?: SignalData[];
    selectedStratTab?: string;
    cleanSelectedName?: string;
    liveStats?: any;
    managedStrategies?: ManagedStrategy[];
    selectedBacktestData?: any;
    activeBots?: string[];
  }>(),
  {
    signals: () => [],
    selectedStratTab: 'ALL',
    cleanSelectedName: '',
    liveStats: null,
    managedStrategies: () => [],
    selectedBacktestData: null,
    activeBots: () => [],
  }
);

const activeMode = ref<'LIVE' | 'BENCHMARK'>('LIVE');

const chartIdPrefix = computed(() => {
  const clean = (props.selectedStratTab || 'all').toLowerCase().replace(/[^a-z0-9]/g, '_');
  return `sig_eq_${clean}`;
});

// Filter closed signals for this strategy tab
const closedSignals = computed(() => {
  return (props.signals || [])
    .filter((s) => {
      const isClosed = s.status !== 'ACTIVE_IN_POSITION' && s.exit_reason !== 'ACTIVE_IN_POSITION' && s.pnl_pct !== undefined && s.pnl_pct !== null;
      return isClosed;
    })
    .sort((a, b) => (a.time || 0) - (b.time || 0));
});

const closedTradesCount = computed(() => closedSignals.value.length);

// 1. Live Compounded Equity Curve from real signals
const liveEquityCurve = computed<Point[]>(() => {
  const trades = closedSignals.value;
  if (trades.length === 0) {
    // Check if managedStrategy has precomputed live_equity_curve
    const matched = props.managedStrategies?.find((m) =>
      props.selectedStratTab !== 'ALL'
        ? m.name.toLowerCase().includes(props.selectedStratTab.toLowerCase()) ||
          props.selectedStratTab.toLowerCase().includes(m.name.toLowerCase().replace('.py', ''))
        : m.name.includes(props.cleanSelectedName)
    );
    if (matched?.live_equity_curve && matched.live_equity_curve.length > 1) {
      return matched.live_equity_curve;
    }
    return [];
  }

  let currentEq = 100.0;
  let peak = 100.0;
  const firstTime = (trades[0].time || Math.floor(Date.now() / 1000)) - 60;
  const curve: Point[] = [
    { time: firstTime, equity_pct: 100.0, drawdown_pct: 0.0 }
  ];

  for (const t of trades) {
    const pnl = Number(t.pnl_pct || 0);
    currentEq = Math.round(currentEq * (1.0 + pnl / 100.0) * 10000) / 10000;
    peak = Math.max(peak, currentEq);
    const dd = peak > 0 ? Math.round(((peak - currentEq) / peak) * 10000) / 100 : 0.0;
    curve.push({
      time: t.exit_time || t.time || Math.floor(Date.now() / 1000),
      equity_pct: Number(currentEq.toFixed(2)),
      drawdown_pct: dd,
    });
  }

  return curve;
});

// 2. Theoretical Benchmark Curve from backtest engine
const benchmarkEquityCurve = computed<Point[]>(() => {
  if (props.selectedStratTab !== 'ALL') {
    // Isolated single strategy benchmark
    const target = props.selectedStratTab.toLowerCase();
    const matched = props.managedStrategies?.find((m) =>
      m.name.toLowerCase().includes(target) ||
      target.includes(m.name.toLowerCase().replace('.py', ''))
    );
    if (matched?.backtest_equity_curve && matched.backtest_equity_curve.length > 1) {
      return matched.backtest_equity_curve;
    }
  } else {
    // Combined multi-strategy portfolio benchmark across active strategies
    const activeStrats = (props.managedStrategies || []).filter(
      (s) => (props.activeBots && props.activeBots.includes(s.name.replace('.py', ''))) || s.status === 'ACTIVE_LIVE'
    );
    const candidateStrats = activeStrats.length > 0 ? activeStrats : (props.managedStrategies || []);
    const validCurves = candidateStrats
      .map((s) => s.backtest_equity_curve || [])
      .filter((c) => c.length > 1);

    if (validCurves.length > 1) {
      const numSteps = 50;
      const blended: Point[] = [];
      let peak = 100.0;

      for (let i = 0; i < numSteps; i++) {
        let sumDelta = 0;
        let validCount = 0;

        for (const curve of validCurves) {
          const idx = Math.min(Math.round((i / (numSteps - 1)) * (curve.length - 1)), curve.length - 1);
          const eqVal = curve[idx]?.equity_pct ?? 100.0;
          sumDelta += (eqVal - 100.0);
          validCount++;
        }

        const avgDelta = validCount > 0 ? sumDelta / validCount : 0.0;
        const eq = Math.round((100.0 + avgDelta) * 100) / 100;
        peak = Math.max(peak, eq);
        const dd = peak > 0 ? Math.round(((peak - eq) / peak) * 10000) / 100 : 0.0;
        blended.push({
          equity_pct: eq,
          drawdown_pct: dd,
        });
      }
      return blended;
    } else if (validCurves.length === 1) {
      return validCurves[0];
    }
  }

  if (props.selectedBacktestData?.equity_curve && props.selectedBacktestData.equity_curve.length > 1) {
    return props.selectedBacktestData.equity_curve;
  }

  const defaultStrat = props.managedStrategies?.find((m) => m.name.includes(props.cleanSelectedName));
  if (defaultStrat?.backtest_equity_curve && defaultStrat.backtest_equity_curve.length > 1) {
    return defaultStrat.backtest_equity_curve;
  }

  return [];
});

const hasBenchmarkData = computed(() => benchmarkEquityCurve.value.length > 1);

const effectiveMode = computed<'LIVE' | 'BENCHMARK'>(() => {
  if (activeMode.value === 'BENCHMARK' && hasBenchmarkData.value) {
    return 'BENCHMARK';
  }
  if (liveEquityCurve.value.length > 1) {
    return 'LIVE';
  }
  if (hasBenchmarkData.value) {
    return 'BENCHMARK';
  }
  return 'LIVE';
});

const displayedCurve = computed<Point[]>(() => {
  if (effectiveMode.value === 'BENCHMARK') {
    return benchmarkEquityCurve.value;
  }
  return liveEquityCurve.value;
});

// Curve Metrics
const currentEquity = computed(() => {
  const pts = displayedCurve.value;
  if (!pts || pts.length === 0) return 100.0;
  return pts[pts.length - 1]?.equity_pct ?? 100.0;
});

const netChangePct = computed(() => currentEquity.value - 100.0);

const peakGainPct = computed(() => {
  const pts = displayedCurve.value;
  if (!pts || pts.length === 0) return 0.0;
  const maxEq = Math.max(...pts.map((p) => p.equity_pct), 100.0);
  return Math.max(maxEq - 100.0, 0.0);
});

const maxDrawdown = computed(() => {
  const pts = displayedCurve.value;
  if (!pts || pts.length === 0) return 0.0;
  return Math.max(...pts.map((p) => p.drawdown_pct || 0.0), 0.0);
});

const scopeWinRate = computed(() => {
  if (effectiveMode.value === 'LIVE') {
    const trades = closedSignals.value;
    if (trades.length === 0) return props.liveStats?.win_rate ?? 0.5;
    const wins = trades.filter((t) => (t.pnl_pct || 0) > 0).length;
    return wins / trades.length;
  }
  return props.selectedBacktestData?.summary?.win_rate ?? props.liveStats?.win_rate ?? 0.5;
});

const timeRangeText = computed(() => {
  const pts = displayedCurve.value;
  if (!pts || pts.length < 2) return '';
  const first = pts[0]?.time;
  const last = pts[pts.length - 1]?.time;
  if (!first || !last) return '';

  const format = (ts: number) => {
    const ms = ts < 1e11 ? ts * 1000 : ts;
    const d = new Date(ms);
    return d.toLocaleDateString([], { month: 'short', day: 'numeric' });
  };

  return `${format(first)} → ${format(last)}`;
});
</script>

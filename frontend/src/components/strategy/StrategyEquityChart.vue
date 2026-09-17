<template>
  <div class="card bg-base-200 border border-base-content/10 p-4 md:p-5 space-y-3 font-mono shadow-sm">
    <!-- Top Header & Scope Controls -->
    <div class="flex flex-wrap items-center justify-between border-b border-base-content/10 pb-3 gap-3">
      <!-- Title & Status Badge -->
      <div class="flex flex-wrap items-center gap-2.5">
        <span class="font-bold text-sm flex items-center gap-2 text-primary">
          <LineChart class="w-4 h-4" />
          <span>{{ screenMode === 'LIVE' ? 'REALIZED EQUITY TRAJECTORY' : 'BENCHMARK EQUITY TRAJECTORY' }}</span>
        </span>

        <!-- Current Scope Badge -->
        <span class="badge badge-sm badge-neutral font-semibold text-[11px]">
          {{ selectedScope === 'ALL' ? 'PORTFOLIO (ALL STRATEGIES)' : cleanScopeName }}
        </span>

        <!-- Mode Indicator Badge -->
        <span 
          v-if="screenMode === 'LIVE'"
          class="badge badge-sm badge-success badge-outline font-bold gap-1 text-[10px]"
        >
          <span class="w-1.5 h-1.5 rounded-full bg-success animate-pulse" />
          LIVE SIGNALS
        </span>
        <span 
          v-else
          class="badge badge-sm badge-info badge-outline font-bold text-[10px]"
        >
          {{ selectedScope === 'ALL' ? 'BLENDED PORTFOLIO BENCHMARK' : 'BACKTEST BENCHMARK' }}
        </span>

        <!-- Time Period Badge -->
        <span class="badge badge-sm badge-neutral border-base-content/20 font-bold gap-1 text-[10px] font-mono">
          <Calendar class="w-3 h-3 text-primary shrink-0" />
          <span>{{ equityPeriodLabel }}</span>
        </span>
      </div>

      <!-- Scope Selector Dropdown & Screen Mode Pill -->
      <div class="flex items-center gap-2 flex-wrap">
        <!-- Strategy Scope Selector -->
        <div class="flex items-center gap-1.5">
          <span class="text-[10px] text-base-content/50 uppercase font-bold">Scope:</span>
          <select 
            :value="selectedScope" 
            @change="$emit('update:selectedScope', ($event.target as HTMLSelectElement).value)"
            class="select select-xs select-bordered font-mono text-xs max-w-[220px] bg-base-300"
          >
            <option value="ALL">Portfolio (All Active)</option>
            <option 
              v-for="s in strategies" 
              :key="s.id" 
              :value="s.name"
            >
              #{{ s.rank }} {{ s.display_name || s.name }} ({{ s.tier ? s.tier.split(' ')[0] : 'C-Tier' }})
            </option>
          </select>
        </div>

        <!-- Mode Toggle Pill -->
        <div class="join border border-base-content/10 rounded-box bg-base-300/60 p-0.5">
          <button
            type="button"
            @click="$emit('update:screenMode', 'LIVE')"
            class="btn btn-xs join-item font-mono text-[10px] transition-all"
            :class="screenMode === 'LIVE' ? 'btn-success font-bold shadow-sm' : 'btn-ghost text-base-content/60'"
          >
            <span class="w-1.5 h-1.5 rounded-full mr-1 bg-current" />
            LIVE ({{ closedTradesCount }})
          </button>
          <button
            type="button"
            @click="$emit('update:screenMode', 'BACKTEST')"
            class="btn btn-xs join-item font-mono text-[10px] transition-all"
            :class="screenMode === 'BACKTEST' ? 'btn-info font-bold shadow-sm' : 'btn-ghost text-base-content/60'"
          >
            BACKTEST
          </button>
        </div>
      </div>
    </div>

    <!-- 7 Quick Metric Strip -->
    <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-7 gap-2.5 pt-1">
      <div class="p-2 rounded-box bg-base-300/40 border border-base-content/10 flex flex-col">
        <span class="text-[9px] text-base-content/50 uppercase font-bold">Baseline Capital</span>
        <span class="text-xs font-bold font-mono mt-0.5 text-base-content/80">0.00%</span>
      </div>

      <div class="p-2 rounded-box bg-base-300/40 border border-base-content/10 flex flex-col">
        <span class="text-[9px] text-base-content/50 uppercase font-bold">
          {{ screenMode === 'LIVE' ? 'Current Live Return' : 'Ending Backtest Return' }}
        </span>
        <span 
          class="text-xs font-bold font-mono mt-0.5"
          :class="netChangePct >= 0 ? 'text-success' : 'text-error'"
        >
          {{ netChangePct >= 0 ? '+' : '' }}{{ netChangePct.toFixed(2) }}%
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
          {{ screenMode === 'LIVE' ? `${closedTradesCount} Closed Trades` : `${displayedCurve.length} Points` }}
        </span>
      </div>

      <div class="p-2 rounded-box bg-base-300/40 border border-base-content/10 flex flex-col">
        <span class="text-[9px] text-base-content/50 uppercase font-bold">
          {{ screenMode === 'LIVE' ? 'Live Win Rate' : 'Backtest Win Rate' }}
        </span>
        <span 
          class="text-xs font-bold font-mono mt-0.5"
          :class="scopeWinRate >= 0.5 ? 'text-success' : 'text-warning'"
        >
          {{ (scopeWinRate * 100).toFixed(1) }}%
        </span>
      </div>

      <div class="p-2 rounded-box bg-base-300/40 border border-base-content/10 flex flex-col">
        <span class="text-[9px] text-base-content/50 uppercase font-bold flex items-center gap-1">
          <Calendar class="w-2.5 h-2.5 text-primary shrink-0" /> Time Window
        </span>
        <span class="text-[11px] font-bold font-mono mt-0.5 text-primary truncate" :title="equityPeriodLabel">
          {{ equityPeriodLabel }}
        </span>
      </div>
    </div>

    <!-- Equity Curve SVG Container -->
    <div class="pt-1">
      <DaisyEquityChart
        v-if="displayedCurve && displayedCurve.length > 1"
        :data="displayedCurve"
        :chartHeight="170"
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
          {{ screenMode === 'LIVE' 
            ? `No Closed Live Trades Yet for ${selectedScope === 'ALL' ? 'Active Strategies' : cleanScopeName}`
            : `No Backtest Equity Points Available for ${cleanScopeName}`
          }}
        </div>
        <p class="text-[11px] text-base-content/50 mt-1 max-w-md">
          {{ screenMode === 'LIVE'
            ? 'Live equity compounds dynamically with each closed signal. You can switch to Backtest mode to inspect historical simulation curves.'
            : 'Run a backtest evaluation (F3 or table Play button) to generate the high-resolution simulation curve.'
          }}
        </p>
        <button
          v-if="screenMode === 'LIVE' && hasBenchmarkData"
          @click="$emit('update:screenMode', 'BACKTEST')"
          class="btn btn-xs btn-outline btn-info mt-2 font-mono text-[10px]"
        >
          View Backtest Benchmark Curve
        </button>
      </div>
    </div>

    <!-- Chart Footer Note -->
    <div class="flex flex-wrap items-center justify-between text-[10px] text-base-content/50 pt-1 border-t border-base-content/5">
      <div class="flex items-center gap-1.5">
        <span class="w-1.5 h-1.5 rounded-full" :class="netChangePct >= 0 ? 'bg-success' : 'bg-error'" />
        <span>
          {{ screenMode === 'LIVE' 
            ? 'Compounded real-time live trading trajectory net of exchange fees and slippage.' 
            : 'Historical backtest equity progression across market regime slices (Bull, Bear, Range).' 
          }}
        </span>
      </div>
      <div class="flex items-center gap-3 font-mono">
        <span v-if="timeRangeText">{{ timeRangeText }}</span>
        <span class="text-base-content/40">Friction Model: 5 bps fee + 2 bps slippage</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { LineChart, TrendingUp, Calendar } from 'lucide-vue-next';
import DaisyEquityChart from '../charts/DaisyEquityChart.vue';
import type { SignalData, ManagedStrategy } from '../../types';
import { getTimePeriodInfo, getDatasetFallbackPeriod } from '../../utils/formatters';

interface Point {
  time?: number;
  equity_pct: number;
  drawdown_pct?: number;
}

const props = withDefaults(
  defineProps<{
    signals?: SignalData[];
    strategies?: ManagedStrategy[];
    screenMode?: 'LIVE' | 'BACKTEST';
    selectedScope?: string;
    activeBots?: string[];
  }>(),
  {
    signals: () => [],
    strategies: () => [],
    screenMode: 'LIVE',
    selectedScope: 'ALL',
    activeBots: () => [],
  }
);

defineEmits<{
  (e: 'update:screenMode', mode: 'LIVE' | 'BACKTEST'): void;
  (e: 'update:selectedScope', scope: string): void;
}>();

const cleanScopeName = computed(() => {
  if (props.selectedScope === 'ALL') return 'Portfolio';
  const matched = props.strategies.find(
    (s) => s.name === props.selectedScope || s.name.replace('.py', '') === props.selectedScope
  );
  return matched?.display_name || props.selectedScope.replace('.py', '');
});

const chartIdPrefix = computed(() => {
  const clean = (props.selectedScope || 'all').toLowerCase().replace(/[^a-z0-9]/g, '_');
  return `strat_eq_${props.screenMode.toLowerCase()}_${clean}`;
});

// 1. Filter closed signals for the selected scope
const scopedSignals = computed(() => {
  const allClosed = (props.signals || [])
    .filter((s) => {
      const isClosed = s.status !== 'ACTIVE_IN_POSITION' && s.exit_reason !== 'ACTIVE_IN_POSITION' && s.pnl_pct !== undefined && s.pnl_pct !== null;
      return isClosed;
    })
    .sort((a, b) => (a.time || 0) - (b.time || 0));

  if (props.selectedScope === 'ALL') {
    return allClosed;
  }

  const target = props.selectedScope.toLowerCase().replace('.py', '');
  return allClosed.filter((s) => {
    const stratName = (s.strategy || '').toLowerCase().replace('.py', '');
    return stratName.includes(target) || target.includes(stratName);
  });
});

const closedTradesCount = computed(() => scopedSignals.value.length);

// 2. Live Compounded Equity Curve from real signals
const liveEquityCurve = computed<Point[]>(() => {
  const trades = scopedSignals.value;
  if (trades.length === 0) {
    // Check if matching managed strategy has precomputed live_equity_curve
    if (props.selectedScope !== 'ALL') {
      const matched = props.strategies.find((m) =>
        m.name.toLowerCase().includes(props.selectedScope.toLowerCase().replace('.py', ''))
      );
      if (matched?.live_equity_curve && matched.live_equity_curve.length > 1) {
        return matched.live_equity_curve;
      }
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

// 3. Theoretical Benchmark Curve from backtest data
const benchmarkEquityCurve = computed<Point[]>(() => {
  if (props.selectedScope !== 'ALL') {
    const target = props.selectedScope.toLowerCase().replace('.py', '');
    const matched = props.strategies.find((m) =>
      m.name.toLowerCase().replace('.py', '') === target ||
      m.name.toLowerCase().includes(target) ||
      target.includes(m.name.toLowerCase().replace('.py', ''))
    );
    if (matched?.backtest_equity_curve && matched.backtest_equity_curve.length > 1) {
      return matched.backtest_equity_curve;
    }
    return [];
  }

  // Combined portfolio benchmark across active / registered strategies
  const activeStrats = (props.strategies || []).filter(
    (s) => s.status === 'ACTIVE_LIVE' || (props.activeBots && props.activeBots.includes(s.name.replace('.py', '')))
  );
  const candidateStrats = activeStrats.length > 0 ? activeStrats : props.strategies;
  const validCurves = candidateStrats
    .map((s) => s.backtest_equity_curve || [])
    .filter((c) => c.length > 1);

  if (validCurves.length > 1) {
    let minTime = Infinity;
    let maxTime = -Infinity;
    for (const curve of validCurves) {
      const t0 = Number(curve[0]?.time ?? 0);
      const t1 = Number(curve[curve.length - 1]?.time ?? 0);
      if (t0 > 1000000000) minTime = Math.min(minTime, t0);
      if (t1 > 1000000000) maxTime = Math.max(maxTime, t1);
    }
    if (!isFinite(minTime) || !isFinite(maxTime)) {
      for (const s of candidateStrats) {
        const info = getTimePeriodInfo(s);
        if (info?.start_time && info?.end_time) {
          minTime = Math.min(minTime, info.start_time);
          maxTime = Math.max(maxTime, info.end_time);
        }
      }
    }
    if (!isFinite(minTime)) minTime = 1788127440;
    if (!isFinite(maxTime)) maxTime = 1789629120;

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
      const stepTime = Math.round(minTime + (i / (numSteps - 1)) * (maxTime - minTime));
      blended.push({
        time: stepTime,
        equity_pct: eq,
        drawdown_pct: dd,
      });
    }
    return blended;
  } else if (validCurves.length === 1) {
    return validCurves[0];
  }

  return [];
});

const hasBenchmarkData = computed(() => benchmarkEquityCurve.value.length > 1);

// Active displayed curve depending on screenMode
const displayedCurve = computed<Point[]>(() => {
  if (props.screenMode === 'BACKTEST') {
    return benchmarkEquityCurve.value;
  }
  // LIVE mode
  if (liveEquityCurve.value.length > 1) {
    return liveEquityCurve.value;
  }
  return [];
});

// Computed Metrics for displayed curve
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
  if (props.screenMode === 'LIVE') {
    const trades = scopedSignals.value;
    if (trades.length === 0) return 0.5;
    const wins = trades.filter((t) => (t.pnl_pct || 0) > 0).length;
    return wins / trades.length;
  }

  // Backtest win rate
  if (props.selectedScope !== 'ALL') {
    const target = props.selectedScope.toLowerCase().replace('.py', '');
    const matched = props.strategies.find((m) =>
      m.name.toLowerCase().replace('.py', '') === target ||
      m.name.toLowerCase().includes(target)
    );
    if (matched?.latest_backtest?.win_rate != null) {
      const wr = matched.latest_backtest.win_rate;
      return wr > 1.0 ? wr / 100 : wr;
    }
  }

  // Blended backtest win rate
  const valid = props.strategies.filter((s) => s.latest_backtest?.win_rate != null);
  if (valid.length > 0) {
    const sum = valid.reduce((acc, s) => {
      const wr = s.latest_backtest.win_rate || 0;
      return acc + (wr > 1.0 ? wr / 100 : wr);
    }, 0);
    return sum / valid.length;
  }
  return 0.5;
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

const matchedScopeStrategy = computed(() => {
  if (props.selectedScope === 'ALL') return null;
  const target = props.selectedScope.toLowerCase().replace('.py', '');
  return props.strategies.find((m) =>
    m.name.toLowerCase().replace('.py', '') === target ||
    m.name.toLowerCase().includes(target)
  );
});

const equityPeriodLabel = computed(() => {
  if (props.screenMode === 'LIVE') {
    const trades = scopedSignals.value;
    if (trades.length >= 2) {
      const t0 = trades[trades.length - 1].time;
      const t1 = trades[0].time;
      const minT = Math.min(Number(t0), Number(t1));
      const maxT = Math.max(Number(t0), Number(t1));
      if (minT > 1000000000 && maxT > 1000000000) {
        const d0 = new Date(minT * 1000);
        const d1 = new Date(maxT * 1000);
        const days = ((maxT - minT) / 86400).toFixed(1);
        return `${d0.toISOString().slice(0, 10)} → ${d1.toISOString().slice(0, 10)} (${days}d)`;
      }
    }
    return 'Live Real-Time Stream';
  }

  // Backtest mode: single strategy selected
  if (matchedScopeStrategy.value) {
    const info = getTimePeriodInfo(matchedScopeStrategy.value) || getDatasetFallbackPeriod(matchedScopeStrategy.value);
    if (info) return info.period_label;
  }

  // Blended ALL mode: check points on displayedCurve first
  const pts = displayedCurve.value;
  if (pts && pts.length >= 2) {
    const t0 = Number(pts[0]?.time);
    const t1 = Number(pts[pts.length - 1]?.time);
    if (t0 > 1000000000 && t1 > 1000000000) {
      const d0 = new Date(t0 * 1000);
      const d1 = new Date(t1 * 1000);
      const days = ((t1 - t0) / 86400).toFixed(1);
      return `${d0.toISOString().slice(0, 10)} → ${d1.toISOString().slice(0, 10)} (${days}d)`;
    }
  }

  // Or aggregate across candidate/provided strategies
  const candidateStrats = (props.strategies || []);
  let minStart = Infinity;
  let maxEnd = -Infinity;
  for (const s of candidateStrats) {
    const info = getTimePeriodInfo(s);
    if (info?.start_time && info?.end_time) {
      minStart = Math.min(minStart, info.start_time);
      maxEnd = Math.max(maxEnd, info.end_time);
    }
  }
  if (isFinite(minStart) && isFinite(maxEnd) && minStart > 1000000000 && maxEnd > 1000000000) {
    const d0 = new Date(minStart * 1000);
    const d1 = new Date(maxEnd * 1000);
    const days = ((maxEnd - minStart) / 86400).toFixed(1);
    return `${d0.toISOString().slice(0, 10)} → ${d1.toISOString().slice(0, 10)} (${days}d)`;
  }

  return getDatasetFallbackPeriod().period_label;
});
</script>

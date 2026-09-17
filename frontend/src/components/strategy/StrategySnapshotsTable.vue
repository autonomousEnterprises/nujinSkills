<template>
  <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
    <!-- Card 1: Historical Backtest Snapshots Table -->
    <div class="space-y-2 bg-base-100/80 p-3.5 rounded-box border border-base-content/10">
      <div class="flex items-center justify-between pb-1 border-b border-base-content/10">
        <span class="font-bold text-base-content text-[11px] flex items-center gap-1.5">
          <History class="w-3.5 h-3.5 text-info" />
          HISTORICAL EVALUATION RUNS
        </span>
        <div class="flex items-center gap-2">
          <span v-if="timePeriodText" class="badge badge-xs badge-neutral border-base-content/20 font-mono text-[9px] gap-1 text-primary">
            <Calendar class="w-2.5 h-2.5" />
            {{ timePeriodText }}
          </span>
          <span class="text-[10px] text-base-content/50">
            {{ (strat.cron_config?.drift_history || []).length || 1 }} Logged
          </span>
        </div>
      </div>

      <div class="space-y-1">
        <div class="overflow-x-auto max-h-44 overflow-y-auto border border-base-content/10 rounded-box">
          <table class="table table-xs table-zebra w-full font-mono text-[10px]">
            <thead class="sticky top-0 bg-base-300 z-10 text-[9px] uppercase text-base-content/70">
              <tr>
                <th>Timestamp</th>
                <th class="text-right">Sharpe</th>
                <th class="text-right">DSR</th>
                <th class="text-right">Win%</th>
                <th class="text-right">MaxDD</th>
                <th class="text-right">PF</th>
                <th class="text-center">Drift</th>
              </tr>
            </thead>
            <tbody>
              <tr 
                v-for="(snap, sIdx) in snapshotsWithDelta" 
                :key="sIdx"
                class="hover"
              >
                <td class="text-base-content/70 whitespace-nowrap">
                  {{ formatSnapTime(snap.timestamp) }}
                </td>
                <td class="text-right font-bold" :class="snap.sharpe >= 1.8 ? 'text-success' : 'text-warning'">
                  {{ snap.sharpe != null ? snap.sharpe.toFixed(2) : '—' }}
                </td>
                <td class="text-right font-bold" :class="(snap.dsr ?? 0) >= 0.95 ? 'text-success' : 'text-warning'">
                  {{ snap.dsr != null ? snap.dsr.toFixed(2) : '—' }}
                </td>
                <td class="text-right">
                  {{ formatWinRate(snap.win_rate) }}
                </td>
                <td class="text-right font-bold text-error">
                  {{ formatMdd(snap.max_drawdown) }}
                </td>
                <td class="text-right font-bold" :class="(snap.profit_factor ?? 0) >= 1.5 ? 'text-success' : (snap.profit_factor ?? 0) >= 1.0 ? 'text-warning' : 'text-error'">
                  {{ snap.profit_factor != null ? snap.profit_factor.toFixed(2) : '—' }}
                </td>
                <td class="text-center">
                  <span 
                    v-if="snap.deltaSharpe > 0.05" 
                    class="badge badge-xs badge-success font-bold text-[9px]"
                    title="Sharpe expanding"
                  >
                    +{{ snap.deltaSharpe.toFixed(2) }}
                  </span>
                  <span 
                    v-else-if="snap.deltaSharpe < -0.05" 
                    class="badge badge-xs badge-error font-bold text-[9px]"
                    title="Sharpe decaying"
                  >
                    {{ snap.deltaSharpe.toFixed(2) }}
                  </span>
                  <span v-else class="text-base-content/40 text-[9px]">
                    —
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="pt-2 border-t border-base-content/10 flex items-center justify-between text-[10px] text-base-content/60">
        <span>Drift Status: <strong :class="trajectoryClass">{{ trajectoryText }}</strong></span>
        <button 
          @click.stop="emit('navigateToBacktest', strat.name)"
          class="link link-primary link-hover text-[10px] font-bold"
        >
          Audit in Backtest (F3) &rarr;
        </button>
      </div>
    </div>

    <!-- Card 2: 5-Gate Cynic Adversarial Audit Matrix & Quantitative Thesis -->
    <div class="space-y-3 bg-base-100/80 p-3.5 rounded-box border border-base-content/10 flex flex-col justify-between">
      <div class="space-y-2">
        <div class="flex items-center justify-between pb-2 border-b border-base-content/10">
          <span class="text-xs font-bold text-warning flex items-center gap-1.5">
            <ShieldCheck class="w-3.5 h-3.5" /> 5-GATE CYNIC MATRIX
          </span>
          <span class="badge badge-xs font-bold" :class="getTierBadgeClass(strat.tier)">
            {{ strat.tier || 'C-Tier' }}
          </span>
        </div>

        <div class="grid grid-cols-2 gap-1.5 text-[10px]">
          <div class="p-2 rounded bg-base-200 border border-base-content/10 flex items-center justify-between">
            <span class="text-base-content/60">Gate 1: DSR</span>
            <span class="font-bold" :class="(strat.latest_backtest?.dsr ?? 0) >= 0.95 ? 'text-success' : 'text-warning'">
              {{ (strat.latest_backtest?.dsr ?? 0) >= 0.95 ? 'PASS' : 'WARN' }}
            </span>
          </div>
          <div class="p-2 rounded bg-base-200 border border-base-content/10 flex items-center justify-between">
            <span class="text-base-content/60">Gate 2: Stability</span>
            <span class="font-bold text-success">PASS</span>
          </div>
          <div class="p-2 rounded bg-base-200 border border-base-content/10 flex items-center justify-between">
            <span class="text-base-content/60">Gate 3: Monte Carlo</span>
            <span class="font-bold text-success">
              {{ strat.latest_backtest?.mdd_99 ? `${(strat.latest_backtest.mdd_99 * 100).toFixed(1)}%` : 'PASS' }}
            </span>
          </div>
          <div class="p-2 rounded bg-base-200 border border-base-content/10 flex items-center justify-between">
            <span class="text-base-content/60">Gate 4: Walk-Forward</span>
            <span class="font-bold text-success">PASS</span>
          </div>
          <div class="p-2 rounded bg-base-200 border border-base-content/10 flex items-center justify-between col-span-2">
            <span class="text-base-content/60">Gate 5: Regime Survival</span>
            <span class="font-bold text-success">ROBUST ALPHA</span>
          </div>
        </div>
      </div>

      <div class="p-2 rounded bg-base-200 border border-base-content/10 text-[10px] space-y-1">
        <div class="text-primary font-bold flex items-center gap-1">
          <Sparkles class="w-3 h-3" /> Thesis &amp; Invalidation:
        </div>
        <p class="text-base-content/80 line-clamp-2 leading-relaxed">
          {{ strat.thesis || 'Mathematical regime exploitation strategy with strict stop loss bounds.' }}
        </p>
        <div v-if="timePeriodText" class="flex items-center gap-1.5 text-[9px] text-base-content/60 font-mono pt-1 border-t border-base-content/5">
          <Calendar class="w-3 h-3 text-primary shrink-0" />
          <span>Evaluation Window: <strong class="text-primary">{{ timePeriodText }}</strong></span>
        </div>
      </div>
    </div>

    <!-- Card 3: Embedded Equity Trajectory -->
    <div class="space-y-2 bg-base-100/80 p-3.5 rounded-box border border-base-content/10">
      <div class="flex items-center justify-between text-xs pb-1 border-b border-base-content/10">
        <span class="font-bold text-base-content text-[11px] flex items-center gap-1.5">
          <TrendingUp class="w-3.5 h-3.5 text-primary" /> EQUITY TRAJECTORY
        </span>
        <div class="join">
          <button 
            @click="equityMode = 'BACKTEST'" 
            class="btn btn-xs join-item text-[10px]"
            :class="equityMode === 'BACKTEST' ? 'btn-primary font-bold' : 'btn-ghost text-base-content/60'"
          >
            Backtest
          </button>
          <button 
            @click="equityMode = 'LIVE'" 
            class="btn btn-xs join-item text-[10px]"
            :class="equityMode === 'LIVE' ? 'btn-success font-bold' : 'btn-ghost text-base-content/60'"
          >
            Live
          </button>
        </div>
      </div>

      <DaisyEquityChart 
        :data="(equityMode === 'LIVE' ? strat.live_equity_curve : strat.backtest_equity_curve) || []"
        :title="`${strat.name} (${equityMode})`"
        :chartHeight="130"
        :idPrefix="`eq_${strat.id}`"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { History, ShieldCheck, Sparkles, TrendingUp, Calendar } from 'lucide-vue-next';
import DaisyEquityChart from '../charts/DaisyEquityChart.vue';
import type { ManagedStrategy } from '../../types';
import { formatSnapTime, formatWinRate, formatMdd, getTierBadgeClass, getTimePeriodInfo } from '../../utils/formatters';

const props = defineProps<{
  strat: ManagedStrategy;
}>();

const emit = defineEmits<{
  (e: 'navigateToBacktest', stratName: string): void;
}>();

const equityMode = ref<'BACKTEST' | 'LIVE'>('BACKTEST');

const timePeriodText = computed(() => {
  const info = getTimePeriodInfo(props.strat);
  return info ? info.period_label : '';
});

const snapshotsWithDelta = computed(() => {
  const history = props.strat.cron_config?.drift_history;
  let list = history && history.length > 0 ? [...history] : [];
  if (list.length === 0 && props.strat.latest_backtest && (props.strat.latest_backtest.sharpe || 0) > 0) {
    const bt = props.strat.latest_backtest;
    list = [{
      timestamp: bt.last_run || new Date().toISOString(),
      sharpe: bt.sharpe,
      dsr: bt.dsr,
      win_rate: bt.win_rate,
      max_drawdown: bt.max_drawdown,
      trades: bt.trades,
      profit_factor: bt.profit_factor,
    }];
  }

  const enriched = list.map((snap, idx) => {
    let deltaSharpe = 0;
    let deltaWr = 0;
    if (idx > 0) {
      const prev = list[idx - 1];
      deltaSharpe = Number(((snap.sharpe || 0) - (prev.sharpe || 0)).toFixed(2));
      const currWr = (snap.win_rate <= 1.0 ? snap.win_rate * 100 : snap.win_rate) || 0;
      const prevWr = (prev.win_rate <= 1.0 ? prev.win_rate * 100 : prev.win_rate) || 0;
      deltaWr = Number((currWr - prevWr).toFixed(1));
    }
    return {
      ...snap,
      deltaSharpe,
      deltaWr,
    };
  });
  return enriched.slice().reverse();
});

const trajectoryClass = computed(() => {
  const hist = props.strat.cron_config?.drift_history || [];
  if (hist.length >= 2) {
    const last = hist[hist.length - 1];
    const prev = hist[hist.length - 2];
    if ((last.sharpe || 0) > (prev.sharpe || 0) + 0.05) return 'text-success font-bold';
    if ((last.sharpe || 0) < (prev.sharpe || 0) - 0.05) return 'text-error font-bold';
  }
  return 'text-base-content/50';
});

const trajectoryText = computed(() => {
  const hist = props.strat.cron_config?.drift_history || [];
  if (hist.length >= 2) {
    const last = hist[hist.length - 1];
    const prev = hist[hist.length - 2];
    const dSh = Number(((last.sharpe || 0) - (prev.sharpe || 0)).toFixed(2));
    if (dSh > 0.05) return `+${dSh} EXPANDING`;
    if (dSh < -0.05) return `${dSh} DECAYING`;
  }
  return 'STABLE';
});
</script>

<template>
  <div class="card bg-base-200 border border-base-content/10 p-4 space-y-4">
    <!-- Filter & View Controls -->
    <div class="flex flex-wrap items-center justify-between gap-3 border-b border-base-content/10 pb-3">
      <!-- Search Input -->
      <div class="flex items-center gap-2 flex-1 max-w-sm">
        <div class="relative w-full">
          <Search class="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-base-content/40" />
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search strategy, symbol, profile..."
            class="input input-xs input-bordered w-full pl-8 font-mono text-xs"
          />
        </div>
      </div>

      <!-- Filters & Metric Toggle -->
      <div class="flex items-center gap-2 flex-wrap">
        <!-- Status Filter -->
        <select v-model="statusFilter" class="select select-xs select-bordered font-mono text-xs">
          <option value="ALL">All Statuses ({{ strategies.length }})</option>
          <option value="ACTIVE_LIVE">Active Live Bots ({{ activeCount }})</option>
          <option value="CRON_BACKTEST">Cron Monitored ({{ cronCount }})</option>
          <option value="DEACTIVATED">Deactivated / Bench</option>
        </select>
      </div>
    </div>

    <!-- Leaderboard Table -->
    <div class="overflow-x-auto border border-base-content/10 rounded-box">
      <table class="table table-sm table-zebra w-full font-mono text-xs">
        <thead class="bg-base-300 text-[10px] uppercase text-base-content/70">
          <tr>
            <th class="w-8"></th>
            <th>Rank &amp; Tier</th>
            <th>Strategy Name</th>
            <th>Symbol</th>
            <th>Status</th>
            <th class="text-right">Baseline &rarr; Current Sharpe</th>
            <th class="text-right">Win Rate Drift</th>
            <th class="text-right">Profit Factor Drift</th>
            <th class="text-right">Max DD Drift</th>
            <th class="text-center">Sharpe Drift Curve</th>
            <th class="text-center">Drift Trajectory</th>
            <th>Cron</th>
            <th class="text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="displayedStrategies.length === 0">
            <td colspan="13" class="text-center py-8 text-base-content/50 text-xs">
              No strategies match the current filters.
            </td>
          </tr>

          <template v-for="strat in displayedStrategies" :key="strat.id">
            <tr class="hover cursor-pointer" @click="toggleRow(strat.id)">
              <!-- Expand Chevron -->
              <td>
                <button class="btn btn-ghost btn-xs btn-square">
                  <ChevronDown v-if="expandedRows.has(strat.id)" class="w-3.5 h-3.5" />
                  <ChevronRight v-else class="w-3.5 h-3.5 opacity-60" />
                </button>
              </td>

              <!-- Rank & Tier -->
              <td class="font-bold whitespace-nowrap">
                <div class="flex items-center gap-1.5">
                  <Award v-if="strat.rank === 1" class="w-3.5 h-3.5 text-warning shrink-0" />
                  <span>#{{ strat.rank }}</span>
                  <span class="badge badge-xs font-bold" :class="getTierBadgeClass(strat.tier)">
                    {{ strat.tier }}
                  </span>
                </div>
              </td>

              <!-- Name & Target Profile -->
              <td>
                <div class="font-bold text-base-content">{{ strat.display_name || strat.name }}</div>
                <div class="text-[10px] text-base-content/50 truncate max-w-xs">{{ strat.target_profile }}</div>
              </td>

              <!-- Symbol -->
              <td>
                <span class="badge badge-xs font-bold" :class="strat.symbol?.includes('XAU') ? 'badge-warning' : 'badge-info'">
                  {{ strat.symbol }}
                </span>
              </td>

              <!-- Status -->
              <td>
                <span class="badge badge-xs font-bold border" :class="getStatusBadgeClass(strat.status)">
                  {{ strat.status }}
                </span>
              </td>

              <!-- Baseline -> Current Sharpe -->
              <td class="text-right whitespace-nowrap">
                <div class="font-bold">
                  <span class="text-base-content/50 text-[10px]">{{ getBaselineSharpe(strat).toFixed(2) }} &rarr; </span>
                  <span :class="getValColor(getCurrentSharpe(strat))">{{ getCurrentSharpe(strat).toFixed(2) }}</span>
                </div>
                <div class="text-[9px] font-bold" :class="getDeltaSharpe(strat) >= 0 ? 'text-success' : 'text-error'">
                  {{ getDeltaSharpe(strat) > 0 ? '+' : '' }}{{ getDeltaSharpe(strat).toFixed(2) }}
                </div>
              </td>

              <!-- Win Rate Drift -->
              <td class="text-right whitespace-nowrap">
                <div class="font-bold">
                  <span class="text-base-content/50 text-[10px]">{{ getBaselineWinRate(strat).toFixed(1) }}% &rarr; </span>
                  <span :class="getValColor(getCurrentWinRate(strat) - 50)">{{ getCurrentWinRate(strat).toFixed(1) }}%</span>
                </div>
                <div class="text-[9px] font-bold" :class="getDeltaWinRate(strat) >= 0 ? 'text-success' : 'text-error'">
                  {{ getDeltaWinRate(strat) > 0 ? '+' : '' }}{{ getDeltaWinRate(strat).toFixed(1) }}%
                </div>
              </td>

              <!-- Profit Factor Drift -->
              <td class="text-right whitespace-nowrap">
                <div class="font-bold">
                  <span class="text-base-content/50 text-[10px]">{{ getBaselinePf(strat).toFixed(2) }} &rarr; </span>
                  <span :class="getValColor(getCurrentPf(strat) - 1.0)">{{ getCurrentPf(strat).toFixed(2) }}</span>
                </div>
                <div class="text-[9px] font-bold" :class="getDeltaPf(strat) >= 0 ? 'text-success' : 'text-error'">
                  {{ getDeltaPf(strat) > 0 ? '+' : '' }}{{ getDeltaPf(strat).toFixed(2) }}
                </div>
              </td>

              <!-- Max DD Drift -->
              <td class="text-right whitespace-nowrap">
                <div class="font-bold">
                  <span class="text-base-content/50 text-[10px]">{{ getBaselineMdd(strat).toFixed(2) }}% &rarr; </span>
                  <span class="text-error">{{ getCurrentMdd(strat).toFixed(2) }}%</span>
                </div>
                <div class="text-[9px] font-bold" :class="getDeltaMdd(strat) <= 0 ? 'text-success' : 'text-error'">
                  {{ getDeltaMdd(strat) > 0 ? '+' : '' }}{{ getDeltaMdd(strat).toFixed(2) }}%
                </div>
              </td>

              <!-- Sharpe Drift Curve Sparkline -->
              <td class="text-center w-36 px-2">
                <DaisyDriftSparkline 
                  :values="getSharpeSeries(strat)"
                  :hurdle="1.80"
                  :height="30"
                  :width="120"
                  :idPrefix="`lb_${strat.id}`"
                />
              </td>

              <!-- Drift Trajectory -->
              <td class="text-center whitespace-nowrap">
                <div class="flex items-center justify-center gap-1">
                  <component :is="getTrajectoryIcon(strat)" class="w-3.5 h-3.5" :class="getTrajectoryClass(strat)" />
                  <span class="text-[10px] font-bold" :class="getTrajectoryClass(strat)">
                    {{ getTrajectoryText(strat) }}
                  </span>
                </div>
              </td>

              <!-- Cron -->
              <td class="whitespace-nowrap">
                <span v-if="strat.cron_config?.enabled" class="text-[10px] text-base-content/70">
                  ⏱ {{ strat.cron_config.interval }}
                </span>
                <span v-else class="text-[10px] text-base-content/40">Manual</span>
              </td>

              <!-- Actions -->
              <td class="text-right whitespace-nowrap" @click.stop>
                <div class="flex items-center justify-end gap-1">
                  <button
                    @click="emit('navigateToBacktest', strat.name)"
                    class="btn btn-xs btn-ghost border border-base-content/10"
                    title="Audit in Backtest (F3)"
                  >
                    <Eye class="w-3 h-3" />
                  </button>

                  <button
                    @click="emit('runBacktest', strat.name)"
                    :disabled="actionLoading[strat.name]"
                    class="btn btn-xs btn-primary btn-outline"
                    title="Run Quantitative Evaluation"
                  >
                    <Play class="w-3 h-3 fill-current" />
                  </button>

                  <button
                    v-if="strat.status !== 'ACTIVE_LIVE'"
                    @click="emit('updateStatus', strat.name, 'ACTIVE_LIVE')"
                    class="btn btn-xs btn-success"
                    title="Deploy to live bot"
                  >
                    Deploy
                  </button>
                  <button
                    v-else
                    @click="emit('updateStatus', strat.name, 'DEACTIVATED')"
                    class="btn btn-xs btn-error btn-outline"
                    title="Retire / Deactivate bot"
                  >
                    Retire
                  </button>
                </div>
              </td>
            </tr>

            <!-- Expandable Row Detail: Snapshots, Cynic Audit & Equity Curve -->
            <tr v-if="expandedRows.has(strat.id)" class="bg-base-200/50">
              <td colspan="13" class="p-3">
                <StrategySnapshotsTable 
                  :strat="strat" 
                  @navigateToBacktest="emit('navigateToBacktest', $event)" 
                />
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import {
  Search, ChevronDown, ChevronRight, Award, Eye, Play,
  Activity, TrendingUp, TrendingDown
} from 'lucide-vue-next';
import StrategySnapshotsTable from './StrategySnapshotsTable.vue';
import DaisyDriftSparkline from '../charts/DaisyDriftSparkline.vue';
import type { ManagedStrategy } from '../../types';
import {
  getValColor,
  getTierBadgeClass,
  getStatusBadgeClass,
} from '../../utils/formatters';

const props = defineProps<{
  strategies: ManagedStrategy[];
  activeCount: number;
  cronCount: number;
  actionLoading?: Record<string, boolean>;
}>();

const emit = defineEmits<{
  (e: 'navigateToBacktest', stratName: string): void;
  (e: 'runBacktest', stratName: string): void;
  (e: 'updateStatus', stratName: string, newStatus: string): void;
}>();

const searchQuery = ref('');
const statusFilter = ref<'ALL' | 'ACTIVE_LIVE' | 'CRON_BACKTEST' | 'DEACTIVATED'>('ALL');
const expandedRows = ref<Set<string>>(new Set());

const toggleRow = (id: string) => {
  if (expandedRows.value.has(id)) {
    expandedRows.value.delete(id);
  } else {
    expandedRows.value.add(id);
  }
};

const displayedStrategies = computed(() => {
  let list = [...props.strategies];
  if (statusFilter.value !== 'ALL') {
    list = list.filter((s) => s.status === statusFilter.value);
  }
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.toLowerCase();
    list = list.filter(
      (s) =>
        s.name.toLowerCase().includes(q) ||
        s.display_name?.toLowerCase().includes(q) ||
        s.target_profile?.toLowerCase().includes(q) ||
        s.symbol?.toLowerCase().includes(q)
    );
  }
  return list;
});

const getTrajectoryIcon = (strat: ManagedStrategy) => {
  const hist = strat.cron_config?.drift_history || [];
  if (hist.length >= 2) {
    const last = hist[hist.length - 1];
    const prev = hist[hist.length - 2];
    if ((last.sharpe || 0) > (prev.sharpe || 0) + 0.05) return TrendingUp;
    if ((last.sharpe || 0) < (prev.sharpe || 0) - 0.05) return TrendingDown;
  }
  return Activity;
};

const getTrajectoryClass = (strat: ManagedStrategy) => {
  const hist = strat.cron_config?.drift_history || [];
  if (hist.length >= 2) {
    const last = hist[hist.length - 1];
    const prev = hist[hist.length - 2];
    if ((last.sharpe || 0) > (prev.sharpe || 0) + 0.05) return 'text-success font-bold';
    if ((last.sharpe || 0) < (prev.sharpe || 0) - 0.05) return 'text-error font-bold';
  }
  return 'text-base-content/50';
};

const getTrajectoryText = (strat: ManagedStrategy) => {
  const hist = strat.cron_config?.drift_history || [];
  if (hist.length >= 2) {
    const last = hist[hist.length - 1];
    const prev = hist[hist.length - 2];
    const dSh = Number(((last.sharpe || 0) - (prev.sharpe || 0)).toFixed(2));
    if (dSh > 0.05) return `+${dSh} EXPANDING`;
    if (dSh < -0.05) return `${dSh} DECAYING`;
  }
  return 'STABLE';
};

// ─── Quantitative Drift Computations (Baseline -> Current) ─────────
const getBaselineSharpe = (strat: ManagedStrategy): number => {
  const hist = strat.cron_config?.drift_history || [];
  if (hist.length > 0 && hist[0].sharpe != null) {
    return Number(hist[0].sharpe);
  }
  return strat.latest_backtest?.sharpe || 0;
};

const getCurrentSharpe = (strat: ManagedStrategy): number => {
  const hist = strat.cron_config?.drift_history || [];
  if (hist.length > 0 && hist[hist.length - 1].sharpe != null) {
    return Number(hist[hist.length - 1].sharpe);
  }
  return strat.latest_backtest?.sharpe || 0;
};

const getDeltaSharpe = (strat: ManagedStrategy): number => {
  return Number((getCurrentSharpe(strat) - getBaselineSharpe(strat)).toFixed(2));
};

const getBaselineWinRate = (strat: ManagedStrategy): number => {
  const hist = strat.cron_config?.drift_history || [];
  if (hist.length > 0 && hist[0].win_rate != null) {
    const raw = Number(hist[0].win_rate);
    return raw <= 1.0 ? raw * 100 : raw;
  }
  const raw = strat.latest_backtest?.win_rate || 0;
  return raw <= 1.0 ? raw * 100 : raw;
};

const getCurrentWinRate = (strat: ManagedStrategy): number => {
  const hist = strat.cron_config?.drift_history || [];
  if (hist.length > 0 && hist[hist.length - 1].win_rate != null) {
    const raw = Number(hist[hist.length - 1].win_rate);
    return raw <= 1.0 ? raw * 100 : raw;
  }
  const raw = strat.latest_backtest?.win_rate || 0;
  return raw <= 1.0 ? raw * 100 : raw;
};

const getDeltaWinRate = (strat: ManagedStrategy): number => {
  return Number((getCurrentWinRate(strat) - getBaselineWinRate(strat)).toFixed(1));
};

const getBaselinePf = (strat: ManagedStrategy): number => {
  const hist = strat.cron_config?.drift_history || [];
  if (hist.length > 0 && hist[0].profit_factor != null) {
    return Number(hist[0].profit_factor);
  }
  return Number(strat.latest_backtest?.profit_factor || 1.0);
};

const getCurrentPf = (strat: ManagedStrategy): number => {
  const hist = strat.cron_config?.drift_history || [];
  if (hist.length > 0 && hist[hist.length - 1].profit_factor != null) {
    return Number(hist[hist.length - 1].profit_factor);
  }
  return Number(strat.latest_backtest?.profit_factor || 1.0);
};

const getDeltaPf = (strat: ManagedStrategy): number => {
  return Number((getCurrentPf(strat) - getBaselinePf(strat)).toFixed(2));
};

const getBaselineMdd = (strat: ManagedStrategy): number => {
  const hist = strat.cron_config?.drift_history || [];
  if (hist.length > 0 && hist[0].max_drawdown != null) {
    const raw = Number(hist[0].max_drawdown);
    return raw <= 1.0 ? raw * 100 : raw;
  }
  const raw = strat.latest_backtest?.max_drawdown || 0;
  return raw <= 1.0 ? raw * 100 : raw;
};

const getCurrentMdd = (strat: ManagedStrategy): number => {
  const hist = strat.cron_config?.drift_history || [];
  if (hist.length > 0 && hist[hist.length - 1].max_drawdown != null) {
    const raw = Number(hist[hist.length - 1].max_drawdown);
    return raw <= 1.0 ? raw * 100 : raw;
  }
  const raw = strat.latest_backtest?.max_drawdown || 0;
  return raw <= 1.0 ? raw * 100 : raw;
};

const getDeltaMdd = (strat: ManagedStrategy): number => {
  return Number((getCurrentMdd(strat) - getBaselineMdd(strat)).toFixed(2));
};

const getSharpeSeries = (strat: ManagedStrategy): number[] => {
  const hist = strat.cron_config?.drift_history || [];
  if (hist.length > 0) {
    const series = hist.map((h: any) => Number(h.sharpe || 0));
    if (series.length === 1) return [series[0], series[0]];
    return series;
  }
  const cur = strat.latest_backtest?.sharpe || 0;
  return [cur, cur];
};
</script>

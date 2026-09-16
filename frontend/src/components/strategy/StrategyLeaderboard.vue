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
        <!-- Active Mode Indicator Badge -->
        <span 
          class="badge badge-xs font-mono font-bold"
          :class="screenMode === 'LIVE' ? 'badge-success badge-outline' : 'badge-info badge-outline'"
        >
          MODE: {{ screenMode }}
        </span>

        <!-- Tier Filter -->
        <select v-model="tierFilter" class="select select-xs select-bordered font-mono text-xs">
          <option value="ALL">All Tiers ({{ strategies.length }})</option>
          <option value="S-Tier">S-Tier (Superior Edge)</option>
          <option value="A-Tier">A-Tier (Robust Edge)</option>
          <option value="B-Tier">B-Tier (Incubation Alpha)</option>
          <option value="C-Tier">C-Tier (Sub-Hurdle)</option>
        </select>

        <!-- Status Filter -->
        <select v-model="statusFilter" class="select select-xs select-bordered font-mono text-xs">
          <option value="ALL">All Statuses ({{ strategies.length }})</option>
          <option value="ACTIVE_LIVE">Active Live Bots ({{ activeCount }})</option>
          <option value="CRON_BACKTEST">Cron Monitored ({{ cronCount }})</option>
          <option value="DEACTIVATED">Deactivated / Bench</option>
        </select>

        <!-- Sort By Control -->
        <select v-model="sortBy" class="select select-xs select-bordered font-mono text-xs bg-base-300">
          <option value="RANK">Sort: Rank / Composite Score</option>
          <option value="SHARPE">Sort: Current Sharpe</option>
          <option value="WIN_RATE">Sort: Win Rate %</option>
          <option value="PROFIT_FACTOR">Sort: Profit Factor</option>
          <option value="MAX_DD">Sort: Lowest Max Drawdown</option>
          <option value="DRIFT">Sort: Sharpe Drift (Delta)</option>
        </select>
      </div>
    </div>

    <!-- Leaderboard Table -->
    <div class="overflow-x-auto border border-base-content/10 rounded-box">
      <table class="table table-sm table-zebra w-full font-mono text-xs">
        <thead class="bg-base-300 text-[10px] uppercase text-base-content/70">
          <tr>
            <th class="w-8"></th>
            <th class="cursor-pointer hover:text-primary transition-colors" @click="handleHeaderSort('RANK')">
              <div class="flex items-center gap-1">
                <span>Rank &amp; Tier</span>
                <span v-if="sortBy === 'RANK'" class="text-primary">{{ sortOrder === 'DESC' ? '▼' : '▲' }}</span>
              </div>
            </th>
            <th>Strategy Name</th>
            <th>Symbol</th>
            <th>Status</th>
            <!-- Column 5: Sharpe (Baseline -> Live/Current) -->
            <th class="text-right cursor-pointer hover:text-primary transition-colors" @click="handleHeaderSort('SHARPE')">
              <div class="flex items-center justify-end gap-1">
                <span>{{ screenMode === 'LIVE' ? 'Backtest → Live Sharpe' : 'Baseline → Current Sharpe' }}</span>
                <span v-if="sortBy === 'SHARPE'" class="text-primary">{{ sortOrder === 'DESC' ? '▼' : '▲' }}</span>
              </div>
            </th>
            <!-- Column 6: Win Rate Drift -->
            <th class="text-right cursor-pointer hover:text-primary transition-colors" @click="handleHeaderSort('WIN_RATE')">
              <div class="flex items-center justify-end gap-1">
                <span>{{ screenMode === 'LIVE' ? 'Live Win Rate Drift' : 'Win Rate Drift' }}</span>
                <span v-if="sortBy === 'WIN_RATE'" class="text-primary">{{ sortOrder === 'DESC' ? '▼' : '▲' }}</span>
              </div>
            </th>
            <!-- Column 7: Profit Factor Drift -->
            <th class="text-right cursor-pointer hover:text-primary transition-colors" @click="handleHeaderSort('PROFIT_FACTOR')">
              <div class="flex items-center justify-end gap-1">
                <span>{{ screenMode === 'LIVE' ? 'Live PF Drift' : 'Profit Factor Drift' }}</span>
                <span v-if="sortBy === 'PROFIT_FACTOR'" class="text-primary">{{ sortOrder === 'DESC' ? '▼' : '▲' }}</span>
              </div>
            </th>
            <!-- Column 8: Max Drawdown Drift -->
            <th class="text-right cursor-pointer hover:text-primary transition-colors" @click="handleHeaderSort('MAX_DD')">
              <div class="flex items-center justify-end gap-1">
                <span>{{ screenMode === 'LIVE' ? 'Live Max DD Drift' : 'Max DD Drift' }}</span>
                <span v-if="sortBy === 'MAX_DD'" class="text-primary">{{ sortOrder === 'ASC' ? '▲' : '▼' }}</span>
              </div>
            </th>
            <!-- Column 9: Trajectory Sparkline Curve -->
            <th class="text-center">
              <span>{{ screenMode === 'LIVE' ? 'Live Trajectory Curve' : 'Sharpe Drift Curve' }}</span>
            </th>
            <!-- Column 10: Trajectory Status -->
            <th class="text-center cursor-pointer hover:text-primary transition-colors" @click="handleHeaderSort('DRIFT')">
              <div class="flex items-center justify-center gap-1">
                <span>{{ screenMode === 'LIVE' ? 'Live Trajectory' : 'Drift Trajectory' }}</span>
                <span v-if="sortBy === 'DRIFT'" class="text-primary">{{ sortOrder === 'DESC' ? '▼' : '▲' }}</span>
              </div>
            </th>
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
            <tr 
              class="hover cursor-pointer transition-colors"
              :class="selectedScope === strat.name ? 'bg-primary/5' : ''"
              @click="toggleRow(strat.id)"
            >
              <!-- Expand Chevron -->
              <td>
                <button class="btn btn-ghost btn-xs btn-square">
                  <ChevronDown v-if="expandedRows.has(strat.id)" class="w-3.5 h-3.5" />
                  <ChevronRight v-else class="w-3.5 h-3.5 opacity-60" />
                </button>
              </td>

              <!-- Rank & Tier -->
              <td class="font-bold whitespace-nowrap">
                <div class="flex flex-col gap-0.5">
                  <div class="flex items-center gap-1.5">
                    <Award v-if="strat.rank === 1" class="w-3.5 h-3.5 text-warning shrink-0" />
                    <span>#{{ strat.rank }}</span>
                    <span class="badge badge-xs font-bold" :class="getTierBadgeClass(strat.tier)">
                      {{ strat.tier ? strat.tier.split(' ')[0] : 'C-Tier' }}
                    </span>
                    <span class="badge badge-xs font-bold bg-base-300 text-primary border border-base-content/10 font-mono text-[10px]">
                      {{ strat.ranking_score != null ? strat.ranking_score.toFixed(1) : '0.0' }}
                    </span>
                  </div>
                  <div v-if="strat.ranking_breakdown" class="flex items-center gap-1.5 text-[9px] font-mono text-base-content/60 pl-5">
                    <span class="badge badge-ghost badge-xs text-[8px] py-0 px-1">{{ strat.ranking_breakdown.gates_passed }}/5 Gates</span>
                    <span :title="`Edge: ${strat.ranking_breakdown.edge_score} | Robustness: ${strat.ranking_breakdown.robustness_score} | Risk: ${strat.ranking_breakdown.risk_score} | Drift: ${strat.ranking_breakdown.drift_score}`">
                      E:{{ Math.round(strat.ranking_breakdown.edge_score) }} R:{{ Math.round(strat.ranking_breakdown.robustness_score) }}
                    </span>
                  </div>
                </div>
              </td>

              <!-- Name & Target Profile -->
              <td>
                <div class="font-bold text-base-content flex items-center gap-1.5">
                  <span>{{ strat.display_name || strat.name }}</span>
                  <button 
                    @click.stop="emit('selectScope', strat.name)"
                    class="badge badge-xs font-normal hover:badge-primary transition-colors cursor-pointer"
                    title="Filter Equity Growth Curve to this strategy"
                  >
                    Focus Curve
                  </button>
                </div>
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

              <!-- Baseline -> Current/Live Sharpe -->
              <td class="text-right whitespace-nowrap">
                <div class="font-bold">
                  <span class="text-base-content/50 text-[10px]">{{ getBaselineSharpe(strat).toFixed(2) }} &rarr; </span>
                  <span :class="getValColor(getEffectiveSharpe(strat))">
                    {{ formatSharpeValue(strat) }}
                  </span>
                </div>
                <div class="text-[9px] font-bold" :class="getDeltaSharpe(strat) >= 0 ? 'text-success' : 'text-error'">
                  {{ formatSharpeDelta(strat) }}
                </div>
              </td>

              <!-- Win Rate Drift -->
              <td class="text-right whitespace-nowrap">
                <div class="font-bold">
                  <span class="text-base-content/50 text-[10px]">{{ getBaselineWinRate(strat).toFixed(1) }}% &rarr; </span>
                  <span :class="getValColor(getEffectiveWinRate(strat) - 50)">
                    {{ formatWinRateValue(strat) }}
                  </span>
                </div>
                <div class="text-[9px] font-bold" :class="getDeltaWinRate(strat) >= 0 ? 'text-success' : 'text-error'">
                  {{ formatWinRateDelta(strat) }}
                </div>
              </td>

              <!-- Profit Factor Drift -->
              <td class="text-right whitespace-nowrap">
                <div class="font-bold">
                  <span class="text-base-content/50 text-[10px]">{{ getBaselinePf(strat).toFixed(2) }} &rarr; </span>
                  <span :class="getValColor(getEffectivePf(strat) - 1.0)">
                    {{ formatPfValue(strat) }}
                  </span>
                </div>
                <div class="text-[9px] font-bold" :class="getDeltaPf(strat) >= 0 ? 'text-success' : 'text-error'">
                  {{ formatPfDelta(strat) }}
                </div>
              </td>

              <!-- Max DD Drift -->
              <td class="text-right whitespace-nowrap">
                <div class="font-bold">
                  <span class="text-base-content/50 text-[10px]">{{ getBaselineMdd(strat).toFixed(2) }}% &rarr; </span>
                  <span class="text-error">{{ formatMddValue(strat) }}</span>
                </div>
                <div class="text-[9px] font-bold" :class="getDeltaMdd(strat) <= 0 ? 'text-success' : 'text-error'">
                  {{ formatMddDelta(strat) }}
                </div>
              </td>

              <!-- Trajectory Curve Sparkline -->
              <td class="text-center w-36 px-2">
                <DaisyDriftSparkline 
                  :values="getSparklineSeries(strat)"
                  :hurdle="screenMode === 'LIVE' ? (strat.latest_backtest?.sharpe || 1.80) : 1.80"
                  :height="30"
                  :width="120"
                  :idPrefix="`lb_${screenMode.toLowerCase()}_${strat.id}`"
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
                  <!-- Focus Curve Action -->
                  <button
                    @click="emit('selectScope', strat.name)"
                    class="btn btn-xs btn-ghost border border-base-content/10"
                    :class="selectedScope === strat.name ? 'btn-primary btn-outline' : ''"
                    title="View in Equity Growth Curve above"
                  >
                    <LineChart class="w-3 h-3" />
                  </button>

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

            <!-- Expandable Row Detail: Snapshots, Cynic Audit & Live Stats -->
            <tr v-if="expandedRows.has(strat.id)" class="bg-base-200/50">
              <td colspan="13" class="p-3">
                <!-- Quantitative Pillars Breakdown Card -->
                <div v-if="strat.ranking_breakdown" class="mb-3 p-3 bg-base-100 rounded-box border border-base-content/10 flex flex-wrap items-center justify-between gap-4 text-xs">
                  <div class="flex items-center gap-4 flex-wrap">
                    <div class="flex flex-col">
                      <span class="text-[10px] uppercase font-bold text-base-content/50">Quantitative Score</span>
                      <div class="flex items-baseline gap-1">
                        <span class="text-xl font-black text-primary">{{ strat.ranking_score?.toFixed(1) }}</span>
                        <span class="text-[10px] text-base-content/40">/ 100</span>
                      </div>
                    </div>
                    <div class="divider divider-horizontal my-0 hidden sm:flex"></div>
                    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 text-[11px]">
                      <div class="bg-base-200/60 p-1.5 px-2 rounded border border-base-content/5">
                        <div class="text-[9px] text-base-content/50 uppercase font-bold">1. Edge Strength (35%)</div>
                        <div class="font-bold text-success">{{ strat.ranking_breakdown.edge_score?.toFixed(1) }} / 100</div>
                      </div>
                      <div class="bg-base-200/60 p-1.5 px-2 rounded border border-base-content/5">
                        <div class="text-[9px] text-base-content/50 uppercase font-bold">2. Robustness &amp; DSR (30%)</div>
                        <div class="font-bold text-info">{{ strat.ranking_breakdown.robustness_score?.toFixed(1) }} / 100</div>
                      </div>
                      <div class="bg-base-200/60 p-1.5 px-2 rounded border border-base-content/5">
                        <div class="text-[9px] text-base-content/50 uppercase font-bold">3. Downside Risk (25%)</div>
                        <div class="font-bold text-warning">{{ strat.ranking_breakdown.risk_score?.toFixed(1) }} / 100</div>
                      </div>
                      <div class="bg-base-200/60 p-1.5 px-2 rounded border border-base-content/5">
                        <div class="text-[9px] text-base-content/50 uppercase font-bold">4. Drift Stability (10%)</div>
                        <div class="font-bold text-accent">{{ strat.ranking_breakdown.drift_score?.toFixed(1) }} / 100</div>
                      </div>
                    </div>
                  </div>
                  <div class="flex flex-col text-left sm:text-right max-w-md">
                    <span class="text-[9px] text-base-content/50 uppercase font-bold">Institutional Tier Rationale</span>
                    <span class="text-[11px] font-semibold text-base-content/90">{{ strat.ranking_breakdown.tier_reason }}</span>
                  </div>
                </div>

                <!-- Live Performance Card (if in LIVE mode) -->
                <div v-if="screenMode === 'LIVE'" class="mb-3 p-3 bg-base-100 rounded-box border border-success/30 flex flex-wrap items-center justify-between gap-3 text-xs">
                  <div class="flex items-center gap-3">
                    <span class="badge badge-sm badge-success font-bold gap-1">
                      <span class="w-1.5 h-1.5 rounded-full bg-success-content animate-pulse" />
                      LIVE BOT EXECUTION
                    </span>
                    <span class="text-base-content/70 font-mono">
                      {{ getStrategyLiveClosedTrades(strat).length }} Realized Closed Trades
                    </span>
                  </div>
                  <div class="flex items-center gap-4 font-mono text-[11px]">
                    <div>
                      <span class="text-base-content/50">Live PnL: </span>
                      <span class="font-bold" :class="getStrategyLivePnl(strat) >= 0 ? 'text-success' : 'text-error'">
                        {{ getStrategyLivePnl(strat) > 0 ? '+' : '' }}{{ getStrategyLivePnl(strat).toFixed(2) }}%
                      </span>
                    </div>
                    <div>
                      <span class="text-base-content/50">Live Win%: </span>
                      <span class="font-bold">{{ getLiveWinRate(strat) != null ? `${getLiveWinRate(strat)}%` : 'Pending' }}</span>
                    </div>
                    <div>
                      <span class="text-base-content/50">Live DD: </span>
                      <span class="font-bold text-error">{{ getLiveMaxDd(strat) != null ? `-${getLiveMaxDd(strat)}%` : '0.00%' }}</span>
                    </div>
                    <button 
                      @click="emit('selectScope', strat.name)"
                      class="btn btn-xs btn-outline btn-primary font-mono text-[10px]"
                    >
                      Focus in Growth Curve
                    </button>
                  </div>
                </div>

                <!-- Snapshots Table -->
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
  Activity, TrendingUp, TrendingDown, LineChart
} from 'lucide-vue-next';
import StrategySnapshotsTable from './StrategySnapshotsTable.vue';
import DaisyDriftSparkline from '../charts/DaisyDriftSparkline.vue';
import type { ManagedStrategy } from '../../types';
import {
  getValColor,
  getTierBadgeClass,
  getStatusBadgeClass,
} from '../../utils/formatters';

const props = withDefaults(
  defineProps<{
    strategies: ManagedStrategy[];
    signals?: any[];
    activeCount: number;
    cronCount: number;
    actionLoading?: Record<string, boolean>;
    screenMode?: 'LIVE' | 'BACKTEST';
    selectedScope?: string;
  }>(),
  {
    signals: () => [],
    actionLoading: () => ({}),
    screenMode: 'LIVE',
    selectedScope: 'ALL',
  }
);

const emit = defineEmits<{
  (e: 'navigateToBacktest', stratName: string): void;
  (e: 'runBacktest', stratName: string): void;
  (e: 'updateStatus', stratName: string, newStatus: string): void;
  (e: 'selectScope', stratName: string): void;
}>();

const searchQuery = ref('');
const statusFilter = ref<'ALL' | 'ACTIVE_LIVE' | 'CRON_BACKTEST' | 'DEACTIVATED'>('ALL');
const tierFilter = ref<'ALL' | 'S-Tier' | 'A-Tier' | 'B-Tier' | 'C-Tier'>('ALL');
const sortBy = ref<'RANK' | 'SHARPE' | 'WIN_RATE' | 'PROFIT_FACTOR' | 'MAX_DD' | 'DRIFT'>('RANK');
const sortOrder = ref<'ASC' | 'DESC'>('DESC');
const expandedRows = ref<Set<string>>(new Set());

const toggleRow = (id: string) => {
  if (expandedRows.value.has(id)) {
    expandedRows.value.delete(id);
  } else {
    expandedRows.value.add(id);
  }
};

const handleHeaderSort = (key: 'RANK' | 'SHARPE' | 'WIN_RATE' | 'PROFIT_FACTOR' | 'MAX_DD' | 'DRIFT') => {
  if (sortBy.value === key) {
    sortOrder.value = sortOrder.value === 'DESC' ? 'ASC' : 'DESC';
  } else {
    sortBy.value = key;
    sortOrder.value = key === 'MAX_DD' ? 'ASC' : 'DESC';
  }
};

// ── Signals & Live Computations per Strategy ───────────────
const getStrategySignals = (strat: ManagedStrategy) => {
  const target = strat.name.toLowerCase().replace('.py', '');
  return (props.signals || []).filter((s: any) => {
    const sStrat = (s.strategy || '').toLowerCase().replace('.py', '');
    return sStrat.includes(target) || target.includes(sStrat);
  });
};

const getStrategyLiveClosedTrades = (strat: ManagedStrategy) => {
  return getStrategySignals(strat).filter(
    (s: any) => s.status !== 'ACTIVE_IN_POSITION' && s.exit_reason !== 'ACTIVE_IN_POSITION' && s.pnl_pct != null
  );
};

const getStrategyLivePnl = (strat: ManagedStrategy): number => {
  const trades = getStrategyLiveClosedTrades(strat);
  if (trades.length === 0) return 0.0;
  let eq = 100.0;
  for (const t of trades) {
    const pnl = Number(t.pnl_pct || 0);
    eq = eq * (1.0 + pnl / 100.0);
  }
  return Number((eq - 100.0).toFixed(2));
};

const getLiveSharpe = (strat: ManagedStrategy): number | null => {
  const trades = getStrategyLiveClosedTrades(strat);
  if (trades.length < 2) return null;
  const returns = trades.map((t: any) => Number(t.pnl_pct || 0) / 100);
  const mean = returns.reduce((a, b) => a + b, 0) / returns.length;
  const variance = returns.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / (returns.length - 1);
  const std = Math.sqrt(variance);
  if (std === 0) return null;
  return Number(((mean / std) * Math.sqrt(252)).toFixed(2));
};

const getLiveWinRate = (strat: ManagedStrategy): number | null => {
  const trades = getStrategyLiveClosedTrades(strat);
  if (trades.length === 0) return null;
  const wins = trades.filter((t: any) => Number(t.pnl_pct || 0) > 0).length;
  return Number(((wins / trades.length) * 100).toFixed(1));
};

const getLivePf = (strat: ManagedStrategy): number | null => {
  const trades = getStrategyLiveClosedTrades(strat);
  if (trades.length === 0) return null;
  let grossWin = 0;
  let grossLoss = 0;
  for (const t of trades) {
    const pnl = Number(t.pnl_pct || 0);
    if (pnl > 0) grossWin += pnl;
    else if (pnl < 0) grossLoss += Math.abs(pnl);
  }
  if (grossLoss === 0) return grossWin > 0 ? 3.0 : 1.5;
  return Number((grossWin / grossLoss).toFixed(2));
};

const getLiveMaxDd = (strat: ManagedStrategy): number | null => {
  const trades = getStrategyLiveClosedTrades(strat);
  if (trades.length === 0) return null;
  let eq = 100.0;
  let peak = 100.0;
  let maxDd = 0.0;
  for (const t of trades) {
    const pnl = Number(t.pnl_pct || 0);
    eq = eq * (1.0 + pnl / 100.0);
    peak = Math.max(peak, eq);
    const dd = peak > 0 ? ((peak - eq) / peak) * 100 : 0.0;
    maxDd = Math.max(maxDd, dd);
  }
  return Number(maxDd.toFixed(2));
};

// ── Baseline Computations ─────────────────────────────────
const getBaselineSharpe = (strat: ManagedStrategy): number => {
  const hist = strat.cron_config?.drift_history || [];
  if (hist.length > 0 && hist[0].sharpe != null) {
    return Number(hist[0].sharpe);
  }
  return strat.latest_backtest?.sharpe || 0;
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

const getBaselinePf = (strat: ManagedStrategy): number => {
  const hist = strat.cron_config?.drift_history || [];
  if (hist.length > 0 && hist[0].profit_factor != null) {
    return Number(hist[0].profit_factor);
  }
  return Number(strat.latest_backtest?.profit_factor || 1.0);
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

// ── Effective (Live vs Backtest) Values ─────────────────────
const getEffectiveSharpe = (strat: ManagedStrategy): number => {
  if (props.screenMode === 'LIVE') {
    const live = getLiveSharpe(strat);
    if (live != null) return live;
    return getBaselineSharpe(strat);
  }
  const hist = strat.cron_config?.drift_history || [];
  if (hist.length > 0 && hist[hist.length - 1].sharpe != null) {
    return Number(hist[hist.length - 1].sharpe);
  }
  return strat.latest_backtest?.sharpe || 0;
};

const formatSharpeValue = (strat: ManagedStrategy): string => {
  if (props.screenMode === 'LIVE') {
    const live = getLiveSharpe(strat);
    if (live != null) return live.toFixed(2);
    return '⏳ Pending';
  }
  return getEffectiveSharpe(strat).toFixed(2);
};

const getDeltaSharpe = (strat: ManagedStrategy): number => {
  return Number((getEffectiveSharpe(strat) - getBaselineSharpe(strat)).toFixed(2));
};

const formatSharpeDelta = (strat: ManagedStrategy): string => {
  if (props.screenMode === 'LIVE' && getLiveSharpe(strat) == null) {
    return '–';
  }
  const delta = getDeltaSharpe(strat);
  return `${delta > 0 ? '+' : ''}${delta.toFixed(2)}`;
};

const getEffectiveWinRate = (strat: ManagedStrategy): number => {
  if (props.screenMode === 'LIVE') {
    const live = getLiveWinRate(strat);
    if (live != null) return live;
    return getBaselineWinRate(strat);
  }
  const hist = strat.cron_config?.drift_history || [];
  if (hist.length > 0 && hist[hist.length - 1].win_rate != null) {
    const raw = Number(hist[hist.length - 1].win_rate);
    return raw <= 1.0 ? raw * 100 : raw;
  }
  const raw = strat.latest_backtest?.win_rate || 0;
  return raw <= 1.0 ? raw * 100 : raw;
};

const formatWinRateValue = (strat: ManagedStrategy): string => {
  if (props.screenMode === 'LIVE') {
    const live = getLiveWinRate(strat);
    if (live != null) return `${live.toFixed(1)}%`;
    return '⏳ Pending';
  }
  return `${getEffectiveWinRate(strat).toFixed(1)}%`;
};

const getDeltaWinRate = (strat: ManagedStrategy): number => {
  return Number((getEffectiveWinRate(strat) - getBaselineWinRate(strat)).toFixed(1));
};

const formatWinRateDelta = (strat: ManagedStrategy): string => {
  if (props.screenMode === 'LIVE' && getLiveWinRate(strat) == null) {
    return '–';
  }
  const delta = getDeltaWinRate(strat);
  return `${delta > 0 ? '+' : ''}${delta.toFixed(1)}%`;
};

const getEffectivePf = (strat: ManagedStrategy): number => {
  if (props.screenMode === 'LIVE') {
    const live = getLivePf(strat);
    if (live != null) return live;
    return getBaselinePf(strat);
  }
  const hist = strat.cron_config?.drift_history || [];
  if (hist.length > 0 && hist[hist.length - 1].profit_factor != null) {
    return Number(hist[hist.length - 1].profit_factor);
  }
  return Number(strat.latest_backtest?.profit_factor || 1.0);
};

const formatPfValue = (strat: ManagedStrategy): string => {
  if (props.screenMode === 'LIVE') {
    const live = getLivePf(strat);
    if (live != null) return live.toFixed(2);
    return '⏳ Pending';
  }
  return getEffectivePf(strat).toFixed(2);
};

const getDeltaPf = (strat: ManagedStrategy): number => {
  return Number((getEffectivePf(strat) - getBaselinePf(strat)).toFixed(2));
};

const formatPfDelta = (strat: ManagedStrategy): string => {
  if (props.screenMode === 'LIVE' && getLivePf(strat) == null) {
    return '–';
  }
  const delta = getDeltaPf(strat);
  return `${delta > 0 ? '+' : ''}${delta.toFixed(2)}`;
};

const getEffectiveMdd = (strat: ManagedStrategy): number => {
  if (props.screenMode === 'LIVE') {
    const live = getLiveMaxDd(strat);
    if (live != null) return live;
    return getBaselineMdd(strat);
  }
  const hist = strat.cron_config?.drift_history || [];
  if (hist.length > 0 && hist[hist.length - 1].max_drawdown != null) {
    const raw = Number(hist[hist.length - 1].max_drawdown);
    return raw <= 1.0 ? raw * 100 : raw;
  }
  const raw = strat.latest_backtest?.max_drawdown || 0;
  return raw <= 1.0 ? raw * 100 : raw;
};

const formatMddValue = (strat: ManagedStrategy): string => {
  if (props.screenMode === 'LIVE') {
    const live = getLiveMaxDd(strat);
    if (live != null) return `${live.toFixed(2)}%`;
    return '0.00%';
  }
  return `${getEffectiveMdd(strat).toFixed(2)}%`;
};

const getDeltaMdd = (strat: ManagedStrategy): number => {
  return Number((getEffectiveMdd(strat) - getBaselineMdd(strat)).toFixed(2));
};

const formatMddDelta = (strat: ManagedStrategy): string => {
  if (props.screenMode === 'LIVE' && getLiveMaxDd(strat) == null) {
    return '–';
  }
  const delta = getDeltaMdd(strat);
  return `${delta > 0 ? '+' : ''}${delta.toFixed(2)}%`;
};

// ── Sparkline Series Selection (Live vs Backtest) ──────────
const getSparklineSeries = (strat: ManagedStrategy): number[] => {
  if (props.screenMode === 'LIVE') {
    const trades = getStrategyLiveClosedTrades(strat);
    if (trades.length > 0) {
      let eq = 100.0;
      const series = [100.0];
      for (const t of trades) {
        const pnl = Number(t.pnl_pct || 0);
        eq = eq * (1.0 + pnl / 100.0);
        series.push(Number(eq.toFixed(2)));
      }
      return series;
    }
    const cur = strat.latest_backtest?.sharpe || 2.0;
    return [cur, cur];
  }

  // Backtest snapshot series
  const hist = strat.cron_config?.drift_history || [];
  if (hist.length > 0) {
    const series = hist.map((h: any) => Number(h.sharpe || 0));
    if (series.length === 1) return [series[0], series[0]];
    return series;
  }
  const cur = strat.latest_backtest?.sharpe || 0;
  return [cur, cur];
};

// ── Trajectory Indicators ─────────────────────────────────
const getTrajectoryIcon = (strat: ManagedStrategy) => {
  if (props.screenMode === 'LIVE') {
    const pnl = getStrategyLivePnl(strat);
    if (pnl > 0) return TrendingUp;
    if (pnl < 0) return TrendingDown;
    return Activity;
  }
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
  if (props.screenMode === 'LIVE') {
    const pnl = getStrategyLivePnl(strat);
    if (pnl > 0.05) return 'text-success font-bold';
    if (pnl < -0.05) return 'text-error font-bold';
    return 'text-base-content/50';
  }
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
  if (props.screenMode === 'LIVE') {
    const trades = getStrategyLiveClosedTrades(strat);
    if (trades.length === 0) return 'PENDING';
    const pnl = getStrategyLivePnl(strat);
    if (pnl > 0.05) return `+${pnl}% GAIN`;
    if (pnl < -0.05) return `${pnl}% DD`;
    return 'STABLE';
  }
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

// ── Filtered & Sorted Strategies List ─────────────────────
const displayedStrategies = computed(() => {
  let list = [...props.strategies];
  if (statusFilter.value !== 'ALL') {
    list = list.filter((s) => s.status === statusFilter.value);
  }
  if (tierFilter.value !== 'ALL') {
    list = list.filter((s) => (s.tier || '').includes(tierFilter.value));
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

  list.sort((a, b) => {
    let diff = 0;
    if (sortBy.value === 'RANK') {
      diff = (b.ranking_score || 0) - (a.ranking_score || 0);
      if (diff === 0) diff = (a.rank || 99) - (b.rank || 99);
    } else if (sortBy.value === 'SHARPE') {
      diff = getEffectiveSharpe(b) - getEffectiveSharpe(a);
    } else if (sortBy.value === 'WIN_RATE') {
      diff = getEffectiveWinRate(b) - getEffectiveWinRate(a);
    } else if (sortBy.value === 'PROFIT_FACTOR') {
      diff = getEffectivePf(b) - getEffectivePf(a);
    } else if (sortBy.value === 'MAX_DD') {
      diff = getEffectiveMdd(a) - getEffectiveMdd(b);
    } else if (sortBy.value === 'DRIFT') {
      diff = getDeltaSharpe(b) - getDeltaSharpe(a);
    }
    return sortOrder.value === 'DESC' ? diff : -diff;
  });

  return list;
});
</script>

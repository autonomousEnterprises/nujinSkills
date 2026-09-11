<template>
  <div class="w-full h-full overflow-y-auto font-mono select-none bg-base-100 text-base-content transition-colors">
    <div class="w-full px-3 md:px-6 py-4 space-y-4">

      <!-- ── TOP HEADER & LIVE TELEMETRY BAR ── -->
      <div class="card bg-base-200 border border-base-content/10 shadow-sm p-4">
        <div class="flex flex-wrap items-center justify-between gap-4">
          <div class="flex items-center gap-3">
            <div class="p-2.5 rounded-box bg-primary/10 border border-primary/30 text-primary">
              <Send class="w-5 h-5" />
            </div>
            <div>
              <div class="flex items-center gap-2 flex-wrap">
                <span class="font-bold text-sm text-base-content">
                  SIGNAL DECK — MULTI-STRATEGY TELEMETRY GATEWAY
                </span>
                <span class="badge badge-sm badge-secondary font-bold">
                  {{ activeBots.length }} ACTIVE IN BOT
                </span>
                <span 
                  class="badge badge-sm font-bold border"
                  :class="isRunning ? 'badge-success badge-outline bg-success/10 text-success' : 'badge-neutral bg-base-300 text-base-content/60'"
                >
                  {{ isRunning ? `🟢 BOT: RUNNING (${activeBots.length} Active)` : '🔴 BOT: STOPPED / IDLE' }}
                </span>
                <span 
                  class="badge badge-sm font-bold border"
                  :class="systemStatus?.telegram?.configured ? 'badge-info badge-outline bg-info/10 text-info' : 'badge-neutral bg-base-300 text-base-content/50'"
                >
                  {{ systemStatus?.telegram?.configured ? '💬 TELEGRAM: CONNECTED' : '⚪ TELEGRAM: LOG ONLY' }}
                </span>
              </div>
              <div class="text-[11px] text-base-content/60 mt-0.5">
                Real-time position tracking, live R/R bounds, multi-asset spot tickers &amp; automated alert dispatch
              </div>
            </div>
          </div>

          <!-- Bot Controls (Start/Stop), Refresh & Clear -->
          <div class="flex items-center gap-2 flex-wrap">
            <button
              @click="handleDeployBot()"
              :disabled="actionLoading || isRunning"
              class="btn btn-xs sm:btn-sm btn-success gap-1 shadow font-bold"
            >
              <Play class="w-3.5 h-3.5 fill-current" />
              <span>{{ isRunning ? 'Bot Running' : 'Start Bot' }}</span>
            </button>

            <button
              @click="handleStopBot()"
              :disabled="actionLoading || !isRunning"
              class="btn btn-xs sm:btn-sm btn-error gap-1 shadow font-bold"
            >
              <Square class="w-3 h-3 fill-current" />
              <span>Stop Bot</span>
            </button>

            <div class="divider divider-horizontal mx-1 my-1 hidden sm:flex" />

            <button
              @click="fetchSignals"
              :disabled="loading"
              class="btn btn-xs sm:btn-sm btn-ghost border border-base-content/10 gap-1"
            >
              <RefreshCw class="w-3.5 h-3.5" :class="loading ? 'animate-spin' : ''" />
              <span class="hidden sm:inline">Refresh</span>
            </button>

            <button
              @click="handleClearSignals"
              :disabled="actionLoading"
              class="btn btn-xs sm:btn-sm btn-ghost border border-base-content/10 text-error hover:bg-error/10 gap-1"
              title="Clear signals under current scope"
            >
              <Trash2 class="w-3.5 h-3.5" />
              <span class="hidden sm:inline">Clear</span>
            </button>
          </div>
        </div>
      </div>

      <!-- ── STRATEGY SCOPE FILTER TABS ── -->
      <div class="card bg-base-200 border border-base-content/10 p-3 flex flex-wrap items-center justify-between gap-3">
        <div class="flex items-center gap-2 flex-wrap">
          <span class="text-[11px] font-bold text-base-content/50 uppercase flex items-center gap-1 mr-1">
            <Filter class="w-3.5 h-3.5" /> Scope:
          </span>

          <button
            @click="selectedStratTab = 'ALL'"
            class="btn btn-xs font-mono font-bold gap-1.5"
            :class="selectedStratTab === 'ALL' ? 'btn-secondary text-secondary-content shadow' : 'btn-ghost text-base-content/70 border border-base-content/10'"
          >
            <Layers class="w-3.5 h-3.5" />
            <span>ALL ACTIVE STRATEGIES</span>
            <span class="badge badge-xs badge-neutral">{{ stratOptions.length }}</span>
          </button>

          <button
            v-for="strat in stratOptions"
            :key="strat.name"
            @click="selectedStratTab = strat.name"
            class="btn btn-xs font-mono font-bold gap-1.5"
            :class="selectedStratTab === strat.name ? 'btn-primary text-primary-content shadow' : 'btn-ghost text-base-content/70 border border-base-content/10'"
          >
            <span class="w-2 h-2 rounded-full" :class="strat.isActive ? 'bg-success animate-pulse' : 'bg-base-content/30'" />
            <span>{{ strat.name }}</span>
            <span class="badge badge-xs" :class="strat.symbol.includes('XAU') ? 'badge-warning' : 'badge-info'">
              {{ strat.symbol }}
            </span>
          </button>
        </div>

        <!-- Scope-specific quick action -->
        <div v-if="selectedStratTab !== 'ALL'" class="flex items-center gap-2">
          <button
            v-if="activeBots.includes(selectedStratTab)"
            @click="handleStopBot(selectedStratTab)"
            :disabled="actionLoading"
            class="btn btn-xs btn-outline btn-error gap-1 font-bold"
          >
            <XCircle class="w-3 h-3" /> Stop {{ selectedStratTab }}
          </button>
          <button
            v-else
            @click="handleDeployBot(selectedStratTab)"
            :disabled="actionLoading"
            class="btn btn-xs btn-outline btn-success gap-1 font-bold"
          >
            <Play class="w-3 h-3 fill-current" /> Deploy {{ selectedStratTab }}
          </button>
        </div>
      </div>

      <!-- ── LIVE PERFORMANCE STATS (DAISYUI STATS) ── -->
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
            <span class="text-sm font-bold text-info mt-0.5">{{ openPositions.length }} In Flight</span>
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

      <!-- ── ACTIVE OPEN POSITIONS (MULTI-BOT PARALLEL) ── -->
      <div class="card bg-base-200 border border-base-content/10 p-5 space-y-4">
        <div class="flex flex-wrap items-center justify-between border-b border-base-content/10 pb-3 gap-3">
          <div class="flex items-center gap-3">
            <span class="font-bold text-sm flex items-center gap-2 text-success">
              <Zap class="w-4 h-4 fill-current" />
              CURRENT ACTIVE OPEN POSITIONS ({{ openPositions.length }} IN FLIGHT)
            </span>
            <span 
              class="badge badge-sm font-bold gap-1.5"
              :class="openPositions.length > 0 ? 'badge-success badge-outline bg-success/10 text-success' : 'badge-neutral bg-base-300 text-base-content/50'"
            >
              <span v-if="openPositions.length > 0" class="w-2 h-2 rounded-full bg-success animate-ping" />
              {{ openPositions.length > 0 ? `${openPositions.length} ACTIVE RUNNING` : 'NO OPEN POSITIONS' }}
            </span>
          </div>

          <!-- Spot Market Feeds -->
          <div class="flex items-center gap-2">
            <div class="px-2.5 py-1 rounded-box bg-base-300 border border-base-content/10 text-right">
              <div class="text-[9px] text-warning font-bold uppercase">🟡 OANDA SPOT XAU</div>
              <div class="text-xs font-bold font-mono text-warning">
                {{ liveGoldPrice ? `$${liveGoldPrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '—' }}
              </div>
            </div>
            <div class="px-2.5 py-1 rounded-box bg-base-300 border border-base-content/10 text-right">
              <div class="text-[9px] text-info font-bold uppercase">🔵 BINANCE BTC/USDT</div>
              <div class="text-xs font-bold font-mono text-info">
                {{ liveBtcPrice ? `$${liveBtcPrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '—' }}
              </div>
            </div>
          </div>
        </div>

        <!-- Position Cards Grid -->
        <div v-if="openPositions.length > 0" class="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div 
            v-for="pos in openPositions" 
            :key="pos.id"
            class="card bg-base-300/60 border border-base-content/10 p-4 space-y-3 hover:border-primary/50 transition-all"
          >
            <!-- Card Header -->
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <span class="badge badge-sm font-bold" :class="(pos.pair || '').includes('XAU') ? 'badge-warning' : 'badge-info'">
                  {{ pos.pair || ((pos.pair || '').includes('XAU') ? 'XAU/USD' : 'BTC/USDT') }}
                </span>
                <span class="text-xs font-bold text-secondary font-mono">{{ pos.strategy || cleanSelectedName }}</span>
              </div>
              <span class="badge badge-sm font-bold" :class="isShort(pos) ? 'badge-error' : 'badge-success'">
                {{ isShort(pos) ? '⬇ SHORT ENTRY' : '⬆ LONG ENTRY' }}
              </span>
            </div>

            <!-- Pricing Grid -->
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 bg-base-100/60 p-2.5 rounded-box border border-base-content/10 text-xs">
              <div>
                <span class="text-[9px] text-base-content/50 uppercase block">Entry</span>
                <span class="font-bold text-accent font-mono">${{ pos.price?.toLocaleString() }}</span>
              </div>
              <div>
                <span class="text-[9px] text-base-content/50 uppercase block">Stop Loss</span>
                <span class="font-bold text-error font-mono">${{ pos.stop_loss?.toLocaleString() || '—' }}</span>
              </div>
              <div>
                <span class="text-[9px] text-base-content/50 uppercase block">Take Profit</span>
                <span class="font-bold text-success font-mono">${{ pos.take_profit?.toLocaleString() || '—' }}</span>
              </div>
              <div>
                <span class="text-[9px] text-base-content/50 uppercase block">Live Spot</span>
                <span class="font-bold font-mono" :class="(pos.pair || '').includes('XAU') ? 'text-warning' : 'text-info'">
                  ${{ getLiveSpot(pos) ? getLiveSpot(pos)?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '—' }}
                </span>
              </div>
            </div>

            <!-- Floating PnL & Close Button -->
            <div 
              class="flex items-center justify-between p-3 rounded-box border transition-colors"
              :class="calculateFloatingPnl(pos) >= 0 ? 'bg-success/10 border-success/30' : 'bg-error/10 border-error/30'"
            >
              <div>
                <span class="text-[10px] text-base-content/60 uppercase font-bold block">Unrealized Floating PnL</span>
                <span class="text-2xl font-bold font-mono" :class="calculateFloatingPnl(pos) >= 0 ? 'text-success' : 'text-error'">
                  {{ calculateFloatingPnl(pos) >= 0 ? '+' : '' }}{{ calculateFloatingPnl(pos).toFixed(2) }}%
                </span>
              </div>
              <button
                @click="handleClosePosition(pos)"
                :disabled="actionLoading"
                class="btn btn-sm btn-error shadow font-bold text-xs"
              >
                Close Position
              </button>
            </div>

            <!-- AI Reasoning Box -->
            <div class="text-xs text-base-content/80 bg-base-100/80 p-2.5 rounded-box border border-base-content/10">
              <div class="text-[10px] font-bold text-secondary mb-1 flex items-center gap-1">
                <MessageSquare class="w-3 h-3" /> QUANT THESIS &amp; TRIGGER:
              </div>
              <p class="leading-relaxed text-[11px] opacity-90">
                {{ pos.reasoning_md || pos.annotation || 'Quantitative edge setup detected with statistical confirmation.' }}
              </p>
            </div>
          </div>
        </div>

        <!-- Empty state -->
        <div v-else class="py-8 text-center text-xs text-base-content/50 space-y-2">
          <Activity class="w-8 h-8 mx-auto text-base-content/30 animate-pulse" />
          <div class="font-bold text-base-content/80">No open positions matching current filter scope.</div>
          <div class="text-[11px]">
            {{ isRunning ? 'Bot supervisor is actively running and streaming real-time regime telemetry.' : 'Bot supervisor is idle. Click "Start Bot" to activate.' }}
          </div>
        </div>
      </div>

      <!-- ── SIGNAL TELEMETRY & AUDIT FEED TABLE ── -->
      <div class="card bg-base-200 border border-base-content/10 p-5 space-y-4">
        <div class="flex items-center justify-between border-b border-base-content/10 pb-3">
          <span class="font-bold text-sm flex items-center gap-2 text-secondary">
            <Clock class="w-4 h-4" />
            SIGNAL TELEMETRY &amp; AUDIT FEED
          </span>
          <span class="text-xs text-base-content/60">
            {{ allSignals.length }} Total Signals Recorded
          </span>
        </div>

        <div class="overflow-x-auto max-h-96 overflow-y-auto border border-base-content/10 rounded-box">
          <table class="table table-zebra table-sm w-full font-mono text-xs">
            <thead class="sticky top-0 bg-base-300 z-10">
              <tr>
                <th>#</th>
                <th>Time</th>
                <th>Strategy</th>
                <th>Pair</th>
                <th>Action</th>
                <th>Entry</th>
                <th>SL</th>
                <th>TP</th>
                <th>Exit Reason</th>
                <th>Net PnL</th>
                <th>Status</th>
                <th class="text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="allSignals.length === 0">
                <td colspan="12" class="p-6 text-center text-base-content/50">
                  No signals recorded yet under selected filter scope.
                </td>
              </tr>
              <tr v-for="(sig, idx) in allSignals" :key="sig.id || idx" class="hover">
                <td class="font-bold opacity-70">#{{ sig.id || idx + 1 }}</td>
                <td class="opacity-70 whitespace-nowrap">
                  {{ formatDate(sig.time) }}
                </td>
                <td class="font-bold text-secondary">
                  {{ (sig.strategy || cleanSelectedName).replace('Strategy', '') }}
                </td>
                <td>
                  <span class="badge badge-xs font-bold" :class="(sig.pair || '').includes('XAU') ? 'badge-warning' : 'badge-info'">
                    {{ sig.pair || ((sig.pair || '').includes('XAU') ? 'XAU/USD' : 'BTC/USDT') }}
                  </span>
                </td>
                <td>
                  <span class="badge badge-xs font-bold" :class="isLongAction(sig) ? 'badge-success' : 'badge-error'">
                    {{ isLongAction(sig) ? '⬆ LONG' : '⬇ SHORT' }}
                  </span>
                </td>
                <td class="font-bold text-accent">${{ sig.price ? sig.price.toLocaleString() : '—' }}</td>
                <td class="text-error">${{ sig.stop_loss ? sig.stop_loss.toLocaleString() : '—' }}</td>
                <td class="text-success">${{ sig.take_profit ? sig.take_profit.toLocaleString() : '—' }}</td>
                <td>
                  <span 
                    class="badge badge-xs font-bold"
                    :class="sig.exit_reason === 'TAKE_PROFIT' ? 'badge-success' : sig.exit_reason === 'STOP_LOSS' ? 'badge-error' : 'badge-neutral'"
                  >
                    {{ sig.exit_reason || (sig.status === 'ACTIVE_IN_POSITION' ? 'IN PROGRESS' : 'CLOSED') }}
                  </span>
                </td>
                <td class="font-bold">
                  <span v-if="sig.status === 'ACTIVE_IN_POSITION'" class="text-info">LIVE</span>
                  <span v-else :class="(sig.pnl_pct || 0) >= 0 ? 'text-success' : 'text-error'">
                    {{ (sig.pnl_pct || 0) > 0 ? '+' : '' }}{{ (sig.pnl_pct || 0).toFixed(2) }}%
                  </span>
                </td>
                <td>
                  <span 
                    class="badge badge-xs font-bold"
                    :class="sig.status === 'ACTIVE_IN_POSITION' ? 'badge-success badge-outline animate-pulse' : 'badge-neutral'"
                  >
                    {{ sig.status || 'CLOSED' }}
                  </span>
                </td>
                <td class="text-right">
                  <button
                    v-if="sig.status === 'ACTIVE_IN_POSITION'"
                    @click="handleClosePosition(sig)"
                    :disabled="actionLoading"
                    class="btn btn-xs btn-error btn-outline font-bold"
                  >
                    Close
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import {
  Send, Zap, Cpu, CheckCircle2, ShieldCheck,
  Clock, Target, AlertTriangle, RefreshCw, Activity, MessageSquare,
  TrendingUp, BarChart3, Award, Percent, DollarSign, XCircle, Trash2,
  Filter, Layers, Play, Square
} from 'lucide-vue-next';
import type { SignalData, WidgetData, ManagedStrategy, PortfolioSummary } from '../composables/useWebSocket';

const props = withDefaults(
  defineProps<{
    signals?: SignalData[];
    widgets?: WidgetData[];
    theme?: 'dark' | 'light';
    selectedStrategy?: string;
    selectedBacktestData?: any;
    activeState?: any;
    managedStrategies?: ManagedStrategy[];
    portfolioSummary?: PortfolioSummary | null;
  }>(),
  {
    signals: () => [],
    theme: 'dark',
    selectedStrategy: 'GoatFundedTraderXauusdScalper.py',
    managedStrategies: () => [],
  }
);

const selectedStratTab = ref('ALL');
const loading = ref(false);
const actionLoading = ref(false);

const liveGoldPrice = ref<number | null>(null);
const liveBtcPrice = ref<number | null>(null);

const signalState = ref<{
  signals: any[];
  active_signal: any;
  active_signals: any[];
}>({
  signals: [],
  active_signal: null,
  active_signals: [],
});

const liveStats = ref<any>(null);
const systemStatus = ref<any>(null);

let pollTimer: any = null;
let goldTimer: any = null;
let btcWs: WebSocket | null = null;

const cleanSelectedName = computed(() => (props.activeState?.active_strategy || props.selectedStrategy || 'GoatFundedTraderXauusdScalper').replace('.py', ''));

const isRunning = computed(() => Boolean(systemStatus.value?.bot?.is_running));
const activeBots = computed<string[]>(() => {
  if (isRunning.value) {
    return systemStatus.value?.bot?.active_strategies || props.activeState?.active_strategies || [];
  }
  return [];
});

const stratOptions = computed(() => {
  const list: Array<{ name: string; display: string; symbol: string; isActive: boolean }> = [];
  if (props.managedStrategies && props.managedStrategies.length > 0) {
    props.managedStrategies.forEach((s) => {
      list.push({
        name: s.name,
        display: s.display_name || s.name,
        symbol: s.symbol || 'ASSET',
        isActive: s.status === 'ACTIVE_LIVE' || activeBots.value.includes(s.name),
      });
    });
  } else {
    list.push({ name: 'GoatFundedTraderXauusdScalper', display: 'GoatFundedTrader XAU/USD', symbol: 'XAU/USD', isActive: true });
    list.push({ name: 'PropFirmVsaWickRejection', display: 'PropFirm VSA Wick Rejection', symbol: 'BTC/USDT', isActive: true });
  }
  return list;
});

const allSignals = computed(() => {
  const raw = [...(props.signals || []), ...(signalState.value.signals || [])];
  const seen = new Set<string>();
  const deduped: any[] = [];
  for (const s of raw) {
    const key = `${s.id || s.time}-${s.action || (s as any).side}-${s.price}`;
    if (!seen.has(key)) {
      seen.add(key);
      if (
        selectedStratTab.value === 'ALL' ||
        (s.strategy && s.strategy.replace('.py', '').toLowerCase() === selectedStratTab.value.replace('.py', '').toLowerCase())
      ) {
        deduped.push(s);
      }
    }
  }
  return deduped;
});

const openPositions = computed(() => {
  const actives = signalState.value.active_signals && signalState.value.active_signals.length > 0
    ? signalState.value.active_signals
    : (signalState.value.active_signal ? [signalState.value.active_signal] : []);

  if (selectedStratTab.value === 'ALL') {
    return actives.filter((s: any) => s.status === 'ACTIVE_IN_POSITION');
  }
  return actives.filter((s: any) =>
    s.status === 'ACTIVE_IN_POSITION' &&
    s.strategy && s.strategy.replace('.py', '').toLowerCase() === selectedStratTab.value.replace('.py', '').toLowerCase()
  );
});

const profitRatioPct = computed(() => {
  if (!liveStats.value) return 50;
  const tot = (liveStats.value.gross_profit_pct || 0) + (liveStats.value.gross_loss_pct || 0);
  return tot > 0 ? ((liveStats.value.gross_profit_pct || 0) / tot) * 100 : 50;
});

const isShort = (pos: any) => (pos.side || pos.action) === 'SHORT' || pos.action === 'SELL';
const isLongAction = (sig: any) => (sig.side || sig.action) === 'LONG' || sig.action === 'BUY';

const getLiveSpot = (pos: any) => {
  const isGold = (pos.pair || '').toUpperCase().includes('XAU');
  return isGold ? liveGoldPrice.value : liveBtcPrice.value;
};

const calculateFloatingPnl = (sig: any) => {
  if (!sig || !sig.price) return sig?.pnl_pct ?? 0;
  const isGold = (sig.pair || '').toUpperCase().includes('XAU');
  const livePrice = isGold ? liveGoldPrice.value : liveBtcPrice.value;
  if (!livePrice) return sig?.pnl_pct ?? 0;
  const isLong = (sig.side || sig.action) === 'BUY' || (sig.side || sig.action) === 'LONG';
  const diff = isLong ? livePrice - sig.price : sig.price - livePrice;
  return Math.round(((diff / sig.price) * 100 + Number.EPSILON) * 100) / 100;
};

const formatDate = (time: number) => {
  const t = time > 2000000000 ? time : time * 1000;
  const d = new Date(t || Date.now());
  return `${d.toLocaleDateString([], { month: '2-digit', day: '2-digit' })} ${d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
};

const fetchSignals = async () => {
  try {
    loading.value = true;
    const stratQuery = selectedStratTab.value !== 'ALL' ? `?strategy=${encodeURIComponent(selectedStratTab.value)}` : '';
    const [sigRes, statsRes, sysRes] = await Promise.all([
      fetch(`/api/signals${stratQuery}`),
      fetch(`/api/signals/stats${stratQuery}`),
      fetch('/api/system/status'),
    ]);
    const sigData = await sigRes.json();
    const statsData = await statsRes.json();
    const sysData = await sysRes.json();

    signalState.value = {
      signals: sigData.signals || [],
      active_signal: sigData.active_signal || null,
      active_signals: sigData.active_signals || (sigData.active_signal ? [sigData.active_signal] : []),
    };
    liveStats.value = statsData;
    systemStatus.value = sysData;
  } catch (e) {
    console.error('[SignalDeck] Fetch error:', e);
  } finally {
    loading.value = false;
  }
};

const handleDeployBot = async (strat?: string) => {
  try {
    actionLoading.value = true;
    const target = strat || (selectedStratTab.value !== 'ALL' ? selectedStratTab.value : cleanSelectedName.value);
    await fetch('/api/bot/deploy', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ strategy: target, mode: 'dry-run' }),
    });
    await fetchSignals();
  } catch (e) {
    console.error('[SignalDeck] Deploy failed:', e);
  } finally {
    actionLoading.value = false;
  }
};

const handleStopBot = async (strat?: string) => {
  try {
    actionLoading.value = true;
    const target = strat || (selectedStratTab.value !== 'ALL' ? selectedStratTab.value : undefined);
    await fetch('/api/bot/stop', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(target ? { strategy: target } : {}),
    });
    await fetchSignals();
  } catch (e) {
    console.error('[SignalDeck] Stop failed:', e);
  } finally {
    actionLoading.value = false;
  }
};

const handleClosePosition = async (sig: any) => {
  try {
    actionLoading.value = true;
    const isGold = (sig.pair || '').toUpperCase().includes('XAU');
    const currentPrice = isGold ? (liveGoldPrice.value || sig.price) : (liveBtcPrice.value || sig.price);
    await fetch('/api/signals/close', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        id: sig.id,
        strategy: sig.strategy,
        exit_price: currentPrice,
        exit_reason: 'MANUAL_CLOSE',
      }),
    });
    await fetchSignals();
  } catch (e) {
    console.error('[SignalDeck] Close position failed:', e);
  } finally {
    actionLoading.value = false;
  }
};

const handleClearSignals = async () => {
  const scopeMsg = selectedStratTab.value !== 'ALL' ? `for ${selectedStratTab.value}` : 'for ALL strategies';
  if (!window.confirm(`Clear signals ${scopeMsg}?`)) return;
  try {
    actionLoading.value = true;
    await fetch('/api/signals/clear', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(selectedStratTab.value !== 'ALL' ? { strategy: selectedStratTab.value } : {}),
    });
    await fetchSignals();
  } catch (e) {
    console.error('[SignalDeck] Clear signals failed:', e);
  } finally {
    actionLoading.value = false;
  }
};

watch(selectedStratTab, () => {
  fetchSignals();
});

onMounted(() => {
  fetchSignals();
  pollTimer = setInterval(fetchSignals, 15000);

  // Spot feeds
  const fetchOanda = async () => {
    try {
      const res = await fetch('/api/xauusd/quote');
      const data = await res.json();
      if (data?.quote?.price) {
        liveGoldPrice.value = parseFloat(data.quote.price);
      }
    } catch {}
  };
  fetchOanda();
  goldTimer = setInterval(fetchOanda, 2500);

  try {
    btcWs = new WebSocket('wss://stream.binance.com:9443/ws/btcusdt@kline_15m');
    btcWs.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data);
        if (msg?.k?.c) liveBtcPrice.value = parseFloat(msg.k.c);
      } catch {}
    };
  } catch {}
});

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer);
  if (goldTimer) clearInterval(goldTimer);
  if (btcWs) btcWs.close();
});
</script>

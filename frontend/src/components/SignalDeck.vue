<template>
  <div class="w-full h-full overflow-y-auto font-mono select-none bg-base-100 text-base-content transition-colors">
    <div class="w-full px-3 md:px-6 py-4 space-y-4">

      <!-- ── 1. TOP HEADER & LIVE TELEMETRY CONTROLS ── -->
      <SignalHeader
        :activeBots="activeBots"
        :isRunning="isRunning"
        :telegramConfigured="!!systemStatus?.telegram?.configured"
        :actionLoading="actionLoading"
        :loading="loading"
        @deployBot="handleDeployBot"
        @stopBot="handleStopBot"
        @fetchSignals="fetchSignals"
        @clearSignals="handleClearSignals"
      />

      <!-- ── 2. STRATEGY SCOPE FILTER TABS ── -->
      <SignalScopeFilter
        v-model:selectedStratTab="selectedStratTab"
        :stratOptions="stratOptions"
        :activeBots="activeBots"
        :actionLoading="actionLoading"
        @deployBot="handleDeployBot"
        @stopBot="handleStopBot"
      />

      <!-- ── 3. LIVE PERFORMANCE STATS (DAISYUI STATS) ── -->
      <SignalPerformanceStats
        :selectedStratTab="selectedStratTab"
        :liveStats="liveStats"
        :openPositionsCount="openPositions.length"
      />

      <!-- ── 4. REALIZED EQUITY TRAJECTORY CHART ── -->
      <SignalEquityChart
        :signals="allSignals"
        :selectedStratTab="selectedStratTab"
        :cleanSelectedName="cleanSelectedName"
        :liveStats="liveStats"
        :managedStrategies="managedStrategies"
        :selectedBacktestData="selectedBacktestData"
        :activeBots="activeBots"
      />

      <!-- ── 5. ACTIVE OPEN POSITIONS (MULTI-BOT PARALLEL) ── -->
      <SignalPositionsGrid
        :openPositions="openPositions"
        :liveGoldPrice="liveGoldPrice"
        :liveBtcPrice="liveBtcPrice"
        :liveSp500Price="liveSp500Price"
        :cleanSelectedName="cleanSelectedName"
        :actionLoading="actionLoading"
        @closePosition="handleClosePosition"
        @inspectPosition="(pos) => emit('inspectSignal', pos)"
      />

      <!-- ── 6. SIGNAL TELEMETRY & AUDIT FEED TABLE ── -->
      <SignalHistoryTable
        :allSignals="allSignals"
        :cleanSelectedName="cleanSelectedName"
        :actionLoading="actionLoading"
        @closePosition="handleClosePosition"
        @inspectPosition="(sig) => emit('inspectSignal', sig)"
      />

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import SignalHeader from './signal/SignalHeader.vue';
import SignalScopeFilter from './signal/SignalScopeFilter.vue';
import SignalPerformanceStats from './signal/SignalPerformanceStats.vue';
import SignalEquityChart from './signal/SignalEquityChart.vue';
import SignalPositionsGrid from './signal/SignalPositionsGrid.vue';
import SignalHistoryTable from './signal/SignalHistoryTable.vue';
import type { SignalData, WidgetData, ManagedStrategy, PortfolioSummary } from '../types';

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
    selectedStrategy: '',
    managedStrategies: () => [],
    portfolioSummary: null,
  }
);

const emit = defineEmits<{
  (e: 'inspectSignal', signal: SignalData): void;
  (e: 'clearSignals'): void;
  (e: 'closePosition', signal: SignalData): void;
  (e: 'refreshStrategies'): void;
}>();

const fetchedSignals = ref<SignalData[]>([]);
const loading = ref(false);
const actionLoading = ref(false);
const systemStatus = ref<any>(null);
const liveGoldPrice = ref<number | null>(null);
const liveBtcPrice = ref<number | null>(null);
const liveSp500Price = ref<number | null>(null);
const selectedStratTab = ref<string>('ALL');

let pollTimer: any = null;
let btcWs: WebSocket | null = null;
let priceTimer: any = null;
let spPriceTimer: any = null;

const cleanSelectedName = computed(() => (props.selectedStrategy || props.portfolioSummary?.active_strategies?.[0] || props.managedStrategies?.[0]?.name || '').replace('.py', ''));

const activeBots = computed(() => {
  const fromManaged = (props.managedStrategies || [])
    .filter((s) => s.status === 'ACTIVE_LIVE')
    .map((s) => s.name.replace('.py', ''));
  if (fromManaged.length > 0) return fromManaged;

  if (props.portfolioSummary?.active_strategies && props.portfolioSummary.active_strategies.length > 0) {
    return props.portfolioSummary.active_strategies.map((s: string) => s.replace('.py', ''));
  }
  if (props.activeState?.active_strategies && props.activeState.active_strategies.length > 0) {
    return props.activeState.active_strategies.map((s: string) => s.replace('.py', ''));
  }
  if (props.activeState?.active_strategy && props.activeState?.status === 'ACTIVE_DEPLOYED') {
    return [props.activeState.active_strategy.replace('.py', '')];
  }
  return [];
});

const isRunning = computed(() => {
  if (activeBots.value.length > 0) return true;
  return Boolean(
    systemStatus.value?.bot_status?.is_running ||
    systemStatus.value?.status === 'ACTIVE_DEPLOYED' ||
    systemStatus.value?.status === 'RUNNING'
  );
});

const stratOptions = computed(() => {
  const set = new Map<string, { name: string; symbol: string; isActive: boolean }>();
  if (props.managedStrategies && props.managedStrategies.length > 0) {
    props.managedStrategies.forEach((s) => {
      const clean = s.name.replace('.py', '');
      set.set(clean, {
        name: clean,
        symbol: s.symbol || (s.name.toLowerCase().includes('xau') ? 'XAU/USD' : 'BTC/USDT'),
        isActive: s.status === 'ACTIVE_LIVE',
      });
    });
  }
  allSignals.value.forEach((sig) => {
    if (sig.strategy) {
      const clean = sig.strategy.replace('.py', '').replace('Strategy', '');
      if (!set.has(clean)) {
        set.set(clean, {
          name: clean,
          symbol: sig.pair || (clean.toLowerCase().includes('xau') ? 'XAU/USD' : 'BTC/USDT'),
          isActive: activeBots.value.includes(clean),
        });
      }
    }
  });
  return Array.from(set.values());
});

const allSignals = computed<SignalData[]>(() => {
  const map = new Map<number | string, SignalData>();
  (props.signals || []).forEach((s, idx) => map.set(s.id || `ws-${s.time}-${idx}`, s));
  fetchedSignals.value.forEach((s, idx) => map.set(s.id || `api-${s.time}-${idx}`, s));

  let list = Array.from(map.values()).sort((a, b) => (b.time || 0) - (a.time || 0));
  if (selectedStratTab.value !== 'ALL') {
    const target = selectedStratTab.value.toLowerCase();
    list = list.filter((s) => {
      const strat = (s.strategy || '').toLowerCase();
      return strat.includes(target) || target.includes(strat);
    });
  }
  return list;
});

const openPositions = computed(() => {
  return allSignals.value.filter((s) => {
    return s.status === 'ACTIVE_IN_POSITION' || s.exit_reason === 'ACTIVE_IN_POSITION';
  });
});

const liveStats = computed(() => {
  const closed = allSignals.value.filter((s) => s.status !== 'ACTIVE_IN_POSITION' && s.exit_reason !== 'ACTIVE_IN_POSITION' && s.pnl_pct !== undefined);
  if (closed.length === 0) {
    if (selectedStratTab.value !== 'ALL') {
      const matched = props.managedStrategies?.find((m) => m.name.includes(selectedStratTab.value));
      if (matched?.live_stats) return matched.live_stats;
    }
    const defaultStats = props.managedStrategies?.find((m) => m.name.includes(cleanSelectedName.value))?.live_stats;
    if (defaultStats) return defaultStats;
    return null;
  }
  let wins = 0;
  let losses = 0;
  let grossProfit = 0;
  let grossLoss = 0;
  let totalPnl = 0;
  let maxLossStreak = 0;
  let currLossStreak = 0;

  closed.forEach((s) => {
    const pnl = s.pnl_pct || 0;
    totalPnl += pnl;
    if (pnl > 0) {
      wins++;
      grossProfit += pnl;
      currLossStreak = 0;
    } else {
      losses++;
      grossLoss += Math.abs(pnl);
      currLossStreak++;
      if (currLossStreak > maxLossStreak) maxLossStreak = currLossStreak;
    }
  });

  const pf = grossLoss > 0 ? grossProfit / grossLoss : grossProfit > 0 ? 99.0 : 0;
  return {
    total_trades: closed.length,
    wins,
    losses,
    win_rate: wins / closed.length,
    profit_factor: Number(pf.toFixed(2)),
    sharpe_live: Number((pf * 0.95).toFixed(2)),
    total_pnl_pct: Number(totalPnl.toFixed(2)),
    gross_profit_pct: Number(grossProfit.toFixed(1)),
    gross_loss_pct: Number(grossLoss.toFixed(1)),
    avg_win_pct: wins > 0 ? Number((grossProfit / wins).toFixed(2)) : 0,
    avg_loss_pct: losses > 0 ? Number((grossLoss / losses).toFixed(2)) : 0,
    max_consecutive_losses: maxLossStreak,
  };
});

const fetchSignals = async () => {
  try {
    loading.value = true;
    const res = await fetch('/api/signals');
    if (res.ok) {
      const data = await res.json();
      if (Array.isArray(data)) {
        fetchedSignals.value = data;
      } else if (data && Array.isArray(data.signals)) {
        fetchedSignals.value = data.signals;
      }
    }
    const stRes = await fetch('/api/status');
    if (stRes.ok) systemStatus.value = await stRes.json();
  } catch (err) {
    console.error('Failed to fetch signals:', err);
  } finally {
    loading.value = false;
  }
};

const handleDeployBot = async (strategyName?: string) => {
  const target = strategyName || (selectedStratTab.value !== 'ALL' ? selectedStratTab.value : cleanSelectedName.value);
  try {
    actionLoading.value = true;
    await fetch('/api/bot/deploy', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ strategy: target, strategy_name: `${target}.py`, mode: 'dry-run' }),
    });
    emit('refreshStrategies');
    await fetchSignals();
  } catch (e) {
    console.error('Failed to activate bot:', e);
  } finally {
    actionLoading.value = false;
  }
};

const handleStopBot = async (strategyName?: string) => {
  const target = strategyName || (selectedStratTab.value !== 'ALL' ? selectedStratTab.value : undefined);
  try {
    actionLoading.value = true;
    await fetch('/api/bot/stop', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(target ? { strategy: target, strategy_name: `${target}.py` } : {}),
    });
    emit('refreshStrategies');
    await fetchSignals();
  } catch (e) {
    console.error('Failed to deactivate bot:', e);
  } finally {
    actionLoading.value = false;
  }
};

const handleClearSignals = async () => {
  try {
    actionLoading.value = true;
    const target = selectedStratTab.value !== 'ALL' ? selectedStratTab.value : undefined;
    await fetch('/api/signals/clear', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(target ? { strategy: target } : {}),
    });
    fetchedSignals.value = [];
    emit('clearSignals');
    await fetchSignals();
  } catch (e) {
    console.error('Failed to clear signals:', e);
  } finally {
    actionLoading.value = false;
  }
};

const handleClosePosition = async (pos: SignalData) => {
  try {
    actionLoading.value = true;
    const isGold = (pos.pair || '').includes('XAU') || (pos.strategy || '').toLowerCase().includes('goat') || (pos.strategy || '').toLowerCase().includes('xau') || (pos.strategy || '').toLowerCase().includes('otad');
    const isSp = (pos.pair || '').includes('SP') || (pos.pair || '').includes('ES') || (pos.strategy || '').toLowerCase().includes('opening') || (pos.strategy || '').toLowerCase().includes('sp500');
    const spot = isGold ? liveGoldPrice.value : (isSp ? liveSp500Price.value : liveBtcPrice.value);
    const exitPrice = spot || pos.price || 0.0;

    await fetch('/api/signals/close', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        id: pos.id,
        strategy: pos.strategy,
        exit_price: exitPrice,
        exit_reason: 'MANUAL_CLOSE',
      }),
    });
    emit('closePosition', pos);
    await fetchSignals();
  } catch (e) {
    console.error('Failed to manually close position:', e);
  } finally {
    actionLoading.value = false;
  }
};

const fetchGoldPrice = async () => {
  try {
    const res = await fetch('/api/xauusd/quote');
    if (res.ok) {
      const data = await res.json();
      const p = data.price ?? data.quote?.price ?? data.quote?.bid;
      if (p != null && !isNaN(Number(p))) liveGoldPrice.value = Number(p);
    }
  } catch {}
};

const fetchSp500Price = async () => {
  try {
    const res = await fetch('/api/sp500/quote');
    if (res.ok) {
      const data = await res.json();
      const p = data.price ?? data.quote?.price ?? data.quote?.bid;
      if (p != null && !isNaN(Number(p))) liveSp500Price.value = Number(p);
    }
  } catch {}
};

const connectBtcWs = () => {
  try {
    btcWs = new WebSocket('wss://stream.binance.com:9443/ws/btcusdt@trade');
    btcWs.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data);
        if (msg && msg.p) liveBtcPrice.value = parseFloat(msg.p);
      } catch {}
    };
  } catch {}
};

onMounted(() => {
  fetchSignals();
  fetchGoldPrice();
  fetchSp500Price();
  connectBtcWs();
  pollTimer = setInterval(fetchSignals, 4000);
  priceTimer = setInterval(fetchGoldPrice, 3000);
  spPriceTimer = setInterval(fetchSp500Price, 3000);
});

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer);
  if (priceTimer) clearInterval(priceTimer);
  if (spPriceTimer) clearInterval(spPriceTimer);
  if (btcWs) btcWs.close();
});
</script>

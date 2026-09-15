<template>
  <div 
    class="w-screen h-screen flex flex-col overflow-hidden bg-base-100 text-base-content transition-colors duration-200"
    :data-theme="theme"
  >
    <!-- Header Top Bar -->
    <Header
      :activeScreen="activeScreen"
      @update:activeScreen="activeScreen = $event"
      :isConnected="isConnected"
      :theme="theme"
      @update:theme="setTheme"
      :activeBots="activeBots"
      :activeStrategy="activeBots[0] || ''"
      :viewingStrategy="selectedStrategy"
    />

    <!-- Main Screens Viewports (v-show keeps state, chart canvas & ws connections alive) -->
    
    <!-- F1 — TradingView Live Chart Canvas -->
    <main class="w-full flex-1 relative overflow-hidden" v-show="activeScreen === 'CHART'">
      <ChartCanvas
        :latestSignal="latestSignalForSelectedStrategy"
        :signals="signalsForSelectedStrategy"
        :targetedSignal="targetedSignal"
        :theme="theme"
        :selectedStrategy="selectedStrategy"
        :tradeMarkers="currentStrategyBacktest?.trade_markers || (isLiveStrategySelected ? activeState?.trade_markers : []) || []"
        :tradesDetail="currentStrategyBacktest?.trades_detail || (isLiveStrategySelected ? activeState?.trades_detail : []) || []"
        :activeStrategy="activeBots[0] || 'GoatFundedTraderXauusdScalper'"
        :strategies="strategies"
        :isActiveScreen="activeScreen === 'CHART'"
        :latestMarketTick="latestMarketTick"
        @selectStrategy="handleSelectStrategy"
        @dismissSignal="targetedSignal = null"
      />
    </main>

    <!-- F2 — Signal Deck (Multi-Bot Telemetry & Positions) -->
    <main class="w-full flex-1 overflow-hidden" v-show="activeScreen === 'AGENT_DECK'">
      <SignalDeck
        :widgets="widgets"
        :signals="signals"
        :theme="theme"
        :selectedStrategy="selectedStrategy"
        :selectedBacktestData="currentStrategyBacktest"
        :activeState="activeState"
        :managedStrategies="managedStrategies"
        :portfolioSummary="portfolioSummary"
        @inspectSignal="handleInspectSignal"
        @clearSignals="targetedSignal = null"
        @closePosition="(pos) => { if (targetedSignal?.id === pos.id) targetedSignal = null; }"
        @refreshStrategies="pollStrategies"
      />
    </main>

    <!-- F3 — Backtest Analytics & Cynic Audit -->
    <main class="w-full flex-1 overflow-hidden" v-show="activeScreen === 'BACKTEST'">
      <BacktestDeck
        :theme="theme"
        :selectedStrategy="selectedStrategy"
        :selectedBacktestData="currentStrategyBacktest"
        :activeState="activeState"
        :strategies="strategies"
        :managedStrategies="managedStrategies"
        :loading="loadingBacktest"
        @selectStrategy="handleSelectStrategy"
        @activateStrategy="handleActivateStrategy"
        @runBacktest="handleSelectStrategy"
      />
    </main>

    <!-- F4 — Strategy Lifecycle & Portfolio Management -->
    <main class="w-full flex-1 overflow-hidden" v-show="activeScreen === 'STRATEGY_MANAGER'">
      <StrategyManagerDeck
        :theme="theme"
        :strategies="managedStrategies"
        :signals="signals"
        :activeStrategy="activeState?.active_strategy || 'GoatFundedTraderXauusdScalper'"
        :portfolioSummary="portfolioSummary"
        :distributionAnalytics="distributionAnalytics"
        @selectStrategy="handleSelectStrategy"
        @activateStrategy="handleActivateStrategy"
        @updateStatus="handleUpdateManagedStatus"
        @runBacktest="handleRunManageBacktest"
        @triggerCron="handleTriggerCron"
        @navigateToBacktest="handleNavigateToBacktest"
      />
    </main>

    <!-- Real-Time Strategy Discovery Toast Alert -->
    <transition
      enter-active-class="transform transition ease-out duration-300"
      enter-from-class="translate-y-4 opacity-0 scale-95"
      enter-to-class="translate-y-0 opacity-100 scale-100"
      leave-active-class="transition ease-in duration-200"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div v-if="activeToast" class="fixed bottom-4 right-4 z-50 max-w-sm">
        <div class="alert alert-info shadow-2xl border border-info/40 backdrop-blur-md bg-base-300/95 flex items-center justify-between gap-3 text-xs">
          <div class="flex items-center gap-2.5 overflow-hidden">
            <Sparkles class="w-5 h-5 text-info shrink-0 animate-bounce" />
            <div class="truncate">
              <div class="font-bold flex items-center gap-1.5 text-base-content">
                <span>New Strategy Discovered!</span>
                <span class="badge badge-xs badge-info font-mono">{{ activeToast.timeframe || '15m' }}</span>
              </div>
              <div class="text-[11px] font-mono text-base-content/80 truncate">
                {{ activeToast.display_name || activeToast.strategy }}
              </div>
            </div>
          </div>
          <div class="flex items-center gap-1.5 shrink-0">
            <button 
              @click="inspectDiscoveredStrategy(activeToast.file || activeToast.strategy)"
              class="btn btn-xs btn-primary font-bold font-mono shadow-sm"
            >
              Inspect (F4)
            </button>
            <button 
              @click="activeToast = null"
              class="btn btn-xs btn-ghost btn-circle text-base-content/60 hover:text-base-content"
            >
              ✕
            </button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import { Sparkles } from 'lucide-vue-next';
import Header from './components/Header.vue';
import ChartCanvas from './components/ChartCanvas.vue';
import SignalDeck from './components/SignalDeck.vue';
import BacktestDeck from './components/BacktestDeck.vue';
import StrategyManagerDeck from './components/StrategyManagerDeck.vue';
import { useWebSocket } from './composables/useWebSocket';
import type { SignalData } from './types';

type ScreenType = 'CHART' | 'AGENT_DECK' | 'BACKTEST' | 'STRATEGY_MANAGER';

const activeScreen = ref<ScreenType>('CHART');

// System & Preference Theme Resolution
const resolveSystemTheme = (): 'dark' | 'light' => {
  if (typeof window !== 'undefined' && window.matchMedia) {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  return 'dark';
};

const getInitialTheme = (): 'dark' | 'light' => {
  if (typeof window !== 'undefined') {
    const saved = localStorage.getItem('nujin_theme') as 'dark' | 'light' | null;
    if (saved === 'dark' || saved === 'light') return saved;
    return resolveSystemTheme();
  }
  return 'dark';
};

const theme = ref<'dark' | 'light'>(getInitialTheme());

const setTheme = (newTheme: 'dark' | 'light', manual: boolean = true) => {
  theme.value = newTheme;
  if (typeof document !== 'undefined') {
    document.documentElement.setAttribute('data-theme', newTheme);
  }
  if (typeof localStorage !== 'undefined' && manual) {
    localStorage.setItem('nujin_theme', newTheme);
  }
};

const selectedStrategy = ref('GoatFundedTraderXauusdScalper.py');
const selectedBacktestData = ref<any>(null);
const strategies = ref<any[]>([]);
const loadingBacktest = ref(false);
const targetedSignal = ref<SignalData | null>(null);

const {
  isConnected,
  widgets,
  latestSignal,
  signals,
  liveSystemState,
  managedStrategies,
  portfolioSummary,
  distributionAnalytics,
  latestDiscoveredStrategy,
  latestMarketTick,
} = useWebSocket();

const activeState = computed(() => liveSystemState.value);

// Derive genuinely active strategies
const activeBots = computed(() => {
  const fromManaged = managedStrategies.value
    .filter((s) => s.status === 'ACTIVE_LIVE')
    .map((s) => s.name.replace('.py', ''));
  if (fromManaged.length > 0) return fromManaged;

  if (portfolioSummary.value?.active_strategies && portfolioSummary.value.active_strategies.length > 0) {
    return portfolioSummary.value.active_strategies.map((s: string) => s.replace('.py', ''));
  }

  if (liveSystemState.value?.active_strategies && liveSystemState.value.active_strategies.length > 0) {
    return liveSystemState.value.active_strategies.map((s: string) => s.replace('.py', ''));
  }

  if (liveSystemState.value?.active_strategy && liveSystemState.value?.status === 'ACTIVE_DEPLOYED') {
    return [liveSystemState.value.active_strategy.replace('.py', '')];
  }

  return [];
});

const fetchStrategies = async () => {
  try {
    const res = await fetch('/api/strategies');
    const data = await res.json();
    strategies.value = data.strategies || [];
  } catch (e) {
    console.error('[App] Error fetching strategies:', e);
  }
};

const currentStrategyBacktest = computed(() => {
  if (selectedBacktestData.value) {
    const currClean = selectedStrategy.value.replace('.py', '').toLowerCase();
    const backtestStrat = (selectedBacktestData.value.strategy || '').replace('.py', '').toLowerCase();
    if (backtestStrat && currClean && backtestStrat === currClean) {
      return selectedBacktestData.value;
    }
  }
  const currClean = selectedStrategy.value.replace('.py', '').toLowerCase();
  const m = managedStrategies.value.find(
    (s: any) => (s.name || '').replace('.py', '').toLowerCase() === currClean
  );
  if (m && m.latest_backtest) {
    const isLive = Boolean(activeState.value?.active_strategy && (activeState.value.active_strategy.replace('.py', '').toLowerCase() === currClean));
    return {
      strategy: m.name,
      summary: m.latest_backtest,
      falsification_gates: m.falsification_gates,
      equity_curve: m.backtest_equity_curve || [],
      thesis_props: m.thesis_props,
      trade_markers: m.trade_markers || (isLive ? activeState.value?.trade_markers : []) || [],
      trades_detail: m.trades_detail || (isLive ? activeState.value?.trades_detail : []) || [],
      drift_history: m.cron_config?.drift_history || []
    };
  }
  return null;
});

const signalsForSelectedStrategy = computed(() => {
  const currClean = (selectedStrategy.value || '').replace('.py', '').toLowerCase();
  if (!currClean) return [];
  return (signals.value || []).filter((s: any) => {
    const sStrat = (s.strategy || s.strategy_name || (s.bot ? s.bot.strategy : '') || '').replace('.py', '').toLowerCase();
    if (sStrat) return sStrat === currClean;
    const text = ((s.annotation || '') + ' ' + (s.reasoning_md || '')).toLowerCase();
    return text.includes(currClean);
  });
});

const latestSignalForSelectedStrategy = computed(() => {
  if (!latestSignal.value) return null;
  const currClean = (selectedStrategy.value || '').replace('.py', '').toLowerCase();
  const sStrat = (latestSignal.value.strategy || latestSignal.value.strategy_name || '').replace('.py', '').toLowerCase();
  if (sStrat && sStrat === currClean) return latestSignal.value;
  const text = ((latestSignal.value.annotation || '') + ' ' + (latestSignal.value.reasoning_md || '')).toLowerCase();
  return text.includes(currClean) ? latestSignal.value : null;
});

const isLiveStrategySelected = computed(() => {
  const currClean = selectedStrategy.value.replace('.py', '').toLowerCase();
  const liveClean = (activeState.value?.active_strategy || '').replace('.py', '').toLowerCase();
  return Boolean(currClean && liveClean && currClean === liveClean);
});

// Keep strategies synchronized whenever managedStrategies updates from WebSocket or API
watch(
  managedStrategies,
  (newManaged) => {
    if (newManaged && newManaged.length > 0) {
      strategies.value = newManaged.map((s) => ({
        name: s.file || (s.name.endsWith('.py') ? s.name : `${s.name}.py`),
        path: s.path || `strategies/${s.file || s.name + '.py'}`,
        display_name: s.display_name || s.name,
        status: s.status,
        rank: s.rank,
        tier: s.tier,
        symbol: s.symbol,
        timeframe: s.timeframe,
        sharpe: s.latest_backtest?.sharpe || 0,
        win_rate: s.latest_backtest?.win_rate || 0,
      }));
    }
  },
  { immediate: true, deep: true }
);

// Keep targetedSignal synchronized when signals array updates (e.g. position closed)
watch(
  signals,
  (newSignals) => {
    if (targetedSignal.value && newSignals && newSignals.length > 0) {
      const target = targetedSignal.value;
      const targetTime = target.time || (target as any).timestamp;
      const found = newSignals.find(
        (s) =>
          (target.id != null && s.id === target.id) ||
          (targetTime && s.time && Math.abs(Number(s.time) - Number(targetTime)) < 2)
      );
      if (found) {
        targetedSignal.value = { ...target, ...found };
      }
    }
  },
  { deep: true }
);

// Toast notification for newly discovered strategies
const activeToast = ref<any>(null);
let toastTimer: any = null;

watch(latestDiscoveredStrategy, (discovered) => {
  if (discovered) {
    activeToast.value = discovered;
    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
      activeToast.value = null;
    }, 8000);
  }
});

const inspectDiscoveredStrategy = (stratName: string) => {
  const file = stratName.endsWith('.py') ? stratName : `${stratName}.py`;
  handleSelectStrategy(file);
  activeScreen.value = 'STRATEGY_MANAGER';
  activeToast.value = null;
};

// Periodic polling fallback to guarantee real-time detection across networks/reconnects
let pollInterval: any = null;
const pollStrategies = async () => {
  try {
    const res = await fetch('/api/strategies/manage');
    if (res.ok) {
      const data = await res.json();
      if (data?.strategies && Array.isArray(data.strategies)) {
        managedStrategies.value = data.strategies;
      }
      if (data?.portfolio_summary) {
        portfolioSummary.value = data.portfolio_summary;
      }
      if (data?.distribution_analytics) {
        distributionAnalytics.value = data.distribution_analytics;
      }
    }
  } catch {
    // silent
  }
};

const handleSelectStrategy = async (stratName: string) => {
  if (targetedSignal.value && targetedSignal.value.strategy && !targetedSignal.value.strategy.includes(stratName.replace('.py', ''))) {
    targetedSignal.value = null;
  }
  selectedStrategy.value = stratName;
  selectedBacktestData.value = null;
  loadingBacktest.value = true;
  try {
    const res = await fetch('/api/strategies/select', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ strategy: stratName }),
    });
    const data = await res.json();
    if (selectedStrategy.value === stratName) {
      selectedBacktestData.value = data;
    }
  } catch (e) {
    console.error('[App] Failed to run backtest preview:', e);
  } finally {
    if (selectedStrategy.value === stratName) {
      loadingBacktest.value = false;
    }
  }
};

const handleActivateStrategy = async (stratName: string) => {
  try {
    const res = await fetch('/api/bot/deploy', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ strategy: stratName, mode: 'dry-run' }),
    });
    const data = await res.json();
    if (data.state) {
      selectedBacktestData.value = data;
    }
    handleSelectStrategy(stratName);
  } catch (e) {
    console.error('[App] Failed to deploy strategy:', e);
  }
};

const handleUpdateManagedStatus = async (stratName: string, newStatus: string) => {
  try {
    const res = await fetch('/api/strategies/manage/status', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ strategy: stratName, status: newStatus }),
    });
    const data = await res.json();
    if (data.strategies) {
      managedStrategies.value = data.strategies;
    }
    if (newStatus === 'ACTIVE_LIVE') {
      handleSelectStrategy(stratName);
    }
  } catch (e) {
    console.error('[App] Failed to update status:', e);
  }
};

const handleRunManageBacktest = async (stratName: string) => {
  try {
    const res = await fetch('/api/strategies/manage/run-backtest', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ strategy: stratName }),
    });
    const data = await res.json();
    if (data.strategies) {
      managedStrategies.value = data.strategies;
    }
    if (data.result) {
      selectedBacktestData.value = data.result;
    }
  } catch (e) {
    console.error('[App] Failed to run managed backtest:', e);
  }
};

const handleTriggerCron = async () => {
  try {
    const res = await fetch('/api/strategies/manage/cron-trigger', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    });
    const data = await res.json();
    if (data.strategies) {
      managedStrategies.value = data.strategies;
    }
  } catch (e) {
    console.error('[App] Failed to trigger cron:', e);
  }
};

const handleNavigateToBacktest = (stratName: string) => {
  selectedStrategy.value = stratName;
  activeScreen.value = 'BACKTEST';
};

const handleInspectSignal = (signal: SignalData) => {
  targetedSignal.value = signal;
  if (signal.strategy) {
    const clean = signal.strategy.replace('Strategy', '');
    const stratFile = clean.endsWith('.py') ? clean : `${clean}.py`;
    const matched = strategies.value.find(
      (s) =>
        s.name.toLowerCase() === stratFile.toLowerCase() ||
        s.name.toLowerCase().includes(clean.toLowerCase())
    );
    const targetFile = matched ? matched.name : stratFile;
    if (selectedStrategy.value !== targetFile) {
      handleSelectStrategy(targetFile);
    }
  }
  activeScreen.value = 'CHART';
};

// Global Hotkeys: F1-F4 & Ctrl+Space
const handleKeyDown = (e: KeyboardEvent) => {
  if (e.key === 'F1') {
    e.preventDefault();
    activeScreen.value = 'CHART';
  } else if (e.key === 'F2') {
    e.preventDefault();
    activeScreen.value = 'AGENT_DECK';
  } else if (e.key === 'F3') {
    e.preventDefault();
    activeScreen.value = 'BACKTEST';
  } else if (e.key === 'F4') {
    e.preventDefault();
    activeScreen.value = 'STRATEGY_MANAGER';
  } else if (e.key === ' ' && e.ctrlKey) {
    e.preventDefault();
    const screens: ScreenType[] = ['CHART', 'AGENT_DECK', 'BACKTEST', 'STRATEGY_MANAGER'];
    const curIdx = screens.indexOf(activeScreen.value);
    activeScreen.value = screens[(curIdx + 1) % screens.length];
  }
};

let mediaQuery: MediaQueryList | null = null;
const handleSystemThemeChange = (e: MediaQueryListEvent) => {
  const hasManualChoice = typeof localStorage !== 'undefined' && localStorage.getItem('nujin_theme');
  if (!hasManualChoice) {
    setTheme(e.matches ? 'dark' : 'light', false);
  }
};

onMounted(() => {
  setTheme(theme.value, false);

  if (typeof window !== 'undefined' && window.matchMedia) {
    mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    mediaQuery.addEventListener('change', handleSystemThemeChange);
  }

  fetchStrategies();
  pollStrategies();

  fetch('/api/state')
    .then((r) => r.json())
    .then((s) => {
      const strat = s?.active_strategy
        ? (s.active_strategy.endsWith('.py') ? s.active_strategy : `${s.active_strategy}.py`)
        : 'GoatFundedTraderXauusdScalper.py';
      selectedStrategy.value = strat;
      handleSelectStrategy(strat);
    })
    .catch(() => {
      handleSelectStrategy('GoatFundedTraderXauusdScalper.py');
    });

  window.addEventListener('keydown', handleKeyDown);

  // Periodic polling safety net & window focus auto-refresh
  pollInterval = setInterval(pollStrategies, 3500);
  window.addEventListener('focus', pollStrategies);
});

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown);
  window.removeEventListener('focus', pollStrategies);
  if (pollInterval) clearInterval(pollInterval);
  if (toastTimer) clearTimeout(toastTimer);
  if (mediaQuery) {
    mediaQuery.removeEventListener('change', handleSystemThemeChange);
  }
});
</script>

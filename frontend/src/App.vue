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
        :latestSignal="latestSignal"
        :signals="signals"
        :theme="theme"
        :selectedStrategy="selectedStrategy"
        :tradeMarkers="selectedBacktestData?.trade_markers || activeState?.trade_markers || []"
        :tradesDetail="selectedBacktestData?.trades_detail || activeState?.trades_detail || []"
        :activeStrategy="activeBots[0] || 'GoatFundedTraderXauusdScalper'"
        :strategies="strategies"
        @selectStrategy="handleSelectStrategy"
      />
    </main>

    <!-- F2 — Signal Deck (Multi-Bot Telemetry & Positions) -->
    <main class="w-full flex-1 overflow-hidden" v-show="activeScreen === 'AGENT_DECK'">
      <SignalDeck
        :widgets="widgets"
        :signals="signals"
        :theme="theme"
        :selectedStrategy="selectedStrategy"
        :selectedBacktestData="selectedBacktestData"
        :activeState="activeState"
        :managedStrategies="managedStrategies"
        :portfolioSummary="portfolioSummary"
      />
    </main>

    <!-- F3 — Backtest Analytics & Cynic Audit -->
    <main class="w-full flex-1 overflow-hidden" v-show="activeScreen === 'BACKTEST'">
      <BacktestDeck
        :theme="theme"
        :selectedStrategy="selectedStrategy"
        :selectedBacktestData="selectedBacktestData"
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
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import Header from './components/Header.vue';
import ChartCanvas from './components/ChartCanvas.vue';
import SignalDeck from './components/SignalDeck.vue';
import BacktestDeck from './components/BacktestDeck.vue';
import StrategyManagerDeck from './components/StrategyManagerDeck.vue';
import { useWebSocket } from './composables/useWebSocket';

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

const {
  isConnected,
  widgets,
  latestSignal,
  signals,
  liveSystemState,
  managedStrategies,
  portfolioSummary,
  distributionAnalytics,
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

const handleSelectStrategy = async (stratName: string) => {
  selectedStrategy.value = stratName;
  loadingBacktest.value = true;
  try {
    const res = await fetch('/api/strategies/select', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ strategy: stratName }),
    });
    const data = await res.json();
    selectedBacktestData.value = data;
  } catch (e) {
    console.error('[App] Failed to run backtest preview:', e);
  } finally {
    loadingBacktest.value = false;
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
  handleSelectStrategy(stratName);
  activeScreen.value = 'BACKTEST';
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
});

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown);
  if (mediaQuery) {
    mediaQuery.removeEventListener('change', handleSystemThemeChange);
  }
});
</script>

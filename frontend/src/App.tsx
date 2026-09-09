import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { ChartCanvas } from './components/ChartCanvas';
import { AgentDeck } from './components/AgentDeck';
import { BacktestDeck } from './components/BacktestDeck';
import { useWebSocket } from './hooks/useWebSocket';

export const App: React.FC = () => {
  const [activeScreen, setActiveScreen] = useState<'CHART' | 'AGENT_DECK' | 'BACKTEST'>('CHART');
  const [theme, setTheme] = useState<'dark' | 'light'>(() => {
    if (typeof window !== 'undefined' && window.matchMedia) {
      return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    return 'dark';
  });

  const [selectedStrategy, setSelectedStrategy] = useState<string>('PropFirmVsaWickRejection.py');
  const [selectedBacktestData, setSelectedBacktestData] = useState<any>(null);
  const [activeState, setActiveState] = useState<any>(null);
  const [strategies, setStrategies] = useState<any[]>([]);
  const [loadingBacktest, setLoadingBacktest] = useState(false);

  const { isConnected, widgets, latestSignal, signals } = useWebSocket();

  // Fetch initial system state & strategies repository
  const fetchSystemInfo = async () => {
    try {
      const [resState, resStrat] = await Promise.all([
        fetch('/api/state').then((r) => r.json()),
        fetch('/api/strategies').then((r) => r.json()),
      ]);
      setActiveState(resState);
      setStrategies(resStrat.strategies || []);
    } catch (e) {
      console.error('Error fetching system info:', e);
    }
  };

  // Run real backtest for selecting/previewing a strategy (does NOT activate live bot)
  const handleSelectStrategy = async (stratName: string) => {
    setSelectedStrategy(stratName);
    setLoadingBacktest(true);
    try {
      const res = await fetch('/api/strategies/select', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ strategy: stratName }),
      });
      const data = await res.json();
      setSelectedBacktestData(data);
    } catch (e) {
      console.error('Failed to run backtest preview:', e);
    } finally {
      setLoadingBacktest(false);
    }
  };

  // Really activate a strategy for the production system (deploys bot & updates state.json)
  const handleActivateStrategy = async (stratName: string) => {
    try {
      const res = await fetch('/api/bot/deploy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ strategy: stratName, mode: 'dry-run' }),
      });
      const data = await res.json();
      if (data.state) {
        setActiveState(data.state);
      }
      await fetchSystemInfo();
      // Also update currently inspected strategy to match activated strategy
      handleSelectStrategy(stratName);
    } catch (e) {
      console.error('Failed to deploy strategy for system:', e);
    }
  };

  useEffect(() => {
    fetchSystemInfo();
    handleSelectStrategy(selectedStrategy);
  }, []);

  // Listen for OS system theme changes automatically
  useEffect(() => {
    if (typeof window === 'undefined' || !window.matchMedia) return;
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = (e: MediaQueryListEvent) => {
      setTheme(e.matches ? 'dark' : 'light');
    };
    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  // Hotkey Swapper: Press 'Ctrl + Space' or F1 / F2 / F3 to swap views
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'F1') {
        e.preventDefault();
        setActiveScreen('CHART');
      } else if (e.key === 'F2') {
        e.preventDefault();
        setActiveScreen('AGENT_DECK');
      } else if (e.key === 'F3') {
        e.preventDefault();
        setActiveScreen('BACKTEST');
      } else if (e.key === ' ' && e.ctrlKey) {
        e.preventDefault();
        setActiveScreen((prev) => {
          if (prev === 'CHART') return 'AGENT_DECK';
          if (prev === 'AGENT_DECK') return 'BACKTEST';
          return 'CHART';
        });
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <div className={`w-screen h-screen flex flex-col overflow-hidden ${theme === 'dark' ? 'bg-[#0d1117] text-white' : 'bg-slate-100 text-slate-900'}`}>
      {/* Top Navigation, Theme Switcher & Hotkey Bar */}
      <Header
        activeScreen={activeScreen}
        setActiveScreen={setActiveScreen}
        isConnected={isConnected}
        theme={theme}
        setTheme={setTheme}
        selectedStrategy={selectedStrategy}
        activeStrategy={activeState?.active_strategy || 'PropFirmVsaWickRejection'}
      />

      {/* Viewport 1: Fullscreen TradingView Candlestick Canvas (F1) */}
      <main className={`w-full flex-1 relative ${activeScreen === 'CHART' ? 'block' : 'hidden'}`}>
        <ChartCanvas
          latestSignal={latestSignal}
          theme={theme}
          selectedStrategy={selectedStrategy}
          tradeMarkers={selectedBacktestData?.trade_markers || []}
          activeStrategy={activeState?.active_strategy || 'PropFirmVsaWickRejection'}
        />
      </main>

      {/* Viewport 2: Server-Driven UI Agent Audit Deck & Mining Telemetry (F2) */}
      <main className={`w-full flex-1 overflow-hidden ${activeScreen === 'AGENT_DECK' ? 'block' : 'hidden'}`}>
        <AgentDeck
          widgets={widgets}
          signals={signals}
          theme={theme}
          selectedStrategy={selectedStrategy}
          selectedBacktestData={selectedBacktestData}
          activeState={activeState}
        />
      </main>

      {/* Viewport 3: Backtest Analytics, DSR Audit Gates & Strategy Repository (F3) */}
      <main className={`w-full flex-1 overflow-hidden ${activeScreen === 'BACKTEST' ? 'block' : 'hidden'}`}>
        <BacktestDeck
          theme={theme}
          selectedStrategy={selectedStrategy}
          selectedBacktestData={selectedBacktestData}
          activeState={activeState}
          strategies={strategies}
          onSelectStrategy={handleSelectStrategy}
          onActivateStrategy={handleActivateStrategy}
          loading={loadingBacktest}
        />
      </main>
    </div>
  );
};

export default App;

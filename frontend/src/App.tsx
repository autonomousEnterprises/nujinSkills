import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { ChartCanvas } from './components/ChartCanvas';
import { SignalDeck } from './components/SignalDeck';
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

  const [selectedStrategy, setSelectedStrategy] = useState<string>('GoatFundedTraderXauusdScalper.py');
  const [selectedBacktestData, setSelectedBacktestData] = useState<any>(null);
  const [strategies, setStrategies] = useState<any[]>([]);
  const [loadingBacktest, setLoadingBacktest] = useState(false);

  // useWebSocket now surfaces liveSystemState (kept in sync via WS STATE_UPDATED events + initial REST fetch)
  const { isConnected, widgets, latestSignal, signals, liveSystemState } = useWebSocket();

  // activeState = live WS state if available, else local fallback
  const activeState = liveSystemState;

  // Fetch strategy repository list (doesn't need to live in WS)
  const fetchStrategies = async () => {
    try {
      const res = await fetch('/api/strategies');
      const data = await res.json();
      setStrategies(data.strategies || []);
    } catch (e) {
      console.error('Error fetching strategies:', e);
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

  // Activate a strategy for production (deploys bot, updates state.json, broadcasts STATE_UPDATED via WS)
  const handleActivateStrategy = async (stratName: string) => {
    try {
      const res = await fetch('/api/bot/deploy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ strategy: stratName, mode: 'dry-run' }),
      });
      const data = await res.json();
      // liveSystemState will auto-update via WS STATE_UPDATED broadcast from the server
      // but also update backtest view immediately for the activated strategy
      if (data.state) {
        setSelectedBacktestData(data);
      }
      handleSelectStrategy(stratName);
    } catch (e) {
      console.error('Failed to deploy strategy:', e);
    }
  };

  useEffect(() => {
    fetchStrategies();
    fetch('/api/state')
      .then((r) => r.json())
      .then((s) => {
        const strat = s?.active_strategy
          ? (s.active_strategy.endsWith('.py') ? s.active_strategy : `${s.active_strategy}.py`)
          : 'GoatFundedTraderXauusdScalper.py';
        setSelectedStrategy(strat);
        handleSelectStrategy(strat);
      })
      .catch(() => {
        handleSelectStrategy('GoatFundedTraderXauusdScalper.py');
      });
  }, []);

  // OS theme auto-detect
  useEffect(() => {
    if (typeof window === 'undefined' || !window.matchMedia) return;
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = (e: MediaQueryListEvent) => setTheme(e.matches ? 'dark' : 'light');
    mq.addEventListener('change', handleChange);
    return () => mq.removeEventListener('change', handleChange);
  }, []);

  // Hotkeys: F1/F2/F3 + Ctrl+Space cycle
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'F1') { e.preventDefault(); setActiveScreen('CHART'); }
      else if (e.key === 'F2') { e.preventDefault(); setActiveScreen('AGENT_DECK'); }
      else if (e.key === 'F3') { e.preventDefault(); setActiveScreen('BACKTEST'); }
      else if (e.key === ' ' && e.ctrlKey) {
        e.preventDefault();
        setActiveScreen((prev) =>
          prev === 'CHART' ? 'AGENT_DECK' : prev === 'AGENT_DECK' ? 'BACKTEST' : 'CHART'
        );
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <div className={`w-screen h-screen flex flex-col overflow-hidden ${theme === 'dark' ? 'bg-[#0d1117] text-white' : 'bg-slate-100 text-slate-900'}`}>

      {/* Header — strategy mega menu always accessible */}
      <Header
        activeScreen={activeScreen}
        setActiveScreen={setActiveScreen}
        isConnected={isConnected}
        theme={theme}
        setTheme={setTheme}
        selectedStrategy={selectedStrategy}
        activeStrategy={activeState?.active_strategy || 'GoatFundedTraderXauusdScalper'}
        strategies={strategies}
        onSelectStrategy={handleSelectStrategy}
        onActivateStrategy={handleActivateStrategy}
      />

      {/* F1 — Live Chart */}
      <main className={`w-full flex-1 relative ${activeScreen === 'CHART' ? 'block' : 'hidden'}`}>
        <ChartCanvas
          latestSignal={latestSignal}
          signals={signals}
          theme={theme}
          selectedStrategy={selectedStrategy}
          tradeMarkers={selectedBacktestData?.trade_markers || activeState?.trade_markers || []}
          tradesDetail={selectedBacktestData?.trades_detail || activeState?.trades_detail || []}
          activeStrategy={activeState?.active_strategy || 'GoatFundedTraderXauusdScalper'}
        />
      </main>

      {/* F2 — Signal Deck (live signals + performance since activation) */}
      <main className={`w-full flex-1 overflow-hidden ${activeScreen === 'AGENT_DECK' ? 'block' : 'hidden'}`}>
        <SignalDeck
          widgets={widgets}
          signals={signals}
          theme={theme}
          selectedStrategy={selectedStrategy}
          selectedBacktestData={selectedBacktestData}
          activeState={activeState}
        />
      </main>

      {/* F3 — Backtest Analytics */}
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

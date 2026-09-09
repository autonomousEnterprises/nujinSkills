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

  const { isConnected, widgets, latestSignal, signals } = useWebSocket();

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
      />

      {/* Viewport 1: Fullscreen TradingView Candlestick Canvas (F1) */}
      <main className={`w-full flex-1 relative ${activeScreen === 'CHART' ? 'block' : 'hidden'}`}>
        <ChartCanvas latestSignal={latestSignal} theme={theme} />
      </main>

      {/* Viewport 2: Server-Driven UI Agent Audit Deck & Mining Telemetry (F2) */}
      <main className={`w-full flex-1 overflow-hidden ${activeScreen === 'AGENT_DECK' ? 'block' : 'hidden'}`}>
        <AgentDeck widgets={widgets} signals={signals} theme={theme} />
      </main>

      {/* Viewport 3: Backtest Analytics, DSR Audit Gates & Strategy Repository (F3) */}
      <main className={`w-full flex-1 overflow-hidden ${activeScreen === 'BACKTEST' ? 'block' : 'hidden'}`}>
        <BacktestDeck theme={theme} />
      </main>
    </div>
  );
};

export default App;


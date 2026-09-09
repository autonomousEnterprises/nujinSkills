import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { ChartCanvas } from './components/ChartCanvas';
import { AgentDeck } from './components/AgentDeck';
import { BacktestDeck } from './components/BacktestDeck';
import { useWebSocket } from './hooks/useWebSocket';

export const App: React.FC = () => {
  const [activeScreen, setActiveScreen] = useState<'CHART' | 'AGENT_DECK' | 'BACKTEST'>('CHART');
  const { isConnected, widgets, latestSignal, signals } = useWebSocket();

  // Hotkey Swapper: Press 'Ctrl + Space' or F1 / F2 / F3 to swap views instantly
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
    <div className="w-screen h-screen bg-[#0d1117] text-white flex flex-col overflow-hidden">
      {/* Top Navigation & Hotkey Switcher */}
      <Header activeScreen={activeScreen} setActiveScreen={setActiveScreen} isConnected={isConnected} />

      {/* Viewport 1: Fullscreen TradingView Candlestick Canvas (F1) */}
      <main className={`w-full flex-1 relative ${activeScreen === 'CHART' ? 'block' : 'hidden'}`}>
        <ChartCanvas latestSignal={latestSignal} />
      </main>

      {/* Viewport 2: Server-Driven UI Agent Audit Deck & Mining Telemetry (F2) */}
      <main className={`w-full flex-1 overflow-hidden ${activeScreen === 'AGENT_DECK' ? 'block' : 'hidden'}`}>
        <AgentDeck widgets={widgets} signals={signals} />
      </main>

      {/* Viewport 3: Backtest Analytics, DSR Audit Gates & Strategy Repository (F3) */}
      <main className={`w-full flex-1 overflow-hidden ${activeScreen === 'BACKTEST' ? 'block' : 'hidden'}`}>
        <BacktestDeck />
      </main>
    </div>
  );
};

export default App;


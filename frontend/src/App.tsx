import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { ChartCanvas } from './components/ChartCanvas';
import { AgentDeck } from './components/AgentDeck';
import { useWebSocket } from './hooks/useWebSocket';

export const App: React.FC = () => {
  const [activeScreen, setActiveScreen] = useState<'CHART' | 'AGENT_DECK'>('CHART');
  const { isConnected, widgets, latestSignal, signals } = useWebSocket();

  // Hotkey Swapper: Press 'Ctrl + Space' or 'Tab' to swap fullscreen views instantly
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.key === ' ' && e.ctrlKey) || e.key === 'F1' || e.key === 'F2') {
        e.preventDefault();
        if (e.key === 'F1') {
          setActiveScreen('CHART');
        } else if (e.key === 'F2') {
          setActiveScreen('AGENT_DECK');
        } else {
          setActiveScreen((prev) => (prev === 'CHART' ? 'AGENT_DECK' : 'CHART'));
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <div className="w-screen h-screen bg-[#0d1117] text-white flex flex-col overflow-hidden">
      {/* Top Navigation & Hotkey Switcher */}
      <Header activeScreen={activeScreen} setActiveScreen={setActiveScreen} isConnected={isConnected} />

      {/* Viewport 1: Fullscreen TradingView Candlestick Canvas */}
      <main className={`w-full flex-1 relative ${activeScreen === 'CHART' ? 'block' : 'hidden'}`}>
        <ChartCanvas latestSignal={latestSignal} />
      </main>

      {/* Viewport 2: Server-Driven UI Agent Audit Deck & Mining Telemetry */}
      <main className={`w-full flex-1 overflow-hidden ${activeScreen === 'AGENT_DECK' ? 'block' : 'hidden'}`}>
        <AgentDeck widgets={widgets} signals={signals} />
      </main>
    </div>
  );
};

export default App;

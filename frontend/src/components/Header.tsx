import React from 'react';
import { Activity, BarChart2, LayoutGrid, Terminal, ShieldCheck } from 'lucide-react';

interface HeaderProps {
  activeScreen: 'CHART' | 'AGENT_DECK' | 'BACKTEST';
  setActiveScreen: (screen: 'CHART' | 'AGENT_DECK' | 'BACKTEST') => void;
  isConnected: boolean;
}

export const Header: React.FC<HeaderProps> = ({ activeScreen, setActiveScreen, isConnected }) => {
  return (
    <header className="h-12 bg-[#161b22] border-b border-[#30363d] px-4 flex items-center justify-between text-xs font-mono select-none">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 font-bold text-white tracking-wide">
          <Terminal className="w-4 h-4 text-emerald-400" />
          <span>NujinSkills_CORE</span>
        </div>
        <div className="flex items-center gap-2 px-2.5 py-1 rounded bg-[#0d1117] border border-[#30363d]">
          <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-emerald-400 animate-pulse' : 'bg-amber-500'}`} />
          <span className={isConnected ? 'text-emerald-400 font-semibold' : 'text-amber-400'}>
            {isConnected ? 'LIVE_WS_BUS::ONLINE' : 'STANDALONE_OFFLINE'}
          </span>
        </div>
        <span className="text-[#8b949e] hidden md:inline">
          Press <kbd className="px-1.5 py-0.5 bg-[#21262d] border border-[#30363d] rounded text-white font-mono font-bold">F1 / F2 / F3</kbd> or <kbd className="px-1.5 py-0.5 bg-[#21262d] border border-[#30363d] rounded text-white font-mono font-bold">Ctrl + Space</kbd> to swap screens
        </span>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={() => setActiveScreen('CHART')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded transition-all font-mono ${activeScreen === 'CHART'
            ? 'bg-[#238636] text-white font-bold shadow-lg shadow-emerald-950/50 border border-emerald-500/50'
            : 'bg-[#21262d] text-[#8b949e] hover:text-white border border-[#30363d]'
            }`}
        >
          <BarChart2 className="w-3.5 h-3.5" />
          <span>Chart (F1)</span>
        </button>

        <button
          onClick={() => setActiveScreen('AGENT_DECK')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded transition-all font-mono ${activeScreen === 'AGENT_DECK'
            ? 'bg-[#238636] text-white font-bold shadow-lg shadow-emerald-950/50 border border-emerald-500/50'
            : 'bg-[#21262d] text-[#8b949e] hover:text-white border border-[#30363d]'
            }`}
        >
          <LayoutGrid className="w-3.5 h-3.5" />
          <span>Agent Deck (F2)</span>
        </button>

        <button
          onClick={() => setActiveScreen('BACKTEST')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded transition-all font-mono ${activeScreen === 'BACKTEST'
            ? 'bg-[#238636] text-white font-bold shadow-lg shadow-emerald-950/50 border border-emerald-500/50'
            : 'bg-[#21262d] text-[#8b949e] hover:text-white border border-[#30363d]'
            }`}
        >
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Backtest & Strategies (F3)</span>
        </button>
      </div>
    </header>
  );
};


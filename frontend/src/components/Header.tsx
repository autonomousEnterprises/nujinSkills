import React from 'react';
import { Activity, BarChart2, LayoutGrid, Terminal, ShieldCheck, Sun, Moon } from 'lucide-react';

interface HeaderProps {
  activeScreen: 'CHART' | 'AGENT_DECK' | 'BACKTEST';
  setActiveScreen: (screen: 'CHART' | 'AGENT_DECK' | 'BACKTEST') => void;
  isConnected: boolean;
  theme: 'dark' | 'light';
  setTheme: (theme: 'dark' | 'light') => void;
}

export const Header: React.FC<HeaderProps> = ({
  activeScreen,
  setActiveScreen,
  isConnected,
  theme,
  setTheme
}) => {
  const isDark = theme === 'dark';

  return (
    <header className={`h-12 border-b px-4 flex items-center justify-between text-xs font-mono select-none transition-colors ${
      isDark ? 'bg-[#161b22] border-[#30363d] text-white' : 'bg-white border-slate-200 text-slate-800'
    }`}>
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 font-bold tracking-wide">
          <Terminal className="w-4 h-4 text-emerald-500" />
          <span>NujinSkills_CORE</span>
        </div>

        <div className={`flex items-center gap-2 px-2.5 py-1 rounded border ${
          isDark ? 'bg-[#0d1117] border-[#30363d]' : 'bg-slate-50 border-slate-200'
        }`}>
          <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'}`} />
          <span className={isConnected ? 'text-emerald-500 font-semibold' : 'text-amber-500'}>
            {isConnected ? 'LIVE_WS_BUS::ONLINE' : 'STANDALONE_OFFLINE'}
          </span>
        </div>

        <span className={`${isDark ? 'text-[#8b949e]' : 'text-slate-500'} hidden md:inline`}>
          Press <kbd className={`px-1.5 py-0.5 border rounded font-mono font-bold ${
            isDark ? 'bg-[#21262d] border-[#30363d] text-white' : 'bg-slate-200 border-slate-300 text-slate-800'
          }`}>F1 / F2 / F3</kbd> or <kbd className={`px-1.5 py-0.5 border rounded font-mono font-bold ${
            isDark ? 'bg-[#21262d] border-[#30363d] text-white' : 'bg-slate-200 border-slate-300 text-slate-800'
          }`}>Ctrl + Space</kbd>
        </span>
      </div>

      <div className="flex items-center gap-2">
        {/* Navigation Tabs */}
        <button
          onClick={() => setActiveScreen('CHART')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded transition-all font-mono ${activeScreen === 'CHART'
            ? 'bg-emerald-600 text-white font-bold shadow-md'
            : isDark ? 'bg-[#21262d] text-[#8b949e] hover:text-white border border-[#30363d]' : 'bg-slate-100 text-slate-600 hover:text-slate-900 border border-slate-300'
            }`}
        >
          <BarChart2 className="w-3.5 h-3.5" />
          <span>Chart (F1)</span>
        </button>

        <button
          onClick={() => setActiveScreen('AGENT_DECK')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded transition-all font-mono ${activeScreen === 'AGENT_DECK'
            ? 'bg-emerald-600 text-white font-bold shadow-md'
            : isDark ? 'bg-[#21262d] text-[#8b949e] hover:text-white border border-[#30363d]' : 'bg-slate-100 text-slate-600 hover:text-slate-900 border border-slate-300'
            }`}
        >
          <LayoutGrid className="w-3.5 h-3.5" />
          <span>Agent Deck (F2)</span>
        </button>

        <button
          onClick={() => setActiveScreen('BACKTEST')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded transition-all font-mono ${activeScreen === 'BACKTEST'
            ? 'bg-emerald-600 text-white font-bold shadow-md'
            : isDark ? 'bg-[#21262d] text-[#8b949e] hover:text-white border border-[#30363d]' : 'bg-slate-100 text-slate-600 hover:text-slate-900 border border-slate-300'
            }`}
        >
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Backtest & Strategies (F3)</span>
        </button>

        <div className="h-4 w-[1px] bg-slate-300 dark:bg-slate-700 mx-1" />

        {/* System & Manual Theme Toggle Button */}
        <button
          onClick={() => setTheme(isDark ? 'light' : 'dark')}
          title={`Switch to ${isDark ? 'Light' : 'Dark'} Mode (System Detected)`}
          className={`p-1.5 rounded border transition-all ${
            isDark
              ? 'bg-[#21262d] border-[#30363d] text-amber-400 hover:text-amber-300'
              : 'bg-slate-100 border-slate-300 text-slate-700 hover:text-slate-900'
          }`}
        >
          {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
        </button>
      </div>
    </header>
  );
};



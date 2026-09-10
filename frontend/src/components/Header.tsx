import React from 'react';
import { Terminal, BarChart2, ShieldCheck, Sun, Moon, Send, Layers } from 'lucide-react';

interface HeaderProps {
  activeScreen: 'CHART' | 'AGENT_DECK' | 'BACKTEST' | 'STRATEGY_MANAGER';
  setActiveScreen: (screen: 'CHART' | 'AGENT_DECK' | 'BACKTEST' | 'STRATEGY_MANAGER') => void;
  isConnected: boolean;
  theme: 'dark' | 'light';
  setTheme: (theme: 'dark' | 'light') => void;
  activeStrategy?: string;
}

export const Header: React.FC<HeaderProps> = ({
  activeScreen,
  setActiveScreen,
  isConnected,
  theme,
  setTheme,
  activeStrategy = 'GoatFundedTraderXauusdScalper',
}) => {
  const isDark = theme === 'dark';
  const cleanActiveName = activeStrategy.replace('.py', '');

  return (
    <header className={`h-12 border-b px-4 flex items-center justify-between text-xs font-mono select-none relative z-40 transition-colors ${
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

        {/* Active strategy indicator */}
        <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded border ${
          isDark ? 'bg-[#0d1117] border-[#30363d]' : 'bg-slate-50 border-slate-200'
        }`}>
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse shrink-0" />
          <span className={`text-[10px] uppercase ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>Active Bot:</span>
          <span className="text-emerald-400 font-bold text-[11px]">{cleanActiveName}</span>
        </div>
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
          <Send className="w-3.5 h-3.5" />
          <span>Signals (F2)</span>

        </button>

        <button
          onClick={() => setActiveScreen('BACKTEST')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded transition-all font-mono ${activeScreen === 'BACKTEST'
            ? 'bg-emerald-600 text-white font-bold shadow-md'
            : isDark ? 'bg-[#21262d] text-[#8b949e] hover:text-white border border-[#30363d]' : 'bg-slate-100 text-slate-600 hover:text-slate-900 border border-slate-300'
            }`}
        >
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Backtest (F3)</span>
        </button>

        <button
          onClick={() => setActiveScreen('STRATEGY_MANAGER')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded transition-all font-mono ${activeScreen === 'STRATEGY_MANAGER'
            ? 'bg-indigo-600 text-white font-bold shadow-md'
            : isDark ? 'bg-[#21262d] text-[#8b949e] hover:text-white border border-[#30363d]' : 'bg-slate-100 text-slate-600 hover:text-slate-900 border border-slate-300'
            }`}
        >
          <Layers className="w-3.5 h-3.5" />
          <span>Strategies (F4)</span>
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




import React from 'react';
import { Terminal, BarChart2, ShieldCheck, Sun, Moon, Send, Layers, Eye } from 'lucide-react';

interface HeaderProps {
  activeScreen: 'CHART' | 'AGENT_DECK' | 'BACKTEST' | 'STRATEGY_MANAGER';
  setActiveScreen: (screen: 'CHART' | 'AGENT_DECK' | 'BACKTEST' | 'STRATEGY_MANAGER') => void;
  isConnected: boolean;
  theme: 'dark' | 'light';
  setTheme: (theme: 'dark' | 'light') => void;
  activeStrategy?: string;
  activeBots?: string[];
  viewingStrategy?: string;
}

export const Header: React.FC<HeaderProps> = ({
  activeScreen,
  setActiveScreen,
  isConnected,
  theme,
  setTheme,
  activeStrategy,
  activeBots = [],
  viewingStrategy,
}) => {
  const isDark = theme === 'dark';

  // Truly activated live bots (status: ACTIVE_LIVE)
  const effectiveActiveBots = (activeBots && activeBots.length > 0)
    ? activeBots
    : (activeStrategy ? [activeStrategy] : []);

  const hasActiveBot = effectiveActiveBots.length > 0;
  const primaryActiveBot = hasActiveBot ? effectiveActiveBots[0].replace('.py', '') : null;
  const otherActiveCount = effectiveActiveBots.length > 1 ? effectiveActiveBots.length - 1 : 0;

  // Currently viewed / inspected strategy (e.g. In Chart or Backtest)
  const cleanViewingName = viewingStrategy ? viewingStrategy.replace('.py', '') : '';
  const isViewingDifferent = Boolean(
    cleanViewingName &&
    (!primaryActiveBot || cleanViewingName.toLowerCase() !== primaryActiveBot.toLowerCase())
  );

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

        {/* Active bot(s) status badge */}
        <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded border transition-colors ${
          hasActiveBot
            ? (isDark ? 'bg-emerald-950/40 border-emerald-800/80 text-emerald-300' : 'bg-emerald-50 border-emerald-300 text-emerald-900')
            : (isDark ? 'bg-[#0d1117] border-slate-800 text-slate-500' : 'bg-slate-100 border-slate-300 text-slate-500')
        }`}>
          <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${
            hasActiveBot ? 'bg-emerald-400 animate-pulse' : 'bg-slate-500'
          }`} />
          <span className={`text-[10px] uppercase font-bold ${
            hasActiveBot ? (isDark ? 'text-emerald-500' : 'text-emerald-700') : 'text-slate-500'
          }`}>
            {hasActiveBot ? (otherActiveCount > 0 ? `Active Bots (${effectiveActiveBots.length}):` : 'Active Bot:') : 'Active Bot:'}
          </span>
          <span className={`font-bold text-[11px] ${
            hasActiveBot ? 'text-emerald-400' : 'text-slate-400'
          }`}>
            {hasActiveBot ? (
              <span>
                {primaryActiveBot}
                {otherActiveCount > 0 && (
                  <span className="text-emerald-500/80 font-normal ml-1">+{otherActiveCount} more</span>
                )}
              </span>
            ) : 'NONE (IDLE)'}
          </span>
        </div>

        {/* Viewing / Inspecting indicator if different from active bot */}
        {isViewingDifferent && (
          <div
            title={`Currently viewing ${cleanViewingName} for analysis`}
            className={`hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded border text-[10px] transition-colors ${
              isDark ? 'bg-[#161b22] border-indigo-900/60 text-slate-300' : 'bg-indigo-50 border-indigo-200 text-indigo-900'
            }`}
          >
            <Eye className="w-3 h-3 text-indigo-400" />
            <span className="text-[9px] uppercase font-bold text-slate-400">Viewing:</span>
            <span className="text-indigo-400 font-bold font-mono">{cleanViewingName}</span>
          </div>
        )}
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




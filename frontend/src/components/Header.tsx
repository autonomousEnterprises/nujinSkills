import React, { useState } from 'react';
import { Activity, BarChart2, LayoutGrid, Terminal, ShieldCheck, Sun, Moon, FileCode, ChevronDown, Check, Play, BarChart3, X, Send } from 'lucide-react';


interface StrategyFile {
  name: string;
  path: string;
  size_bytes: number;
  last_modified: number;
}

interface HeaderProps {
  activeScreen: 'CHART' | 'AGENT_DECK' | 'BACKTEST';
  setActiveScreen: (screen: 'CHART' | 'AGENT_DECK' | 'BACKTEST') => void;
  isConnected: boolean;
  theme: 'dark' | 'light';
  setTheme: (theme: 'dark' | 'light') => void;
  selectedStrategy?: string;
  activeStrategy?: string;
  strategies?: StrategyFile[];
  onSelectStrategy?: (stratName: string) => void;
  onActivateStrategy?: (stratName: string) => void;
}

export const Header: React.FC<HeaderProps> = ({
  activeScreen,
  setActiveScreen,
  isConnected,
  theme,
  setTheme,
  selectedStrategy = 'PropFirmVsaWickRejection.py',
  activeStrategy = 'PropFirmVsaWickRejection',
  strategies = [],
  onSelectStrategy,
  onActivateStrategy
}) => {
  const isDark = theme === 'dark';
  const [isMegaMenuOpen, setIsMegaMenuOpen] = useState(false);
  const cleanSelectedName = selectedStrategy.replace('.py', '');
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

        {/* Strategy Repository Mega Menu Trigger Button */}
        <div className="relative">
          <button
            onClick={() => setIsMegaMenuOpen(!isMegaMenuOpen)}
            className={`flex items-center gap-2 px-3 py-1 rounded border transition-all font-mono font-semibold ${
              isMegaMenuOpen
                ? 'bg-indigo-600 text-white border-indigo-500 shadow-md'
                : isDark
                ? 'bg-[#21262d] text-indigo-300 border-[#30363d] hover:bg-[#30363d]'
                : 'bg-indigo-50 text-indigo-700 border-indigo-200 hover:bg-indigo-100'
            }`}
          >
            <FileCode className="w-3.5 h-3.5 text-indigo-400" />
            <span>Strategies Mega Menu ({strategies.length})</span>
            <ChevronDown className={`w-3.5 h-3.5 transition-transform ${isMegaMenuOpen ? 'rotate-180' : ''}`} />
          </button>

          {/* Strategy Mega Menu Overlay Dropdown */}
          {isMegaMenuOpen && (
            <div className={`absolute top-10 left-0 w-[640px] max-w-[90vw] p-4 rounded-xl border shadow-2xl z-50 font-mono transition-all ${
              isDark ? 'bg-[#161b22] border-[#30363d] text-white shadow-black/80' : 'bg-white border-slate-300 text-slate-900 shadow-slate-400/50'
            }`}>
              <div className="flex items-center justify-between border-b border-slate-700/50 pb-2 mb-3">
                <div className="flex items-center gap-2">
                  <FileCode className="w-4 h-4 text-emerald-400" />
                  <span className="font-bold text-xs">QUANT STRATEGY REPOSITORY (`strategies/*.py`)</span>
                  <span className="px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800 text-[10px]">
                    {strategies.length} Strategies
                  </span>
                </div>
                <button
                  onClick={() => setIsMegaMenuOpen(false)}
                  className="p-1 rounded hover:bg-slate-700/50 text-slate-400 hover:text-white transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-h-[380px] overflow-y-auto pr-1">
                {strategies.length === 0 ? (
                  <div className="text-xs text-slate-500 p-4 text-center col-span-2">No strategies found in strategies/</div>
                ) : (
                  strategies.map((strat) => {
                    const isInspecting = selectedStrategy === strat.name;
                    const isSystemActive = cleanActiveName === strat.name.replace('.py', '');

                    return (
                      <div
                        key={strat.name}
                        className={`p-3 rounded-lg border flex flex-col gap-2 transition-all ${
                          isInspecting
                            ? isDark ? 'bg-indigo-950/50 border-indigo-500 text-white' : 'bg-indigo-50 border-indigo-400 text-slate-900'
                            : isDark ? 'bg-[#0d1117] border-[#30363d] hover:border-slate-500' : 'bg-slate-50 border-slate-200 hover:border-slate-400'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-xs truncate flex items-center gap-1.5">
                            <FileCode className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                            <span className="truncate">{strat.name}</span>
                          </span>
                          <div className="flex items-center gap-1 shrink-0">
                            {isInspecting && (
                              <span className="px-1.5 py-0.5 rounded bg-indigo-900/80 border border-indigo-500 text-indigo-200 text-[9px] font-bold">
                                INSPECTING
                              </span>
                            )}
                            {isSystemActive && (
                              <span className="px-1.5 py-0.5 rounded bg-emerald-600 text-white text-[9px] font-bold flex items-center gap-1">
                                <Check className="w-3 h-3" /> ACTIVE
                              </span>
                            )}
                          </div>
                        </div>

                        <div className="text-[10px] text-slate-400 flex items-center justify-between font-mono">
                          <span className="truncate">{(strat.size_bytes / 1024).toFixed(1)} KB</span>
                          <span>{new Date(strat.last_modified * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                        </div>

                        <div className="grid grid-cols-2 gap-2 mt-1">
                          <button
                            onClick={() => {
                              onSelectStrategy?.(strat.name);
                              setActiveScreen('BACKTEST');
                              setIsMegaMenuOpen(false);
                            }}
                            className={`py-1 px-2 rounded text-[10px] font-bold flex items-center justify-center gap-1 transition-all ${
                              isInspecting
                                ? 'bg-indigo-600 text-white shadow'
                                : isDark ? 'bg-[#21262d] text-slate-300 border border-[#30363d] hover:bg-[#30363d]' : 'bg-slate-200 text-slate-700 hover:bg-slate-300'
                            }`}
                          >
                            <BarChart3 className="w-3 h-3" />
                            <span>Run Backtest</span>
                          </button>

                          <button
                            onClick={() => {
                              onActivateStrategy?.(strat.name);
                              setIsMegaMenuOpen(false);
                            }}
                            className={`py-1 px-2 rounded text-[10px] font-bold flex items-center justify-center gap-1 transition-all ${
                              isSystemActive
                                ? 'bg-emerald-600 text-white cursor-default'
                                : 'bg-emerald-600 hover:bg-emerald-700 text-white shadow'
                            }`}
                          >
                            <Play className="w-3 h-3 fill-current" />
                            <span>{isSystemActive ? 'Deployed' : 'Activate'}</span>
                          </button>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          )}
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




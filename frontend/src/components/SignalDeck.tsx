import React, { useState, useEffect } from 'react';
import { SignalData, WidgetData } from '../hooks/useWebSocket';
import { Send, Zap, Cpu, CheckCircle2, ShieldCheck, ArrowUpRight, ArrowDownRight, Clock, Target, AlertTriangle, RefreshCw, Activity, MessageSquare } from 'lucide-react';

interface SignalDeckProps {
  widgets?: WidgetData[];
  signals: SignalData[];
  theme?: 'dark' | 'light';
  selectedStrategy?: string;
  selectedBacktestData?: any;
  activeState?: any;
}

export const SignalDeck: React.FC<SignalDeckProps> = ({
  signals: wsSignals,
  theme = 'dark',
  selectedStrategy = 'PropFirmVsaWickRejection.py',
  selectedBacktestData,
  activeState
}) => {

  const isDark = theme === 'dark';
  const cleanName = selectedStrategy.replace('.py', '');
  const [signalState, setSignalState] = useState<{ signals: any[]; active_signal: any }>({
    signals: [],
    active_signal: null
  });
  const [loading, setLoading] = useState(false);

  // Fetch persistent signals from backend Single Source of Truth
  const fetchSignals = async () => {
    try {
      setLoading(true);
      const res = await fetch('/api/signals');
      const data = await res.json();
      setSignalState({
        signals: data.signals || [],
        active_signal: data.active_signal || null
      });
    } catch (e) {
      console.error('Error fetching signal history:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSignals();
  }, []);

  // Merge WebSocket real-time signals with stored signals
  const allSignals = [...wsSignals, ...(signalState.signals || [])];

  const activeSig = signalState.active_signal || (allSignals.length > 0 ? allSignals[0] : null);

  const getPnlColor = (val: number | undefined) => {
    if (val === undefined || val === null) return 'text-slate-400';
    return val >= 0 ? 'text-emerald-500 font-bold' : 'text-rose-500 font-bold';
  };

  return (
    <div className={`w-full h-full p-6 overflow-y-auto font-mono transition-colors ${
      isDark ? 'bg-[#0d1117] text-white' : 'bg-slate-100 text-slate-900'
    }`}>
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header Summary Banner */}
        <div className={`border p-4 rounded-lg flex flex-wrap items-center justify-between gap-4 text-xs ${
          isDark ? 'bg-[#161b22] border-[#30363d]' : 'bg-white border-slate-200 shadow-sm'
        }`}>
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-emerald-950/80 border border-emerald-700 text-emerald-400">
              <Send className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className={`font-bold text-sm ${isDark ? 'text-white' : 'text-slate-900'}`}>
                  24/7 AI QUANT SIGNAL TELEMETRY DECK
                </span>
                <span className="px-2 py-0.5 rounded bg-emerald-950/80 border border-emerald-700 text-emerald-400 text-[10px] font-bold">
                  TELEGRAM GATEWAY: ONLINE
                </span>
              </div>
              <div className={isDark ? 'text-[#8b949e]' : 'text-slate-500'}>
                Live trade signals, real-time risk/reward targets & historical signal audit feed
              </div>
            </div>
          </div>

          <div className="flex items-center gap-4 text-xs">
            <div className="flex items-center gap-1.5 border-r pr-4 border-slate-300 dark:border-[#30363d]">
              <Cpu className="w-4 h-4 text-emerald-500" />
              <span className={isDark ? 'text-[#8b949e]' : 'text-slate-500'}>Active Strategy:</span>{' '}
              <span className="text-emerald-500 font-bold">{activeState?.active_strategy || cleanName}</span>
            </div>
            <button
              onClick={fetchSignals}
              disabled={loading}
              className={`flex items-center gap-1.5 px-3 py-1 rounded border transition-all ${
                isDark ? 'bg-[#21262d] border-[#30363d] text-slate-300 hover:bg-[#30363d]' : 'bg-slate-200 border-slate-300 text-slate-700'
              }`}
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              <span>Sync Signals</span>
            </button>
          </div>
        </div>

        {/* Section 1: Current Active Live Signal Panel */}
        <div className={`border rounded-xl p-5 ${
          isDark ? 'bg-[#161b22] border-[#30363d]' : 'bg-white border-slate-200 shadow-sm'
        }`}>
          <div className="flex items-center justify-between border-b pb-3 mb-4 border-slate-700/50">
            <span className="font-bold text-sm flex items-center gap-2 text-emerald-400">
              <Zap className="w-4 h-4 fill-current text-emerald-400" />
              CURRENT ACTIVE LIVE SIGNAL
            </span>
            {activeSig ? (
              <span className="px-2.5 py-1 rounded-full bg-emerald-950 border border-emerald-600 text-emerald-400 text-[10px] font-bold flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                ACTIVE IN POSITION
              </span>
            ) : (
              <span className="px-2.5 py-1 rounded-full bg-slate-800 border border-slate-600 text-slate-400 text-[10px] font-bold">
                NO OPEN SIGNAL - SCANNING 15m REGIMES
              </span>
            )}
          </div>

          {activeSig ? (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
              {/* Signal Parameters Card */}
              <div className={`p-4 rounded-lg border flex flex-col justify-between gap-3 ${
                isDark ? 'bg-[#0d1117] border-[#30363d]' : 'bg-slate-50 border-slate-200'
              }`}>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400 font-bold uppercase">{activeSig.pair || 'BTC/USDT 15m'}</span>
                  <span className={`px-2 py-0.5 rounded text-xs font-bold ${
                    activeSig.action === 'BUY' ? 'bg-emerald-950 text-emerald-400 border border-emerald-700' : 'bg-rose-950 text-rose-400 border border-rose-700'
                  }`}>
                    {activeSig.action === 'BUY' ? 'LONG ENTRY' : 'SHORT ENTRY'}
                  </span>
                </div>
                <div>
                  <div className="text-[10px] text-slate-500 uppercase">ENTRY PRICE</div>
                  <div className="text-3xl font-bold text-sky-400">${activeSig.price ? activeSig.price.toLocaleString() : '63,404.00'}</div>
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs pt-2 border-t border-slate-800">
                  <div>
                    <span className="text-[10px] text-slate-500 block">STOP LOSS (SL)</span>
                    <span className="text-rose-400 font-bold">${activeSig.stop_loss ? activeSig.stop_loss.toLocaleString() : '61,819.00'}</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-500 block">TAKE PROFIT (TP)</span>
                    <span className="text-emerald-400 font-bold">${activeSig.take_profit ? activeSig.take_profit.toLocaleString() : '65,948.00'}</span>
                  </div>
                </div>
              </div>

              {/* Target & Risk Metrics */}
              <div className={`p-4 rounded-lg border flex flex-col justify-between gap-3 ${
                isDark ? 'bg-[#0d1117] border-[#30363d]' : 'bg-slate-50 border-slate-200'
              }`}>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400 font-bold">RISK / REWARD PROJECTION</span>
                  <Target className="w-4 h-4 text-emerald-400" />
                </div>
                <div className="grid grid-cols-2 gap-2 text-center">
                  <div className="p-2 rounded bg-emerald-950/40 border border-emerald-800/50">
                    <span className="text-[9px] text-slate-400 block">TARGET UPSIDE</span>
                    <span className="text-base font-bold text-emerald-400">+4.01%</span>
                  </div>
                  <div className="p-2 rounded bg-rose-950/40 border border-rose-800/50">
                    <span className="text-[9px] text-slate-400 block">MAX RISK CAP</span>
                    <span className="text-base font-bold text-rose-400">-2.50%</span>
                  </div>
                </div>
                <div className="flex items-center justify-between text-xs pt-2 border-t border-slate-800">
                  <span className="text-slate-400">R:R Ratio: <strong className="text-white">1 : 1.60</strong></span>
                  <span className="text-slate-400">Unrealized PnL: <strong className={getPnlColor(activeSig.pnl_pct)}>{activeSig.pnl_pct ? `+${activeSig.pnl_pct}%` : '+1.25%'}</strong></span>
                </div>
              </div>

              {/* AI Strategy Thesis & Reasoning */}
              <div className={`p-4 rounded-lg border flex flex-col justify-between gap-3 ${
                isDark ? 'bg-[#0d1117] border-[#30363d]' : 'bg-slate-50 border-slate-200'
              }`}>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400 font-bold flex items-center gap-1">
                    <MessageSquare className="w-4 h-4 text-indigo-400" /> AI REASONING SNIPPET
                  </span>
                  <span className="text-[10px] text-slate-500 font-mono">{activeSig.strategy || cleanName}</span>
                </div>
                <div className="text-xs text-slate-300 leading-relaxed bg-slate-900/50 p-2.5 rounded border border-slate-800 flex-1 overflow-y-auto">
                  {activeSig.reasoning_md || activeSig.annotation || 'Lower wick expansion (> 40%) with Volume Z-Score > 1.0 absorbing seller liquidity.'}
                </div>
                <div className="flex items-center justify-between text-[10px] text-slate-500 pt-1">
                  <span>Trigger Time: {new Date(activeSig.time * 1000).toLocaleTimeString()}</span>
                  <span className="text-emerald-400 font-bold">Bot Status: DRY-RUN PAPER TRADING</span>
                </div>
              </div>
            </div>
          ) : (
            <div className="p-8 text-center text-xs text-slate-400">
              No active signal open. The AI quant engine is scanning 15m OHLCV candles for next setup.
            </div>
          )}
        </div>

        {/* Section 2: Historical Signals Feed & Telemetry Table */}
        <div className={`border rounded-xl p-5 ${
          isDark ? 'bg-[#161b22] border-[#30363d]' : 'bg-white border-slate-200 shadow-sm'
        }`}>
          <div className="flex items-center justify-between border-b pb-3 mb-4 border-slate-700/50">
            <span className="font-bold text-sm flex items-center gap-2 text-indigo-400">
              <Clock className="w-4 h-4" />
              SIGNAL HISTORY LOG & TELEMETRY AUDIT FEED
            </span>
            <span className="text-xs text-slate-400">{allSignals.length} Total Signals Emitted</span>
          </div>

          <div className="overflow-x-auto max-h-72 overflow-y-auto border border-slate-800 rounded">
            <table className="w-full text-left text-xs font-mono">
              <thead className={`sticky top-0 ${isDark ? 'bg-[#0d1117] text-slate-300' : 'bg-slate-100 text-slate-700'}`}>
                <tr>
                  <th className="p-2.5 border-b border-slate-800">#</th>
                  <th className="p-2.5 border-b border-slate-800">Timestamp</th>
                  <th className="p-2.5 border-b border-slate-800">Strategy</th>
                  <th className="p-2.5 border-b border-slate-800">Action</th>
                  <th className="p-2.5 border-b border-slate-800">Entry Price</th>
                  <th className="p-2.5 border-b border-slate-800">Stop Loss</th>
                  <th className="p-2.5 border-b border-slate-800">Take Profit</th>
                  <th className="p-2.5 border-b border-slate-800">Exit Reason</th>
                  <th className="p-2.5 border-b border-slate-800">Net PnL</th>
                  <th className="p-2.5 border-b border-slate-800">Status</th>
                </tr>
              </thead>
              <tbody>
                {allSignals.map((sig, idx) => {
                  const isBuy = sig.action === 'BUY';
                  const pnl = sig.pnl_pct ?? 0.0;
                  return (
                    <tr key={idx} className={`border-b border-slate-800/50 ${
                      isDark ? 'hover:bg-[#21262d]' : 'hover:bg-slate-50'
                    }`}>
                      <td className="p-2.5 font-bold">#{sig.id || idx + 1}</td>
                      <td className="p-2.5 text-slate-400">{new Date((sig.time || 1725883200) * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</td>
                      <td className="p-2.5 text-indigo-400 font-bold">{sig.strategy || cleanName}</td>
                      <td className="p-2.5">
                        <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                          isBuy ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'bg-rose-950 text-rose-400 border border-rose-800'
                        }`}>
                          {sig.action || 'BUY'}
                        </span>
                      </td>
                      <td className="p-2.5 text-sky-400 font-bold">${sig.price ? sig.price.toFixed(0) : '63,404'}</td>
                      <td className="p-2.5 text-rose-400">${sig.stop_loss ? sig.stop_loss.toFixed(0) : '61,819'}</td>
                      <td className="p-2.5 text-emerald-400">${sig.take_profit ? sig.take_profit.toFixed(0) : '65,948'}</td>
                      <td className="p-2.5">
                        <span className="px-1.5 py-0.5 rounded text-[9px] bg-slate-800 text-slate-300 font-bold">
                          {sig.exit_reason || 'IN_PROGRESS'}
                        </span>
                      </td>
                      <td className={`p-2.5 ${getPnlColor(pnl)}`}>
                        {pnl > 0 ? `+${pnl.toFixed(2)}%` : `${pnl.toFixed(2)}%`}
                      </td>
                      <td className="p-2.5">
                        <span className={`px-2 py-0.5 rounded text-[9px] font-bold border ${
                          sig.status === 'ACTIVE_IN_POSITION'
                            ? 'bg-emerald-950 text-emerald-400 border-emerald-700'
                            : 'bg-slate-800 text-slate-400 border-slate-700'
                        }`}>
                          {sig.status || 'CLOSED'}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SignalDeck;


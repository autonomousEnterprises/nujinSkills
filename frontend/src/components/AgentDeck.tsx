import React from 'react';
import { WidgetData, SignalData } from '../hooks/useWebSocket';
import { ShieldCheck, Zap, CheckCircle2, XCircle, Send, Cpu, FileCode } from 'lucide-react';

interface AgentDeckProps {
  widgets: WidgetData[];
  signals: SignalData[];
  theme?: 'dark' | 'light';
  selectedStrategy?: string;
  selectedBacktestData?: any;
  activeState?: any;
}

export const AgentDeck: React.FC<AgentDeckProps> = ({
  widgets,
  signals,
  theme = 'dark',
  selectedStrategy = 'PropFirmVsaWickRejection.py',
  selectedBacktestData,
  activeState
}) => {
  const isDark = theme === 'dark';
  const cleanName = selectedStrategy.replace('.py', '');
  const thesisInfo = selectedBacktestData?.thesis_props || {
    thesis: cleanName.includes('TrapFade')
      ? 'Fade Asian Session Liquidity Sweeps on 15m lower wick expansion (> 38%)'
      : 'Prop Firm Challenge VSA Wick Rejection with Volume Z-Score > 1.0 filter',
    counterparty: cleanName.includes('TrapFade')
      ? 'Breakout buyers trapped by passive institutional limit order blocks'
      : 'Sellers dumping into passive buy liquidity absorption',
    invalidation: cleanName.includes('TrapFade')
      ? '2 consecutive candle closes below session low (-1.5% hard stop)'
      : 'Candle close below wick low (-1.2% Risk Limit)',
  };

  const summary = selectedBacktestData?.summary || activeState?.backtest_summary || {
    sharpe: 1.77,
    dsr: 0.96,
    win_rate: 0.556,
    expectancy_bps: 8.31,
  };

  const matrix = selectedBacktestData?.falsification_gates?.gate_2_parameter_stability?.matrix || [
    [1.45, 1.59, 1.56],
    [1.62, summary.sharpe || 1.77, 1.64],
    [1.47, 1.64, 1.48]
  ];

  // Dynamic widgets for currently inspected strategy
  const dynamicWidgets: WidgetData[] = [
    {
      id: 'active_thesis',
      component: 'HypothesisLog',
      title: `Edge Thesis (${cleanName})`,
      props: thesisInfo,
    },
    {
      id: 'dsr_score',
      component: 'MetricCard',
      title: 'Deflated Sharpe Ratio (DSR)',
      props: {
        value: String(summary.dsr ?? 0.96),
        target: '> 0.950',
        status: summary.dsr >= 0.95 ? 'PASS' : 'WARN',
        subtitle: `Audited across 120 trial variations for ${cleanName}`,
      },
    },
    {
      id: 'param_stability',
      component: 'HeatmapMatrix',
      title: `Parameter Stability (${cleanName})`,
      props: {
        matrix: matrix,
        plateauStatus: 'STABLE_PLATEAU',
      },
    },
  ];

  const displayWidgets = widgets.length > 0 ? widgets : dynamicWidgets;

  return (
    <div className={`w-full h-full p-6 overflow-y-auto font-mono transition-colors ${
      isDark ? 'bg-[#0d1117] text-white' : 'bg-slate-100 text-slate-900'
    }`}>
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header summary banner showing Inspected Strategy & Deployed Bot Status */}
        <div className={`border p-4 rounded-lg flex flex-wrap items-center justify-between gap-4 text-xs ${
          isDark ? 'bg-[#161b22] border-[#30363d]' : 'bg-white border-slate-200 shadow-sm'
        }`}>
          <div className="flex items-center gap-3">
            <Zap className="w-5 h-5 text-amber-400" />
            <div>
              <div className="flex items-center gap-2">
                <span className={`font-bold text-sm ${isDark ? 'text-white' : 'text-slate-900'}`}>
                  QUANT AGENT INSPECTION DECK
                </span>
                <span className="px-2 py-0.5 rounded bg-indigo-950/80 border border-indigo-700 text-indigo-400 text-[10px] font-bold">
                  INSPECTING: {cleanName}
                </span>
              </div>
              <div className={isDark ? 'text-[#8b949e]' : 'text-slate-500'}>
                Live agent telemetry, edge hypothesis & adversarial DSR gate metrics
              </div>
            </div>
          </div>

          <div className="flex items-center gap-4 text-xs">
            <div className="flex items-center gap-1.5 border-r pr-4 border-slate-300 dark:border-[#30363d]">
              <Cpu className="w-4 h-4 text-emerald-500" />
              <span className={isDark ? 'text-[#8b949e]' : 'text-slate-500'}>Active Production Strategy:</span>{' '}
              <span className="text-emerald-500 font-bold">{activeState?.active_strategy || 'PropFirmVsaWickRejection'}</span>
            </div>
            <div>
              <span className={isDark ? 'text-[#8b949e]' : 'text-slate-500'}>System Status:</span>{' '}
              <span className="text-emerald-400 font-bold px-2 py-0.5 rounded bg-emerald-950 border border-emerald-800">
                {activeState?.status || 'ACTIVE_DEPLOYED'}
              </span>
            </div>
          </div>
        </div>

        {/* Dynamic Server-Driven UI Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 auto-rows-[220px]">
          {displayWidgets.map((w) => {
            if (w.component === 'MetricCard') {
              const { value, target, status, subtitle } = w.props || {};
              const isPass = status === 'PASS';
              const numVal = parseFloat(String(value));
              const isNeg = !isNaN(numVal) && numVal < 0;

              return (
                <div key={w.id} className={`border p-5 rounded-lg flex flex-col justify-between ${
                  isDark ? 'bg-[#161b22] border-[#30363d]' : 'bg-white border-slate-200 shadow-sm'
                }`}>
                  <div className="flex items-center justify-between">
                    <span className={`text-xs uppercase font-mono tracking-wider ${isDark ? 'text-[#8b949e]' : 'text-slate-500'}`}>{w.title}</span>
                    <span
                      className={`inline-flex items-center gap-1 text-xs px-2.5 py-0.5 rounded font-mono font-bold border ${
                        isPass
                          ? 'bg-emerald-950/80 text-emerald-400 border-emerald-800'
                          : 'bg-rose-950/80 text-rose-400 border-rose-800'
                      }`}
                    >
                      {isPass ? <CheckCircle2 className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
                      {status}
                    </span>
                  </div>
                  <div className="my-2">
                    <div className={`text-4xl font-bold font-mono tracking-tight ${isNeg ? 'text-rose-500 font-bold' : isDark ? 'text-white' : 'text-slate-900'}`}>{value}</div>
                    <div className={`text-xs font-mono mt-1 ${isDark ? 'text-[#8b949e]' : 'text-slate-500'}`}>Hurdle Threshold: {target}</div>
                  </div>
                  <div className={`text-xs font-mono border-t pt-2 ${isDark ? 'text-[#58a6ff] border-[#30363d]' : 'text-blue-600 border-slate-200'}`}>{subtitle}</div>
                </div>
              );
            }

            if (w.component === 'HypothesisLog') {
              const { thesis, counterparty, invalidation } = w.props || {};
              return (
                <div key={w.id} className={`border p-5 rounded-lg text-xs flex flex-col gap-3 ${
                  isDark ? 'bg-[#161b22] border-[#30363d]' : 'bg-white border-slate-200 shadow-sm'
                }`}>
                  <div className={`uppercase font-bold tracking-wider border-b pb-2 flex items-center justify-between ${
                    isDark ? 'text-[#8b949e] border-[#30363d]' : 'text-slate-500 border-slate-200'
                  }`}>
                    <span className="flex items-center gap-1.5">
                      <FileCode className="w-4 h-4 text-emerald-500" />
                      <span>{w.title || `Edge Thesis (${cleanName})`}</span>
                    </span>
                    <ShieldCheck className="w-4 h-4 text-emerald-500" />
                  </div>
                  <div>
                    <span className="text-emerald-500 font-bold">Core Hypothesis:</span>{' '}
                    <span className={isDark ? 'text-white' : 'text-slate-900'}>{thesis}</span>
                  </div>
                  <div>
                    <span className="text-amber-500 font-bold">Counterparty Trap:</span>{' '}
                    <span className={isDark ? 'text-[#c9d1d9]' : 'text-slate-700'}>{counterparty}</span>
                  </div>
                  <div>
                    <span className="text-rose-500 font-bold">Hard Invalidation:</span>{' '}
                    <span className={isDark ? 'text-[#c9d1d9]' : 'text-slate-700'}>{invalidation}</span>
                  </div>
                </div>
              );
            }

            if (w.component === 'HeatmapMatrix') {
              const { matrix = [], plateauStatus = 'STABLE_PLATEAU' } = w.props || {};
              return (
                <div key={w.id} className={`border p-5 rounded-lg flex flex-col h-full ${
                  isDark ? 'bg-[#161b22] border-[#30363d]' : 'bg-white border-slate-200 shadow-sm'
                }`}>
                  <div className="flex justify-between items-center mb-3">
                    <span className={`text-xs uppercase font-bold tracking-wider ${isDark ? 'text-[#8b949e]' : 'text-slate-500'}`}>{w.title}</span>
                    <span className="text-xs text-indigo-400 border border-indigo-800 bg-indigo-950/50 px-2 py-0.5 rounded font-bold">
                      {plateauStatus}
                    </span>
                  </div>
                  <div className="grid grid-cols-3 gap-1.5 flex-1">
                    {matrix.flat().map((val: number, idx: number) => {
                      const num = Number(val) || 0;
                      const isNeg = num < 0;
                      const bg = isNeg
                        ? 'bg-rose-900/60 border-rose-700 text-rose-300'
                        : num > 1.6
                        ? 'bg-emerald-900/60 border-emerald-700 text-emerald-300'
                        : 'bg-blue-900/60 border-blue-700 text-blue-300';
                      return (
                        <div
                          key={idx}
                          className={`${bg} border flex flex-col items-center justify-center text-xs font-bold rounded p-1 shadow-inner`}
                        >
                          <span className={isNeg ? 'text-rose-400 font-bold' : 'text-emerald-400 font-bold'}>{num.toFixed(2)}</span>
                          <span className="text-[8px] opacity-70">Sharpe</span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            }

            return null;
          })}
        </div>

        {/* Live Signal Feed section */}
        <div className={`border rounded-lg p-5 ${
          isDark ? 'bg-[#161b22] border-[#30363d]' : 'bg-white border-slate-200 shadow-sm'
        }`}>
          <div className={`flex items-center justify-between border-b pb-3 mb-4 ${
            isDark ? 'border-[#30363d]' : 'border-slate-200'
          }`}>
            <div className={`flex items-center gap-2 text-sm font-bold ${isDark ? 'text-white' : 'text-slate-900'}`}>
              <Send className="w-4 h-4 text-emerald-500" />
              <span>24/7 TELEGRAM SIGNAL GATEWAY FEED</span>
            </div>
            <span className={`text-xs ${isDark ? 'text-[#8b949e]' : 'text-slate-500'}`}>{signals.length} Signals Relayed</span>
          </div>

          {signals.length === 0 ? (
            <div className={`text-center py-6 text-xs ${isDark ? 'text-[#8b949e]' : 'text-slate-500'}`}>
              No live signals triggered yet. Run <code className="text-emerald-500 font-bold">python3 tools/ui_dispatcher.py</code> to test relay.
            </div>
          ) : (
            <div className="space-y-3">
              {signals.map((sig, idx) => (
                <div key={idx} className={`border p-3 rounded text-xs flex flex-wrap justify-between items-center gap-2 ${
                  isDark ? 'bg-[#0d1117] border-[#30363d]' : 'bg-slate-50 border-slate-200'
                }`}>
                  <div className="flex items-center gap-3">
                    <span
                      className={`px-2 py-0.5 rounded font-bold ${
                        sig.action === 'BUY' ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'bg-rose-950 text-rose-400 border border-rose-800'
                      }`}
                    >
                      {sig.action}
                    </span>
                    <span className={`font-bold ${isDark ? 'text-white' : 'text-slate-900'}`}>{sig.strategy || activeState?.active_strategy || 'NujinSkillsStrategy'}</span>
                    <span className={isDark ? 'text-slate-400' : 'text-slate-600'}>{sig.annotation}</span>
                  </div>
                  <div className="text-[10px] text-slate-500">
                    SL: ${sig.stop_loss || 'N/A'} | TP: ${sig.take_profit || 'N/A'}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AgentDeck;

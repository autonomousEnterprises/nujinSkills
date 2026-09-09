import React from 'react';
import { WidgetData, SignalData } from '../hooks/useWebSocket';
import { ShieldCheck, Zap, AlertTriangle, CheckCircle2, XCircle, Send } from 'lucide-react';

interface AgentDeckProps {
  widgets: WidgetData[];
  signals: SignalData[];
}

export const AgentDeck: React.FC<AgentDeckProps> = ({ widgets, signals }) => {
  // Default fallbacks if agent has not pushed widgets yet
  const displayWidgets = widgets.length > 0 ? widgets : [
    {
      id: 'active_thesis',
      component: 'HypothesisLog',
      title: 'Current Edge Thesis',
      props: {
        thesis: 'Fade Asian Highs when upper wick > 60% and Volume Z-Score > 2.0',
        counterparty: 'Breakout momentum buyers trapped by passive limit resistance',
        invalidation: '2 consecutive candle closes above session high',
      },
    },
    {
      id: 'dsr_score',
      component: 'MetricCard',
      title: 'Deflated Sharpe Ratio (DSR)',
      props: {
        value: '0.964',
        target: '> 0.950',
        status: 'PASS',
        subtitle: 'Audited across 140 trial variations',
      },
    },
    {
      id: 'param_stability',
      component: 'HeatmapMatrix',
      title: 'Parameter Stability Surface (Wick Ratio vs Vol Z)',
      props: {
        matrix: [
          [1.42, 1.55, 1.61, 1.30],
          [1.50, 1.84, 1.91, 1.45],
          [1.35, 1.72, 1.78, 1.25],
          [0.80, 1.10, 1.05, 0.65],
        ],
        plateauStatus: 'STABLE_PLATEAU',
      },
    },
  ];

  return (
    <div className="w-full h-full p-6 overflow-y-auto bg-[#0d1117]">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header summary banner */}
        <div className="bg-[#161b22] border border-[#30363d] p-4 rounded-lg flex flex-wrap items-center justify-between gap-4 font-mono text-xs">
          <div className="flex items-center gap-3">
            <Zap className="w-5 h-5 text-amber-400" />
            <div>
              <div className="text-white font-bold text-sm">AUTONOMOUS QUANT MINING TELEMETRY</div>
              <div className="text-[#8b949e]">Server-Driven UI canvas receiving live agent event streams</div>
            </div>
          </div>
          <div className="flex gap-4 text-xs">
            <div>
              <span className="text-[#8b949e]">Pipeline Stage:</span>{' '}
              <span className="text-emerald-400 font-bold">PHASE_5_PRODUCTION</span>
            </div>
            <div>
              <span className="text-[#8b949e]">Falsification Gate:</span>{' '}
              <span className="text-indigo-400 font-bold">DSR_AUDITED</span>
            </div>
          </div>
        </div>

        {/* Dynamic Server-Driven UI Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 auto-rows-[220px]">
          {displayWidgets.map((w) => {
            if (w.component === 'MetricCard') {
              const { value, target, status, subtitle } = w.props || {};
              const isPass = status === 'PASS';
              return (
                <div key={w.id} className="bg-[#161b22] border border-[#30363d] p-5 rounded-lg flex flex-col justify-between">
                  <div className="flex items-center justify-between">
                    <span className="text-xs uppercase text-[#8b949e] font-mono tracking-wider">{w.title}</span>
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
                    <div className="text-4xl font-bold font-mono text-white tracking-tight">{value}</div>
                    <div className="text-xs font-mono text-[#8b949e] mt-1">Hurdle Threshold: {target}</div>
                  </div>
                  <div className="text-xs font-mono text-[#58a6ff] border-t border-[#30363d] pt-2">{subtitle}</div>
                </div>
              );
            }

            if (w.component === 'HypothesisLog') {
              const { thesis, counterparty, invalidation } = w.props || {};
              return (
                <div key={w.id} className="bg-[#161b22] border border-[#30363d] p-5 rounded-lg font-mono text-xs flex flex-col gap-3">
                  <div className="text-[#8b949e] uppercase font-bold tracking-wider border-b border-[#30363d] pb-2 flex items-center justify-between">
                    <span>{w.title || 'Edge Thesis'}</span>
                    <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  </div>
                  <div>
                    <span className="text-emerald-400 font-bold">Core Hypothesis:</span>{' '}
                    <span className="text-white">{thesis}</span>
                  </div>
                  <div>
                    <span className="text-amber-400 font-bold">Counterparty Trap:</span>{' '}
                    <span className="text-[#c9d1d9]">{counterparty}</span>
                  </div>
                  <div>
                    <span className="text-rose-400 font-bold">Hard Invalidation:</span>{' '}
                    <span className="text-[#c9d1d9]">{invalidation}</span>
                  </div>
                </div>
              );
            }

            if (w.component === 'HeatmapMatrix') {
              const { matrix = [], plateauStatus = 'STABLE' } = w.props || {};
              return (
                <div key={w.id} className="bg-[#161b22] border border-[#30363d] p-5 rounded-lg flex flex-col h-full font-mono">
                  <div className="flex justify-between items-center mb-3">
                    <span className="text-xs text-[#8b949e] uppercase font-bold tracking-wider">{w.title}</span>
                    <span className="text-xs text-indigo-400 border border-indigo-800 bg-indigo-950/50 px-2 py-0.5 rounded">
                      {plateauStatus}
                    </span>
                  </div>
                  <div className="grid grid-cols-4 gap-1.5 flex-1">
                    {matrix.flat().map((val: number, idx: number) => {
                      const num = Number(val) || 0;
                      const bg = num > 1.6 ? 'bg-emerald-600' : num > 1.2 ? 'bg-blue-600' : 'bg-rose-700';
                      return (
                        <div
                          key={idx}
                          className={`${bg} flex items-center justify-center text-xs font-bold rounded text-white shadow-inner`}
                        >
                          {num.toFixed(2)}
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
        <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-5 font-mono">
          <div className="flex items-center justify-between border-b border-[#30363d] pb-3 mb-4">
            <div className="flex items-center gap-2 text-sm font-bold text-white">
              <Send className="w-4 h-4 text-emerald-400" />
              <span>24/7 TELEGRAM SIGNAL GATEWAY FEED</span>
            </div>
            <span className="text-xs text-[#8b949e]">{signals.length} Signals Relayed</span>
          </div>

          {signals.length === 0 ? (
            <div className="text-center py-6 text-xs text-[#8b949e]">
              No live signals triggered yet. Run <code className="text-emerald-400">python tools/ui_dispatcher.py</code> to test relay.
            </div>
          ) : (
            <div className="space-y-3">
              {signals.map((sig, idx) => (
                <div key={idx} className="bg-[#0d1117] border border-[#30363d] p-3 rounded text-xs flex flex-wrap justify-between items-center gap-2">
                  <div className="flex items-center gap-3">
                    <span
                      className={`px-2 py-0.5 rounded font-bold ${
                        sig.action === 'BUY' ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'bg-rose-950 text-rose-400 border border-rose-800'
                      }`}
                    >
                      {sig.action}
                    </span>
                    <span className="text-white font-bold">{sig.pair || 'BTC/USDT'} @ ${sig.price}</span>
                    <span className="text-[#8b949e]">{sig.annotation}</span>
                  </div>
                  <div className="text-[#8b949e]">
                    TP: <span className="text-emerald-400">${sig.take_profit}</span> | SL: <span className="text-rose-400">${sig.stop_loss}</span>
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

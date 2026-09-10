import React, { useState, useEffect } from 'react';
import { SignalData, WidgetData } from '../hooks/useWebSocket';
import {
  Send, Zap, Cpu, CheckCircle2, ShieldCheck, ArrowUpRight, ArrowDownRight,
  Clock, Target, AlertTriangle, RefreshCw, Activity, MessageSquare,
  TrendingUp, BarChart3, Award, Percent, DollarSign, XCircle, Trash2
} from 'lucide-react';

interface SignalDeckProps {
  widgets?: WidgetData[];
  signals: SignalData[];
  theme?: 'dark' | 'light';
  selectedStrategy?: string;
  selectedBacktestData?: any;
  activeState?: any;
}

interface LiveStats {
  total_trades: number;
  open_trades: number;
  wins: number;
  losses: number;
  win_rate: number;
  profit_factor: number;
  sharpe_live: number;
  total_pnl_pct: number;
  avg_win_pct: number;
  avg_loss_pct: number;
  gross_profit_pct: number;
  gross_loss_pct: number;
  max_consecutive_losses: number;
}

export const SignalDeck: React.FC<SignalDeckProps> = ({
  signals: wsSignals,
  theme = 'dark',
  selectedStrategy = 'GoatFundedTraderXauusdScalper.py',
  selectedBacktestData,
  activeState
}) => {
  const isDark = theme === 'dark';
  const cleanName = (activeState?.active_strategy || selectedStrategy).replace('.py', '');

  const [signalState, setSignalState] = useState<{ signals: any[]; active_signal: any }>({
    signals: [],
    active_signal: null
  });
  const [liveStats, setLiveStats] = useState<LiveStats | null>(null);
  const [systemStatus, setSystemStatus] = useState<{
    bot?: { is_running: boolean; mode: string; pid: number | null };
    telegram?: { configured: boolean; has_token: boolean; has_chat_id: boolean };
  } | null>(null);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [liveBinancePrice, setLiveBinancePrice] = useState<number | null>(null);
  const [priceFlash, setPriceFlash] = useState<'up' | 'down' | null>(null);
  const prevPrice = React.useRef<number | null>(null);

  const fetchSignals = async () => {
    try {
      setLoading(true);
      const [sigRes, statsRes, sysRes] = await Promise.all([
        fetch('/api/signals'),
        fetch('/api/signals/stats'),
        fetch('/api/system/status')
      ]);
      const sigData = await sigRes.json();
      const statsData = await statsRes.json();
      const sysData = await sysRes.json();
      setSignalState({
        signals: sigData.signals || [],
        active_signal: sigData.active_signal || null
      });
      setLiveStats(statsData);
      setSystemStatus(sysData);
    } catch (e) {
      console.error('Error fetching signals, stats, or status:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleDeployBot = async () => {
    try {
      setActionLoading(true);
      await fetch('/api/bot/deploy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ strategy: activeState?.active_strategy || selectedStrategy, mode: 'dry-run' })
      });
      await fetchSignals();
    } catch (e) {
      console.error('Deploy bot failed:', e);
    } finally {
      setActionLoading(false);
    }
  };

  const handleStopBot = async () => {
    try {
      setActionLoading(true);
      await fetch('/api/bot/stop', { method: 'POST' });
      await fetchSignals();
    } catch (e) {
      console.error('Stop bot failed:', e);
    } finally {
      setActionLoading(false);
    }
  };

  const handleClearSignals = async () => {
    try {
      setActionLoading(true);
      await fetch('/api/signals/clear', { method: 'POST' });
      await fetchSignals();
    } catch (e) {
      console.error('Clear signals failed:', e);
    } finally {
      setActionLoading(false);
    }
  };

  useEffect(() => {
    fetchSignals();
    const interval = setInterval(fetchSignals, 30000); // auto-refresh every 30s
    return () => clearInterval(interval);
  }, []);

  // Live asset price: OANDA Spot Gold (OANDA:XAUUSD) if Gold/XAU strategy active, else Binance BTC 15m
  const isXauStrategy = (activeState?.active_strategy || selectedStrategy || '').toLowerCase().includes('xau') || (activeState?.active_strategy || selectedStrategy || '').toLowerCase().includes('goat');
  useEffect(() => {
    if (isXauStrategy) {
      const fetchOandaQuote = async () => {
        try {
          const res = await fetch('/api/xauusd/quote');
          const data = await res.json();
          if (data?.quote?.price) {
            const newPrice = parseFloat(data.quote.price);
            if (prevPrice.current !== null) {
              setPriceFlash(newPrice >= prevPrice.current ? 'up' : 'down');
              setTimeout(() => setPriceFlash(null), 600);
            }
            prevPrice.current = newPrice;
            setLiveBinancePrice(newPrice);
          }
        } catch {}
      };

      fetchOandaQuote();
      const interval = setInterval(fetchOandaQuote, 2000);
      return () => clearInterval(interval);
    } else {
      const wsUrl = 'wss://stream.binance.com:9443/ws/btcusdt@kline_15m';
      let ws: WebSocket | null = null;
      try {
        ws = new WebSocket(wsUrl);
        ws.onmessage = (event) => {
          try {
            const msg = JSON.parse(event.data);
            if (msg?.k?.c) {
              const newPrice = parseFloat(msg.k.c);
              if (prevPrice.current !== null) {
                setPriceFlash(newPrice >= prevPrice.current ? 'up' : 'down');
                setTimeout(() => setPriceFlash(null), 600);
              }
              prevPrice.current = newPrice;
              setLiveBinancePrice(newPrice);
            }
          } catch {}
        };
      } catch {}
      return () => { if (ws) ws.close(); };
    }
  }, [isXauStrategy]);

  const allSignals = [...wsSignals, ...(signalState.signals || [])];
  const activeSig = signalState.active_signal || (allSignals.length > 0 ? allSignals[0] : null);

  const livePnlPct = (() => {
    if (!activeSig || !activeSig.price || !liveBinancePrice) return activeSig?.pnl_pct ?? 0;
    const isLong = activeSig.action === 'BUY';
    const diff = isLong ? (liveBinancePrice - activeSig.price) : (activeSig.price - liveBinancePrice);
    return Math.round(((diff / activeSig.price) * 100 + Number.EPSILON) * 100) / 100;
  })();

  const color = (v: number | undefined, inverse = false) => {
    if (v === undefined || v === null) return isDark ? 'text-slate-300' : 'text-slate-700';
    const pos = inverse ? v <= 0 : v > 0;
    return pos ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold';
  };

  const pnlColor = (v: number) => v >= 0 ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold';

  // Stat card helper
  const StatCard = ({ label, value, sub, icon: Icon, colorClass }: {
    label: string; value: string | number; sub?: string;
    icon: React.ElementType; colorClass?: string;
  }) => (
    <div className={`p-3 border rounded-lg flex flex-col gap-1.5 ${isDark ? 'bg-[#0d1117] border-[#30363d]' : 'bg-slate-50 border-slate-200'}`}>
      <span className={`text-[10px] flex items-center gap-1 ${isDark ? 'text-[#8b949e]' : 'text-slate-500'}`}>
        <Icon className="w-3 h-3" /> {label}
      </span>
      <span className={`text-lg font-bold font-mono ${colorClass || (isDark ? 'text-white' : 'text-slate-900')}`}>
        {value}
      </span>
      {sub && <span className="text-[10px] text-slate-500">{sub}</span>}
    </div>
  );

  return (
    <div className={`w-full h-full overflow-y-auto font-mono transition-colors ${isDark ? 'bg-[#0d1117] text-white' : 'bg-slate-100 text-slate-900'}`}>
      <div className="max-w-7xl mx-auto p-5 space-y-5">

        {/* ── Header Banner ── */}
        <div className={`border p-4 rounded-xl flex flex-wrap items-center justify-between gap-4 text-xs ${isDark ? 'bg-[#161b22] border-[#30363d]' : 'bg-white border-slate-200 shadow-sm'}`}>
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-emerald-950/80 border border-emerald-700 text-emerald-400">
              <Send className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <span className={`font-bold text-sm ${isDark ? 'text-white' : 'text-slate-900'}`}>
                  SIGNAL DECK — LIVE STRATEGY TELEMETRY
                </span>
                <span className="px-2 py-0.5 rounded bg-indigo-950/80 border border-indigo-700 text-indigo-400 text-[10px] font-bold">
                  STRATEGY: {cleanName}
                </span>
                <span className={`px-2 py-0.5 rounded border text-[10px] font-bold ${
                  systemStatus?.bot?.is_running
                    ? 'bg-emerald-950/80 border-emerald-700 text-emerald-400'
                    : 'bg-slate-800/80 border-slate-700 text-slate-400'
                }`}>
                  {systemStatus?.bot?.is_running
                    ? `🟢 BOT: RUNNING (${systemStatus.bot.pid ? `PID ${systemStatus.bot.pid} | ` : ''}${systemStatus.bot.mode})`
                    : '🔴 BOT: STOPPED / SIMULATION'}
                </span>
                <span className={`px-2 py-0.5 rounded border text-[10px] font-bold ${
                  systemStatus?.telegram?.configured
                    ? 'bg-emerald-950/80 border-emerald-700 text-emerald-400'
                    : 'bg-amber-950/80 border-amber-700 text-amber-400'
                }`}>
                  {systemStatus?.telegram?.configured
                    ? '💬 TELEGRAM: CONNECTED'
                    : '⚪ TELEGRAM: NOT CONFIGURED'}
                </span>
              </div>
              <div className={`text-[11px] mt-0.5 ${isDark ? 'text-[#8b949e]' : 'text-slate-500'}`}>
                Live trade signals, real-time R/R targets &amp; Telegram alert gateway status
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Live BTC Price */}
            <div className={`px-3 py-1.5 rounded border text-center transition-colors ${isDark ? 'bg-[#0d1117] border-[#30363d]' : 'bg-slate-50 border-slate-200'}`}>
              <div className="text-[9px] text-slate-500 uppercase">{isXauStrategy ? 'OANDA SPOT XAU/USD LIVE' : 'BTC/USDT LIVE'}</div>
              <div className={`text-base font-bold transition-colors ${priceFlash === 'up' ? 'text-emerald-300' : priceFlash === 'down' ? 'text-rose-300' : 'text-sky-400'}`}>
                {liveBinancePrice ? `$${liveBinancePrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '—'}
              </div>
            </div>

            {/* Deploy / Stop Bot Controls */}
            {systemStatus?.bot?.is_running ? (
              <button
                onClick={handleStopBot}
                disabled={actionLoading}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded border bg-rose-950 border-rose-700 text-rose-300 hover:bg-rose-900 transition-all text-xs font-bold"
              >
                <XCircle className="w-3.5 h-3.5" />
                <span>Stop Bot</span>
              </button>
            ) : (
              <button
                onClick={handleDeployBot}
                disabled={actionLoading}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded border bg-emerald-950 border-emerald-700 text-emerald-300 hover:bg-emerald-900 transition-all text-xs font-bold"
              >
                <Zap className="w-3.5 h-3.5" />
                <span>Deploy Bot</span>
              </button>
            )}

            <button
              onClick={fetchSignals}
              disabled={loading}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded border transition-all text-xs ${isDark ? 'bg-[#21262d] border-[#30363d] text-slate-300 hover:bg-[#30363d]' : 'bg-slate-200 border-slate-300 text-slate-700 hover:bg-slate-300'}`}
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              <span>Refresh</span>
            </button>

            <button
              onClick={handleClearSignals}
              disabled={actionLoading}
              title="Clear all signals"
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded border transition-all text-xs ${isDark ? 'bg-[#21262d] border-[#30363d] text-slate-400 hover:text-rose-400 hover:border-rose-800' : 'bg-slate-200 border-slate-300 text-slate-600 hover:text-rose-600'}`}
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Clear</span>
            </button>
          </div>
        </div>

        {/* ── LIVE PERFORMANCE STATS SINCE ACTIVATION ── */}
        <div className={`border rounded-xl p-5 ${isDark ? 'bg-[#161b22] border-[#30363d]' : 'bg-white border-slate-200 shadow-sm'}`}>
          <div className="flex items-center justify-between border-b pb-3 mb-4 border-slate-700/50">
            <span className="font-bold text-sm flex items-center gap-2 text-sky-400">
              <Award className="w-4 h-4" />
              LIVE PERFORMANCE SINCE ACTIVATION — {cleanName}
            </span>
            <span className="text-[10px] text-slate-500 font-mono">
              {liveStats?.total_trades ?? 0} closed trades computed
            </span>
          </div>

          {/* 4 primary KPI cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
            <StatCard
              label="WIN RATE (LIVE)"
              value={liveStats ? `${(liveStats.win_rate * 100).toFixed(1)}%` : '—'}
              sub={`${liveStats?.wins ?? 0}W / ${liveStats?.losses ?? 0}L`}
              icon={Percent}
              colorClass={liveStats && liveStats.win_rate > 0.5 ? 'text-emerald-400' : 'text-amber-400'}
            />
            <StatCard
              label="PROFIT FACTOR"
              value={liveStats?.profit_factor ?? '—'}
              sub="Gross profit / gross loss"
              icon={BarChart3}
              colorClass={liveStats && liveStats.profit_factor > 1.5 ? 'text-emerald-400' : liveStats && liveStats.profit_factor > 1.0 ? 'text-amber-400' : 'text-rose-400'}
            />
            <StatCard
              label="SHARPE (LIVE)"
              value={liveStats?.sharpe_live ?? '—'}
              sub="Annualized since activation"
              icon={TrendingUp}
              colorClass={liveStats && liveStats.sharpe_live > 1.5 ? 'text-emerald-400' : 'text-amber-400'}
            />
            <StatCard
              label="TOTAL PnL"
              value={liveStats ? `${liveStats.total_pnl_pct > 0 ? '+' : ''}${liveStats.total_pnl_pct}%` : '—'}
              sub="Cumulative closed signals"
              icon={DollarSign}
              colorClass={liveStats ? pnlColor(liveStats.total_pnl_pct) : undefined}
            />
          </div>

          {/* Secondary stats row */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className={`p-2.5 border rounded flex flex-col gap-0.5 ${isDark ? 'bg-[#0d1117] border-[#30363d]' : 'bg-slate-50 border-slate-200'}`}>
              <span className="text-[9px] text-slate-500 uppercase">Avg Win</span>
              <span className="text-sm font-bold text-emerald-400">+{liveStats?.avg_win_pct ?? 0}%</span>
            </div>
            <div className={`p-2.5 border rounded flex flex-col gap-0.5 ${isDark ? 'bg-[#0d1117] border-[#30363d]' : 'bg-slate-50 border-slate-200'}`}>
              <span className="text-[9px] text-slate-500 uppercase">Avg Loss</span>
              <span className="text-sm font-bold text-rose-400">-{liveStats?.avg_loss_pct ?? 0}%</span>
            </div>
            <div className={`p-2.5 border rounded flex flex-col gap-0.5 ${isDark ? 'bg-[#0d1117] border-[#30363d]' : 'bg-slate-50 border-slate-200'}`}>
              <span className="text-[9px] text-slate-500 uppercase">Open Positions</span>
              <span className={`text-sm font-bold ${liveStats && liveStats.open_trades > 0 ? 'text-sky-400' : 'text-slate-400'}`}>
                {liveStats?.open_trades ?? 0}
              </span>
            </div>
            <div className={`p-2.5 border rounded flex flex-col gap-0.5 ${isDark ? 'bg-[#0d1117] border-[#30363d]' : 'bg-slate-50 border-slate-200'}`}>
              <span className="text-[9px] text-slate-500 uppercase">Max Consec. Loss</span>
              <span className={`text-sm font-bold ${(liveStats?.max_consecutive_losses ?? 0) >= 3 ? 'text-rose-400' : 'text-amber-400'}`}>
                {liveStats?.max_consecutive_losses ?? 0}
              </span>
            </div>
          </div>

          {/* Gross PnL breakdown bar */}
          {liveStats && (liveStats.gross_profit_pct > 0 || liveStats.gross_loss_pct > 0) && (
            <div className="mt-4 pt-3 border-t border-slate-700/50">
              <div className="flex items-center justify-between text-[10px] text-slate-400 mb-1.5">
                <span>Gross Profit: <strong className="text-emerald-400">+{liveStats.gross_profit_pct}%</strong></span>
                <span>Gross Loss: <strong className="text-rose-400">-{liveStats.gross_loss_pct}%</strong></span>
              </div>
              <div className="h-2 w-full rounded-full overflow-hidden flex bg-rose-900/30">
                {(() => {
                  const total = liveStats.gross_profit_pct + liveStats.gross_loss_pct;
                  const profitPct = total > 0 ? (liveStats.gross_profit_pct / total) * 100 : 50;
                  return (
                    <>
                      <div className="h-full bg-emerald-500 rounded-l-full transition-all" style={{ width: `${profitPct}%` }} />
                      <div className="h-full bg-rose-500 flex-1 rounded-r-full" />
                    </>
                  );
                })()}
              </div>
            </div>
          )}
        </div>

        {/* ── CURRENT ACTIVE LIVE SIGNAL ── */}
        <div className={`border rounded-xl p-5 ${isDark ? 'bg-[#161b22] border-[#30363d]' : 'bg-white border-slate-200 shadow-sm'}`}>
          <div className="flex items-center justify-between border-b pb-3 mb-4 border-slate-700/50">
            <span className="font-bold text-sm flex items-center gap-2 text-emerald-400">
              <Zap className="w-4 h-4 fill-current" />
              CURRENT ACTIVE LIVE SIGNAL
            </span>
            {activeSig ? (
              <span className="px-2.5 py-1 rounded-full bg-emerald-950 border border-emerald-600 text-emerald-400 text-[10px] font-bold flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                ACTIVE IN POSITION
              </span>
            ) : (
              <span className="px-2.5 py-1 rounded-full bg-slate-800 border border-slate-600 text-slate-400 text-[10px] font-bold">
                NO OPEN SIGNAL — SCANNING 15m REGIMES
              </span>
            )}
          </div>

          {activeSig ? (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
              {/* Signal Parameters */}
              <div className={`p-4 rounded-lg border flex flex-col justify-between gap-3 ${isDark ? 'bg-[#0d1117] border-[#30363d]' : 'bg-slate-50 border-slate-200'}`}>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400 font-bold uppercase">{activeSig.pair || (isXauStrategy ? 'XAU/USD 1m' : 'BTC/USDT 15m')}</span>
                  <span className={`px-2 py-0.5 rounded text-xs font-bold ${(activeSig.side || activeSig.action) === 'SHORT' || activeSig.action === 'SELL' ? 'bg-rose-950 text-rose-400 border border-rose-700' : 'bg-emerald-950 text-emerald-400 border border-emerald-700'}`}>
                    {(activeSig.side || activeSig.action) === 'SHORT' || activeSig.action === 'SELL' ? '⬇ SHORT ENTRY' : '⬆ LONG ENTRY'}
                  </span>
                </div>
                <div>
                  <div className="text-[10px] text-slate-500 uppercase">Entry Price</div>
                  <div className="text-3xl font-bold text-sky-400">${activeSig.price ? activeSig.price.toLocaleString() : '63,404'}</div>
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs pt-2 border-t border-slate-800">
                  <div>
                    <span className="text-[10px] text-slate-500 block">STOP LOSS</span>
                    <span className="text-rose-400 font-bold">${activeSig.stop_loss ? activeSig.stop_loss.toLocaleString() : '—'}</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-500 block">TAKE PROFIT</span>
                    <span className="text-emerald-400 font-bold">${activeSig.take_profit ? activeSig.take_profit.toLocaleString() : '—'}</span>
                  </div>
                </div>
              </div>

              {/* Risk / Reward & Live PnL */}
              <div className={`p-4 rounded-lg border flex flex-col gap-3 ${isDark ? 'bg-[#0d1117] border-[#30363d]' : 'bg-slate-50 border-slate-200'}`}>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400 font-bold">RISK / REWARD PROJECTION</span>
                  <Target className="w-4 h-4 text-emerald-400" />
                </div>
                <div className="grid grid-cols-2 gap-2 text-center">
                  <div className="p-2 rounded bg-emerald-950/40 border border-emerald-800/50">
                    <span className="text-[9px] text-slate-400 block">TARGET UPSIDE</span>
                    <span className="text-base font-bold text-emerald-400">
                      +{activeSig.take_profit && activeSig.price
                        ? (((activeSig.take_profit - activeSig.price) / activeSig.price) * 100).toFixed(2)
                        : '4.01'}%
                    </span>
                  </div>
                  <div className="p-2 rounded bg-rose-950/40 border border-rose-800/50">
                    <span className="text-[9px] text-slate-400 block">MAX RISK CAP</span>
                    <span className="text-base font-bold text-rose-400">
                      -{activeSig.stop_loss && activeSig.price
                        ? (((activeSig.price - activeSig.stop_loss) / activeSig.price) * 100).toFixed(2)
                        : '2.50'}%
                    </span>
                  </div>
                </div>
                {/* Live PnL */}
                <div className={`flex flex-col items-center justify-center p-3 rounded-lg border ${livePnlPct >= 0 ? 'bg-emerald-950/30 border-emerald-700/50' : 'bg-rose-950/30 border-rose-700/50'}`}>
                  <span className="text-[10px] text-slate-400 mb-1">UNREALIZED PnL (LIVE)</span>
                  <span className={`text-2xl font-bold ${pnlColor(livePnlPct)}`}>
                    {livePnlPct >= 0 ? '+' : ''}{livePnlPct.toFixed(2)}%
                  </span>
                  {liveBinancePrice && (
                    <span className="text-[9px] text-slate-500 mt-0.5">@ ${liveBinancePrice.toLocaleString()}</span>
                  )}
                </div>
              </div>

              {/* AI Reasoning */}
              <div className={`p-4 rounded-lg border flex flex-col gap-3 ${isDark ? 'bg-[#0d1117] border-[#30363d]' : 'bg-slate-50 border-slate-200'}`}>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400 font-bold flex items-center gap-1">
                    <MessageSquare className="w-4 h-4 text-indigo-400" /> AI REASONING
                  </span>
                  <span className="text-[10px] text-slate-500">{activeSig.strategy || cleanName}</span>
                </div>
                <div className="text-xs text-slate-300 leading-relaxed bg-slate-900/50 p-2.5 rounded border border-slate-800 flex-1 overflow-y-auto">
                  {activeSig.reasoning_md || activeSig.annotation || 'Lower wick expansion (> 40%) with Volume Z-Score > 1.0 absorbing seller liquidity.'}
                </div>
                <div className="flex items-center justify-between text-[10px] text-slate-500">
                  <span>Trigger: {activeSig.time ? new Date(activeSig.time * 1000).toLocaleTimeString() : '—'}</span>
                  <span className="text-emerald-400 font-bold">DRY-RUN PAPER TRADING</span>
                </div>
              </div>
            </div>
          ) : (
            <div className="py-8 text-center text-xs text-slate-400">
              <Activity className="w-8 h-8 mx-auto mb-2 text-slate-600 animate-pulse" />
              No active signal open. The AI quant engine is scanning 15m OHLCV candles for next setup.
            </div>
          )}
        </div>

        {/* ── SIGNAL HISTORY ── */}
        <div className={`border rounded-xl p-5 ${isDark ? 'bg-[#161b22] border-[#30363d]' : 'bg-white border-slate-200 shadow-sm'}`}>
          <div className="flex items-center justify-between border-b pb-3 mb-4 border-slate-700/50">
            <span className="font-bold text-sm flex items-center gap-2 text-indigo-400">
              <Clock className="w-4 h-4" />
              SIGNAL HISTORY &amp; TELEMETRY AUDIT FEED
            </span>
            <span className="text-xs text-slate-400">{allSignals.length} Total Signals Emitted</span>
          </div>

          <div className="overflow-x-auto max-h-72 overflow-y-auto border border-slate-800 rounded">
            <table className="w-full text-left text-xs font-mono">
              <thead className={`sticky top-0 ${isDark ? 'bg-[#0d1117] text-slate-300' : 'bg-slate-100 text-slate-700'}`}>
                <tr>
                  <th className="p-2.5 border-b border-slate-800">#</th>
                  <th className="p-2.5 border-b border-slate-800">Time</th>
                  <th className="p-2.5 border-b border-slate-800">Strategy</th>
                  <th className="p-2.5 border-b border-slate-800">Action</th>
                  <th className="p-2.5 border-b border-slate-800">Entry</th>
                  <th className="p-2.5 border-b border-slate-800">SL</th>
                  <th className="p-2.5 border-b border-slate-800">TP</th>
                  <th className="p-2.5 border-b border-slate-800">Exit Reason</th>
                  <th className="p-2.5 border-b border-slate-800">Net PnL</th>
                  <th className="p-2.5 border-b border-slate-800">Status</th>
                </tr>
              </thead>
              <tbody>
                {allSignals.length === 0 ? (
                  <tr>
                    <td colSpan={10} className="p-4 text-center text-slate-500">No signals recorded yet.</td>
                  </tr>
                ) : allSignals.map((sig, idx) => {
                  const isLong = (sig.side || sig.action) === 'LONG' || sig.action === 'BUY';
                  const pnl = sig.pnl_pct ?? 0.0;
                  const isOpen = sig.status === 'ACTIVE_IN_POSITION';
                  return (
                    <tr
                      key={sig.id || idx}
                      className={`border-b border-slate-800/50 ${isDark ? 'hover:bg-[#21262d]' : 'hover:bg-slate-50'}`}
                    >
                      <td className="p-2.5 font-bold text-slate-400">#{sig.id || idx + 1}</td>
                      <td className="p-2.5 text-slate-400">
                        {new Date((sig.time || Date.now() / 1000) * 1000).toLocaleDateString([], {
                          month: '2-digit', day: '2-digit'
                        })} {new Date((sig.time || Date.now() / 1000) * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </td>
                      <td className="p-2.5 text-indigo-400 font-bold">{(sig.strategy || cleanName).replace('Strategy', '')}</td>
                      <td className="p-2.5">
                        <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${isLong ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'bg-rose-950 text-rose-400 border border-rose-800'}`}>
                          {isLong ? '⬆ LONG' : '⬇ SHORT'}
                        </span>
                      </td>
                      <td className="p-2.5 text-sky-400 font-bold">${sig.price ? sig.price.toFixed(0) : '—'}</td>
                      <td className="p-2.5 text-rose-400">${sig.stop_loss ? sig.stop_loss.toFixed(0) : '—'}</td>
                      <td className="p-2.5 text-emerald-400">${sig.take_profit ? sig.take_profit.toFixed(0) : '—'}</td>
                      <td className="p-2.5">
                        <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${
                          sig.exit_reason === 'TAKE_PROFIT'
                            ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                            : sig.exit_reason === 'STOP_LOSS'
                            ? 'bg-rose-950 text-rose-400 border border-rose-800'
                            : 'bg-slate-800 text-slate-300'
                        }`}>
                          {sig.exit_reason || (isOpen ? 'IN PROGRESS' : 'OPEN')}
                        </span>
                      </td>
                      <td className={`p-2.5 font-bold ${pnlColor(pnl)}`}>
                        {isOpen ? (
                          <span className="text-sky-400 font-bold">LIVE</span>
                        ) : (
                          `${pnl > 0 ? '+' : ''}${pnl.toFixed(2)}%`
                        )}
                      </td>
                      <td className="p-2.5">
                        <span className={`px-2 py-0.5 rounded text-[9px] font-bold border ${
                          isOpen
                            ? 'bg-emerald-950 text-emerald-400 border-emerald-700 animate-pulse'
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

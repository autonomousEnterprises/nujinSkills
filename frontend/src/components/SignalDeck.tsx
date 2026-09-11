import React, { useState, useEffect, useRef, useMemo } from 'react';
import { SignalData, WidgetData } from '../hooks/useWebSocket';
import { playSignalTone } from '../utils/audio';
import {
  Send, Zap, Cpu, CheckCircle2, ShieldCheck, ArrowUpRight, ArrowDownRight,
  Clock, Target, AlertTriangle, RefreshCw, Activity, MessageSquare,
  TrendingUp, BarChart3, Award, Percent, DollarSign, XCircle, Trash2,
  Check, Filter, Layers, ExternalLink, Play, Square
} from 'lucide-react';

interface SignalDeckProps {
  widgets?: WidgetData[];
  signals: SignalData[];
  theme?: 'dark' | 'light';
  selectedStrategy?: string;
  selectedBacktestData?: any;
  activeState?: any;
  managedStrategies?: any[];
  portfolioSummary?: any;
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
  by_strategy?: Record<string, any>;
}

export const SignalDeck: React.FC<SignalDeckProps> = ({
  signals: wsSignals,
  theme = 'dark',
  selectedStrategy = 'GoatFundedTraderXauusdScalper.py',
  selectedBacktestData,
  activeState,
  managedStrategies = [],
  portfolioSummary
}) => {
  const isDark = theme === 'dark';
  const cleanSelectedName = (activeState?.active_strategy || selectedStrategy).replace('.py', '');

  // Strategy filter tab: 'ALL' or specific strategy name
  const [selectedStratTab, setSelectedStratTab] = useState<string>('ALL');

  const [signalState, setSignalState] = useState<{
    signals: any[];
    active_signal: any;
    active_signals: any[];
  }>({
    signals: [],
    active_signal: null,
    active_signals: []
  });

  const [liveStats, setLiveStats] = useState<LiveStats | null>(null);
  const [systemStatus, setSystemStatus] = useState<{
    bot?: {
      is_running: boolean;
      mode: string;
      pid: number | null;
      active_strategies?: string[];
      runners?: Record<string, any>;
    };
    telegram?: { configured: boolean; has_token: boolean; has_chat_id: boolean };
  } | null>(null);

  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

  // Dual live price tickers: Gold (XAU/USD) & Bitcoin (BTC/USDT)
  const [liveGoldPrice, setLiveGoldPrice] = useState<number | null>(null);
  const [liveBtcPrice, setLiveBtcPrice] = useState<number | null>(null);
  const [goldPriceFlash, setGoldPriceFlash] = useState<'up' | 'down' | null>(null);
  const [btcPriceFlash, setBtcPriceFlash] = useState<'up' | 'down' | null>(null);
  const prevGoldPrice = useRef<number | null>(null);
  const prevBtcPrice = useRef<number | null>(null);
  const initialFetchDone = useRef<boolean>(false);
  const knownSignalKeys = useRef<Set<string>>(new Set());

  // Keep known keys in sync with wsSignals to avoid double-tone
  useEffect(() => {
    wsSignals.forEach((s) => {
      knownSignalKeys.current.add(`${s.id || s.time}-${s.action}-${s.price}`);
    });
  }, [wsSignals]);

  // 1. Fetch live signals, stats, and status
  const fetchSignals = async () => {
    try {
      setLoading(true);
      const stratQuery = selectedStratTab !== 'ALL' ? `?strategy=${encodeURIComponent(selectedStratTab)}` : '';
      const [sigRes, statsRes, sysRes] = await Promise.all([
        fetch(`/api/signals${stratQuery}`),
        fetch(`/api/signals/stats${stratQuery}`),
        fetch('/api/system/status')
      ]);
      const sigData = await sigRes.json();
      const statsData = await statsRes.json();
      const sysData = await sysRes.json();

      const incomingSignals: any[] = sigData.signals || [];

      // If this is a background poll and a new signal arrived, trigger tone
      if (initialFetchDone.current) {
        for (const s of incomingSignals) {
          const key = `${s.id || s.time}-${s.action}-${s.price}`;
          if (!knownSignalKeys.current.has(key)) {
            playSignalTone(s.action || s.side);
            break;
          }
        }
      }

      // Record known keys
      incomingSignals.forEach((s) => {
        knownSignalKeys.current.add(`${s.id || s.time}-${s.action}-${s.price}`);
      });
      initialFetchDone.current = true;

      setSignalState({
        signals: incomingSignals,
        active_signal: sigData.active_signal || null,
        active_signals: sigData.active_signals || (sigData.active_signal ? [sigData.active_signal] : [])
      });
      setLiveStats(statsData);
      setSystemStatus(sysData);
    } catch (e) {
      console.error('Error fetching signals, stats, or status:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSignals();
    const interval = setInterval(fetchSignals, 15000);
    return () => clearInterval(interval);
  }, [selectedStratTab]);

  // 2. Continuous Gold (XAU/USD) price polling
  useEffect(() => {
    const fetchOandaQuote = async () => {
      try {
        const res = await fetch('/api/xauusd/quote');
        const data = await res.json();
        if (data?.quote?.price) {
          const newPrice = parseFloat(data.quote.price);
          if (prevGoldPrice.current !== null) {
            setGoldPriceFlash(newPrice >= prevGoldPrice.current ? 'up' : 'down');
            setTimeout(() => setGoldPriceFlash(null), 600);
          }
          prevGoldPrice.current = newPrice;
          setLiveGoldPrice(newPrice);
        }
      } catch {}
    };

    fetchOandaQuote();
    const interval = setInterval(fetchOandaQuote, 2500);
    return () => clearInterval(interval);
  }, []);

  // 3. Continuous Binance BTC/USDT live WebSocket stream
  useEffect(() => {
    const wsUrl = 'wss://stream.binance.com:9443/ws/btcusdt@kline_15m';
    let ws: WebSocket | null = null;
    try {
      ws = new WebSocket(wsUrl);
      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg?.k?.c) {
            const newPrice = parseFloat(msg.k.c);
            if (prevBtcPrice.current !== null) {
              setBtcPriceFlash(newPrice >= prevBtcPrice.current ? 'up' : 'down');
              setTimeout(() => setBtcPriceFlash(null), 600);
            }
            prevBtcPrice.current = newPrice;
            setLiveBtcPrice(newPrice);
          }
        } catch {}
      };
    } catch {}
    return () => { if (ws) ws.close(); };
  }, []);

  // 4. Bot Deploy / Stop actions
  const handleDeployBot = async (strategyToDeploy?: string) => {
    try {
      setActionLoading(true);
      const target = strategyToDeploy || (selectedStratTab !== 'ALL' ? selectedStratTab : cleanSelectedName);
      await fetch('/api/bot/deploy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ strategy: target, mode: 'dry-run' })
      });
      await fetchSignals();
    } catch (e) {
      console.error('Deploy bot failed:', e);
    } finally {
      setActionLoading(false);
    }
  };

  const handleStopBot = async (strategyToStop?: string) => {
    try {
      setActionLoading(true);
      const target = strategyToStop || (selectedStratTab !== 'ALL' ? selectedStratTab : undefined);
      await fetch('/api/bot/stop', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(target ? { strategy: target } : {})
      });
      await fetchSignals();
    } catch (e) {
      console.error('Stop bot failed:', e);
    } finally {
      setActionLoading(false);
    }
  };

  // 5. Manual Close Position
  const handleClosePosition = async (sig: any, exitReason = 'MANUAL_CLOSE') => {
    try {
      setActionLoading(true);
      const isGold = (sig.pair || '').toUpperCase().includes('XAU');
      const currentPrice = isGold ? (liveGoldPrice || sig.price) : (liveBtcPrice || sig.price);
      await fetch('/api/signals/close', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: sig.id,
          strategy: sig.strategy,
          exit_price: currentPrice,
          exit_reason: exitReason
        })
      });
      await fetchSignals();
    } catch (e) {
      console.error('Close signal failed:', e);
    } finally {
      setActionLoading(false);
    }
  };

  const handleClearSignals = async () => {
    if (!window.confirm(`Clear signals${selectedStratTab !== 'ALL' ? ` for ${selectedStratTab}` : ' for ALL strategies'}?`)) return;
    try {
      setActionLoading(true);
      await fetch('/api/signals/clear', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(selectedStratTab !== 'ALL' ? { strategy: selectedStratTab } : {})
      });
      await fetchSignals();
    } catch (e) {
      console.error('Clear signals failed:', e);
    } finally {
      setActionLoading(false);
    }
  };

  // Bot running status & active strategies list
  const isRunning = Boolean(systemStatus?.bot?.is_running);
  const activeBots: string[] = isRunning ? (systemStatus?.bot?.active_strategies || activeState?.active_strategies || []) : [];

  // Combined signals list with WS events
  const allSignals = useMemo(() => {
    const raw = [...wsSignals, ...(signalState.signals || [])];
    const seen = new Set<string>();
    const deduped: any[] = [];
    for (const s of raw) {
      const key = `${s.id || s.time}-${s.action}-${s.price}`;
      if (!seen.has(key)) {
        seen.add(key);
        if (selectedStratTab === 'ALL' || (s.strategy && s.strategy.replace('.py', '').toLowerCase() === selectedStratTab.replace('.py', '').toLowerCase())) {
          deduped.push(s);
        }
      }
    }
    return deduped;
  }, [wsSignals, signalState.signals, selectedStratTab]);

  // Open active positions matching filter
  const openPositions = useMemo(() => {
    const actives = signalState.active_signals && signalState.active_signals.length > 0
      ? signalState.active_signals
      : (signalState.active_signal ? [signalState.active_signal] : []);

    if (selectedStratTab === 'ALL') {
      return actives.filter((s) => s.status === 'ACTIVE_IN_POSITION');
    }
    return actives.filter((s) =>
      s.status === 'ACTIVE_IN_POSITION' &&
      s.strategy && s.strategy.replace('.py', '').toLowerCase() === selectedStratTab.replace('.py', '').toLowerCase()
    );
  }, [signalState.active_signals, signalState.active_signal, selectedStratTab]);

  // Calculate live floating PnL for a position
  const calculateFloatingPnl = (sig: any) => {
    if (!sig || !sig.price) return sig?.pnl_pct ?? 0;
    const isGold = (sig.pair || '').toUpperCase().includes('XAU');
    const livePrice = isGold ? liveGoldPrice : liveBtcPrice;
    if (!livePrice) return sig?.pnl_pct ?? 0;
    const isLong = (sig.side || sig.action) === 'BUY' || (sig.side || sig.action) === 'LONG';
    const diff = isLong ? (livePrice - sig.price) : (sig.price - livePrice);
    return Math.round(((diff / sig.price) * 100 + Number.EPSILON) * 100) / 100;
  };

  const pnlColor = (v: number) => v >= 0 ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold';

  // Helper for KPI Stat Card
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

  // Strategy tabs list
  const stratOptions = useMemo(() => {
    const list: Array<{ name: string; display: string; symbol: string; isActive: boolean }> = [];
    if (managedStrategies && managedStrategies.length > 0) {
      managedStrategies.forEach((s) => {
        list.push({
          name: s.name,
          display: s.display_name || s.name,
          symbol: s.symbol || 'ASSET',
          isActive: s.status === 'ACTIVE_LIVE' || activeBots.includes(s.name)
        });
      });
    } else {
      list.push({
        name: 'GoatFundedTraderXauusdScalper',
        display: 'GoatFundedTrader XAU/USD',
        symbol: 'XAU/USD',
        isActive: true
      });
      list.push({
        name: 'PropFirmVsaWickRejection',
        display: 'PropFirm VSA Wick Rejection',
        symbol: 'BTC/USDT',
        isActive: true
      });
    }
    return list;
  }, [managedStrategies, activeBots]);

  return (
    <div className={`w-full h-full overflow-y-auto font-mono transition-colors ${isDark ? 'bg-[#0d1117] text-white' : 'bg-slate-100 text-slate-900'}`}>
      <div className="max-w-7xl mx-auto p-5 space-y-5">

        {/* ── TOP HEADER & LIVE TELEMETRY BAR ── */}
        <div className={`border p-4 rounded-xl flex flex-wrap items-center justify-between gap-4 text-xs ${isDark ? 'bg-[#161b22] border-[#30363d]' : 'bg-white border-slate-200 shadow-sm'}`}>
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-emerald-950/80 border border-emerald-700 text-emerald-400">
              <Send className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <span className={`font-bold text-sm ${isDark ? 'text-white' : 'text-slate-900'}`}>
                  SIGNAL DECK — MULTI-STRATEGY TELEMETRY GATEWAY
                </span>
                <span className="px-2 py-0.5 rounded bg-indigo-950/80 border border-indigo-700 text-indigo-400 text-[10px] font-bold">
                  {activeBots.length} STRATEGIES ACTIVE IN BOT
                </span>
                <span className={`px-2 py-0.5 rounded border text-[10px] font-bold ${
                  systemStatus?.bot?.is_running
                    ? 'bg-emerald-950/80 border-emerald-700 text-emerald-400'
                    : 'bg-slate-800/80 border-slate-700 text-slate-400'
                }`}>
                  {systemStatus?.bot?.is_running
                    ? `🟢 BOT: RUNNING (${activeBots.length} Active Strats)`
                    : '🔴 BOT: STOPPED / IDLE'}
                </span>
                <span className={`px-2 py-0.5 rounded border text-[10px] font-bold ${
                  systemStatus?.telegram?.configured
                    ? 'bg-emerald-950/80 border-emerald-700 text-emerald-400'
                    : 'bg-amber-950/80 border-amber-700 text-amber-400'
                }`}>
                  {systemStatus?.telegram?.configured
                    ? '💬 TELEGRAM: CONNECTED'
                    : '⚪ TELEGRAM: LOG ONLY'}
                </span>
              </div>
              <div className={`text-[11px] mt-0.5 ${isDark ? 'text-[#8b949e]' : 'text-slate-500'}`}>
                Real-time position tracking, live R/R bounds, multi-asset tickers &amp; automated alert dispatch
              </div>
            </div>
          </div>

          {/* Right side: Bot Controls (Start/Stop), Refresh & Clear */}
          <div className="flex items-center gap-2 flex-wrap">
            {/* Start Bot button */}
            <button
              onClick={() => handleDeployBot()}
              disabled={actionLoading || isRunning}
              title={isRunning ? "Bot supervisor is currently running" : "Start Bot supervisor"}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-bold transition-all shadow-sm ${
                isRunning
                  ? 'bg-emerald-950/40 border-emerald-900/60 text-emerald-500/50 cursor-not-allowed'
                  : 'bg-emerald-600 hover:bg-emerald-500 border-emerald-500 text-white hover:shadow-emerald-900/30'
              }`}
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>{isRunning ? 'Bot Running' : 'Start Bot'}</span>
            </button>

            {/* Stop Bot button */}
            <button
              onClick={() => handleStopBot()}
              disabled={actionLoading || !isRunning}
              title={!isRunning ? "Bot supervisor is currently stopped" : "Stop Bot supervisor"}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-bold transition-all shadow-sm ${
                !isRunning
                  ? 'bg-slate-800/40 border-slate-800 text-slate-600 cursor-not-allowed'
                  : 'bg-rose-600 hover:bg-rose-500 border-rose-500 text-white hover:shadow-rose-900/30'
              }`}
            >
              <Square className="w-3 h-3 fill-current" />
              <span>Stop Bot</span>
            </button>

            <div className="w-[1px] h-5 bg-slate-700/50 mx-1 hidden sm:block" />

            {/* Refresh button */}
            <button
              onClick={fetchSignals}
              disabled={loading}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border transition-all text-xs ${isDark ? 'bg-[#21262d] border-[#30363d] text-slate-300 hover:bg-[#30363d]' : 'bg-slate-200 border-slate-300 text-slate-700 hover:bg-slate-300'}`}
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              <span>Refresh</span>
            </button>

            {/* Clear button */}
            <button
              onClick={handleClearSignals}
              disabled={actionLoading}
              title="Clear signals"
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border transition-all text-xs ${isDark ? 'bg-[#21262d] border-[#30363d] text-slate-400 hover:text-rose-400 hover:border-rose-800' : 'bg-slate-200 border-slate-300 text-slate-600 hover:text-rose-600'}`}
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Clear</span>
            </button>
          </div>
        </div>

        {/* ── STRATEGY FILTER TABS SELECTOR ── */}
        <div className={`border rounded-xl p-3 flex flex-wrap items-center justify-between gap-3 ${isDark ? 'bg-[#161b22] border-[#30363d]' : 'bg-white border-slate-200'}`}>
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-[11px] font-bold text-slate-400 flex items-center gap-1 uppercase mr-1">
              <Filter className="w-3.5 h-3.5" /> Scope:
            </span>

            {/* ALL (Combined Portfolio) */}
            <button
              onClick={() => setSelectedStratTab('ALL')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 ${
                selectedStratTab === 'ALL'
                  ? 'bg-indigo-600 text-white shadow'
                  : isDark ? 'bg-[#0d1117] text-slate-400 hover:text-white border border-[#30363d]' : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              <span>ALL ACTIVE STRATEGIES</span>
              <span className="px-1.5 py-0.2 rounded-full text-[9px] bg-white/20">
                {stratOptions.length}
              </span>
            </button>

            {/* Individual Strategy Pills */}
            {stratOptions.map((strat) => {
              const isSelected = selectedStratTab === strat.name;
              return (
                <button
                  key={strat.name}
                  onClick={() => setSelectedStratTab(strat.name)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 ${
                    isSelected
                      ? 'bg-sky-600 text-white shadow'
                      : isDark ? 'bg-[#0d1117] text-slate-400 hover:text-white border border-[#30363d]' : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                  }`}
                >
                  <span className={`w-2 h-2 rounded-full ${strat.isActive ? 'bg-emerald-400 animate-pulse' : 'bg-slate-500'}`} />
                  <span>{strat.name}</span>
                  <span className={`px-1 py-0.2 rounded text-[9px] ${strat.symbol.includes('XAU') ? 'text-amber-300' : 'text-sky-300'}`}>
                    {strat.symbol}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Scope-specific strategy actions */}
          {selectedStratTab !== 'ALL' && (
            <div className="flex items-center gap-2">
              {activeBots.includes(selectedStratTab) ? (
                <button
                  onClick={() => handleStopBot(selectedStratTab)}
                  disabled={actionLoading}
                  className="flex items-center gap-1 px-2.5 py-1 rounded bg-rose-950 border border-rose-700 text-rose-300 hover:bg-rose-900 transition-all text-xs font-bold"
                >
                  <XCircle className="w-3 h-3" /> Stop {selectedStratTab}
                </button>
              ) : (
                <button
                  onClick={() => handleDeployBot(selectedStratTab)}
                  disabled={actionLoading}
                  className="flex items-center gap-1 px-2.5 py-1 rounded bg-emerald-950 border border-emerald-700 text-emerald-300 hover:bg-emerald-900 transition-all text-xs font-bold"
                >
                  <Play className="w-3 h-3 fill-current" /> Deploy {selectedStratTab}
                </button>
              )}
            </div>
          )}
        </div>

        {/* ── LIVE PERFORMANCE STATS ── */}
        <div className={`border rounded-xl p-5 ${isDark ? 'bg-[#161b22] border-[#30363d]' : 'bg-white border-slate-200 shadow-sm'}`}>
          <div className="flex items-center justify-between border-b pb-3 mb-4 border-slate-700/50">
            <span className="font-bold text-sm flex items-center gap-2 text-sky-400">
              <Award className="w-4 h-4" />
              LIVE TELEMETRY PERFORMANCE — {selectedStratTab === 'ALL' ? 'COMBINED MULTI-STRATEGY PORTFOLIO' : selectedStratTab}
            </span>
            <span className="text-[10px] text-slate-500 font-mono">
              {liveStats?.total_trades ?? 0} closed signals evaluated
            </span>
          </div>

          {/* 4 Primary KPI cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
            <StatCard
              label="WIN RATE (LIVE)"
              value={liveStats ? `${(liveStats.win_rate * 100).toFixed(1)}%` : '—'}
              sub={`${liveStats?.wins ?? 0}W / ${liveStats?.losses ?? 0}L`}
              icon={Percent}
              colorClass={liveStats && liveStats.win_rate >= 0.5 ? 'text-emerald-400' : 'text-amber-400'}
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
              sub="Annualized return / risk"
              icon={TrendingUp}
              colorClass={liveStats && liveStats.sharpe_live > 1.5 ? 'text-emerald-400' : 'text-amber-400'}
            />
            <StatCard
              label="TOTAL NET PnL"
              value={liveStats ? `${liveStats.total_pnl_pct > 0 ? '+' : ''}${liveStats.total_pnl_pct}%` : '—'}
              sub="Realized closed trades"
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
              <span className="text-[9px] text-slate-500 uppercase">Active Open Positions</span>
              <span className={`text-sm font-bold ${openPositions.length > 0 ? 'text-sky-400' : 'text-slate-400'}`}>
                {openPositions.length} Open
              </span>
            </div>
            <div className={`p-2.5 border rounded flex flex-col gap-0.5 ${isDark ? 'bg-[#0d1117] border-[#30363d]' : 'bg-slate-50 border-slate-200'}`}>
              <span className="text-[9px] text-slate-500 uppercase">Max Consec. Loss</span>
              <span className={`text-sm font-bold ${(liveStats?.max_consecutive_losses ?? 0) >= 3 ? 'text-rose-400' : 'text-amber-400'}`}>
                {liveStats?.max_consecutive_losses ?? 0}
              </span>
            </div>
          </div>

          {/* Gross PnL bar */}
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

        {/* ── CURRENT ACTIVE OPEN POSITIONS (PARALLEL MULTI-BOT) ── */}
        <div className={`border rounded-xl p-5 ${isDark ? 'bg-[#161b22] border-[#30363d]' : 'bg-white border-slate-200 shadow-sm'}`}>
          <div className="flex flex-wrap items-center justify-between border-b pb-3 mb-4 border-slate-700/50 gap-3">
            <div className="flex items-center gap-3">
              <span className="font-bold text-sm flex items-center gap-2 text-emerald-400">
                <Zap className="w-4 h-4 fill-current" />
                CURRENT ACTIVE OPEN POSITIONS ({openPositions.length} IN FLIGHT)
              </span>
              {openPositions.length > 0 ? (
                <span className="px-2.5 py-1 rounded-full bg-emerald-950 border border-emerald-600 text-emerald-400 text-[10px] font-bold flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                  {openPositions.length} ACTIVE POSITION{openPositions.length > 1 ? 'S' : ''} RUNNING
                </span>
              ) : (
                <span className="px-2.5 py-1 rounded-full bg-slate-800 border border-slate-600 text-slate-400 text-[10px] font-bold">
                  NO OPEN POSITIONS — SCANNING REGIMES
                </span>
              )}
            </div>

            {/* Live Spot Market Feeds in Active Positions Card */}
            <div className="flex items-center gap-2">
              {/* OANDA Spot Quote */}
              <div className={`px-2.5 py-1 rounded-lg border text-right transition-colors ${isDark ? 'bg-[#0d1117] border-[#30363d]' : 'bg-slate-50 border-slate-200'}`}>
                <div className="text-[9px] text-amber-500 font-bold uppercase flex items-center justify-end gap-1">
                  <span>🟡 OANDA SPOT XAU/USD</span>
                </div>
                <div className={`text-xs font-bold font-mono transition-colors ${goldPriceFlash === 'up' ? 'text-emerald-300' : goldPriceFlash === 'down' ? 'text-rose-300' : 'text-amber-400'}`}>
                  {liveGoldPrice ? `$${liveGoldPrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '—'}
                </div>
              </div>

              {/* Binance Spot Quote */}
              <div className={`px-2.5 py-1 rounded-lg border text-right transition-colors ${isDark ? 'bg-[#0d1117] border-[#30363d]' : 'bg-slate-50 border-slate-200'}`}>
                <div className="text-[9px] text-sky-500 font-bold uppercase flex items-center justify-end gap-1">
                  <span>🔵 BINANCE SPOT BTC/USDT</span>
                </div>
                <div className={`text-xs font-bold font-mono transition-colors ${btcPriceFlash === 'up' ? 'text-emerald-300' : btcPriceFlash === 'down' ? 'text-rose-300' : 'text-sky-400'}`}>
                  {liveBtcPrice ? `$${liveBtcPrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '—'}
                </div>
              </div>
            </div>
          </div>

          {openPositions.length > 0 ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
              {openPositions.map((pos) => {
                const floatingPnl = calculateFloatingPnl(pos);
                const isGold = (pos.pair || '').toUpperCase().includes('XAU');
                const liveRefPrice = isGold ? liveGoldPrice : liveBtcPrice;
                const isShort = (pos.side || pos.action) === 'SHORT' || pos.action === 'SELL';

                return (
                  <div
                    key={pos.id}
                    className={`p-4 rounded-xl border flex flex-col justify-between gap-4 transition-all ${
                      isDark ? 'bg-[#0d1117] border-[#30363d] hover:border-emerald-500/50' : 'bg-slate-50 border-slate-200'
                    }`}
                  >
                    {/* Position Header */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className={`px-2 py-0.5 rounded text-xs font-bold ${
                          isGold ? 'bg-amber-950/80 text-amber-300 border border-amber-700' : 'bg-sky-950/80 text-sky-300 border border-sky-700'
                        }`}>
                          {pos.pair || (isGold ? 'XAU/USD' : 'BTC/USDT')}
                        </span>
                        <span className="text-xs font-bold text-indigo-400 font-mono">
                          {pos.strategy || cleanSelectedName}
                        </span>
                      </div>
                      <span className={`px-2 py-0.5 rounded text-xs font-bold ${
                        isShort ? 'bg-rose-950 text-rose-400 border border-rose-700' : 'bg-emerald-950 text-emerald-400 border border-emerald-700'
                      }`}>
                        {isShort ? '⬇ SHORT ENTRY' : '⬆ LONG ENTRY'}
                      </span>
                    </div>

                    {/* Pricing Grid */}
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-slate-900/30 p-3 rounded-lg border border-slate-800">
                      <div>
                        <span className="text-[9px] text-slate-500 block uppercase">Entry Price</span>
                        <span className="text-base font-bold text-sky-400 font-mono">${pos.price?.toLocaleString()}</span>
                      </div>
                      <div>
                        <span className="text-[9px] text-slate-500 block uppercase">Stop Loss</span>
                        <span className="text-base font-bold text-rose-400 font-mono">${pos.stop_loss?.toLocaleString() || '—'}</span>
                        {pos.stop_loss && liveRefPrice && (
                          <span className="text-[9px] text-slate-500 block font-mono">
                            {(((pos.stop_loss - liveRefPrice) / liveRefPrice) * 100).toFixed(2)}% dist
                          </span>
                        )}
                      </div>
                      <div>
                        <span className="text-[9px] text-slate-500 block uppercase">Take Profit</span>
                        <span className="text-base font-bold text-emerald-400 font-mono">${pos.take_profit?.toLocaleString() || '—'}</span>
                        {pos.take_profit && liveRefPrice && (
                          <span className="text-[9px] text-slate-500 block font-mono">
                            {(((pos.take_profit - liveRefPrice) / liveRefPrice) * 100).toFixed(2)}% dist
                          </span>
                        )}
                      </div>
                      <div>
                        <div className="flex items-center justify-between">
                          <span className="text-[9px] text-slate-500 uppercase">Live Spot Price</span>
                          <span className={`text-[8px] font-bold px-1 rounded ${isGold ? 'bg-amber-950 text-amber-300' : 'bg-sky-950 text-sky-300'}`}>
                            {isGold ? 'OANDA' : 'BINANCE'}
                          </span>
                        </div>
                        <span className={`text-base font-bold font-mono transition-colors ${
                          isGold
                            ? (goldPriceFlash === 'up' ? 'text-emerald-300' : goldPriceFlash === 'down' ? 'text-rose-300' : 'text-amber-400')
                            : (btcPriceFlash === 'up' ? 'text-emerald-300' : btcPriceFlash === 'down' ? 'text-rose-300' : 'text-sky-400')
                        }`}>
                          ${liveRefPrice ? liveRefPrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '—'}
                        </span>
                      </div>
                    </div>

                    {/* Live Floating PnL Card */}
                    <div className={`flex items-center justify-between p-3 rounded-lg border ${
                      floatingPnl >= 0 ? 'bg-emerald-950/30 border-emerald-700/50' : 'bg-rose-950/30 border-rose-700/50'
                    }`}>
                      <div>
                        <span className="text-[10px] text-slate-400 block uppercase font-bold">Unrealized Floating PnL</span>
                        <span className={`text-2xl font-bold font-mono ${pnlColor(floatingPnl)}`}>
                          {floatingPnl >= 0 ? '+' : ''}{floatingPnl.toFixed(2)}%
                        </span>
                      </div>

                      {/* Manual Close Button */}
                      <button
                        onClick={() => handleClosePosition(pos, 'MANUAL_CLOSE')}
                        disabled={actionLoading}
                        className="px-3 py-1.5 rounded bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs transition-all shadow"
                      >
                        Close Position
                      </button>
                    </div>

                    {/* AI Reasoning */}
                    <div className="text-xs text-slate-300 bg-slate-900/40 p-2.5 rounded border border-slate-800">
                      <div className="text-[10px] font-bold text-indigo-400 mb-1 flex items-center gap-1">
                        <MessageSquare className="w-3 h-3" /> QUANT THESIS &amp; TRIGGER:
                      </div>
                      <p className="leading-relaxed text-[11px]">
                        {pos.reasoning_md || pos.annotation || 'Quantitative absorption setup detected with statistical confirmation.'}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="py-8 text-center text-xs text-slate-400 space-y-2">
              <Activity className="w-8 h-8 mx-auto text-slate-600 animate-pulse" />
              <div className="font-bold text-slate-300">
                No open positions matching current filter scope.
              </div>
              <div className="text-[11px] text-slate-500">
                {isRunning
                  ? 'Bot supervisor is actively running and streaming real-time regime telemetry.'
                  : 'Bot supervisor is currently idle. Click "Start Bot" in the top header toolbar to start.'}
              </div>
            </div>
          )}
        </div>

        {/* ── SIGNAL HISTORY & AUDIT FEED ── */}
        <div className={`border rounded-xl p-5 ${isDark ? 'bg-[#161b22] border-[#30363d]' : 'bg-white border-slate-200 shadow-sm'}`}>
          <div className="flex items-center justify-between border-b pb-3 mb-4 border-slate-700/50">
            <span className="font-bold text-sm flex items-center gap-2 text-indigo-400">
              <Clock className="w-4 h-4" />
              SIGNAL TELEMETRY &amp; AUDIT FEED
            </span>
            <span className="text-xs text-slate-400">
              {allSignals.length} Total Signals Recorded {selectedStratTab !== 'ALL' ? `for ${selectedStratTab}` : 'across Portfolio'}
            </span>
          </div>

          <div className="overflow-x-auto max-h-96 overflow-y-auto border border-slate-800 rounded-lg">
            <table className="w-full text-left text-xs font-mono">
              <thead className={`sticky top-0 ${isDark ? 'bg-[#0d1117] text-slate-300' : 'bg-slate-100 text-slate-700'}`}>
                <tr>
                  <th className="p-2.5 border-b border-slate-800">#</th>
                  <th className="p-2.5 border-b border-slate-800">Time</th>
                  <th className="p-2.5 border-b border-slate-800">Strategy</th>
                  <th className="p-2.5 border-b border-slate-800">Pair</th>
                  <th className="p-2.5 border-b border-slate-800">Action</th>
                  <th className="p-2.5 border-b border-slate-800">Entry</th>
                  <th className="p-2.5 border-b border-slate-800">SL</th>
                  <th className="p-2.5 border-b border-slate-800">TP</th>
                  <th className="p-2.5 border-b border-slate-800">Exit Reason</th>
                  <th className="p-2.5 border-b border-slate-800">Net PnL</th>
                  <th className="p-2.5 border-b border-slate-800">Status</th>
                  <th className="p-2.5 border-b border-slate-800 text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {allSignals.length === 0 ? (
                  <tr>
                    <td colSpan={12} className="p-6 text-center text-slate-500">
                      No signals recorded yet under selected filter scope.
                    </td>
                  </tr>
                ) : allSignals.map((sig, idx) => {
                  const isLong = (sig.side || sig.action) === 'LONG' || sig.action === 'BUY';
                  const pnl = sig.pnl_pct ?? 0.0;
                  const isOpen = sig.status === 'ACTIVE_IN_POSITION';
                  const isGold = (sig.pair || '').toUpperCase().includes('XAU');

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
                      <td className="p-2.5 text-indigo-400 font-bold">
                        {(sig.strategy || cleanSelectedName).replace('Strategy', '')}
                      </td>
                      <td className="p-2.5">
                        <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                          isGold ? 'bg-amber-950/80 text-amber-300 border border-amber-700' : 'bg-sky-950/80 text-sky-300 border border-sky-700'
                        }`}>
                          {sig.pair || (isGold ? 'XAU/USD' : 'BTC/USDT')}
                        </span>
                      </td>
                      <td className="p-2.5">
                        <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                          isLong ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'bg-rose-950 text-rose-400 border border-rose-800'
                        }`}>
                          {isLong ? '⬆ LONG' : '⬇ SHORT'}
                        </span>
                      </td>
                      <td className="p-2.5 text-sky-400 font-bold">${sig.price ? sig.price.toLocaleString() : '—'}</td>
                      <td className="p-2.5 text-rose-400">${sig.stop_loss ? sig.stop_loss.toLocaleString() : '—'}</td>
                      <td className="p-2.5 text-emerald-400">${sig.take_profit ? sig.take_profit.toLocaleString() : '—'}</td>
                      <td className="p-2.5">
                        <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${
                          sig.exit_reason === 'TAKE_PROFIT'
                            ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                            : sig.exit_reason === 'STOP_LOSS'
                            ? 'bg-rose-950 text-rose-400 border border-rose-800'
                            : 'bg-slate-800 text-slate-300'
                        }`}>
                          {sig.exit_reason || (isOpen ? 'IN PROGRESS' : 'CLOSED')}
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
                      <td className="p-2.5 text-right">
                        {isOpen && (
                          <button
                            onClick={() => handleClosePosition(sig, 'MANUAL_CLOSE')}
                            disabled={actionLoading}
                            className="px-2 py-0.5 rounded bg-rose-950 border border-rose-700 text-rose-300 hover:bg-rose-900 transition-all text-[10px] font-bold"
                          >
                            Close
                          </button>
                        )}
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

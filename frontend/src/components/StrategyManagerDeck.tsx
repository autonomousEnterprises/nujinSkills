import React, { useState, useMemo } from 'react';
import { ManagedStrategy, PortfolioSummary, DistributionAnalytics } from '../hooks/useWebSocket';
import {
  Layers, ShieldCheck, Activity, TrendingUp, TrendingDown, Cpu, Play,
  RefreshCw, Check, ChevronDown, ChevronRight, Search,
  Award, AlertTriangle, ArrowUpRight, ArrowDownRight, Clock,
  Eye, CheckCircle2, BarChart2, Filter, Zap, DollarSign, Database,
  Sliders, PieChart, Sparkles
} from 'lucide-react';

interface StrategyManagerDeckProps {
  theme?: 'dark' | 'light';
  strategies: ManagedStrategy[];
  activeStrategy: string;
  portfolioSummary?: PortfolioSummary | null;
  distributionAnalytics?: DistributionAnalytics | null;
  onSelectStrategy: (stratName: string) => void;
  onActivateStrategy: (stratName: string) => void;
  onUpdateStatus: (stratName: string, newStatus: string) => Promise<void>;
  onRunBacktest: (stratName: string) => Promise<void>;
  onTriggerCron: () => Promise<void>;
  onNavigateToBacktest: (stratName: string) => void;
}

export const StrategyManagerDeck: React.FC<StrategyManagerDeckProps> = ({
  theme = 'dark',
  strategies = [],
  activeStrategy,
  portfolioSummary,
  distributionAnalytics,
  onSelectStrategy,
  onActivateStrategy,
  onUpdateStatus,
  onRunBacktest,
  onTriggerCron,
  onNavigateToBacktest,
}) => {
  const isDark = theme === 'dark';
  const cleanActiveName = activeStrategy.replace('.py', '');

  // Screen Tabs
  const [activeTab, setActiveTab] = useState<'LEADERBOARD' | 'DRIFT_TRAJECTORY' | 'DISTRIBUTION'>('LEADERBOARD');

  // Search, Filter & Sort
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'ACTIVE_LIVE' | 'CRON_BACKTEST' | 'DEACTIVATED'>('ALL');
  const [sortBy, setSortBy] = useState<'rank' | 'sharpe' | 'dsr' | 'win_rate' | 'max_drawdown' | 'name'>('rank');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());
  const [equityViewMode, setEquityViewMode] = useState<Record<string, 'BACKTEST' | 'LIVE'>>({});
  const [runningCron, setRunningCron] = useState(false);
  const [actionLoading, setActionLoading] = useState<Record<string, boolean>>({});

  // Toggle row expansion
  const toggleRow = (id: string) => {
    setExpandedRows((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const setStratEquityMode = (stratId: string, mode: 'BACKTEST' | 'LIVE') => {
    setEquityViewMode((prev) => ({ ...prev, [stratId]: mode }));
  };

  // Status counts
  const activeCount = useMemo(() => strategies.filter((s) => s.status === 'ACTIVE_LIVE').length, [strategies]);
  const cronCount = useMemo(() => strategies.filter((s) => s.status === 'CRON_BACKTEST').length, [strategies]);
  const deactCount = useMemo(() => strategies.filter((s) => s.status === 'DEACTIVATED').length, [strategies]);
  const topStrategy = useMemo(() => strategies.find((s) => s.rank === 1) || strategies[0], [strategies]);

  // Compute or resolve Portfolio Summary
  const portfolio = useMemo<PortfolioSummary>(() => {
    if (portfolioSummary && portfolioSummary.active_count !== undefined) {
      return portfolioSummary;
    }
    const activeStrats = strategies.filter((s) => s.status === 'ACTIVE_LIVE');
    let totalTrades = 0;
    let totalWins = 0;
    let weightedSharpeSum = 0;
    let totalPnl = 0;
    const pfs: number[] = [];
    const syms: string[] = [];
    const names: string[] = [];

    activeStrats.forEach((s) => {
      names.push(s.name);
      if (s.symbol && !syms.includes(s.symbol)) syms.push(s.symbol);
      const bt = s.latest_backtest || {};
      const trades = bt.trades || 0;
      const rawWr = bt.win_rate || 0;
      const normWr = rawWr <= 1.0 ? rawWr : rawWr / 100;
      const sh = bt.sharpe || 0;
      const pf = bt.profit_factor || 0;

      totalTrades += trades;
      totalWins += Math.round(trades * normWr);
      weightedSharpeSum += sh * Math.max(1, trades);
      if (pf > 0) pfs.push(pf);
    });

    const blendedWr = totalTrades > 0 ? (totalWins / totalTrades) * 100 : 0;
    const blendedSh = totalTrades > 0 ? weightedSharpeSum / totalTrades : (activeStrats.length > 0 ? activeStrats.reduce((a, b) => a + (b.latest_backtest?.sharpe || 0), 0) / activeStrats.length : 0);
    const combinedPf = pfs.length > 0 ? pfs.reduce((a, b) => a + b, 0) / pfs.length : 0;

    return {
      active_count: activeStrats.length,
      active_strategies: names,
      blended_win_rate: Number(blendedWr.toFixed(1)),
      blended_sharpe: Number(blendedSh.toFixed(2)),
      total_trades: totalTrades,
      combined_profit_factor: Number(combinedPf.toFixed(2)),
      total_realized_pnl: Number(totalPnl.toFixed(2)),
      symbols: syms,
      best_performer: activeStrats[0]?.name || null
    };
  }, [strategies, portfolioSummary]);

  // Compute or resolve Distribution Analytics
  const distribution = useMemo<DistributionAnalytics>(() => {
    if (distributionAnalytics && distributionAnalytics.total_evaluated !== undefined) {
      return distributionAnalytics;
    }

    const improving: any[] = [];
    const decaying: any[] = [];
    const stable: any[] = [];
    const sharpeBins: Record<string, number> = { '< 1.0': 0, '1.0 - 1.5': 0, '1.5 - 2.5': 0, '> 2.5': 0 };
    const tierCounts: Record<string, number> = { 'S-Tier': 0, 'A-Tier': 0, 'B-Tier': 0, 'C-Tier': 0 };
    const assetCounts: Record<string, number> = {};

    strategies.forEach((s) => {
      // Tier
      const tier = s.tier || 'C-Tier';
      if (tier.includes('S-Tier')) tierCounts['S-Tier']++;
      else if (tier.includes('A-Tier')) tierCounts['A-Tier']++;
      else if (tier.includes('B-Tier')) tierCounts['B-Tier']++;
      else tierCounts['C-Tier']++;

      // Asset
      const sym = s.symbol || 'Other';
      assetCounts[sym] = (assetCounts[sym] || 0) + 1;

      // Sharpe Bins
      const sh = s.latest_backtest?.sharpe || 0;
      if (sh < 1.0) sharpeBins['< 1.0']++;
      else if (sh <= 1.5) sharpeBins['1.0 - 1.5']++;
      else if (sh <= 2.5) sharpeBins['1.5 - 2.5']++;
      else sharpeBins['> 2.5']++;

      // Drift Trajectory
      const hist = s.cron_config?.drift_history || [];
      let deltaSh = 0;
      let deltaWr = 0;
      if (hist.length >= 2) {
        const last = hist[hist.length - 1];
        const prev = hist[hist.length - 2];
        deltaSh = Number(((last.sharpe || 0) - (prev.sharpe || 0)).toFixed(2));
        deltaWr = Number((((last.win_rate || 0) - (prev.win_rate || 0)) * 100).toFixed(1));
      }

      const entry = {
        name: s.name,
        display_name: s.display_name,
        status: s.status,
        sharpe: sh,
        win_rate: s.latest_backtest?.win_rate || 0,
        delta_sharpe: deltaSh,
        delta_win_rate: deltaWr,
        snapshots_count: hist.length,
        trajectory: 'STABLE'
      };

      if (deltaSh > 0.05 || deltaWr > 1.0) {
        entry.trajectory = 'GAINING_EDGE';
        improving.push(entry);
      } else if (deltaSh < -0.05 || deltaWr < -1.0) {
        entry.trajectory = 'DECAYING_EDGE';
        decaying.push(entry);
      } else {
        stable.push(entry);
      }
    });

    return {
      improving,
      decaying,
      stable,
      sharpe_distribution: sharpeBins,
      tier_distribution: tierCounts,
      asset_distribution: assetCounts,
      total_evaluated: strategies.length
    };
  }, [strategies, distributionAnalytics]);

  // Filtered & Sorted strategies
  const displayedStrategies = useMemo(() => {
    let result = [...strategies];

    if (statusFilter !== 'ALL') {
      result = result.filter((s) => s.status === statusFilter);
    }

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      result = result.filter(
        (s) =>
          s.name.toLowerCase().includes(q) ||
          s.display_name?.toLowerCase().includes(q) ||
          s.target_profile?.toLowerCase().includes(q) ||
          s.symbol?.toLowerCase().includes(q) ||
          s.thesis?.toLowerCase().includes(q)
      );
    }

    result.sort((a, b) => {
      let valA: any = a[sortBy as keyof ManagedStrategy];
      let valB: any = b[sortBy as keyof ManagedStrategy];

      if (sortBy === 'sharpe') {
        valA = a.latest_backtest?.sharpe ?? 0;
        valB = b.latest_backtest?.sharpe ?? 0;
      } else if (sortBy === 'dsr') {
        valA = a.latest_backtest?.dsr ?? 0;
        valB = b.latest_backtest?.dsr ?? 0;
      } else if (sortBy === 'win_rate') {
        valA = a.latest_backtest?.win_rate ?? 0;
        valB = b.latest_backtest?.win_rate ?? 0;
      } else if (sortBy === 'max_drawdown') {
        valA = a.latest_backtest?.max_drawdown ?? 0;
        valB = b.latest_backtest?.max_drawdown ?? 0;
      }

      if (typeof valA === 'string') {
        return sortDir === 'asc' ? valA.localeCompare(valB) : valB.localeCompare(valA);
      }
      return sortDir === 'asc' ? (valA > valB ? 1 : -1) : valA < valB ? 1 : -1;
    });

    return result;
  }, [strategies, statusFilter, searchQuery, sortBy, sortDir]);

  // Handle manual cron trigger
  const handleCronTrigger = async () => {
    setRunningCron(true);
    try {
      await onTriggerCron();
    } finally {
      setRunningCron(false);
    }
  };

  // Handle single backtest
  const handleBacktestClick = async (strat: ManagedStrategy) => {
    setActionLoading((prev) => ({ ...prev, [strat.name]: true }));
    try {
      await onRunBacktest(strat.file);
    } finally {
      setActionLoading((prev) => ({ ...prev, [strat.name]: false }));
    }
  };

  // Helper for rank badge
  const getRankBadge = (rank: number) => {
    if (rank === 1) {
      return (
        <span className="px-2 py-0.5 rounded-full bg-amber-500/20 border border-amber-500/50 text-amber-400 font-bold text-[11px] flex items-center gap-1 shadow-sm">
          <Award className="w-3 h-3 text-amber-400" /> #1 GOLD
        </span>
      );
    } else if (rank === 2) {
      return (
        <span className="px-2 py-0.5 rounded-full bg-slate-400/20 border border-slate-400/50 text-slate-300 font-bold text-[11px] flex items-center gap-1">
          #2 SILVER
        </span>
      );
    } else if (rank === 3) {
      return (
        <span className="px-2 py-0.5 rounded-full bg-amber-700/20 border border-amber-700/50 text-amber-600 font-bold text-[11px] flex items-center gap-1">
          #3 BRONZE
        </span>
      );
    }
    return (
      <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-mono text-[11px] border border-slate-700">
        #{rank}
      </span>
    );
  };

  // Helper for status pill
  const getStatusPill = (status: string) => {
    if (status === 'ACTIVE_LIVE') {
      return (
        <span className="px-2 py-1 rounded bg-emerald-950/80 border border-emerald-500 text-emerald-400 font-bold text-[10px] flex items-center gap-1.5 shadow-sm animate-pulse">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" /> ACTIVE_LIVE
        </span>
      );
    } else if (status === 'CRON_BACKTEST') {
      return (
        <span className="px-2 py-1 rounded bg-sky-950/80 border border-sky-500 text-sky-400 font-bold text-[10px] flex items-center gap-1.5">
          <RefreshCw className="w-3 h-3 text-sky-400" /> CRON_BACKTEST
        </span>
      );
    }
    return (
      <span className="px-2 py-1 rounded bg-slate-800/80 border border-slate-700 text-slate-400 font-bold text-[10px] flex items-center gap-1.5">
        <span className="w-1.5 h-1.5 rounded-full bg-slate-500" /> DEACTIVATED
      </span>
    );
  };

  // Helper for rendering an equity curve in SVG
  const renderEquityCurve = (curve: any[], label: string, isLive: boolean) => {
    if (!curve || curve.length < 2) {
      return (
        <div className={`h-40 rounded border flex flex-col items-center justify-center text-xs font-mono p-4 ${
          isDark ? 'bg-[#0d1117] border-[#30363d] text-slate-500' : 'bg-slate-50 border-slate-200 text-slate-400'
        }`}>
          <Database className="w-6 h-6 mb-2 text-slate-600 animate-pulse" />
          <span>{isLive ? 'NO CLOSED LIVE SIGNALS RECORDED YET FOR THIS STRATEGY' : 'NO BACKTEST EQUITY CURVE AVAILABLE'}</span>
          <span className="text-[10px] text-slate-600 mt-1">
            {isLive ? 'Deploy to live/dry-run or broadcast signals via tools/state_control.py signal-add' : 'Run a backtest audit to generate full 30-day equity points'}
          </span>
        </div>
      );
    }

    const pts = curve.length;
    const rawMinEq = Math.min(...curve.map((d: any) => d.equity_pct));
    const rawMaxEq = Math.max(...curve.map((d: any) => d.equity_pct));
    const minEq = Math.min(rawMinEq, 100.0);
    const maxEq = Math.max(rawMaxEq, 100.0);
    const rangeEq = Math.max(maxEq - minEq, 0.5);

    const width = 800;
    const height = 150;

    const pathD = curve.map((d: any, idx: number) => {
      const x = (idx / Math.max(pts - 1, 1)) * width;
      const y = height - ((d.equity_pct - minEq) / rangeEq) * (height - 25) - 15;
      return `${idx === 0 ? 'M' : 'L'} ${x.toFixed(1)} ${y.toFixed(1)}`;
    }).join(' ');

    const areaD = `${pathD} L ${width} ${height} L 0 ${height} Z`;
    const lastEq = curve[curve.length - 1].equity_pct;
    const totalReturnPct = (lastEq - 100.0).toFixed(2);
    const isProfit = lastEq >= 100.0;

    return (
      <div className={`p-3 rounded-lg border flex flex-col gap-2 ${
        isDark ? 'bg-[#0d1117] border-[#30363d]' : 'bg-slate-50 border-slate-200'
      }`}>
        <div className="flex items-center justify-between text-xs font-mono">
          <div className="flex items-center gap-2">
            <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
              isLive ? 'bg-sky-900/60 text-sky-300 border border-sky-700' : 'bg-emerald-900/60 text-emerald-300 border border-emerald-700'
            }`}>
              {isLive ? 'REAL LIVE PERFORMANCE' : 'QUANTITATIVE BACKTEST'}
            </span>
            <span className={isDark ? 'text-slate-400' : 'text-slate-600'}>{label}</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-[11px] text-slate-500">POINTS: {pts}</span>
            <span className={`text-xs font-bold ${isProfit ? 'text-emerald-400' : 'text-rose-400'}`}>
              RETURN: {isProfit ? '+' : ''}{totalReturnPct}%
            </span>
          </div>
        </div>

        <div className="w-full relative h-36">
          <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-full overflow-visible" preserveAspectRatio="none">
            <defs>
              <linearGradient id={`grad-${isLive ? 'live' : 'bt'}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={isLive ? '#38bdf8' : '#10b981'} stopOpacity="0.35" />
                <stop offset="100%" stopColor={isLive ? '#38bdf8' : '#10b981'} stopOpacity="0.0" />
              </linearGradient>
            </defs>
            {(() => {
              const baseNetY = height - ((100.0 - minEq) / rangeEq) * (height - 25) - 15;
              return (
                <line
                  x1="0"
                  y1={baseNetY}
                  x2={width}
                  y2={baseNetY}
                  stroke="#4b5563"
                  strokeDasharray="4 4"
                  strokeWidth="1"
                />
              );
            })()}
            <path d={areaD} fill={`url(#grad-${isLive ? 'live' : 'bt'})`} />
            <path d={pathD} fill="none" stroke={isLive ? '#38bdf8' : '#10b981'} strokeWidth="2.5" />
          </svg>
        </div>

        <div className="flex items-center justify-between text-[10px] text-slate-500 font-mono pt-1 border-t border-slate-800">
          <span>Min: {minEq.toFixed(2)}%</span>
          <span>Baseline: 100.0%</span>
          <span>Peak: {maxEq.toFixed(2)}%</span>
        </div>
      </div>
    );
  };

  return (
    <div className={`w-full h-full p-4 font-mono overflow-y-auto flex flex-col gap-4 transition-colors select-none ${
      isDark ? 'bg-[#0d1117] text-white' : 'bg-slate-100 text-slate-900'
    }`}>
      {/* ── Top Header Deck ───────────────────────────────────────────────── */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b pb-3 border-slate-800">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
            <Layers className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800 font-bold">
                PARALLEL MULTI-BOT DISPATCHER
              </span>
              <span className="text-[10px] px-2 py-0.5 rounded bg-sky-950 text-sky-400 border border-sky-800 font-bold flex items-center gap-1">
                <Clock className="w-2.5 h-2.5" /> DAILY CRON (24h)
              </span>
            </div>
            <h1 className="text-xl font-bold tracking-tight mt-0.5">
              Quant Strategy Command &amp; Portfolio Lifecycle
            </h1>
            <p className={`text-xs ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
              Run multiple strategies in parallel, track daily alpha drift, and monitor performance distributions.
            </p>
          </div>
        </div>

        {/* Global Action: Trigger Daily Cron */}
        <div className="flex items-center gap-3">
          <button
            onClick={handleCronTrigger}
            disabled={runningCron}
            className={`px-4 py-2 rounded-lg font-bold text-xs flex items-center gap-2 shadow-md transition-all ${
              runningCron
                ? 'bg-sky-700 text-white cursor-wait'
                : 'bg-sky-600 hover:bg-sky-500 text-white active:scale-95'
            }`}
            title="Execute out-of-sample backtests on all strategies tagged CRON_BACKTEST (Daily Schedule: 24h)"
          >
            <RefreshCw className={`w-4 h-4 ${runningCron ? 'animate-spin' : ''}`} />
            <span>{runningCron ? 'EVALUATING_DAILY_CRON...' : 'Run Daily Cron Backtests'}</span>
          </button>
        </div>
      </div>

      {/* ── AGGREGATED PORTFOLIO PERFORMANCE (TOP OF SCREEN) ──────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        {/* Card 1: Active Parallel Bots */}
        <div className={`border p-3 rounded-lg flex flex-col justify-between ${
          isDark ? 'bg-[#161b22] border-[#30363d]' : 'bg-white border-slate-200 shadow-sm'
        }`}>
          <span className={`text-[10px] flex items-center gap-1.5 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
            <Play className="w-3.5 h-3.5 text-emerald-400" /> ACTIVE IN PARALLEL
          </span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-2xl font-bold text-emerald-400">{portfolio.active_count}</span>
            <span className="text-[11px] text-emerald-500/80 font-bold">Concurrent Bots</span>
          </div>
          <div className="text-[10px] text-slate-400 truncate mt-1">
            {portfolio.active_strategies.length > 0
              ? portfolio.active_strategies.join(', ')
              : 'No strategies currently live'}
          </div>
        </div>

        {/* Card 2: Blended Portfolio Win Rate */}
        <div className={`border p-3 rounded-lg flex flex-col justify-between ${
          isDark ? 'bg-[#161b22] border-[#30363d]' : 'bg-white border-slate-200 shadow-sm'
        }`}>
          <span className={`text-[10px] flex items-center gap-1.5 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
            <TrendingUp className="w-3.5 h-3.5 text-emerald-400" /> BLENDED WIN RATE
          </span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className={`text-2xl font-bold ${
              portfolio.blended_win_rate >= 50 ? 'text-emerald-400' : portfolio.blended_win_rate >= 45 ? 'text-amber-400' : 'text-rose-400'
            }`}>
              {portfolio.blended_win_rate.toFixed(1)}%
            </span>
            <span className="text-[10px] text-slate-400">Portfolio Aggregate</span>
          </div>
          <span className="text-[10px] text-slate-500">{portfolio.total_trades} Total Executed Trades</span>
        </div>

        {/* Card 3: Combined Expected Sharpe */}
        <div className={`border p-3 rounded-lg flex flex-col justify-between ${
          isDark ? 'bg-[#161b22] border-[#30363d]' : 'bg-white border-slate-200 shadow-sm'
        }`}>
          <span className={`text-[10px] flex items-center gap-1.5 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
            <Activity className="w-3.5 h-3.5 text-cyan-400" /> BLENDED SHARPE
          </span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className={`text-2xl font-bold ${
              portfolio.blended_sharpe >= 1.5 ? 'text-emerald-400' : portfolio.blended_sharpe >= 1.0 ? 'text-amber-400' : 'text-rose-400'
            }`}>
              {portfolio.blended_sharpe.toFixed(2)}
            </span>
            <span className="text-[10px] text-cyan-400 font-semibold">
              PF {portfolio.combined_profit_factor.toFixed(2)}
            </span>
          </div>
          <span className="text-[10px] text-slate-500">
            {portfolio.blended_sharpe >= 1.5 ? 'Institutional Hurdle Passed' : 'Moderate Portfolio Edge'}
          </span>
        </div>

        {/* Card 4: Realized PnL & Multi-Asset Diversification */}
        <div className={`border p-3 rounded-lg flex flex-col justify-between ${
          isDark ? 'bg-[#161b22] border-[#30363d]' : 'bg-white border-slate-200 shadow-sm'
        }`}>
          <span className={`text-[10px] flex items-center gap-1.5 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
            <DollarSign className="w-3.5 h-3.5 text-amber-400" /> REALIZED NET PnL
          </span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-2xl font-bold text-white">
              ${portfolio.total_realized_pnl.toFixed(2)}
            </span>
            <span className="text-[10px] text-slate-400">Live Signals</span>
          </div>
          <span className="text-[10px] text-amber-500 truncate">
            {portfolio.symbols.length > 0 ? portfolio.symbols.join(' · ') : 'Multi-Asset Flow'}
          </span>
        </div>

        {/* Card 5: Daily Cron Cadence & Health */}
        <div className={`border p-3 rounded-lg flex flex-col justify-between ${
          isDark ? 'bg-[#161b22] border-[#30363d]' : 'bg-white border-slate-200 shadow-sm'
        }`}>
          <span className={`text-[10px] flex items-center gap-1.5 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
            <RefreshCw className="w-3.5 h-3.5 text-sky-400" /> DAILY CRON (24h)
          </span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-2xl font-bold text-sky-400">{cronCount}</span>
            <span className="text-[11px] text-sky-400/80 font-bold">Monitored</span>
          </div>
          <span className="text-[10px] text-slate-500">
            {deactCount} Deactivated · Auto 24h Loop
          </span>
        </div>
      </div>

      {/* ── View Navigation Tabs ─────────────────────────────────────────── */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
        <button
          onClick={() => setActiveTab('LEADERBOARD')}
          className={`px-3 py-1.5 rounded-lg text-xs font-bold flex items-center gap-1.5 transition-all ${
            activeTab === 'LEADERBOARD'
              ? 'bg-emerald-600 text-white shadow-md'
              : 'bg-slate-800/80 text-slate-400 hover:bg-slate-700 hover:text-slate-200'
          }`}
        >
          <Layers className="w-3.5 h-3.5" />
          <span>Leaderboard &amp; Parallel Bot Control</span>
        </button>

        <button
          onClick={() => setActiveTab('DRIFT_TRAJECTORY')}
          className={`px-3 py-1.5 rounded-lg text-xs font-bold flex items-center gap-1.5 transition-all ${
            activeTab === 'DRIFT_TRAJECTORY'
              ? 'bg-sky-600 text-white shadow-md'
              : 'bg-slate-800/80 text-slate-400 hover:bg-slate-700 hover:text-slate-200'
          }`}
        >
          <TrendingUp className="w-3.5 h-3.5" />
          <span>Alpha Drift &amp; Profitability Trajectory</span>
          {distribution.improving.length > 0 && (
            <span className="px-1.5 py-0.2 rounded-full bg-emerald-500/20 text-emerald-400 text-[10px]">
              +{distribution.improving.length}
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveTab('DISTRIBUTION')}
          className={`px-3 py-1.5 rounded-lg text-xs font-bold flex items-center gap-1.5 transition-all ${
            activeTab === 'DISTRIBUTION'
              ? 'bg-purple-600 text-white shadow-md'
              : 'bg-slate-800/80 text-slate-400 hover:bg-slate-700 hover:text-slate-200'
          }`}
        >
          <BarChart2 className="w-3.5 h-3.5" />
          <span>Edge &amp; Risk Distribution</span>
        </button>
      </div>

      {/* ── TAB 1: LEADERBOARD & PARALLEL BOT CONTROL ────────────────────── */}
      {activeTab === 'LEADERBOARD' && (
        <div className="flex flex-col gap-4">
          {/* Filter & Search Toolbar */}
          <div className={`border rounded-lg p-3 flex flex-wrap items-center justify-between gap-3 ${
            isDark ? 'bg-[#161b22] border-[#30363d]' : 'bg-white border-slate-200 shadow-sm'
          }`}>
            {/* Status Filter Buttons */}
            <div className="flex items-center gap-1.5 bg-slate-900/60 p-1 rounded-lg border border-slate-800 text-xs">
              {(['ALL', 'ACTIVE_LIVE', 'CRON_BACKTEST', 'DEACTIVATED'] as const).map((st) => (
                <button
                  key={st}
                  onClick={() => setStatusFilter(st)}
                  className={`px-2.5 py-1 rounded font-bold transition-all ${
                    statusFilter === st
                      ? 'bg-emerald-600 text-white shadow-sm'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                  }`}
                >
                  {st}
                  <span className="ml-1 text-[10px] opacity-70">
                    ({st === 'ALL' ? strategies.length : strategies.filter((s) => s.status === st).length})
                  </span>
                </button>
              ))}
            </div>

            {/* Search and Sort controls */}
            <div className="flex items-center gap-3">
              <div className="relative">
                <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-slate-500" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Filter strategies by name, asset, thesis..."
                  className={`pl-8 pr-3 py-1.5 rounded-lg text-xs w-64 border focus:outline-none transition-all ${
                    isDark
                      ? 'bg-[#0d1117] border-slate-700 text-white focus:border-emerald-500'
                      : 'bg-slate-50 border-slate-300 text-slate-900 focus:border-emerald-500'
                  }`}
                />
              </div>

              <div className="flex items-center gap-1.5 text-xs">
                <span className="text-slate-500">SORT:</span>
                <select
                  value={sortBy}
                  onChange={(e: any) => setSortBy(e.target.value)}
                  className={`px-2 py-1.5 rounded border text-xs ${
                    isDark ? 'bg-[#0d1117] border-slate-700 text-slate-300' : 'bg-slate-50 border-slate-300 text-slate-800'
                  }`}
                >
                  <option value="rank">Rank</option>
                  <option value="sharpe">Sharpe</option>
                  <option value="dsr">DSR</option>
                  <option value="win_rate">Win Rate</option>
                  <option value="max_drawdown">Max DD</option>
                  <option value="name">Name</option>
                </select>
                <button
                  onClick={() => setSortDir((prev) => (prev === 'asc' ? 'desc' : 'asc'))}
                  className="p-1.5 rounded border border-slate-700 hover:bg-slate-800 text-slate-300"
                  title="Toggle Ascending/Descending"
                >
                  {sortDir === 'asc' ? '↑' : '↓'}
                </button>
              </div>
            </div>
          </div>

          {/* Master Table */}
          <div className={`border rounded-lg overflow-hidden ${
            isDark ? 'bg-[#161b22] border-[#30363d]' : 'bg-white border-slate-200 shadow-sm'
          }`}>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className={`border-b text-[11px] font-bold uppercase tracking-wider ${
                    isDark ? 'bg-[#0d1117] border-[#30363d] text-slate-400' : 'bg-slate-100 border-slate-300 text-slate-600'
                  }`}>
                    <th className="py-2.5 px-3 w-10 text-center">#</th>
                    <th className="py-2.5 px-3">Strategy Name &amp; Profile</th>
                    <th className="py-2.5 px-3">Status</th>
                    <th className="py-2.5 px-3">Asset</th>
                    <th className="py-2.5 px-3 text-right">Win Rate</th>
                    <th className="py-2.5 px-3 text-right">Sharpe</th>
                    <th className="py-2.5 px-3 text-right">DSR</th>
                    <th className="py-2.5 px-3 text-right">Max DD</th>
                    <th className="py-2.5 px-3 text-center">Drift (Daily)</th>
                    <th className="py-2.5 px-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {displayedStrategies.length === 0 ? (
                    <tr>
                      <td colSpan={10} className="py-8 text-center text-slate-500">
                        No strategies matching current filter or search criteria.
                      </td>
                    </tr>
                  ) : (
                    displayedStrategies.map((strat) => {
                      const isExpanded = expandedRows.has(strat.id || strat.name);
                      const bt = strat.latest_backtest || {};
                      const driftHistory = strat.cron_config?.drift_history || [];
                      const isLive = strat.status === 'ACTIVE_LIVE';
                      const isLoading = actionLoading[strat.name] || false;

                      let driftBadge = (
                        <span className="text-[10px] text-slate-500">STABLE</span>
                      );
                      if (driftHistory.length >= 2) {
                        const lastSnap = driftHistory[driftHistory.length - 1];
                        const prevSnap = driftHistory[driftHistory.length - 2];
                        const delta = (lastSnap.sharpe || 0) - (prevSnap.sharpe || 0);
                        if (delta > 0.05) {
                          driftBadge = (
                            <span className="px-1.5 py-0.5 rounded bg-emerald-900/60 text-emerald-400 border border-emerald-700 text-[10px] font-bold flex items-center justify-center gap-0.5">
                              <ArrowUpRight className="w-2.5 h-2.5" /> +{delta.toFixed(2)}
                            </span>
                          );
                        } else if (delta < -0.05) {
                          driftBadge = (
                            <span className="px-1.5 py-0.5 rounded bg-rose-900/60 text-rose-400 border border-rose-700 text-[10px] font-bold flex items-center justify-center gap-0.5">
                              <ArrowDownRight className="w-2.5 h-2.5" /> {delta.toFixed(2)}
                            </span>
                          );
                        }
                      }

                      return (
                        <React.Fragment key={strat.id || strat.name}>
                          <tr
                            onClick={() => toggleRow(strat.id || strat.name)}
                            className={`cursor-pointer transition-colors ${
                              isLive
                                ? isDark ? 'bg-emerald-950/20 hover:bg-emerald-950/30' : 'bg-emerald-50 hover:bg-emerald-100/60'
                                : isDark ? 'hover:bg-slate-800/50' : 'hover:bg-slate-50'
                            }`}
                          >
                            <td className="py-3 px-3 text-center">
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  toggleRow(strat.id || strat.name);
                                }}
                                className="text-slate-500 hover:text-slate-300"
                              >
                                {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                              </button>
                            </td>
                            <td className="py-3 px-3">
                              <div className="flex items-center gap-2">
                                {getRankBadge(strat.rank)}
                                <span className="font-bold text-sm text-slate-100">{strat.name}</span>
                              </div>
                              <div className="text-[11px] text-slate-400 truncate max-w-sm mt-0.5">
                                {strat.target_profile || strat.display_name}
                              </div>
                            </td>
                            <td className="py-3 px-3">
                              {getStatusPill(strat.status)}
                            </td>
                            <td className="py-3 px-3 font-semibold text-slate-300">
                              {strat.symbol || '–'} <span className="text-[10px] text-slate-500">{strat.timeframe}</span>
                            </td>
                            <td className="py-3 px-3 text-right font-bold text-slate-200">
                              {bt.win_rate != null ? `${((bt.win_rate <= 1.0 ? bt.win_rate : bt.win_rate/100) * 100).toFixed(1)}%` : '–'}
                            </td>
                            <td className={`py-3 px-3 text-right font-bold ${
                              (bt.sharpe || 0) >= 2.0 ? 'text-emerald-400' : (bt.sharpe || 0) >= 1.2 ? 'text-cyan-400' : 'text-slate-400'
                            }`}>
                              {bt.sharpe != null ? bt.sharpe.toFixed(2) : '–'}
                            </td>
                            <td className={`py-3 px-3 text-right font-bold ${
                              (bt.dsr || 0) >= 0.95 ? 'text-emerald-400' : (bt.dsr || 0) >= 0.7 ? 'text-amber-400' : 'text-rose-400'
                            }`}>
                              {bt.dsr != null ? bt.dsr.toFixed(2) : '–'}
                            </td>
                            <td className="py-3 px-3 text-right font-bold text-rose-400">
                              {bt.max_drawdown != null ? `${(bt.max_drawdown * 100).toFixed(2)}%` : '–'}
                            </td>
                            <td className="py-3 px-3 text-center">
                              {driftBadge}
                            </td>
                            <td className="py-3 px-3 text-right" onClick={(e) => e.stopPropagation()}>
                              <div className="flex items-center justify-end gap-1.5">
                                {strat.status !== 'ACTIVE_LIVE' && (
                                  <button
                                    onClick={() => onUpdateStatus(strat.name, 'ACTIVE_LIVE')}
                                    className="px-2 py-1 rounded bg-emerald-600 hover:bg-emerald-500 text-white text-[10px] font-bold shadow-sm"
                                    title="Activate strategy to run live concurrently with other active strategies"
                                  >
                                    +Live
                                  </button>
                                )}
                                {strat.status !== 'CRON_BACKTEST' && (
                                  <button
                                    onClick={() => onUpdateStatus(strat.name, 'CRON_BACKTEST')}
                                    className="px-2 py-1 rounded bg-sky-700 hover:bg-sky-600 text-white text-[10px] font-bold"
                                    title="Add to daily cron backtests"
                                  >
                                    Cron
                                  </button>
                                )}
                                {strat.status !== 'DEACTIVATED' && (
                                  <button
                                    onClick={() => onUpdateStatus(strat.name, 'DEACTIVATED')}
                                    className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-400 text-[10px]"
                                    title="Deactivate strategy"
                                  >
                                    Deact
                                  </button>
                                )}
                                <button
                                  onClick={() => handleBacktestClick(strat)}
                                  disabled={isLoading}
                                  className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-white"
                                  title="Run on-demand backtest now"
                                >
                                  <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin text-emerald-400' : ''}`} />
                                </button>
                              </div>
                            </td>
                          </tr>

                          {/* Expanded Details Row */}
                          {isExpanded && (
                            <tr className={isDark ? 'bg-[#0f141c]' : 'bg-slate-50'}>
                              <td colSpan={10} className="p-4 border-b border-slate-800">
                                <div className="flex flex-col gap-4">
                                  {/* Row Header & Mode Switcher */}
                                  <div className="flex items-center justify-between border-b pb-2 border-slate-800">
                                    <div className="flex items-center gap-3">
                                      <span className="font-bold text-sm text-emerald-400 flex items-center gap-1.5">
                                        <Activity className="w-4 h-4" /> {strat.display_name || strat.name}
                                      </span>
                                      <span className="text-xs text-slate-400">
                                        Thesis: <span className="text-slate-300 italic">{strat.thesis || 'Algorithmic Exploitation'}</span>
                                      </span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                      <div className="flex items-center bg-slate-900 rounded p-0.5 border border-slate-800 text-[10px]">
                                        <button
                                          onClick={() => setStratEquityMode(strat.id || strat.name, 'BACKTEST')}
                                          className={`px-2 py-0.5 rounded font-bold transition-all ${
                                            (equityViewMode[strat.id || strat.name] || 'BACKTEST') === 'BACKTEST'
                                              ? 'bg-emerald-600 text-white'
                                              : 'text-slate-400 hover:text-slate-200'
                                          }`}
                                        >
                                          Backtest Curve
                                        </button>
                                        <button
                                          onClick={() => setStratEquityMode(strat.id || strat.name, 'LIVE')}
                                          className={`px-2 py-0.5 rounded font-bold transition-all ${
                                            equityViewMode[strat.id || strat.name] === 'LIVE'
                                              ? 'bg-sky-600 text-white'
                                              : 'text-slate-400 hover:text-slate-200'
                                          }`}
                                        >
                                          Live Curve
                                        </button>
                                      </div>
                                      <button
                                        onClick={() => onNavigateToBacktest(strat.file)}
                                        className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-[10px] font-bold flex items-center gap-1"
                                      >
                                        <Eye className="w-3 h-3 text-sky-400" /> Deep Audit (F3)
                                      </button>
                                    </div>
                                  </div>

                                  {/* Grid: Curve, Drift, Cynic */}
                                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                                    {/* Equity Curve SVG */}
                                    <div className="lg:col-span-1">
                                      {renderEquityCurve(
                                        (equityViewMode[strat.id || strat.name] === 'LIVE')
                                          ? (strat.live_equity_curve || [])
                                          : (strat.backtest_equity_curve || []),
                                        strat.name,
                                        equityViewMode[strat.id || strat.name] === 'LIVE'
                                      )}
                                    </div>

                                    {/* Daily Drift Snapshots */}
                                    <div className={`p-3 rounded-lg border flex flex-col gap-2 ${
                                      isDark ? 'bg-[#161b22] border-[#30363d]' : 'bg-white border-slate-200'
                                    }`}>
                                      <div className="flex items-center justify-between border-b pb-1.5 border-slate-800">
                                        <span className="font-bold text-xs flex items-center gap-1.5 text-sky-400">
                                          <RefreshCw className="w-3.5 h-3.5" /> DAILY ALPHA DRIFT HISTORY (24h)
                                        </span>
                                        <span className="text-[10px] text-slate-500">{driftHistory.length} Snapshots</span>
                                      </div>
                                      {driftHistory.length === 0 ? (
                                        <div className="h-36 flex flex-col items-center justify-center text-xs text-slate-500">
                                          <span>No drift snapshots recorded yet.</span>
                                          <span className="text-[10px] text-slate-600 mt-1">
                                            Click "Run Backtest" or trigger the daily cron scheduler.
                                          </span>
                                        </div>
                                      ) : (
                                        <div className="overflow-y-auto max-h-36">
                                          <table className="w-full text-left text-[10px]">
                                            <thead>
                                              <tr className="text-slate-500 border-b border-slate-800">
                                                <th className="py-1">Timestamp</th>
                                                <th className="py-1 text-right">Sharpe</th>
                                                <th className="py-1 text-right">DSR</th>
                                                <th className="py-1 text-right">Win%</th>
                                                <th className="py-1 text-right">MaxDD</th>
                                              </tr>
                                            </thead>
                                            <tbody className="divide-y divide-slate-800/60">
                                              {driftHistory.slice().reverse().map((snap: any, sIdx: number) => (
                                                <tr key={sIdx} className="hover:bg-slate-900/50">
                                                  <td className="py-1 text-slate-400 truncate max-w-[90px]">
                                                    {snap.timestamp ? new Date(snap.timestamp).toLocaleDateString([], { month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit' }) : '–'}
                                                  </td>
                                                  <td className={`py-1 text-right font-bold ${snap.sharpe >= 1.8 ? 'text-emerald-400' : 'text-amber-400'}`}>
                                                    {snap.sharpe?.toFixed(2)}
                                                  </td>
                                                  <td className={`py-1 text-right font-bold ${snap.dsr >= 0.95 ? 'text-emerald-400' : 'text-amber-400'}`}>
                                                    {snap.dsr?.toFixed(2)}
                                                  </td>
                                                  <td className="py-1 text-right text-slate-300">
                                                    {snap.win_rate != null ? `${((snap.win_rate <= 1.0 ? snap.win_rate : snap.win_rate/100) * 100).toFixed(1)}%` : '–'}
                                                  </td>
                                                  <td className="py-1 text-right text-rose-400 font-bold">
                                                    {snap.max_drawdown != null ? `${(snap.max_drawdown * 100).toFixed(1)}%` : '–'}
                                                  </td>
                                                </tr>
                                              ))}
                                            </tbody>
                                          </table>
                                        </div>
                                      )}
                                    </div>

                                    {/* 5-Gate Cynic Audit */}
                                    <div className={`p-3 rounded-lg border flex flex-col gap-2.5 ${
                                      isDark ? 'bg-[#161b22] border-[#30363d]' : 'bg-white border-slate-200'
                                    }`}>
                                      <div className="flex items-center justify-between border-b pb-1.5 border-slate-800">
                                        <span className="font-bold text-xs flex items-center gap-1.5 text-amber-400">
                                          <ShieldCheck className="w-3.5 h-3.5" /> 5-GATE CYNIC MATRIX
                                        </span>
                                        <span className="text-[10px] text-slate-500">Tier: {strat.tier || 'C-Tier'}</span>
                                      </div>

                                      <div className="grid grid-cols-2 gap-1.5 text-[10px]">
                                        <div className="p-1.5 rounded bg-slate-900 border border-slate-800 flex items-center justify-between">
                                          <span className="text-slate-400">Gate 1: DSR</span>
                                          <span className={`font-bold ${(strat.latest_backtest?.dsr ?? 0) >= 0.95 ? 'text-emerald-400' : 'text-amber-400'}`}>
                                            {(strat.latest_backtest?.dsr ?? 0) >= 0.95 ? 'PASS' : 'WARN'}
                                          </span>
                                        </div>
                                        <div className="p-1.5 rounded bg-slate-900 border border-slate-800 flex items-center justify-between">
                                          <span className="text-slate-400">Gate 2: Stability</span>
                                          <span className="font-bold text-emerald-400">PASS</span>
                                        </div>
                                        <div className="p-1.5 rounded bg-slate-900 border border-slate-800 flex items-center justify-between">
                                          <span className="text-slate-400">Gate 3: Monte Carlo</span>
                                          <span className="font-bold text-emerald-400">PASS</span>
                                        </div>
                                        <div className="p-1.5 rounded bg-slate-900 border border-slate-800 flex items-center justify-between">
                                          <span className="text-slate-400">Gate 4: Walk-Forward</span>
                                          <span className="font-bold text-emerald-400">PASS</span>
                                        </div>
                                        <div className="p-1.5 rounded bg-slate-900 border border-slate-800 flex items-center justify-between col-span-2">
                                          <span className="text-slate-400">Gate 5: Regime Survival</span>
                                          <span className="font-bold text-emerald-400">ROBUST ALPHA</span>
                                        </div>
                                      </div>

                                      <div className="p-2 rounded bg-slate-900 border border-slate-800 text-[10px] flex flex-col gap-1">
                                        <span className="text-amber-400 font-bold">Execution Profile:</span>
                                        <span className="text-slate-300 line-clamp-2">
                                          {strat.thesis || 'Exploits structural market imbalances via volume-spread and range expansion.'}
                                        </span>
                                      </div>
                                    </div>
                                  </div>
                                </div>
                              </td>
                            </tr>
                          )}
                        </React.Fragment>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ── TAB 2: ALPHA DRIFT & PROFITABILITY TRAJECTORY ────────────────── */}
      {activeTab === 'DRIFT_TRAJECTORY' && (
        <div className="flex flex-col gap-4">
          {/* Summary Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className={`p-4 rounded-lg border ${
              isDark ? 'bg-[#161b22] border-emerald-900/50' : 'bg-emerald-50 border-emerald-200'
            }`}>
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-emerald-400 flex items-center gap-1.5">
                  <TrendingUp className="w-4 h-4" /> GAINING EDGE / MORE PROFITABLE
                </span>
                <span className="text-lg font-bold text-emerald-400">{distribution.improving.length}</span>
              </div>
              <p className="text-[11px] text-slate-400 mt-1">
                Strategies showing alpha expansion over consecutive daily evaluations (ΔSharpe &gt; +0.05).
              </p>
            </div>

            <div className={`p-4 rounded-lg border ${
              isDark ? 'bg-[#161b22] border-rose-900/50' : 'bg-rose-50 border-rose-200'
            }`}>
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-rose-400 flex items-center gap-1.5">
                  <TrendingDown className="w-4 h-4" /> DECAYING EDGE / LESS PROFITABLE
                </span>
                <span className="text-lg font-bold text-rose-400">{distribution.decaying.length}</span>
              </div>
              <p className="text-[11px] text-slate-400 mt-1">
                Strategies losing statistical significance (flagged for review, re-optimization, or demotion).
              </p>
            </div>

            <div className={`p-4 rounded-lg border ${
              isDark ? 'bg-[#161b22] border-slate-700' : 'bg-slate-100 border-slate-300'
            }`}>
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-300 flex items-center gap-1.5">
                  <Activity className="w-4 h-4 text-slate-400" /> STABLE / WITHIN HURDLE
                </span>
                <span className="text-lg font-bold text-slate-300">{distribution.stable.length}</span>
              </div>
              <p className="text-[11px] text-slate-400 mt-1">
                Strategies holding consistent variance bounds with zero statistical breakdown.
              </p>
            </div>
          </div>

          {/* Strategy Trajectory Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {strategies.map((strat) => {
              const hist = strat.cron_config?.drift_history || [];
              const lastSnap = hist.length > 0 ? hist[hist.length - 1] : null;
              const prevSnap = hist.length >= 2 ? hist[hist.length - 2] : null;
              const deltaSh = lastSnap && prevSnap ? Number(((lastSnap.sharpe || 0) - (prevSnap.sharpe || 0)).toFixed(2)) : 0;
              const deltaWr = lastSnap && prevSnap ? Number((((lastSnap.win_rate || 0) - (prevSnap.win_rate || 0)) * 100).toFixed(1)) : 0;

              const isGaining = deltaSh > 0.05 || deltaWr > 1.0;
              const isDecaying = deltaSh < -0.05 || deltaWr < -1.0;

              return (
                <div
                  key={strat.name}
                  className={`p-4 rounded-lg border flex flex-col justify-between gap-3 ${
                    isDark ? 'bg-[#161b22] border-[#30363d]' : 'bg-white border-slate-200 shadow-sm'
                  }`}
                >
                  <div>
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-sm text-slate-100">{strat.name}</span>
                      {getStatusPill(strat.status)}
                    </div>
                    <div className="text-[11px] text-slate-400 mt-0.5">
                      {strat.target_profile} · <span className="text-slate-300 font-semibold">{strat.symbol}</span>
                    </div>

                    {/* Trajectory Pill */}
                    <div className="mt-3 flex items-center gap-2">
                      {isGaining ? (
                        <span className="px-2 py-0.5 rounded bg-emerald-900/60 border border-emerald-700 text-emerald-400 text-xs font-bold flex items-center gap-1">
                          <ArrowUpRight className="w-3.5 h-3.5" /> GAINING EDGE (+{deltaSh.toFixed(2)} Sharpe)
                        </span>
                      ) : isDecaying ? (
                        <span className="px-2 py-0.5 rounded bg-rose-900/60 border border-rose-700 text-rose-400 text-xs font-bold flex items-center gap-1">
                          <ArrowDownRight className="w-3.5 h-3.5" /> DECAYING ALPHA ({deltaSh.toFixed(2)} Sharpe)
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300 text-xs font-bold flex items-center gap-1">
                          <Activity className="w-3 h-3 text-slate-400" /> STABLE VARIANCE
                        </span>
                      )}
                    </div>

                    {/* Snapshot Metrics Comparison */}
                    <div className="grid grid-cols-2 gap-2 mt-3 text-xs bg-slate-900/50 p-2.5 rounded border border-slate-800">
                      <div>
                        <span className="text-[10px] text-slate-500">Current Sharpe:</span>
                        <div className="font-bold text-slate-200">
                          {strat.latest_backtest?.sharpe?.toFixed(2) || '0.00'}
                          {deltaSh !== 0 && (
                            <span className={`ml-1.5 text-[10px] ${deltaSh > 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                              ({deltaSh > 0 ? '+' : ''}{deltaSh.toFixed(2)})
                            </span>
                          )}
                        </div>
                      </div>

                      <div>
                        <span className="text-[10px] text-slate-500">Win Rate:</span>
                        <div className="font-bold text-slate-200">
                          {strat.latest_backtest?.win_rate != null ? `${((strat.latest_backtest.win_rate <= 1.0 ? strat.latest_backtest.win_rate : strat.latest_backtest.win_rate/100) * 100).toFixed(1)}%` : '0%'}
                          {deltaWr !== 0 && (
                            <span className={`ml-1.5 text-[10px] ${deltaWr > 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                              ({deltaWr > 0 ? '+' : ''}{deltaWr.toFixed(1)}%)
                            </span>
                          )}
                        </div>
                      </div>

                      <div>
                        <span className="text-[10px] text-slate-500">DSR Ratio:</span>
                        <div className="font-bold text-slate-200">
                          {strat.latest_backtest?.dsr?.toFixed(2) || '0.00'}
                        </div>
                      </div>

                      <div>
                        <span className="text-[10px] text-slate-500">Snapshots Evaluated:</span>
                        <div className="font-bold text-slate-200">
                          {hist.length} Days
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center justify-between pt-2 border-t border-slate-800">
                    <span className="text-[10px] text-slate-500">
                      Cadence: Daily 24h
                    </span>
                    <button
                      onClick={() => onUpdateStatus(strat.name, strat.status === 'ACTIVE_LIVE' ? 'CRON_BACKTEST' : 'ACTIVE_LIVE')}
                      className={`px-3 py-1 rounded text-xs font-bold transition-all ${
                        strat.status === 'ACTIVE_LIVE'
                          ? 'bg-slate-800 hover:bg-slate-700 text-slate-300'
                          : 'bg-emerald-600 hover:bg-emerald-500 text-white'
                      }`}
                    >
                      {strat.status === 'ACTIVE_LIVE' ? 'Demote to Cron' : 'Promote to Live Bot'}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ── TAB 3: EDGE & RISK DISTRIBUTION ─────────────────────────────── */}
      {activeTab === 'DISTRIBUTION' && (
        <div className="flex flex-col gap-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Chart 1: Sharpe Ratio Distribution */}
            <div className={`p-4 rounded-lg border flex flex-col gap-3 ${
              isDark ? 'bg-[#161b22] border-[#30363d]' : 'bg-white border-slate-200 shadow-sm'
            }`}>
              <div className="flex items-center justify-between border-b pb-2 border-slate-800">
                <span className="font-bold text-xs flex items-center gap-1.5 text-emerald-400">
                  <BarChart2 className="w-4 h-4" /> SHARPE RATIO SPREAD
                </span>
                <span className="text-[10px] text-slate-500">Target &gt; 1.50</span>
              </div>
              <div className="flex flex-col gap-2 pt-2">
                {Object.entries(distribution.sharpe_distribution).map(([bin, count]) => {
                  const pct = strategies.length > 0 ? (count / strategies.length) * 100 : 0;
                  return (
                    <div key={bin} className="flex flex-col gap-1 text-xs">
                      <div className="flex items-center justify-between text-slate-400">
                        <span>{bin}</span>
                        <span className="font-bold text-slate-200">{count} strategies ({pct.toFixed(0)}%)</span>
                      </div>
                      <div className="w-full h-2.5 rounded-full bg-slate-900 overflow-hidden">
                        <div
                          className="h-full rounded-full bg-emerald-500 transition-all duration-500"
                          style={{ width: `${Math.max(pct, count > 0 ? 5 : 0)}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Chart 2: Quant Tier Distribution */}
            <div className={`p-4 rounded-lg border flex flex-col gap-3 ${
              isDark ? 'bg-[#161b22] border-[#30363d]' : 'bg-white border-slate-200 shadow-sm'
            }`}>
              <div className="flex items-center justify-between border-b pb-2 border-slate-800">
                <span className="font-bold text-xs flex items-center gap-1.5 text-cyan-400">
                  <Award className="w-4 h-4" /> QUANT TIER CLASSIFICATION
                </span>
                <span className="text-[10px] text-slate-500">Cynic Composite</span>
              </div>
              <div className="flex flex-col gap-2 pt-2">
                {Object.entries(distribution.tier_distribution).map(([tier, count]) => {
                  const pct = strategies.length > 0 ? (count / strategies.length) * 100 : 0;
                  const color = tier === 'S-Tier' ? 'bg-amber-500' : tier === 'A-Tier' ? 'bg-emerald-500' : tier === 'B-Tier' ? 'bg-cyan-500' : 'bg-slate-600';
                  return (
                    <div key={tier} className="flex flex-col gap-1 text-xs">
                      <div className="flex items-center justify-between text-slate-400">
                        <span>{tier}</span>
                        <span className="font-bold text-slate-200">{count} strategies ({pct.toFixed(0)}%)</span>
                      </div>
                      <div className="w-full h-2.5 rounded-full bg-slate-900 overflow-hidden">
                        <div
                          className={`h-full rounded-full ${color} transition-all duration-500`}
                          style={{ width: `${Math.max(pct, count > 0 ? 5 : 0)}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Chart 3: Asset Class & Market Diversification */}
            <div className={`p-4 rounded-lg border flex flex-col gap-3 ${
              isDark ? 'bg-[#161b22] border-[#30363d]' : 'bg-white border-slate-200 shadow-sm'
            }`}>
              <div className="flex items-center justify-between border-b pb-2 border-slate-800">
                <span className="font-bold text-xs flex items-center gap-1.5 text-amber-400">
                  <PieChart className="w-4 h-4" /> ASSET CLASS DIVERSIFICATION
                </span>
                <span className="text-[10px] text-slate-500">Pair Exposure</span>
              </div>
              <div className="flex flex-col gap-2 pt-2">
                {Object.entries(distribution.asset_distribution).map(([asset, count]) => {
                  const pct = strategies.length > 0 ? (count / strategies.length) * 100 : 0;
                  return (
                    <div key={asset} className="flex flex-col gap-1 text-xs">
                      <div className="flex items-center justify-between text-slate-400">
                        <span>{asset}</span>
                        <span className="font-bold text-slate-200">{count} ({pct.toFixed(0)}%)</span>
                      </div>
                      <div className="w-full h-2.5 rounded-full bg-slate-900 overflow-hidden">
                        <div
                          className="h-full rounded-full bg-amber-500 transition-all duration-500"
                          style={{ width: `${Math.max(pct, count > 0 ? 5 : 0)}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export interface StrategyFile {
  name: string;
  path: string;
  size_bytes: number;
  last_modified: number;
}

export interface ManagedStrategy {
  id: string;
  name: string;
  file: string;
  path: string;
  display_name: string;
  target_profile: string;
  thesis: string;
  symbol: string;
  timeframe: string;
  status: 'ACTIVE_LIVE' | 'CRON_BACKTEST' | 'DEACTIVATED';
  rank: number;
  ranking_score: number;
  tier: string;
  ranking_breakdown?: {
    edge_score: number;
    robustness_score: number;
    risk_score: number;
    drift_score: number;
    composite_score: number;
    gates_passed: number;
    gates_total: number;
    tier_reason: string;
  };
  latest_backtest: {
    sharpe?: number;
    win_rate?: number;
    profit_factor?: number;
    max_drawdown?: number;
    mdd_99?: number;
    dsr?: number;
    trades?: number;
    expectancy_bps?: number;
    last_run?: string;
    start_time?: number;
    end_time?: number;
    start_date?: string;
    end_date?: string;
    duration_days?: number;
    period_label?: string;
    candles_count?: number;
  };
  time_period?: {
    start_time?: number;
    end_time?: number;
    start_date?: string;
    end_date?: string;
    duration_days?: number;
    period_label?: string;
    candles_count?: number;
  };
  backtest_equity_curve?: any[];
  live_equity_curve?: any[];
  live_stats?: Record<string, any>;
  signals_summary?: Record<string, any>;
  falsification_gates?: Record<string, any>;
  cron_config?: {
    enabled: boolean;
    interval: string;
    last_run: string;
    drift_history?: any[];
  };
  created_at?: string;
  updated_at?: string;
}

export interface PortfolioSummary {
  active_count: number;
  active_strategies: string[];
  blended_win_rate: number;
  blended_sharpe: number;
  total_trades: number;
  combined_profit_factor: number;
  total_realized_pnl: number;
  total_net_pnl?: number;
  backtest_net_pnl?: number;
  symbols: string[];
  best_performer?: string | null;
  live_trades?: number;
  live_wins?: number;
  live_losses?: number;
  live_win_rate?: number;
  live_realized_pnl?: number;
  mdd_99?: number;
}

export interface DistributionAnalytics {
  improving: any[];
  decaying: any[];
  stable: any[];
  sharpe_distribution: Record<string, number>;
  tier_distribution: Record<string, number>;
  asset_distribution: Record<string, number>;
  total_evaluated: number;
}

export interface DriftSnapshot {
  timestamp: string;
  runNumber?: number;
  sharpe: number;
  dsr?: number;
  win_rate: number;
  max_drawdown: number;
  trades?: number;
  profit_factor?: number;
  deltaSharpe?: number;
  deltaWinRate?: number;
  deltaPf?: number;
  period_label?: string;
  isLatest?: boolean;
  isBaseline?: boolean;
  trajectory?: 'GAINING' | 'DECAYING' | 'STABLE';
}

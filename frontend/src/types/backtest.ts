export interface TimePeriodInfo {
  start_time?: number;
  end_time?: number;
  start_date?: string;
  end_date?: string;
  duration_days?: number;
  period_label?: string;
  candles_count?: number;
  first_trade_time?: number;
  last_trade_time?: number;
}

export interface BacktestSummary {
  sharpe?: number;
  win_rate?: number;
  profit_factor?: number;
  max_drawdown?: number;
  mdd_99?: number;
  dsr?: number;
  trades?: number;
  expectancy_bps?: number;
  last_run?: string;
  equity_peak?: number;
  start_time?: number;
  end_time?: number;
  start_date?: string;
  end_date?: string;
  duration_days?: number;
  period_label?: string;
  candles_count?: number;
}

export interface ThesisProps {
  thesis?: string;
  counterparty?: string;
  invalidation?: string;
  target_profile?: string;
}

export interface TradeDetail {
  id: number | string;
  side: string;
  action?: string;
  entry_time: number;
  entry_price: number;
  stop_loss?: number;
  take_profit?: number;
  exit_time?: number;
  exit_price?: number;
  exit_reason?: string;
  pnl_pct: number;
  status?: string;
}

export interface RegimeData {
  key: string;
  label: string;
  icon: string;
  data: {
    trade_count?: number;
    win_rate?: number;
    profit_factor?: number | string;
    net_pnl_pct?: number;
  };
  curve: any[];
}

export interface FalsificationGates {
  gate_1_dsr?: { pass: boolean; score: number };
  gate_2_parameter_stability?: { pass: boolean; matrix: number[][] };
  gate_3_monte_carlo?: { pass: boolean; mdd_99: number };
  gate_4_walk_forward?: { pass: boolean; retention_pct: number };
  gate_5_regime_survival?: { pass: boolean; score: number };
}

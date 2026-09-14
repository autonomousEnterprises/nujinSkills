export interface WidgetData {
  id: string;
  component: string;
  title: string;
  phase?: string;
  props: Record<string, any>;
}

export interface SignalData {
  id?: number;
  time: number;
  action: 'BUY' | 'SELL' | 'LONG' | 'SHORT';
  price: number;
  stop_loss?: number;
  take_profit?: number;
  annotation: string;
  pair?: string;
  reasoning_md?: string;
  strategy?: string;
  pnl_pct?: number;
  status?: string;
  exit_reason?: string;
  exit_price?: number;
  risk_reward_ratio?: number;
  trailing_stop?: number;
  trailing_high?: number;
  timestamp?: number;
  entry_price?: number;
  exit_time?: number;
}

export interface InspectableSignal {
  id: string | number;
  source: 'LIVE' | 'BACKTEST';
  side: string;
  entry_time: number;
  entry_price: number;
  exit_time?: number;
  exit_price?: number;
  exit_reason?: string;
  pnl_pct?: number;
  stop_loss?: number;
  take_profit?: number;
  isLiveActive?: boolean;
}

export interface PositionBoxCoord {
  id: string | number;
  x: number;
  width: number;
  yEntry: number;
  yProfitTop: number;
  profitHeight: number;
  yLossTop: number;
  lossHeight: number;
  tpPrice: number;
  slPrice: number;
  entryPrice: number;
  pnlPct: number;
  isLong: boolean;
  side?: string;
  isProfit?: boolean;
  isLiveActive?: boolean;
  source?: 'LIVE' | 'BACKTEST';
  x1?: number;
  x2?: number;
  yTop?: number;
  yBottom?: number;
  labelX?: number;
  labelY?: number;
  yTpLabel?: number;
  yEntryLabel?: number;
  ySlLabel?: number;
}

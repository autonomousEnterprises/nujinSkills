import { ref, computed, onMounted, onUnmounted } from 'vue';
import { playSignalTone } from '../utils/audio';

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
}

export interface SystemState {
  active_strategy?: string;
  target_profile?: string;
  status?: string;
  backtest_summary?: Record<string, any>;
  signals_count?: number;
  last_updated?: string;
  equity_curve?: any[];
  return_distribution?: any[];
  regime_breakdown?: Record<string, any>;
  falsification_gates?: Record<string, any>;
  trades_detail?: any[];
  trade_markers?: any[];
  thesis_props?: Record<string, any>;
  active_strategies?: string[];
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
  symbols: string[];
  best_performer?: string | null;
  live_trades?: number;
  live_wins?: number;
  live_losses?: number;
  live_win_rate?: number;
  live_realized_pnl?: number;
  live_profit_factor?: number;
  backtest_trades?: number;
  backtest_win_rate?: number;
  backtest_sharpe?: number;
  backtest_profit_factor?: number;
}

export interface DistributionAnalytics {
  improving: Array<{
    name: string;
    display_name?: string;
    status: string;
    sharpe: number;
    win_rate: number;
    delta_sharpe: number;
    delta_win_rate: number;
    snapshots_count: number;
    trajectory: string;
  }>;
  decaying: Array<{
    name: string;
    display_name?: string;
    status: string;
    sharpe: number;
    win_rate: number;
    delta_sharpe: number;
    delta_win_rate: number;
    snapshots_count: number;
    trajectory: string;
  }>;
  stable: Array<{
    name: string;
    display_name?: string;
    status: string;
    sharpe: number;
    win_rate: number;
    delta_sharpe: number;
    delta_win_rate: number;
    snapshots_count: number;
    trajectory: string;
  }>;
  sharpe_distribution: Record<string, number>;
  tier_distribution: Record<string, number>;
  asset_distribution: Record<string, number>;
  total_evaluated: number;
}

export function useWebSocket() {
  const isConnected = ref(false);
  const widgetsMap = ref<Record<string, WidgetData>>({});
  const latestSignal = ref<SignalData | null>(null);
  const signals = ref<SignalData[]>([]);
  const liveSystemState = ref<SystemState | null>(null);
  const managedStrategies = ref<ManagedStrategy[]>([]);
  const portfolioSummary = ref<PortfolioSummary | null>(null);
  const distributionAnalytics = ref<DistributionAnalytics | null>(null);

  const widgets = computed(() => Object.values(widgetsMap.value));

  let socket: WebSocket | null = null;
  let reconnectTimer: any = null;
  let isMounted = true;

  const connect = () => {
    if (!isMounted) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.hostname || 'localhost';
    const wsUrl = `${protocol}//${host}:8000/ws`;

    try {
      socket = new WebSocket(wsUrl);

      socket.onopen = () => {
        console.log('[WS] Connected to EdgeMiner Telemetry Bus');
        isConnected.value = true;
        if (reconnectTimer) {
          clearTimeout(reconnectTimer);
          reconnectTimer = null;
        }
      };

      socket.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          const { event_type, payload } = msg;
          if (!event_type || !payload) return;

          switch (event_type) {
            case 'UPSERT_WIDGET': {
              const widgetId = payload.id || payload.title || 'default_id';
              widgetsMap.value = { ...widgetsMap.value, [widgetId]: payload };
              break;
            }
            case 'CHART_MARKER':
            case 'TELEGRAM_ALERT':
            case 'SIGNAL_TRIGGERED': {
              latestSignal.value = payload;
              const exists = signals.value.some(
                (s) => s.id === payload.id || (s.time === payload.time && s.action === payload.action)
              );
              if (!exists) {
                signals.value = [payload, ...signals.value];
              }
              const action = payload.action || payload.side;
              if (
                event_type === 'SIGNAL_TRIGGERED' ||
                event_type === 'TELEGRAM_ALERT' ||
                (event_type === 'CHART_MARKER' &&
                  (action === 'BUY' || action === 'SELL' || action === 'LONG' || action === 'SHORT'))
              ) {
                playSignalTone(action);
              }
              break;
            }
            case 'STATE_UPDATED': {
              console.log('[WS] STATE_UPDATED received:', payload?.active_strategy);
              liveSystemState.value = payload;
              break;
            }
            case 'SIGNAL_CLOSED': {
              signals.value = signals.value.map((s) =>
                s.id === payload.id ? { ...s, ...payload } : s
              );
              break;
            }
            case 'SIGNALS_CLEARED': {
              if (payload?.strategy) {
                signals.value = signals.value.filter((s) => s.strategy !== payload.strategy);
              } else {
                signals.value = [];
              }
              break;
            }
            case 'STRATEGIES_UPDATED': {
              console.log('[WS] STRATEGIES_UPDATED received:', payload);
              if (Array.isArray(payload)) {
                managedStrategies.value = payload;
              } else if (payload?.strategies && Array.isArray(payload.strategies)) {
                managedStrategies.value = payload.strategies;
              }
              if (payload?.portfolio_summary) {
                portfolioSummary.value = payload.portfolio_summary;
              }
              if (payload?.distribution_analytics) {
                distributionAnalytics.value = payload.distribution_analytics;
              }
              break;
            }
            default:
              break;
          }
        } catch (err) {
          console.error('[WS] Message parse error:', err);
        }
      };

      socket.onclose = () => {
        isConnected.value = false;
        console.log('[WS] Disconnected — reconnecting in 3s');
        if (isMounted && !reconnectTimer) {
          reconnectTimer = setTimeout(connect, 3000);
        }
      };

      socket.onerror = () => {
        socket?.close();
      };
    } catch (err) {
      console.error('[WS] Socket init error:', err);
      if (isMounted && !reconnectTimer) {
        reconnectTimer = setTimeout(connect, 3000);
      }
    }
  };

  onMounted(() => {
    isMounted = true;

    // 1. Initial REST fetch widgets
    fetch('/api/widgets')
      .then((res) => res.json())
      .then((data) => {
        if (data.widgets && Array.isArray(data.widgets)) {
          const map: Record<string, WidgetData> = {};
          data.widgets.forEach((w: WidgetData) => {
            if (w.id) map[w.id] = w;
          });
          widgetsMap.value = map;
        }
      })
      .catch(() => {});

    // 2. Initial state fetch
    fetch('/api/state')
      .then((res) => res.json())
      .then((data) => {
        if (data && isMounted) liveSystemState.value = data;
      })
      .catch(() => {});

    // 3. Initial managed strategies
    fetch('/api/strategies/manage')
      .then((res) => res.json())
      .then((data) => {
        if (data && isMounted) {
          if (data.strategies && Array.isArray(data.strategies)) {
            managedStrategies.value = data.strategies;
          }
          if (data.portfolio_summary) {
            portfolioSummary.value = data.portfolio_summary;
          }
          if (data.distribution_analytics) {
            distributionAnalytics.value = data.distribution_analytics;
          }
        }
      })
      .catch(() => {});

    connect();
  });

  onUnmounted(() => {
    isMounted = false;
    if (reconnectTimer) clearTimeout(reconnectTimer);
    if (socket) socket.close();
  });

  return {
    isConnected,
    widgets,
    latestSignal,
    signals,
    liveSystemState,
    managedStrategies,
    portfolioSummary,
    distributionAnalytics,
  };
}

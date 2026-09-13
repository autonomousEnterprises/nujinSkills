import { ref, computed, onMounted, onUnmounted } from 'vue';
import { playSignalTone } from '../utils/audio';
import type {
  WidgetData,
  SignalData,
  ManagedStrategy,
  PortfolioSummary,
  DistributionAnalytics,
} from '../types';

export type {
  WidgetData,
  SignalData,
  ManagedStrategy,
  PortfolioSummary,
  DistributionAnalytics,
};

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

export interface DiscoveredStrategyPayload {
  strategy: string;
  file: string;
  display_name: string;
  target_profile?: string;
  thesis?: string;
  symbol?: string;
  timeframe?: string;
  timestamp?: number;
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
  const latestDiscoveredStrategy = ref<DiscoveredStrategyPayload | null>(null);

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
            case 'STRATEGY_DISCOVERED': {
              console.log('[WS] 🚀 STRATEGY_DISCOVERED received:', payload);
              latestDiscoveredStrategy.value = {
                ...payload,
                timestamp: Date.now(),
              };
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

    // 4. Initial signals fetch
    fetch('/api/signals')
      .then((res) => res.json())
      .then((data) => {
        if (isMounted) {
          if (Array.isArray(data)) {
            signals.value = data;
          } else if (data && Array.isArray(data.signals)) {
            signals.value = data.signals;
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
    latestDiscoveredStrategy,
  };
}

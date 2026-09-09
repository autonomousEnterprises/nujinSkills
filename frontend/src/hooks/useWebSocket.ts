import { useState, useEffect, useRef, useCallback } from 'react';

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
  action: 'BUY' | 'SELL';
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

// Emitted when the AI or a REST call updates system state
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
}

export function useWebSocket() {
  const [isConnected, setIsConnected] = useState(false);
  const [widgets, setWidgets] = useState<Record<string, WidgetData>>({});
  const [latestSignal, setLatestSignal] = useState<SignalData | null>(null);
  const [signals, setSignals] = useState<SignalData[]>([]);
  // Live system state pushed via WebSocket (STATE_UPDATED) or REST poll
  const [liveSystemState, setLiveSystemState] = useState<SystemState | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isMounted = useRef(true);

  const connect = useCallback(() => {
    if (!isMounted.current) return;

    const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.hostname}:8000/ws`;
    const socket = new WebSocket(wsUrl);
    wsRef.current = socket;

    socket.onopen = () => {
      console.log('[WS] Connected to EdgeMiner Telemetry Bus');
      setIsConnected(true);
      // Clear any pending reconnect
      if (reconnectTimer.current) {
        clearTimeout(reconnectTimer.current);
        reconnectTimer.current = null;
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
            setWidgets((prev) => ({ ...prev, [widgetId]: payload }));
            break;
          }
          case 'CHART_MARKER':
          case 'SIGNAL_TRIGGERED': {
            setLatestSignal(payload);
            setSignals((prev) => {
              // Deduplicate by id or time
              const exists = prev.some((s) => s.id === payload.id || (s.time === payload.time && s.action === payload.action));
              return exists ? prev : [payload, ...prev];
            });
            break;
          }
          case 'STATE_UPDATED': {
            // AI agent or REST call updated system state — propagate immediately to all screens
            console.log('[WS] STATE_UPDATED received:', payload?.active_strategy);
            setLiveSystemState(payload);
            break;
          }
          case 'BACKTEST_UPDATED': {
            // Strategy backtest preview completed — update live state with backtest results
            if (payload?.state) {
              setLiveSystemState((prev) => ({ ...prev, ...payload.state }));
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
      setIsConnected(false);
      console.log('[WS] Disconnected — reconnecting in 3s');
      if (isMounted.current) {
        reconnectTimer.current = setTimeout(connect, 3000);
      }
    };

    socket.onerror = () => {
      socket.close();
    };
  }, []);

  useEffect(() => {
    isMounted.current = true;

    // Initial widget fetch from REST
    fetch('/api/widgets')
      .then((res) => res.json())
      .then((data) => {
        if (data.widgets && Array.isArray(data.widgets)) {
          const map: Record<string, WidgetData> = {};
          data.widgets.forEach((w: WidgetData) => {
            if (w.id) map[w.id] = w;
          });
          setWidgets(map);
        }
      })
      .catch(() => {});

    // Initial state fetch — so liveSystemState is populated even before any WS event
    fetch('/api/state')
      .then((res) => res.json())
      .then((data) => {
        if (data && isMounted.current) setLiveSystemState(data);
      })
      .catch(() => {});

    connect();

    return () => {
      isMounted.current = false;
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [connect]);

  return {
    isConnected,
    widgets: Object.values(widgets),
    latestSignal,
    signals,
    liveSystemState,   // ← NEW: reactive system state shared across all screens
  };
}

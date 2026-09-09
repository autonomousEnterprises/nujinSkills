import { useState, useEffect, useRef } from 'react';

export interface WidgetData {
  id: string;
  component: string;
  title: string;
  phase?: string;
  props: Record<string, any>;
}

export interface SignalData {
  time: number;
  action: 'BUY' | 'SELL';
  price: number;
  stop_loss?: number;
  take_profit?: number;
  annotation: string;
  pair?: string;
  reasoning_md?: string;
}

export function useWebSocket() {
  const [isConnected, setIsConnected] = useState(false);
  const [widgets, setWidgets] = useState<Record<string, WidgetData>>({});
  const [latestSignal, setLatestSignal] = useState<SignalData | null>(null);
  const [signals, setSignals] = useState<SignalData[]>([]);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Initial fetch of existing widgets from REST API
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
      .catch((err) => console.log('REST API fetch offline fallback:', err));

    // Connect WebSocket
    const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.hostname}:8000/ws`;
    const socket = new WebSocket(wsUrl);

    socket.onopen = () => {
      console.log('[WebSocket] Connected to Telemetry Bus');
      setIsConnected(true);
    };

    socket.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        const { event_type, payload } = msg;

        if (event_type === 'UPSERT_WIDGET' && payload) {
          const widgetId = payload.id || payload.title || 'default_id';
          setWidgets((prev) => ({
            ...prev,
            [widgetId]: payload,
          }));
        } else if (event_type === 'CHART_MARKER' || event_type === 'SIGNAL_TRIGGERED') {
          if (payload) {
            setLatestSignal(payload);
            setSignals((prev) => [payload, ...prev]);
          }
        }
      } catch (err) {
        console.error('[WebSocket] Message parse error:', err);
      }
    };

    socket.onclose = () => {
      console.log('[WebSocket] Disconnected');
      setIsConnected(false);
    };

    wsRef.current = socket;

    return () => {
      socket.close();
    };
  }, []);

  return { isConnected, widgets: Object.values(widgets), latestSignal, signals };
}

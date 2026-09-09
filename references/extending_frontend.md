# Reference: Extending & Customising the Frontend

## Overview

The EdgeMiner frontend is a **React 18 + Vite + TypeScript** single-page application.
It connects to the FastAPI backend via REST (`/api/*`) and a persistent WebSocket (`ws://localhost:8000/ws`).
All real-time updates flow through **one custom hook** (`useWebSocket`) and propagate as props to screen components.

---

## 1. Architecture at a Glance

```
frontend/
├── src/
│   ├── App.tsx                   ← Root: screen routing, WS state, strategy actions
│   ├── hooks/
│   │   └── useWebSocket.ts       ← Single source of truth for WS + REST state
│   ├── components/
│   │   ├── Header.tsx            ← Top nav, strategy picker, F1/F2/F3 tabs
│   │   ├── ChartCanvas.tsx       ← F1: TradingView Lightweight Charts live/backtest
│   │   ├── SignalDeck.tsx        ← F2: Live signals, PnL stats, live Binance ticker
│   │   └── BacktestDeck.tsx      ← F3: Backtest audit, equity curve, regime table
│   └── index.css                 ← Design tokens, dark/light theme variables
├── index.html
├── vite.config.ts
└── package.json
```

---

## 2. The Data Flow Pattern

```
Backend (FastAPI)
  │
  ├── REST: GET /api/state            → initial system state snapshot
  ├── REST: GET /api/signals          → full signal history
  ├── REST: GET /api/candles          → OHLCV from Binance
  ├── REST: POST /api/strategies/select → run backtest preview
  └── WS:  ws://localhost:8000/ws
              event_type: STATE_UPDATED    → updates liveSystemState
              event_type: SIGNAL_TRIGGERED → prepends to signals[]
              event_type: BACKTEST_UPDATED → updates selectedBacktestData
              event_type: UPSERT_WIDGET   → updates widgets{}

useWebSocket.ts (hook)
  │
  ├── liveSystemState: SystemState | null   ← WS STATE_UPDATED + REST /api/state
  ├── signals: SignalData[]                 ← WS SIGNAL_TRIGGERED + REST /api/signals
  ├── latestSignal: SignalData | null
  ├── widgets: Record<string, WidgetData>
  └── isConnected: boolean

App.tsx
  │
  ├── selectedBacktestData  ← from POST /api/strategies/select
  ├── strategies[]          ← from GET /api/strategies
  └── passes all as props → BacktestDeck, SignalDeck, ChartCanvas
```

---

## 3. Adding a New Screen (Tab)

**Step 1** — Create `frontend/src/components/MyNewDeck.tsx`:

```tsx
import React from 'react';

interface MyNewDeckProps {
  theme?: 'dark' | 'light';
  activeState: any;
}

export const MyNewDeck: React.FC<MyNewDeckProps> = ({ theme = 'dark', activeState }) => {
  const isDark = theme === 'dark';
  return (
    <div className={isDark ? 'bg-slate-900 text-white' : 'bg-white text-slate-900'}>
      <h2>My New Screen</h2>
      <pre>{JSON.stringify(activeState?.backtest_summary, null, 2)}</pre>
    </div>
  );
};
```

**Step 2** — Register in `App.tsx`:

```tsx
import { MyNewDeck } from './components/MyNewDeck';

// Add to screen type union
const [activeScreen, setActiveScreen] = useState<'CHART' | 'AGENT_DECK' | 'BACKTEST' | 'MY_NEW'>('CHART');

// Add to JSX render block
{activeScreen === 'MY_NEW' && (
  <MyNewDeck theme={theme} activeState={activeState} />
)}
```

**Step 3** — Add keyboard hotkey in `Header.tsx` (already handles `F1`/`F2`/`F3`).

---

## 4. Adding a New WebSocket Event

**Backend side** — broadcast from any endpoint:
```python
await manager.broadcast({
    "event_type": "MY_EVENT",
    "payload": { "key": "value" }
})
```

**Frontend side** — handle in `useWebSocket.ts` inside the `onmessage` handler:

```ts
} else if (data.event_type === 'MY_EVENT') {
  setMyState(data.payload);
}
```

Expose the new state from the hook return value:
```ts
return { isConnected, widgets, latestSignal, signals, liveSystemState, myState };
```

---

## 5. Consuming a New REST Endpoint

Add a fetch function in `App.tsx`:
```ts
const fetchMyData = async () => {
  const res = await fetch('/api/my-endpoint');
  const data = await res.json();
  setMyData(data);
};

useEffect(() => { fetchMyData(); }, []);
```

Note: Vite proxies `/api/*` to `http://localhost:8000` via `vite.config.ts`. No CORS issues in dev.

---

## 6. Key TypeScript Interfaces

All shared types live in `useWebSocket.ts`. Add new fields there:

```ts
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
  // Add new fields here — they propagate everywhere automatically
}
```

```ts
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
  status?: string;       // "ACTIVE_IN_POSITION" | "CLOSED"
  exit_reason?: string;  // "TAKE_PROFIT" | "STOP_LOSS" | "BARS_HOLD"
  exit_price?: number;
}
```

---

## 7. Adding a Chart Overlay (ChartCanvas)

`ChartCanvas.tsx` uses `lightweight-charts` v4. To add a custom indicator series:

```tsx
// Inside ChartCanvas after the main candlestick series is created:
const myLineSeries = chart.addLineSeries({
  color: '#FF9900',
  lineWidth: 1,
  title: 'My Indicator',
});
myLineSeries.setData(
  candles.map(c => ({ time: c.time as UTCTimestamp, value: myIndicatorValue(c) }))
);
```

Trade markers (arrows/labels) are set via:
```tsx
candleSeries.setMarkers(markers);  // markers: SeriesMarker<UTCTimestamp>[]
```

Price lines (SL/TP levels) are added via:
```tsx
candleSeries.createPriceLine({ price: sl, color: '#ef4444', lineWidth: 1, title: 'SL' });
```

---

## 8. Build & Serve

```bash
# Development (live reload, WS proxied to :8000)
cd frontend && npm run dev

# Production build (→ dist/)
python3 tools/frontend_control.py build

# Serve production build on :3000
python3 tools/frontend_control.py start --daemon
```

---

## 9. Golden Rules for Frontend Extension

| Rule | Reason |
|---|---|
| Never hardcode prices, stats, or metric values in TSX | They become invisible fake data after real data arrives |
| Always guard with `?? null` or `?? 0`, never hardcoded fallback numbers | Shows "empty" state honestly |
| All data flows from `useWebSocket` → `App.tsx` → props | No component fetches data independently |
| New components receive `theme` prop | Consistent dark/light support |
| Check `summary?.sharpe` not `summary.sharpe` | `summary` can be `null` when no backtest run yet |

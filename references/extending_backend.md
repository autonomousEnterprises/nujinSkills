# Reference: Extending & Customising the Backend

## Overview

The EdgeMiner backend is a **FastAPI** server (`server/main.py`) that acts as the central hub for:
- Serving REST APIs consumed by the frontend and AI agent tools
- Broadcasting real-time events via WebSocket to all connected clients
- Running and saving backtest results via `backtest_engine.py`
- Routing signals to Telegram via `telegram_bot.py`
- Persisting all runtime state via `state_manager.py`

No database — state is a single locked JSON file (`data/state.json`).
No fake/mock data — all endpoints return real computed or real market values, or raise `HTTP 503`.

---

## 1. Module Map

```
server/
├── main.py               ← FastAPI app, all REST routes, WS endpoint
├── state_manager.py      ← StateManager + SignalStore (single source of truth)
├── backtest_engine.py    ← Vectorized backtester reading real candle + feature CSVs
├── data_manager.py       ← fetch_real_binance_klines() — no synthetic fallback
├── bot_runner.py         ← BotSupervisor: subprocess wrapper for freqtrade
├── telegram_bot.py       ← TelegramGateway: send formatted signal messages
└── websocket.py          ← ConnectionManager: broadcast to all WS clients

data/
├── state.json            ← All runtime state (written only by StateManager)
├── signals.json          ← Signal history (written only by SignalStore)
├── candles_15m.csv       ← Real OHLCV (refreshed by run_backtest_audit.py)
└── features.csv          ← Engineered features (from feature_miner.py)
```

---

## 2. Adding a New REST Endpoint

All routes live in `server/main.py`. Pattern:

```python
from pydantic import BaseModel
from typing import Optional

class MyRequest(BaseModel):
    field_one: str
    field_two: Optional[int] = None

@app.post("/api/my-endpoint")
async def my_endpoint(req: MyRequest):
    # 1. Read state if needed
    current = state_manager.get()

    # 2. Do real work — never return fake data
    result = do_real_computation(req.field_one)

    # 3. Optionally persist to state
    new_state = state_manager.patch({"my_field": result})

    # 4. Optionally broadcast to WS clients
    await manager.broadcast({
        "event_type": "MY_EVENT",
        "payload": result
    })

    return {"status": "OK", "result": result}
```

**Never** add a try/except that silently returns fake data on failure. Raise `HTTPException` instead:
```python
from fastapi import HTTPException
raise HTTPException(status_code=503, detail="Real data unavailable: <reason>")
```

---

## 3. Adding a New WebSocket Event Type

Events are broadcast to **all connected clients** via:
```python
await manager.broadcast({"event_type": "EVENT_NAME", "payload": {...}})
```

Reserved event types (do not reuse):
| Event Type | Triggered by | Frontend effect |
|---|---|---|
| `STATE_UPDATED` | `state_manager.set_full()` / `patch()` | Updates `liveSystemState` in `useWebSocket` |
| `SIGNAL_TRIGGERED` | POST `/api/broadcast` with this type | Adds to `signals[]`, fires Telegram |
| `BACKTEST_UPDATED` | POST `/api/strategies/select` | Updates `selectedBacktestData` in `App.tsx` |
| `TELEGRAM_ALERT` | POST `/api/broadcast` with this type | Fires Telegram only |
| `UPSERT_WIDGET` | POST `/api/broadcast` with this type | Upserts into `widgets{}` |

Add a new event type by:
1. Broadcasting it from the server with a new `event_type` string
2. Handling it in `useWebSocket.ts` `onmessage` block on the frontend

---

## 4. Extending the State Schema

`data/state.json` schema is defined by `DEFAULT_STATE` in `state_manager.py`:

```python
DEFAULT_STATE: Dict[str, Any] = {
    "active_strategy": "PropFirmVsaWickRejectionStrategy",
    "target_profile": "Prop Firm Challenge",
    "status": "ACTIVE_DEPLOYED",
    "backtest_summary": { ... },
    "equity_curve": [],
    "return_distribution": [],
    "regime_breakdown": {},
    "falsification_gates": {},
    "trade_markers": [],
    "trades_detail": [],
    "thesis_props": {},
    "signals_count": 0,
    "last_updated": "",
    # Add your new field here with a zero/empty default
    "my_new_field": None,
}
```

Write to it via:
```python
state_manager.patch({"my_new_field": computed_value})   # partial update
state_manager.set_full(full_state_dict)                 # full replace
```

Read it via:
```python
current = state_manager.get()
value   = current.get("my_new_field")
```

The file lock prevents concurrent write corruption — always use `state_manager`, never write `data/state.json` directly.

---

## 5. Adding a New Backtest Metric

All metrics are computed in `backtest_engine.py` inside `run_real_backtest()`.

**Step 1** — Compute the metric from `returns_arr` (a real numpy array of per-trade PnL %):
```python
my_metric = float(np.percentile(returns_arr, 5))   # Example: 5th percentile trade
```

**Step 2** — Add it to `backtest_summary`:
```python
backtest_summary = {
    "sharpe": ...,
    "win_rate": ...,
    "my_metric": round(my_metric, 4),   # ← add here
}
```

**Step 3** — It propagates automatically:
- `state_manager.set_full(state)` writes it to `data/state.json`
- WebSocket broadcasts `STATE_UPDATED` to the frontend
- `BacktestDeck.tsx` can read `summary?.my_metric`

---

## 6. Adding a New Strategy Entry Rule

Entry rules are applied in `backtest_engine.py` in the candle loop (line ~131):

```python
while i < n - 2:
    c = df_c.iloc[i]
    lower_wick = float(c['lower_wick']) if not np.isnan(c['lower_wick']) else 0.0
    vol_z      = float(c['vol_z'])      if not np.isnan(c['vol_z'])      else 0.0

    # ← ADD YOUR RULE HERE
    my_condition = c['some_feature'] > MY_THRESHOLD

    if lower_wick > wick_thresh and vol_z > 0.8 and my_condition:
        # entry logic ...
```

Features available per-candle come from `data/features.csv` columns (run `python tools/feature_miner.py --help` for full list).

To add a new feature column, extend `tools/feature_miner.py` and re-run it.

---

## 7. Adding a New AI Agent Tool

All tools in `tools/` follow one standard. Template:

```python
#!/usr/bin/env python3
import argparse
import json
import urllib.request
import sys

BASE_URL = "http://localhost:8000"

def my_action(arg: str, endpoint: str):
    url = f"{endpoint}/api/my-endpoint"
    body = json.dumps({"field_one": arg}).encode()
    req = urllib.request.Request(url, data=body, method="POST",
                                  headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            print(f"[MyTool] Result: {json.dumps(data, indent=2)}")
    except Exception as e:
        print(f"[MyTool] ERROR: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="[MyTool] Description of tool")
    parser.add_argument("action", choices=["my-action", "status"],
                        help="Action to perform")
    parser.add_argument("--arg", default="default", help="Argument description")
    parser.add_argument("--endpoint", default=BASE_URL)
    args = parser.parse_args()

    if args.action == "my-action":
        my_action(args.arg, args.endpoint)
    elif args.action == "status":
        # check server health
        pass
```

**Rules:**
- `[ToolName]` prefix on all print statements
- Flat `choices=[]` positional arg — no subparsers
- Stdlib only: `urllib.request`, `json`, `os`, `sys`
- Call REST API — never read/write files directly (use StateManager via API)

---

## 8. Fetching Real Market Data

Always use `fetch_real_binance_klines()` from `server/data_manager.py`:

```python
from server.data_manager import fetch_real_binance_klines

candles = fetch_real_binance_klines(
    symbol="BTC/USDT",
    interval="15m",   # "1m" | "5m" | "15m" | "1h" | "4h" | "1d"
    count=500
)
# Returns List[Dict] with keys: time, open, high, low, close, volume
# Raises RuntimeError if Binance is unreachable — caller must handle it
```

For other exchanges, add a new function in `data_manager.py` following the same pattern:
- No `try/except` that swallows errors
- Raise `RuntimeError` with a clear message on failure
- Return `List[Dict]` with the same OHLCV schema

---

## 9. Signal Lifecycle

```
AI Agent / Strategy fires →
  POST /api/broadcast { event_type: "SIGNAL_TRIGGERED", payload: {...} }
    │
    ├── telegram_gateway.format_and_send_signal(payload)
    ├── signal_store.add(payload)           ← writes data/signals.json (locked)
    └── manager.broadcast(STATE_UPDATED)    ← pushes to all WS clients

GET /api/signals → returns signal_store.get_all()
GET /api/signals/active → returns signal_store.get_active() (ACTIVE_IN_POSITION only)
GET /api/signals/stats  → returns signal_store.get_stats() (win_rate, PF, Sharpe)
```

To update a signal's exit (close a position):
```python
signal_store.update_exit(
    signal_id=1,
    exit_price=64800.0,
    exit_reason="TAKE_PROFIT",
    pnl_pct=2.19
)
```

---

## 10. Golden Rules for Backend Extension

| Rule | Reason |
|---|---|
| All state writes via `state_manager.patch()` or `set_full()` | File lock prevents corruption |
| All signal writes via `signal_store.add()` / `update_exit()` | Consistent schema, correct stats |
| Never `generate_sample_ohlcv()` — function doesn't exist | Removed — use Binance or fail |
| Raise `HTTPException(503)` when real data unavailable | Frontend handles 503 cleanly |
| No hardcoded fallback numbers in backtest metrics | They mask real computation failures |
| Broadcast `STATE_UPDATED` after every meaningful state change | Frontend stays in sync without polling |

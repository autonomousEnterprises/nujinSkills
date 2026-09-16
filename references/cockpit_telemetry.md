# Reference: Dual-Screen Cockpit, UI Architecture & Telemetry Bus

## 1. Overview: The Trader-Facing Cockpit

**NujinAI's Cockpit** provides a dual-screen, low-latency visual command deck that gives the human trader continuous visibility into Nujin's quantitative research, backtests, active trading bots, and live signals.

```
                    [ Nujin Quant AI Agent ]
                               │
             Dispatches Real-Time Event Envelopes
                               │
            ┌──────────────────┴──────────────────┐
            ▼                                     ▼
┌────────────────────────┐            ┌────────────────────────┐
│ Telegram Gateway (24/7)│            │ FastAPI Telemetry Bus  │
│ Push Alerts to Mobile  │            │ WebSocket Broadcast    │
└────────────────────────┘            └───────────┬────────────┘
                                                  │ /ws
                                                  ▼
                                      ┌────────────────────────┐
                                      │ React Dual-Screen UI   │
                                      │ (TradingView + Decks)  │
                                      └────────────────────────┘
```

---

## 2. Cockpit Screen Architecture & Hotkey Controls

The Cockpit runs on a 100vw / 100vh responsive layout organized into four dedicated operational decks:

| Screen Name | Hotkey | Component | Purpose & Visual Elements |
| --- | --- | --- | --- |
| **Chart Canvas** | **F1** | `ChartCanvas.tsx` | Full-screen interactive **TradingView Lightweight Chart** connected to live Binance 15m/1m feeds. Overlays backtest entry/exit trade markers, stop-loss invalidation lines, and take-profit target bounds. |
| **Signal Deck** | **F2** | `SignalDeck.tsx` | Real-time live execution telemetry: performance stats since activation (win rate, profit factor, annualized Sharpe, total net PnL %), active open position with live unrealized PnL, and signal history audit table. |
| **Backtest Deck** | **F3** | `BacktestDeck.tsx` | Full-width analytical audit: continuous equity growth curve, return distribution histogram, market regime survival breakdown (Bull, Bear, Range), sequential trade log, and 5-Gate Cynic Audit matrix. |
| **Strategy Manager** | **F4** | `StrategyManagerDeck.vue` | Command & Portfolio Lifecycle deck: Global Screen Mode toggle (`LIVE` vs `BACKTEST`), Realized & Benchmark Equity Growth Trajectory Curve (scope: Portfolio or individual strategy), Leaderboard with dynamic live/backtest drift metrics, sparklines, and 4-pillar Cynic audit scorecards. |
| **Cycle Screens** | **Ctrl + Space** | Root Router | Seamlessly toggle focus across all open screens. |

---

### Strategy Manager Deck (F4) — Global Screen Mode & Equity Trajectory

The **Strategy Manager Deck** includes a global operational toggle between **`LIVE TELEMETRY`** and **`BENCHMARK BACKTEST`**:
- **Global Toggle Synchronization:** Switching the mode at the top of the deck updates the entire screen simultaneously—KPI ribbon, equity trajectory chart, leaderboard columns, row sparklines, and expandable inspection scorecards.
- **Equity Growth Curve (`StrategyEquityChart`):**
  - In `LIVE` Mode: Plots the compounded equity trajectory of real closed trades from live execution bots starting at 100.00% baseline.
  - In `BACKTEST` Mode: Plots the theoretical simulation curve across historical market regimes.
  - **Scope Filter:** Toggle between `PORTFOLIO (ALL STRATEGIES)` and any isolated strategy with one click or via table row Focus button.
- **Dynamic Leaderboard Columns:**
  - `LIVE` Mode: Displays `Backtest → Live Sharpe (Drift)`, `Live Win Rate Drift`, `Live PF Drift`, `Live Max DD Drift`, and live realized sparkline series.
  - `BACKTEST` Mode: Displays `Baseline → Current Sharpe (Drift)`, `Win Rate Drift`, `Profit Factor Drift`, `Max DD Drift`, and cron re-evaluation snapshot series.

---

## 3. Real-Time Telemetry Event Bus (`/ws`)

The backend broadcasts structured JSON envelopes over `/ws`. The React cockpit listens via `hooks/useWebSocket.ts`.

### Supported Event Types & JSON Schemas

#### A. `UPSERT_WIDGET` (Research Swarm Telemetry)
Dispatched during the self-improving loop to stream live cycle progress to the agent deck:
```json
{
  "event_type": "UPSERT_WIDGET",
  "payload": {
    "id": "nujin_alpha_swarm",
    "component": "MetricCard",
    "title": "Nujin Alpha Discovery Swarm",
    "phase": "CYCLE #12",
    "props": {
      "value": "KEEP (Score 6/6)",
      "target": "Best 6/6",
      "status": "PASS",
      "subtitle": "Mutation: restructure_exit | Sharpe: 2.14 | DSR: 0.975"
    }
  }
}
```

#### B. `CHART_MARKER`
Places execution arrows and stop/target levels on the TradingView chart canvas:
```json
{
  "event_type": "CHART_MARKER",
  "payload": {
    "time": 1788163980,
    "action": "BUY",
    "price": 64250.0,
    "stop_loss": 63400.0,
    "take_profit": 65950.0,
    "annotation": "Absorption Sweep Entry"
  }
}
```

#### C. `SIGNAL_TRIGGERED`
Dispatched when an active bot generates a real-time trade signal:
```json
{
  "event_type": "SIGNAL_TRIGGERED",
  "payload": {
    "time": 1788163980,
    "action": "BUY",
    "pair": "BTC/USDT",
    "price": 64250.0,
    "stop_loss": 63400.0,
    "take_profit": 65950.0,
    "annotation": "Absorption Sweep (Hurst < 0.42, Lower Wick > 45%)",
    "reasoning_md": "**Counterparty Trap**: Aggressive sellers absorbed at support."
  }
}
```

---

## 4. Cockpit Management CLI Tools

```bash
# Build production bundle (frontend/dist/)
python tools/frontend_control.py build

# Start Cockpit Web Server in background daemon mode (Port 3000)
python tools/frontend_control.py start --port 3000 --daemon

# Check Cockpit status
python tools/frontend_control.py status

# Dispatch telemetry event from CLI
python tools/ui_dispatcher.py --event UPSERT_WIDGET --payload '<JSON>'
```

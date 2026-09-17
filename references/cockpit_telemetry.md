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
                                       │ Vue 3 Dual-Screen UI   │
                                       │ (TradingView + Decks)  │
                                       └────────────────────────┘
```

---

## 2. Cockpit Screen Architecture & Hotkey Controls

The Cockpit runs on a 100vw / 100vh responsive layout organized into four dedicated operational decks:

| Screen Name | Hotkey | Component | Purpose & Visual Elements |
| --- | --- | --- | --- |
| **Chart Canvas** | **F1** | `ChartCanvas.vue` | Full-screen interactive **TradingView Lightweight Chart** connected to live Binance 15m/1m feeds. Overlays Level 3 visual primitives (EMAs, bands, channels, S&R), Fair Value Gap (FVG) imbalance boxes, liquidity sweep levels, trade markers, and stop-loss/take-profit lines. |
| **Signal Deck** | **F2** | `SignalDeck.vue` | Real-time live execution telemetry: performance stats since activation (win rate, profit factor, annualized Sharpe, total net PnL %), active open position card with live unrealized PnL & manual close position button, and signal history audit table. |
| **Backtest Deck** | **F3** | `BacktestDeck.vue` | Full-width analytical audit: authentic calendar time windows (exact start/end dates & bar counts), continuous equity growth curve, return distribution histogram, market regime survival breakdown (Bull, Bear, Range), sequential trade log, and 5-Gate Cynic Audit matrix. |
| **Strategy Manager** | **F4** | `StrategyManagerDeck.vue` | Command & Portfolio Lifecycle deck: Global Screen Mode toggle (`LIVE TELEMETRY` vs `BENCHMARK BACKTEST`), Realized & Benchmark Equity Growth Trajectory Curve (`StrategyEquityChart.vue`), Leaderboard with direct "View Strategy on Chart (F1)" action button, dynamic live/backtest drift metrics, sparklines, and 4-pillar Cynic audit scorecards. |
| **Cycle Screens** | **Ctrl + Space** | Root Router | Seamlessly toggle focus across all open screens. |

---

### Chart Canvas Deck (F1) — Level 3 Universal Visual Primitives Engine

The chart dynamically renders strategy visual features without manual charting code:
- **Indicator Lines:** Auto-classifies and styles fast, mid, and slow EMAs, Donchian channels, Bollinger Bands, and support/resistance levels.
- **Fair Value Gap (FVG) Imbalance Boxes:** Renders semi-transparent bullish (cyan/green) and bearish (rose/red) imbalance zones with auto-expiry.
- **Liquidity Sweep Markers:** Renders high/low sweep levels and rejection signals.
- **RAF & Viewport Throttling:** Viewport panning and zooming are throttled via `requestAnimationFrame` and bar-range caching for zero drag/zoom stutter.

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
- **Direct Chart Navigation:** Each leaderboard row features a direct `View Strategy on Chart (F1)` action button that switches to F1 and activates the strategy's visual primitives.

---

## 3. Real-Time Telemetry Event Bus (`/ws`)

The backend broadcasts structured JSON envelopes over `/ws`. The Vue 3 cockpit subscribes via `frontend/src/composables/useWebSocket.ts`.

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

#### D. Additional Core Bus Events
- **`STATE_UPDATED`:** Real-time push of system-wide state modifications from `StateManager`.
- **`STRATEGIES_UPDATED`:** Broadcast when strategies are ranked, added, removed, or synced. Transmits strategy list, `portfolio_summary`, and `distribution_analytics`.
- **`MARKET_TICK`:** Real-time live OHLCV candlestick ticks from Binance or XAUUSD provider stream.
- **`SIGNAL_CLOSED`:** Emitted when an open position reaches Take-Profit, Stop-Loss, or is manually closed.
- **`SIGNALS_UPDATED` / `SIGNALS_CLEARED` / `SIGNAL_DELETED`:** Synchronization of the live signal ledger.
- **`STRATEGY_DISCOVERED`:** Emitted when a new candidate strategy `.py` file is detected on disk.
- **`TELEGRAM_ALERT` / `TELEGRAM_BROADCAST`:** Real-time push notifications delivered across Telegram subscribers.

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

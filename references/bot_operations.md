# Live Bot Operations & Non-Disruptive Supervision Guide

This reference provides instructions for supervising and operating the live trading bot without interrupting running services or causing race conditions.

---

## ⚠️ 1. Cardinal Rule: The Bot is Live

When operating in this repository, **the trading engine and market data streamers may be actively running in the background**.

- **NEVER** kill or terminate active `python server/main.py` or streamer processes unless explicitly instructed by the user.
- **NEVER** re-bind to running ports (`8000` for backend, `3000` for frontend).
- **ALWAYS** interact with the running system through the safe CLI controllers (`bot_control.py`, `state_control.py`, and `strategy_manager.py`).

---

## 🔍 2. Non-Disruptive Health & State Inspection

### Check Bot Execution Status
To verify whether the bot is running, which strategies are active, and the current broker mode:
```bash
nujinSkills/.venv/bin/python3 tools/bot_control.py status
```
This queries the live backend API and returns:
- Process status & uptime.
- Active strategy name.
- Execution mode (`paper` vs. `live`).
- Broker connectivity status.

### Inspect Live Trading Performance & Signals
To query live performance metrics without disturbing execution:
```bash
nujinSkills/.venv/bin/python3 tools/state_control.py signal-stats
```
Outputs live Win Rate, Profit Factor, Realized PnL, and Sharpe ratio.

To view recently triggered entry/exit signals:
```bash
nujinSkills/.venv/bin/python3 tools/state_control.py signals
```

To inspect specific keys in the shared runtime state:
```bash
nujinSkills/.venv/bin/python3 tools/state_control.py get --key active_strategy
nujinSkills/.venv/bin/python3 tools/state_control.py get --key open_positions
```

---

## 🚀 3. Safe Strategy Hot-Deployment

When a new strategy is synthesized, audited, and approved through the 4-stage pipeline:

### Step 1: Register Strategy
Register the emitted strategy in `strategy_manager.py`:
```bash
nujinSkills/.venv/bin/python3 tools/strategy_manager.py add --file strategies/MyAlphaStrategy.py
```

### Step 2: Hot-Deploy to Paper Mode First
Deploy the strategy to the running engine in **paper trading mode** (dry-run):
```bash
nujinSkills/.venv/bin/python3 tools/bot_control.py deploy --strategy MyAlphaStrategy --mode paper
```
The server dynamically loads the strategy module without dropping active WebSocket connections or interrupting data feeds.

### Step 3: Monitor Live Signal Generation
Confirm that the strategy starts evaluating incoming candle ticks:
```bash
nujinSkills/.venv/bin/python3 tools/state_control.py signals --strategy MyAlphaStrategy
```

### Step 4: Promotion to Live Execution
Only after observing satisfactory live behavior in paper mode, promote to live execution if approved:
```bash
nujinSkills/.venv/bin/python3 tools/bot_control.py deploy --strategy MyAlphaStrategy --mode live
```

---

## 📡 4. Live Telemetry & Alerts

### Dispatch Cockpit Widgets
Stream real-time status cards to the Cockpit UI (`http://localhost:3000`):
```bash
nujinSkills/.venv/bin/python3 tools/ui_dispatcher.py --event UPSERT_WIDGET --payload '{
  "widget_id": "quant_research_status",
  "type": "card",
  "payload": {
    "title": "Alpha Research Pipeline",
    "status": "Cynic Audit Passed",
    "metric": "DSR 0.97"
  }
}'
```

### Send Telegram Notifications
Broadcast research milestones, backtest summaries, or strategy promotions:
```bash
nujinSkills/.venv/bin/python3 tools/telegram_broadcast.py broadcast --type update --title "New Strategy Deployed" -m "Alpha strategy 'MyAlphaStrategy' hot-deployed to paper mode with DSR 0.97."
```

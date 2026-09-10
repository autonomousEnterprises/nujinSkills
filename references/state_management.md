# State Management Reference

## Overview

EdgeMiner uses a **single source of truth** for all runtime state and strategy registries.
The server, AI agent tools, and frontend all read and write the same data
through the `StateManager`, `SignalStore`, and `StrategyRegistry` classes defined in
`server/state_manager.py`.

**No component may read or write `data/state.json`, `data/signals.json`, or `data/strategies.json` directly.**
All access must go through:
- **AI agent (CLI):** `tools/state_control.py` and `tools/strategy_manager.py`  
- **Server (Python):** `from server.state_manager import state_manager, signal_store, strategy_registry`  
- **Frontend:** REST API endpoints (`/api/state`, `/api/signals`, `/api/strategies/manage`)

---

## Tools: `tools/state_control.py` & `tools/strategy_manager.py`

The standardised CLIs for AI agents to read and write shared state and manage the strategy lifecycle.

### `tools/state_control.py` Actions

| Action | What it does |
|---|---|
| `get` | Print full system state as JSON |
| `get --key <path>` | Read a single value by dotted key path |
| `patch --patch <json>` | Merge-patch state with a JSON object |
| `deploy --strategy <file>` | Run backtest and activate strategy as live |
| `stop` | Deactivate current strategy (status → STOPPED) |
| `signals` | List all persisted signals as JSON |
| `signal-stats` | Print live win rate, profit factor, Sharpe, PnL |
| `signal-add --signal <json>` | Broadcast and persist a new signal |
| `strategies` | List all managed strategies with status, ranking, and edge metrics |
| `schema` | Print the canonical state schema (key → type) |

### `tools/strategy_manager.py` Actions

| Action | What it does |
|---|---|
| `list` | Show formatted table of all strategies with status, rank, Sharpe, DSR, win rate |
| `status` | Update strategy lifecycle status (`ACTIVE_LIVE`, `CRON_BACKTEST`, `DEACTIVATED`) |
| `backtest` | Run real backtest and update registry metrics |
| `cron` | Trigger cron evaluation for all `CRON_BACKTEST` strategies and record drift history |
| `rank` | Recalculate composite multi-factor rankings |
| `summary` | Print full quant edge leaderboard and lifecycle summary for AI reasoning |

### Examples

```bash
# Read full state
python tools/state_control.py get

# Read a nested value
python tools/state_control.py get --key backtest_summary.sharpe

# Patch state (merge, not replace)
python tools/state_control.py patch --patch '{"status": "STOPPED"}'

# Run backtest and set as active deployed strategy
python tools/state_control.py deploy --strategy PropFirmVsaWickRejection.py

# Stop the active strategy
python tools/state_control.py stop

# Get all signals
python tools/state_control.py signals

# Get live performance stats since activation
python tools/state_control.py signal-stats

# Broadcast a new live signal
python tools/state_control.py signal-add --signal '{"action":"BUY","price":63404,"stop_loss":61819,"take_profit":65948,"annotation":"VSA Wick Rejection"}'

# Print state schema
python tools/state_control.py schema
```

---

## State Schema (`data/state.json`)

```json
{
  "active_strategy":    "string  — filename of the deployed strategy",
  "target_profile":     "string  — e.g. 'Prop Firm Challenge'",
  "status":             "string  — ACTIVE_DEPLOYED | STOPPED | BACKTESTING",
  "backtest_summary": {
    "sharpe":           "float   — IS Sharpe ratio",
    "win_rate":         "float   — 0.0–1.0",
    "max_drawdown":     "float   — fraction (0.014 = 1.4%)",
    "mdd_99":           "float   — Monte Carlo 99th percentile MDD",
    "dsr":              "float   — Deflated Sharpe Ratio (gate: >= 0.95)",
    "trades":           "int     — number of backtest trades",
    "profit_factor":    "float",
    "expectancy_bps":   "float   — expected bps per trade after fees"
  },
  "equity_curve":       "list[{x, y}] — cumulative PnL over time",
  "return_distribution":"list[{bin_label, count, win}] — trade return histogram",
  "regime_breakdown": {
    "bull_trend":       "{trade_count, win_rate, profit_factor, net_pnl_pct}",
    "bear_trend":       "...",
    "ranging":          "..."
  },
  "falsification_gates":{
    "gate_1_dsr":              "{dsr, observed_sr, status}",
    "gate_2_parameter_stability":"{plateau_status, matrix, status}",
    "gate_3_monte_carlo":      "{mdd_99, mdd_ratio, status}",
    "gate_4_oos_walkforward":  "{sharpe_is, sharpe_oos, retention_pct, status}",
    "gate_5_regime_survival":  "{score, status}"
  },
  "trade_markers":      "list — chart marker objects for the live chart overlay",
  "trades_detail":      "list — individual backtest trade records",
  "thesis_props":       "dict — strategy thesis metadata",
  "signals_count":      "int  — total persisted live signals",
  "last_updated":       "string — ISO 8601 UTC timestamp"
}
```

---

## Signals Schema (`data/signals.json`)

```json
[
  {
    "id":           "int    — auto-incremented",
    "time":         "int    — Unix timestamp",
    "pair":         "string — e.g. BTC/USDT",
    "action":       "string — BUY | SELL",
    "price":        "float",
    "stop_loss":    "float",
    "take_profit":  "float",
    "status":       "string — ACTIVE_IN_POSITION | CLOSED",
    "exit_price":   "float | null",
    "exit_reason":  "string | null — TAKE_PROFIT | STOP_LOSS | TIMEOUT",
    "pnl_pct":      "float  — percent PnL at exit (0.0 while open)",
    "annotation":   "string — human-readable signal label",
    "reasoning_md": "string — markdown explanation of AI reasoning",
    "strategy":     "string — strategy that generated this signal"
  }
]
```

---

## Python Module API (`server/state_manager.py`)

For use inside server code (not CLI tools):

```python
from server.state_manager import state_manager, signal_store

# Read
state = state_manager.get()
sharpe = state_manager.get_key("backtest_summary.sharpe")

# Write (atomic, file-locked)
state_manager.patch({"status": "STOPPED"})
state_manager.set_full(full_state_dict)
state_manager.reset()                    # restore DEFAULT_STATE

# Signals
signal_store.get_all()                   # list of all signals
signal_store.get_active()               # current ACTIVE_IN_POSITION signal
signal_store.add({"action": "BUY", ...}) # append + bump signals_count in state
signal_store.get_stats()                # win_rate, profit_factor, sharpe_live, etc.
```

---

## Data Flow

```
AI agent CLI                Server (FastAPI)            Frontend (React)
─────────────────           ─────────────────           ─────────────────
tools/state_control.py      server/main.py              useWebSocket hook
        │                        │  reads/writes                │
        │  REST POST/GET         ▼  via StateManager            │ REST GET
        └──────────────► server/state_manager.py ◄─────────────┘
                                 │
                         file lock (fcntl)
                                 │
                         data/state.json
                         data/signals.json
                                 │
                  WS broadcast (STATE_UPDATED)
                    ┌────────────┘
                    ▼
          All open frontend screens
          update instantly
```

---

## File Lock Safety

`StateManager` uses POSIX `fcntl.flock` with an atomic `tmp → rename` write pattern.
This prevents corruption when the AI agent CLI and the FastAPI server write simultaneously
(e.g. the AI runs `run_backtest_audit.py --save-state` while the server handles a request).

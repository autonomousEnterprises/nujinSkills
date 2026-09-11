# Reference: State Architecture, Strategy Lifecycle & Concurrency Control

## 1. Overview: Single Source of Truth

**NujinAI** enforces a strict **Single Source of Truth** architecture across three concurrent consumers:
1. **AI Agent (Nujin):** Mines alpha, audits candidates, updates parameters, and deploys bots via CLI tools.
2. **FastAPI Telemetry Server:** Serves REST endpoints and broadcasts real-time WebSocket events.
3. **React Cockpit Frontend:** Subscribes to state updates and renders charts, tables, and metric cards.

All state reads and writes are mediated by `server/state_manager.py` using **atomic POSIX file locks (`fcntl.flock`)** to eliminate race conditions.

---

## 2. Core State Datastores & Schemas

```
data/
├── state.json          # System-wide active state (active strategy, live metrics, backtest summary)
├── strategies.json     # Managed Strategy Registry (tri-state lifecycle, rankings, drift history)
└── signals.json        # SignalStore: Persisted live trade signals and active position
```

### A. `data/state.json` Schema
```json
{
  "active_strategy": "PropFirmVsaWickRejectionStrategy.py",
  "status": "ACTIVE_LIVE",
  "backtest_summary": {
    "sharpe": 2.14,
    "win_rate": 0.58,
    "profit_factor": 1.92,
    "max_drawdown": 0.038,
    "dsr": 0.975,
    "trades": 84,
    "expectancy_bps": 22.4
  },
  "thesis_props": {
    "thesis": "Dual VSA Wick Rejection with Volume Z-Score > 1.2 filter",
    "target_profile": "Prop Firm Challenge (LONG & SHORT)"
  },
  "equity_curve": [{"time": 1788163080, "equity_pct": 100.0}],
  "trade_markers": [{"time": 1788163080, "action": "BUY", "price": 64250.0}]
}
```

### B. `data/strategies.json` Tri-State Lifecycle Schema
```json
[
  {
    "id": "PropFirmVsaWickRejectionStrategy.py",
    "name": "PropFirmVsaWickRejectionStrategy",
    "file": "PropFirmVsaWickRejectionStrategy.py",
    "status": "ACTIVE_LIVE",
    "rank": 1,
    "ranking_score": 94.2,
    "tier": "S-Tier (Superior Edge)",
    "latest_backtest": {
      "sharpe": 2.14,
      "win_rate": 0.58,
      "profit_factor": 1.92,
      "max_drawdown": 0.038,
      "dsr": 0.975,
      "trades": 84,
      "last_run": "2026-09-11T14:00:00Z"
    },
    "drift_history": [
      {"timestamp": "2026-09-10T14:00:00Z", "sharpe": 2.10, "win_rate": 0.57},
      {"timestamp": "2026-09-11T14:00:00Z", "sharpe": 2.14, "win_rate": 0.58}
    ]
  }
]
```

---

## 3. The Tri-State Strategy Lifecycle

```
                     [ Nujin Self-Improving Loop ]
                                   │
                                   ▼
                        Emit to strategies/*.py
                                   │
        ┌──────────────────────────┴──────────────────────────┐
        ▼                                                     ▼
[ Passes DSR >= 0.95 ]                               [ Borderline / R&D ]
        │                                                     │
        ▼                                                     ▼
┌─────────────────────┐                               ┌─────────────────────┐
│     ACTIVE_LIVE     │                               │    CRON_BACKTEST    │
│  • Live Bot Engine  │                               │  • Periodic Drift   │
│  • Real Telegram    │                               │  • Daily Re-Audit   │
│  • Cockpit Telemetry│                               │  • Alpha Decay Test │
└──────────┬──────────┘                               └──────────┬──────────┘
           │                                                     │
   Performance Degrades                                 Fails All Gates / Retired
           │                                                     │
           └──────────────────────────┬──────────────────────────┘
                                      ▼
                           ┌─────────────────────┐
                           │     DEACTIVATED     │
                           │  • Archived Code    │
                           │  • Zero Compute Drag│
                           │  • Reactivatable    │
                           └─────────────────────┘
```

---

## 4. Multi-Factor Ranking & Scoring Formula

Strategies in `data/strategies.json` are ranked by a composite multi-factor score:

$$\text{Score} = (0.35 \times \text{Sharpe}_{\text{Norm}}) + (0.25 \times \text{WR}_{\text{Norm}}) + (0.20 \times \text{DSR}_{\text{Norm}}) + (0.20 \times \text{Expectancy}_{\text{Norm}}) - \text{Drawdown Penalty}$$

- **S-Tier:** Score $\ge 85.0$, DSR $\ge 0.95$, MaxDD $\le 4.5\%$.
- **A-Tier:** Score $\ge 70.0$, DSR $\ge 0.90$, MaxDD $\le 8.0\%$.
- **B-Tier:** Score $< 70.0$, Borderline edge; monitored under `CRON_BACKTEST`.

---

## 5. CLI Control Interfaces

### A. State Control (`tools/state_control.py`)
```bash
# Read full state or specific key
python tools/state_control.py get
python tools/state_control.py get --key backtest_summary.sharpe

# Merge-patch state (atomic locked write)
python tools/state_control.py patch --patch '{"status": "ACTIVE_LIVE"}'

# View live signal performance stats
python tools/state_control.py signal-stats
```

### B. Strategy Lifecycle Manager (`tools/strategy_manager.py`)
```bash
# List all registered strategies with ranks & tiers
python tools/strategy_manager.py list

# Update lifecycle status
python tools/strategy_manager.py status --strategy MyStrategy.py --to ACTIVE_LIVE

# Trigger cron re-backtest across all CRON_BACKTEST strategies
python tools/strategy_manager.py cron

# Inspect alpha drift across daily runs
python tools/strategy_manager.py drift --strategy MyStrategy.py
```

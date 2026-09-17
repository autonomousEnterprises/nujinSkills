# Reference: State Architecture, Strategy Lifecycle & Concurrency Control

## 1. Overview: Single Source of Truth

**NujinAI** enforces a strict **Single Source of Truth** architecture across three concurrent consumers:
1. **AI Agent (Nujin):** Mines alpha, audits candidates, updates parameters, and deploys bots via CLI tools.
2. **FastAPI Telemetry Server:** Serves REST endpoints and broadcasts real-time WebSocket events.
3. **Vue 3 Cockpit Frontend:** Subscribes to state updates and renders charts, tables, and metric cards.

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

## 4. Institutional 4-Pillar Composite Scoring Model

Strategies in `data/strategies.json` are ranked by the Institutional 4-Pillar Composite Score ($0.0 \dots 100.0$):

$$\text{Composite Score} = (0.35 \times \text{Edge}) + (0.30 \times \text{Robustness}) + (0.25 \times \text{Risk}) + (0.10 \times \text{Drift})$$

- **S-Tier (Superior Edge):** Score $\ge 80.0$, Sharpe $\ge 2.50$, DSR $\ge 0.95$, MaxDD $\le 4.5\%$, Win Rate $\ge 50\%$, PF $\ge 1.50$, Trades $\ge 25$.
- **A-Tier (Robust Edge):** Score $\ge 65.0$, Sharpe $\ge 1.80$, DSR $\ge 0.90$, MaxDD $\le 5.0\%$, PF $\ge 1.30$, Trades $\ge 20$.
- **B-Tier (Incubation Alpha):** Score $\ge 45.0$, positive core expectancy ($\text{Sharpe} > 1.0$, $PF > 1.1$).
- **C-Tier (Sub-Hurdle / Decayed):** Score $< 45.0$, failed primary risk hurdles ($\text{MaxDD} > 8.0\%$ or negative Sharpe).

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
# Display institutional 4-pillar rankings & leaderboard
python tools/strategy_manager.py rank

# Deep quantitative insights & tier rationale for a strategy
python tools/strategy_manager.py insights <StrategyName>

# Portfolio correlation matrix and regime orthogonality audit
python tools/strategy_manager.py correlation --threshold 0.50

# Synchronize disk strategies/*.py with registry
python tools/strategy_manager.py sync

# Safely remove obsolete strategy from disk and registry
python tools/strategy_manager.py remove <StrategyName>

# Add new strategy file to production library
python tools/strategy_manager.py add <path_to_strategy.py>

# Trigger cron re-backtest across all CRON_BACKTEST strategies
python tools/strategy_manager.py cron
```

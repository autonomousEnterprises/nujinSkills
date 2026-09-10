# Reference: Strategy Management System & Lifecycle Architecture

## 1. Overview & Quantitative Motivation

Autonomous quantitative edge mining requires continuous hypothesis generation, testing, and lifecycle monitoring. A strategy that passes initial in-sample testing may suffer from alpha decay, regime shifts, or execution drift when market microstructures transition from range-bound chop to volatile trending phases.

The **Strategy Management System** provides a structured lifecycle framework for the AI Agent and the human trader:
1. **Continuous Discovery:** Over time, the AI agent discovers and emits more strategies into `strategies/*.py`.
2. **Tri-State Lifecycle Management:** Strategies are tagged across three distinct operational states:
   - `ACTIVE_LIVE`: Deployed to the execution bot (live or dry-run) and streaming real-time signals to Telegram and the dashboard.
   - `CRON_BACKTEST`: Monitored on recurring schedules (or on-demand cron triggers) against newly synced market data to track statistical drift over time.
   - `DEACTIVATED`: Archived or underperforming setups preserved for analytical benchmarking and potential future parameter re-mining.
3. **Multi-Factor Ranking Leaderboard:** Automated quantitative scoring based on risk-adjusted metrics, penalizing statistical rejection ($DSR < 0.95$) and excessive drawdown.
4. **Statistical Drift Tracking:** Historical snapshots of Sharpe, DSR, Win Rate, and Drawdown recorded across evaluation cycles to detect edge degradation before capital is committed.

---

## 2. Strategy Lifecycle State Machine

```
              ┌────────────────────────────────────────────────────────┐
              │              AI Dialectic Discovery Loop               │
              │   (Feature Extraction, Vectorized Screening, Cynic)    │
              └───────────────────────────┬────────────────────────────┘
                                          │
                                          ▼
                               ┌─────────────────────┐
                               │  Emit & Register    │
                               │  strategies/*.py    │
                               └──────────┬──────────┘
                                          │
                     ┌────────────────────┴────────────────────┐
                     ▼                                         ▼
           [ Passes DSR >= 0.95 ]                    [ Borderline / R&D ]
                     │                                         │
                     ▼                                         ▼
          ┌─────────────────────┐                   ┌─────────────────────┐
          │     ACTIVE_LIVE     │                   │    CRON_BACKTEST    │
          │  • Live Bot Engine  │                   │  • Periodic Audits  │
          │  • Real Telegram    │                   │  • Drift Tracking   │
          │  • Live PnL Telemetry│                   │  • Alpha Decay Test │
          └──────────┬──────────┘                   └──────────┬──────────┘
                     │                                         │
            Performance Degrades                     Fails All Gates / Retired
                     │                                         │
                     └────────────────────┬────────────────────┘
                                          ▼
                               ┌─────────────────────┐
                               │     DEACTIVATED     │
                               │  • Archived Code    │
                               │  • Zero Compute Drag│
                               │  • Reactivatable    │
                               └─────────────────────┘
```

---

## 3. Single Source of Truth: `data/strategies.json` Schema

All strategy records are stored in `data/strategies.json` and accessed exclusively through `StrategyRegistry` with atomic POSIX file locks (`fcntl.flock`).

```json
[
  {
    "id": "GoatFundedTraderXauusdScalper.py",
    "name": "GoatFundedTraderXauusdScalper",
    "file": "GoatFundedTraderXauusdScalper.py",
    "path": "strategies/GoatFundedTraderXauusdScalper.py",
    "display_name": "Goat Funded Trader XAUUSD Prop Scalper",
    "target_profile": "Goat Funded Trader Prop Scalper (2m-15m)",
    "thesis": "Dynamic Range Expansion Momentum Train on 1m-15m London/NY sessions",
    "symbol": "XAU/USD",
    "timeframe": "1m",
    "status": "ACTIVE_LIVE",
    "rank": 1,
    "ranking_score": 92.4,
    "tier": "S-Tier (Superior Edge)",
    "latest_backtest": {
      "sharpe": 3.56,
      "win_rate": 0.5,
      "profit_factor": 1.77,
      "max_drawdown": 0.0075,
      "mdd_99": 0.0165,
      "dsr": 0.99,
      "trades": 90,
      "expectancy_bps": 3.48,
      "last_run": "2026-09-10T16:29:48Z"
    },
    "backtest_equity_curve": [
      { "time": 1788163080, "equity_pct": 100.0, "drawdown_pct": 0.0 },
      { "time": 1788163980, "equity_pct": 100.07, "drawdown_pct": 0.0 }
    ],
    "falsification_gates": {
      "gate_1_dsr": { "dsr": 0.99, "status": "PASS" },
      "gate_2_parameter_stability": { "status": "PASS", "plateau_status": "STABLE_PLATEAU" },
      "gate_3_monte_carlo": { "mdd_99": 0.0165, "status": "PASS" },
      "gate_4_oos_walkforward": { "retention_pct": 78.0, "status": "PASS" },
      "gate_5_regime_survival": { "score": 90.0, "status": "PASS" }
    },
    "live_stats": {
      "total_trades": 12,
      "open_trades": 0,
      "wins": 8,
      "losses": 4,
      "win_rate": 0.6667,
      "profit_factor": 2.14,
      "sharpe_live": 2.85,
      "total_pnl_pct": 5.42
    },
    "live_equity_curve": [
      { "time": 1788200000, "equity_pct": 100.0, "drawdown_pct": 0.0 },
      { "time": 1788203600, "equity_pct": 101.4, "drawdown_pct": 0.0 }
    ],
    "cron_config": {
      "enabled": true,
      "interval": "1h",
      "last_run": "2026-09-10T16:29:48Z",
      "drift_history": [
        {
          "timestamp": "2026-09-08T12:00:00Z",
          "sharpe": 3.45,
          "dsr": 0.98,
          "win_rate": 0.49,
          "max_drawdown": 0.008,
          "trades": 84
        },
        {
          "timestamp": "2026-09-10T16:29:48Z",
          "sharpe": 3.56,
          "dsr": 0.99,
          "win_rate": 0.50,
          "max_drawdown": 0.0075,
          "trades": 90
        }
      ]
    },
    "created_at": "2026-09-10T16:29:00Z",
    "updated_at": "2026-09-10T16:29:48Z"
  }
]
```

---

## 4. Quantitative Ranking Formula & Tiers

The ranking engine calculates a composite score (0–100 scale) for each strategy:

$$\text{Score} = (\text{Sharpe} \times 3.5) + (\text{DSR} \times 25.0) + (\text{WinRate} \times 20.0) + \left(\min(\text{ProfitFactor}, 5.0) \times 5.0\right) - (\text{MaxDD} \times 30.0)$$

### Penalty Rules:
- If $\text{DSR} < 0.95$ and $\text{DSR} > 0$, a hard **15.0-point penalty** is subtracted (falsification hurdle violation).
- If $\text{Trades} == 0$, $\text{Score} = 0.0$.

### Tier Classification:
- **`S-Tier (Superior Edge)`**: $\text{Score} \ge 80.0$ — Exceptional edge, passes all 5 gates with robust DSR $\ge 0.96$. Prime candidate for `ACTIVE_LIVE`.
- **`A-Tier (Robust Edge)`**: $65.0 \le \text{Score} < 80.0$ — Profitable, stable parameters, suitable for live paper execution or cron tracking.
- **`B-Tier (Marginal Edge)`**: $50.0 \le \text{Score} < 65.0$ — Edge exists but sensitive to volatility or regime shifts.
- **`C-Tier (Sub-Hurdle)`**: $\text{Score} < 50.0$ — Failed statistical gates or unbacktested. Candidate for deactivation or re-engineering.

---

## 5. CLI Tool Reference: `tools/strategy_manager.py`

| Action | Command | Purpose |
|---|---|---|
| `list` | `python tools/strategy_manager.py list` | Formatted table of all strategies with status, rank, Sharpe, DSR, Win Rate, and MaxDD |
| `status` | `python tools/strategy_manager.py status <name> <status> [--exclusive]` | Transition strategy lifecycle status (supports concurrent multi-bot execution) |
| `portfolio` | `python tools/strategy_manager.py portfolio` | Aggregated portfolio performance across all currently active strategies (Blended Win Rate, Sharpe, Trades, PnL) |
| `drift` | `python tools/strategy_manager.py drift` | Strategy profitability drift trajectory (gaining edge vs decaying edge) & distributions |
| `backtest` | `python tools/strategy_manager.py backtest <name>` | Execute full backtest and update registry metrics |
| `cron` | `python tools/strategy_manager.py cron` | Evaluate all `CRON_BACKTEST` strategies and append snapshots to `drift_history` (Daily cadence) |
| `rank` | `python tools/strategy_manager.py rank` | Recalculate composite leaderboard rankings |
| `register` | `python tools/strategy_manager.py register <name> --thesis <...> --profile <...>` | Register a newly mined strategy |
| `summary` | `python tools/strategy_manager.py summary` | Comprehensive Markdown/ASCII health leaderboard for AI agent reasoning |

---

## 6. Parallel Execution & Daily Cron Architecture

1. **Concurrent Multi-Bot Execution:**
   - Multiple strategies can simultaneously hold `ACTIVE_LIVE` status (e.g. concurrent scalping on `XAU/USD` 1m and momentum fading on `BTC/USDT` 15m).
   - `BotSupervisor` maintains a dictionary of running processes, allowing independent start/stop lifecycle management per strategy.
2. **Aggregated Portfolio Performance:**
   - Evaluates portfolio-level blended win rate, volume-weighted Sharpe ratio, combined profit factor, and total realized PnL across all active bots.
3. **Daily Cron Cadence (24 Hours):**
   - Background evaluations run once every 24 hours (`interval: "24h"` / `86400s`) to track structural alpha drift across market regimes without CPU waste.
4. **Profitability Drift & Distribution Tracking:**
   - Identifies whether each strategy is **Gaining Edge** ($\Delta > 0$), **Decaying Edge** ($\Delta < 0$), or **Stable**.
   - Binned distributions for Sharpe ratios, Quant tiers, and asset exposure diversification.

---

## 7. AI Agent Autonomous Heuristics

When creating and testing strategies over time, the AI agent adheres to the following guidelines:
1. **Parallel Exploration & Diversification:** Discover strategies across uncorrelated assets (`XAU/USD`, `BTC/USDT`, `ETH/USDT`) and run viable candidates concurrently in `ACTIVE_LIVE`.
2. **Do not immediately deploy untested strategies to `ACTIVE_LIVE`.** Register new strategies as `CRON_BACKTEST` with a 24h evaluation interval.
3. **Monitor Drift Across Daily Cron Cycles:** If a strategy maintains $\text{DSR} \ge 0.95$ and stable Sharpe across consecutive daily evaluations, promote it to `ACTIVE_LIVE`.
4. **Alpha Decay Retirement:** If an active strategy's live win rate or rolling Sharpe deteriorates below target thresholds ($\Delta \text{Sharpe} < -0.20$ or $\Delta \text{WinRate} < -3\%$), demote it to `CRON_BACKTEST`.
5. **Deactivation Policy:** Strategies failing multiple gates with $\text{DSR} < 0.80$ should be transitioned to `DEACTIVATED` to avoid unnecessary compute overhead during daily cron runs.


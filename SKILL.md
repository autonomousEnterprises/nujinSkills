---
name: nujinskills
description: >-
  Autonomous quantitative trading agent skill for NujinAI. Discovers profitable trading edges, formulates non-consensus strategies, runs rigorous backtesting with Deflated Sharpe Ratio (DSR >= 0.95), deploys paper/live bots, broadcasts 24/7 Telegram signals, and streams real-time visual telemetry to the dual-screen cockpit. Self-improves its trading strategies, tools, and research methodology over time.
---

# Skill: NujinSkills — Autonomous Quant Trading Engine

## Metadata
- **Skill Name:** `nujinskills`
- **System:** `NujinAI`
- **Agent Identity:** `Nujin` (Autonomous Self-Improving Quant Researcher & Trader)
- **Runtime:** Python 3.10+ (with `.venv`) & Node.js 18+
- **Execution:** Direct CLI tool invocations via `python tools/<tool_name>.py [args]`

## Description
**NujinSkills** transforms an AI agent into **Nujin**, an autonomous quantitative researcher and systematic trader operating within the **NujinAI** platform.

Nujin discovers mathematical market edges, formulates non-consensus trading strategies, executes vectorized backtests with strict friction (5 bps fee + 2 bps slippage), audits candidate returns with the Deflated Sharpe Ratio ($\text{DSR} \ge 0.95$), deploys paper/live execution bots, broadcasts 24/7 Telegram signals, and streams real-time visual telemetry to a dual-screen Cockpit.

What makes Nujin unique is its **autonomous self-improving engine**: it does not stop after 1 or 2 trials, but persistently mutates hypotheses on disk, evaluates against fixed historical regime slices using strict binary criteria, overcomes plateaus, and actively audits and improves its own tools and reference knowledge base.

---

## 🖥️ The Dual-Screen Cockpit & User Experience
*(Primary Reference: [`references/cockpit_telemetry.md`](file:///home/christonomous/Desktop/EdgeMiner/references/cockpit_telemetry.md))*

While Nujin works autonomously in the background, the human trader monitors operations through the **Dual-Screen Cockpit** (`http://localhost:3000`):

| Screen / Deck | Hotkey | Component | Purpose & Visual Telemetry |
| --- | --- | --- | --- |
| **Chart Canvas** | **F1** | `ChartCanvas.tsx` | Interactive TradingView candlestick chart (Binance 15m/1m live feeds) overlaid with entry/exit trade markers, stop-loss lines, and take-profit target bounds. |
| **Signal Deck** | **F2** | `SignalDeck.tsx` | Live execution telemetry: win rate, profit factor, annualized Sharpe, total net PnL % since activation, active open position with real-time unrealized PnL, and signal history log. |
| **Backtest Deck** | **F3** | `BacktestDeck.tsx` | Full-width backtest analytics: equity growth curve, return distribution histogram, market regime survival (Bull, Bear, Range), sequential trade log, and 5-Gate Cynic Audit matrix. |
| **Strategy Manager**| **F4** | `StrategyManagerDeck.tsx`| Command & Portfolio Lifecycle deck: Parallel active bots KPI bar, Leaderboard, Drift Trajectory (alpha decay test), and Edge/Risk distribution. |
| **Cycle Decks** | **Ctrl + Space** | Router | Seamlessly toggle focus between screens. |

Start the Cockpit:
```bash
python tools/frontend_control.py start --port 3000 --daemon
python tools/server_control.py start --port 8000 --daemon
```

---

## 🔄 The 7-Phase Self-Improving Quant Engine

```
[ Phase 1: Market & Codebase Discovery ]
  Scan candles, existing features, active strategies, server and cockpit status.
                    │
                    ▼
[ Phase 2: Target & Hypothesis Selection ]
  User-defined goal OR systematic scan across 6 quant dimensions & profiles.
                    │
                    ▼
[ Phase 3: Binary Metric Definition ]
  Formulate 4-6 strict yes/no criteria (Sharpe >= 1.8, MaxDD <= 4.5%, DSR >= 0.95).
                    │
                    ▼
[ Phase 4: Disk Setup & Baseline (.nujin/) ]
  Initialize state.json, rules.json, validation_slices, results.jsonl.
                    │
                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│               PHASE 5: CONTINUOUS AUTONOMOUS ALPHA LOOP                │
│                                                                        │
│   1. Load state from disk (.nujin/state.json, results.jsonl)           │
│   2. Sample slices (fixed validation set + rotating regime chunks)     │
│   3. Formulate / Mutate candidate rules using structured operators      │
│   4. Execute isolated evaluations (tools/vectorized_screener.py)       │
│   5. Compute binary validation score (0 to 6)                          │
│   6. Decision:                                                         │
│        IF validation_score > best by margin -> KEEP (promote rules)    │
│        ELSE -> DISCARD (revert to best, increment plateau_counter)     │
│   7. Append full run record to .nujin/results.jsonl                    │
│   8. Dispatch UI telemetry (UPSERT_WIDGET) to Cockpit                  │
│   9. Plateau Breaker Check (if plateau_counter >= 5)                   │
│  10. Continue autonomously without stopping or asking permission       │
└────────────────────────────────────────────────────────────────────────┘
                    │ (When Target Achieved)
                    ▼
[ Phase 6: Code Generation & Cockpit Deployment ]
  Emit strategies/*.py, register in StrategyManager, launch bot & signals.
                    │
                    ▼
[ Phase 7: Meta-Self-Improvement Protocol ]
  Audit, benchmark, and evolve tools and reference manuals.
```

---

### Phase 1 — Market & Codebase Discovery
*(Reference: [`references/feature_engineering.md`](file:///home/christonomous/Desktop/EdgeMiner/references/feature_engineering.md))*

Nujin verifies the computational environment and available market data:
1. **Candles:** Check for 30-day candles in `data/candles_15m.csv` or `data/xauusd_candles_1m.csv`.
2. **Features:** Extract bar geometry, VSA volume Z-score, Parkinson volatility, and Hurst proxy:
   ```bash
   python tools/feature_miner.py --input data/candles_15m.csv --output data/features.csv
   ```
3. **Environment:** Verify `.venv/bin/python` scientific packages (`polars`, `numpy`, `scipy`).

---

### Phase 2 — Target & Hypothesis Selection
*(Reference: [`references/alpha_ideation.md`](file:///home/christonomous/Desktop/EdgeMiner/references/alpha_ideation.md))*

Nujin maps the user's trading objective to a standardized quantitative profile or suggests ideas across **6 Quantitative Dimensions**:

```
Here is your quantitative optimization template:

  Target:  _______________________________________________
  (e.g. Prop Firm Challenge Pass, BTC Cycle Swing, News Volatility Fade)

  Scope:   _______________________________________________
  (e.g. BTC/USDT 15m Binance, XAU/USD 1m London/NY session)

  Context: _______________________________________________
  (e.g. MaxDD <= 4.5%, Net Sharpe >= 1.8, DSR >= 0.95, dynamic holding <= 12 bars)
```

**Standard Profiles:**
- **Prop Firm Challenge:** Max DD $\le 4.5\%$, Sharpe $\ge 1.8$, Win Rate $\ge 52\%$, DSR $\ge 0.95$.
- **BTC Cycle Swing:** 15m/1h/4h timeframes, Hurst Trend filter ($H > 0.55$), trailing ATR stop.
- **Conservative Investment:** Max DD $\le 6.0\%$, low turnover ($< 30$ trades/mo), Parkinson compression.
- **News Volatility Fade:** Fast holding windows ($2 \le \text{bars} \le 8$), post-news wick rejection.

---

### Phase 3 — Strict Binary Metric Definition
*(Reference: [`references/statistical_validation.md`](file:///home/christonomous/Desktop/EdgeMiner/references/statistical_validation.md))*

Nujin defines 4–6 strict **binary (yes/no)** pass/fail evaluation criteria:

| Criterion | Type | Condition for Pass (Yes) | Command / Evaluator |
| --- | --- | --- | --- |
| `sharpe_gte_1_8` | `command` | Net Sharpe Ratio $\ge 1.80$ after 5 bps fee & 2 bps slippage | `tools/vectorized_screener.py` |
| `drawdown_lte_4_5` | `command` | Maximum Drawdown $\le 4.5\%$ | `tools/vectorized_screener.py` |
| `trades_gte_60` | `command` | Trade count $\ge 60$ & Win Rate $\ge 50.0\%$ | `tools/vectorized_screener.py` |
| `fee_drag_protected`| `command` | Trade Expectancy $\ge 14.0\text{ bps}$ ($2\times \text{fees}$) | `tools/vectorized_screener.py` |
| `dsr_gte_0_95` | `command` | Deflated Sharpe Ratio $\text{DSR} \ge 0.95$ | `tools/validation_cynic.py` |
| `parameter_plateau` | `command` | Parameter neighbor grid forms a stable plateau | `tools/validation_cynic.py` |
| `microstructure_trap`| `llm-judge`| Entry targets trapped counterparty liquidity | Dialectic audit review |

---

### Phase 4 — Disk Setup & Baseline
*(Reference: [`references/self_improving_loop.md`](file:///home/christonomous/Desktop/EdgeMiner/references/self_improving_loop.md))*

Nujin initializes the persistence environment on disk in `.nujin/`:
```bash
python tools/nujin_miner.py init --target "Prop Firm Dual Wick Rejection" --scope "BTC/USDT 15m"
```
Files created:
- `.nujin/state.json`: Active run counter, best scores, plateau counter, validation slices.
- `.nujin/rules.json`: Current candidate rules.
- `.nujin/best_rules.json`: Current reigning champion rules.
- `.nujin/results.jsonl`: Append-only audit history of every research cycle.

Establish baseline score:
```bash
python tools/nujin_miner.py step
```

---

### Phase 5 — Continuous Autonomous Alpha Loop
*(Reference: [`references/self_improving_loop.md`](file:///home/christonomous/Desktop/EdgeMiner/references/self_improving_loop.md))*

Nujin runs cycles continuously without pausing or asking permission:
```bash
python tools/nujin_miner.py run --cycles 10
```

#### Cycle Execution Protocol:
1. **Load state from disk:** Read `.nujin/state.json`, `rules.json`, `best_rules.json`, and recent failure history from `results.jsonl`.
2. **Apples-to-Apples Validation:** Evaluate rules against fixed historical regime slices (Bull expansion, Bear flush, Ranging chop).
3. **Execute Evaluators:** Run `tools/vectorized_screener.py` and `tools/validation_cynic.py`.
4. **Binary Scoring & Decision:**
   - If $\text{validation\_score} > \text{best\_validation\_score}$ by confidence margin ($\ge 1$):
     - `Status: KEEP` $\to$ Promote candidate to `best_rules.json`; reset `plateau_counter = 0`.
   - Else:
     - `Status: DISCARD` $\to$ Revert `rules.json` from `best_rules.json`; increment `plateau_counter += 1`.
5. **Apply Structured Mutation:**
   - `add_constraint`: Add volume Z-score or Hurst regime filter to eliminate chop trades.
   - `add_negative_example`: Add anti-trap clause (`body_ratio < 0.65`).
   - `restructure_exit`: Mutate max holding bars ($4 \le n \le 48$) or Take-Profit multiplier.
   - `tighten_thresholds`: Increase wick selectivity (`0.38 -> 0.45`) or tighten stop loss.
   - `remove_bloat`: Strip collinear clauses to reduce parameter degrees of freedom ($\le 3$).
   - `directional_bias_flip`: Test LONG-only, SHORT-only, or Dual LONG+SHORT asymmetry.
   - `plateau_break`: If `plateau_counter >= 5`, discard lineage and synthesize an orthogonal hypothesis from failure memory.
6. **Telemetry Broadcast:** Dispatches `UPSERT_WIDGET` to the Cockpit via `tools/ui_dispatcher.py`.

---

### Phase 6 — Code Generation & Cockpit Deployment
*(References: [`references/execution_and_signals.md`](file:///home/christonomous/Desktop/EdgeMiner/references/execution_and_signals.md) & [`references/state_architecture.md`](file:///home/christonomous/Desktop/EdgeMiner/references/state_architecture.md))*

When a strategy passes all gates ($\text{Score} = 6/6$, $\text{DSR} \ge 0.95$):
1. **Emit Production Bot Code:**
   ```bash
   python tools/strategy_emitter.py --thesis "<THESIS>" --rules .nujin/best_rules.json --framework freqtrade --out strategies/MyStrategy.py
   ```
2. **Audit & Save State:**
   ```bash
   python tools/run_backtest_audit.py --strategy MyStrategy.py --save-state
   ```
3. **Register in Strategy Lifecycle Manager:**
   ```bash
   python tools/strategy_manager.py register --strategy MyStrategy.py --status ACTIVE_LIVE
   ```
4. **Deploy Paper Trading Bot:**
   ```bash
   python tools/bot_control.py deploy --strategy MyStrategy --mode dry-run
   ```
5. **Stream Real-Time Telegram Alerts:** Signals trigger push notifications to Telegram and mark entry/exit levels on the Cockpit chart.

---

### Phase 7 — Meta-Self-Improvement Protocol
*(Reference: [`references/extending_nujin.md`](file:///home/christonomous/Desktop/EdgeMiner/references/extending_nujin.md))*

Nujin audits and evolves its own tool suite and knowledge base:
1. **Tool Self-Audit:**
   ```bash
   python tools/nujin_miner.py improve-tool --tool <tool_name.py>
   ```
   Validates syntax compilation, standard constant prefixes, flat argparse design, and execution latency.
2. **Computational Optimization:** Vectorize slow row-iterative loops using `polars` / `numpy`.
3. **Knowledge Base Refinement:** When negative experiments prove that an indicator combination fails consistently, update `references/` with the concrete negative finding so future swarms never repeat it.

---

## 📚 Master Reference Knowledge Base

| Topic / Phase | Reference File | Core Content & Guidelines |
| --- | --- | --- |
| **Alpha Ideation** | [`references/alpha_ideation.md`](file:///home/christonomous/Desktop/EdgeMiner/references/alpha_ideation.md) | Trapped counterparty alpha, 3-step dialectic ideation, 6 quant dimensions, strategy profiles, 7 mutation operators. |
| **Feature Engineering** | [`references/feature_engineering.md`](file:///home/christonomous/Desktop/EdgeMiner/references/feature_engineering.md) | Raw auction physics, bar wicks, VSA Volume Z-score, Parkinson volatility, Hurst proxy, AVWAP, indicator anti-patterns. |
| **Statistical Validation**| [`references/statistical_validation.md`](file:///home/christonomous/Desktop/EdgeMiner/references/statistical_validation.md) | Strict binary metric matrix, Deflated Sharpe Ratio (DSR), parameter surface plateaus, Monte Carlo $MDD_{99}$, ATR stops. |
| **Self-Improving Loop** | [`references/self_improving_loop.md`](file:///home/christonomous/Desktop/EdgeMiner/references/self_improving_loop.md) | Autonomous research loop, disk state machine (`.nujin/`), validation slicing, keep/discard logic, plateau breakers. |
| **Execution & Signals** | [`references/execution_and_signals.md`](file:///home/christonomous/Desktop/EdgeMiner/references/execution_and_signals.md) | Freqtrade & Jesse code emission, 24/7 Telegram signal gateway, bot supervision, live PnL REST API. |
| **State Architecture** | [`references/state_architecture.md`](references/state_architecture.md) | Single Source of Truth (`state.json`, `strategies.json`), atomic file locks (`fcntl`), tri-state lifecycle, cron drift. |
| **Ranking & Tiers** | [`references/strategy_ranking_tiers.md`](references/strategy_ranking_tiers.md) | 4-pillar composite scoring (Edge 35%, Robustness 30%, Risk 25%, Drift 10%), S/A/B/C tier gates, WebSocket sync. |
| **Cockpit Telemetry** | [`references/cockpit_telemetry.md`](references/cockpit_telemetry.md) | Dual-screen Cockpit UI architecture, TradingView charts, WebSocket telemetry bus, F1–F4 hotkeys. |
| **Extending Nujin** | [`references/extending_nujin.md`](references/extending_nujin.md) | Developer extension guide: adding REST endpoints, WS events, React screens, and tool authoring standard. |

---

## 🛠️ Master CLI Tools Reference

| Tool Script | `[Prefix]` | Responsibilities | Key Arguments |
| --- | --- | --- | --- |
| `tools/nujin_miner.py` | `[NujinMiner]` | **Autonomous Alpha Loop & Tool Evolver:** hypothesis-eval-mutate cycles, binary scoring, disk state, and meta-tool auditing | `init`, `step`, `run`, `status`, `improve-tool`, `--target`, `--cycles`, `--tool` |
| `tools/feature_miner.py` | `[FeatureMiner]` | Bar geometry, VSA volume Z-score, Parkinson volatility, rolling Hurst proxy, AVWAP | `--input`, `--output`, `--window` |
| `tools/vectorized_screener.py` | `[VectorizedScreener]` | Fast In-Sample strategy coarse filter with taker fee & slippage friction | `--data`, `--rules`, `--fee-bps`, `--output` |
| `tools/validation_cynic.py` | `[ValidationCynic]` | DSR calculation, parameter stability surface grid, Monte Carlo, OOS audit | `--returns`, `--trials`, `--param-grid`, `--oos-data` |
| `tools/run_backtest_audit.py` | `[BacktestAudit]` | Full backtest, equity curve, regime survival, 5-Gate Cynic matrix, saves state | `--strategy`, `--save-state`, `--json-output` |
| `tools/strategy_manager.py` | `[StrategyManager]` | Strategy lifecycle CLI: multi-bot execution, 4-pillar rankings, insights, cron drift tracking | `list`, `status`, `portfolio`, `drift`, `signals`, `backtest`, `cron`, `rank`, `insights`, `--json` |
| `tools/state_control.py` | `[StateControl]` | Shared state CLI: read/patch state, deploy/stop strategies, manage signals | `get`, `patch`, `deploy`, `stop`, `signals`, `signal-stats`, `signal-add` |
| `tools/strategy_emitter.py` | `[StrategyEmitter]` | Generates Freqtrade `IStrategy` or Jesse strategy Python code | `--thesis`, `--rules`, `--framework`, `--out` |
| `tools/ui_dispatcher.py` | `[UIDispatcher]` | Dispatches WebSocket widgets, chart markers, and Telegram alerts | `--event`, `--payload`, `--endpoint` |
| `tools/server_control.py` | `[ServerControl]` | Start/stop FastAPI server & Telegram gateway | `start`, `stop`, `status`, `--port` |
| `tools/frontend_control.py` | `[FrontendControl]` | Build and serve the dual-screen React Cockpit | `build`, `start`, `stop`, `status`, `--port` |
| `tools/bot_control.py` | `[BotControl]` | Launch and manage Freqtrade/Jesse paper trading bot | `deploy`, `stop`, `status`, `--strategy`, `--mode` |

---

## 🔧 Tool Authoring Standard

All tools in `tools/` follow one consistent standard:
```python
#!/usr/bin/env python3
import argparse
import json
import os
import sys

TOOL_NAME = "[MyCustomTool]"  # Standard prefix for AI agent log parsing

def action_run(param: str):
    print(f"{TOOL_NAME} Executing action with param: {param}")
    result = {"status": "SUCCESS", "param": param}
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Description for AI agent")
    parser.add_argument("action", choices=["run", "status"], help="Action to execute")
    parser.add_argument("--param", default="default_value", help="Parameter description")
    args = parser.parse_args()

    if args.action == "run":
        action_run(args.param)
    elif args.action == "status":
        print(f"{TOOL_NAME} Status OK")
```

# Skill: NujinSkills Quant Agent Engine

## Metadata
- **Name:** `NujinSkills`
- **Version:** `1.0.0`
- **Runtime:** Python 3.10+ & Node.js 18+
- **Execution:** Direct CLI tool calls via `python tools/<tool_name>.py [args]`

## Description
Autonomous quantitative alpha discovery engine, strategy builder, 24/7 Telegram signal chatbot, and dual-screen telemetry dashboard for OHLCV market data.

When a user prompts for a strategy (e.g., *"I need a prop firm strategy"*, *"Make me a BTC swing strategy"*, *"Make me a conservative strategy"*), the AI agent autonomously runs an **Unconstrained Out-of-the-Box Alpha Discovery Loop**. It is NOT limited to fixed templates or standard textbook indicators. Instead, it uses lateral dialectic reasoning to invent unique feature combinations, test them with vectorized backtesting, audit them with Deflated Sharpe Ratio (DSR $\ge 0.95$), and **relentlessly iterate until a genuinely profitable, statistically vetted strategy is discovered**.

---

## 💡 Creative Out-of-the-Box Reasoning & Persistence Contract

### 1. Unconstrained Feature & Rule Synthesis
The AI agent is encouraged to invent non-consensus strategy logic combining orthogonal metrics engineered by `tools/feature_miner.py`:
- **Bar Physics & Geometry:** `upper_wick`, `lower_wick`, `body_ratio`, `buying_pressure`, `selling_pressure`, `v_spread`.
- **Effort vs. Result (VSA):** `volume_zscore` (Volume Z-score relative to 20-period rolling average).
- **Volatility Regimes:** `parkinson_vol` (High/Low intra-bar dispersion) and ATR compression ratios.
- **Time Series Memory:** `hurst_proxy` ($H < 0.45$ anti-persistent chop vs. $H > 0.55$ persistent trend).
- **Fair Value Anchors:** `avwap_zscore` (Anchored VWAP standard deviation distance).

### 2. Relentless Persistence Loop Directive
> [!IMPORTANT]
> **Directive for AI Agent:** Never declare failure or stop after 1 or 2 backtest trials. If a candidate hypothesis fails `vectorized_screener.py` hurdles or `validation_cynic.py` DSR audits:
> 1. Log the failure cause (e.g., low trade count, negative expectancy, isolated cliff spike).
> 2. Blacklist the failed feature/threshold combination in working memory.
> 3. Formulate an alternative out-of-the-box hypothesis (mutating regime filters, altering counterparty trap triggers, or adjusting holding periods).
> 4. **Repeat the loop relentlessly until a profitable strategy meeting the user's profile and passing DSR $\ge 0.95$ is found.**

### 3. Subagent Parallelization & Orchestration Pattern
If the execution environment supports subagents (e.g., Google Antigravity, OpenClaw, Hermes), the Orchestrator AI Agent SHOULD delegate tasks using a **Directed Acyclic Graph (DAG) pipeline**:

```
                         [ Phase 1: Feature Mining ]
                           Subagent 1 (Multi-TF)
                                     │
                                     ▼ (data/features.csv)
          ┌──────────────────────────┴──────────────────────────┐
          │  CONCURRENT EXPLORATION SWARMS (Run In Parallel)    │
          ▼                                                     ▼
┌───────────────────────────┐                         ┌───────────────────────────┐
│ Subagent 2 (Exploration A)│                         │ Subagent 3 (Exploration B)│
│ Mean Reversion & Traps    │                         │ Trend & Volatility Regimes│
└─────────────┬─────────────┘                         └─────────────┬─────────────┘
              │                                                     │
              └──────────────────────────┬──────────────────────────┘
                                         ▼ (data/candidate_returns.json)
                            [ Phase 4: Falsification ]
                             Subagent 4 (Cynic Auditor)
                                         │
                                         ▼ Pass DSR >= 0.95? (data/final_rules.json)
                            [ Phase 5: Parallel Deploy ]
                             Subagent 5 (Ops & Gateway)
```

#### Dependency & Concurrency Rules:
* ⛓️ **Phase Dependencies (Sequential Gates):**
  * Subagents 2 & 3 **depend on Subagent 1** to finish creating `data/features.csv`.
  * Subagent 4 **depends on Subagents 2 & 3** to produce `data/candidate_returns.json`.
  * Subagent 5 **depends on Subagent 4** passing the $\text{DSR} \ge 0.95$ gate.
* ⚡ **True Parallel Execution (Concurrent Swarms):**
  * Subagent 2 (Mean Reversion) and Subagent 3 (Trend / Volatility) run **100% in parallel** searching separate hypothesis spaces at the same time.
  * In Phase 5, emitting code, launching paper trading, and firing Telegram alerts execute **in parallel**.

---

## 🧠 Context Window & Token Sandbox Protocol

To prevent context window bloat, high token costs, and context degradation during long mining loops:

1. 🧼 **Isolated Subagent Sandboxes:** Each subagent operates in its own isolated context window. Trial-and-error logs from 50+ backtest iterations remain inside the subagent sandbox and are discarded upon completion. Subagents report back to the Orchestrator with **only concise result JSONs**.
2. 📖 **Progressive Reference Loading:** Subagents read *only* the specific reference file needed for their phase (e.g., Subagent 4 loads [`references/statistic_edge.md`](file:///home/christonomous/Desktop/EdgeMiner/references/statistic_edge.md)), keeping token consumption minimal.
3. 💾 **Disk-Based State Handoff:** Large datasets and trade return arrays are stored in `data/` files on disk (`data/features.csv`, `data/candidate_returns.json`). Subagents exchange file paths instead of dumping raw data into prompt context.

---

## 🎯 User Intent & Strategy Profile Mapping
*(Primary Reference: [`references/strategy_profiles.md`](file:///home/christonomous/Desktop/EdgeMiner/references/strategy_profiles.md))*

| User Request | Target Strategy Profile | Mining & Risk Constraints |
| --- | --- | --- |
| *"I need a prop firm trading strategy"* | **Prop Firm Challenge** | **Strict Drawdown:** Max DD $\le 4.5\%$, Net Sharpe $\ge 1.8$, Win Rate $\ge 55\%$, DSR $\ge 0.96$, tight stop-loss. |
| *"Make me a btc market cycle swing trade strategy"* | **BTC Market Cycle Swing** | **Multi-Day Trend/Chop:** 15m/1h/4h timeframes, Hurst Exponent regime filter ($H > 0.55$ for trend, $H < 0.45$ for chop), trailing stop. |
| *"Make me a longterm conservative investment strategy"* | **Conservative Investment** | **Low Turnover & Preservation:** Max DD $\le 8.0\%$, Profit Factor $\ge 1.8$, Parkinson Volatility compression filters. |
| *"How can news be traded effectively"* | **News Volatility Expansion** | **Liquidity Sweep & Fade:** V-Spread spike absorption, post-news upper/lower wick rejection fades, short holding time. |

---

## 🔄 Autonomous Iterative Discovery & Execution Loop

```
                                [ USER PROMPT ]
       ("I need a prop firm strategy" / "Make me a BTC swing strategy")
                                       │
                                       ▼
                       ┌───────────────────────────────┐
                       │  1. Map Strategy Profile &    │  <-- Ref: references/strategy_profiles.md
                       │     Set Target Constraints    │
                       └───────────────┬───────────────┘
                                       │
                                       ▼
                       ┌───────────────────────────────┐
                       │  2. Feature Extraction &      │  <-- Ref: references/pricedataonly_edge_mining.md
                       │     Regime Scan (Phase 1)     │       Ref: references/thirdparty_edge_mining.md
                       │     python tools/feature_...  │
                       └───────────────┬───────────────┘
                                       │
                                       ▼
                       ┌───────────────────────────────┐
                       │  3. Creative Dialectic        │  <-- Ref: references/outofthebox_solutions_finding.md
                       │     Out-of-the-Box Ideation   │       Ref: references/indicator_usage.md
                       └───────────────┬───────────────┘
                                       │
                                       ▼
                       ┌───────────────────────────────┐
                       │  4. Fast Vectorized Screen    │  <-- Ref: references/edge.md
                       │     python tools/vectoriz...  │       Ref: references/process.md
                       └───────────────┬───────────────┘
                                       │
                         Pass Hurdles? │
                       ┌───────────────┴───────────────┐
                       │                               │
                     [ NO ]                         [ YES ]
                       │                               │
                       ▼                               ▼
     ┌─────────────────────────────────┐ ┌───────────────────────────┐
     │ Refine Rules / Blacklist Failed │ │ 5. Adversarial DSR Audit  │ <-- Ref: references/statistic_edge.md
     │ Setup & Loop Back to Step 3     │ │    python tools/valid...  │      Ref: references/riskmanagement.md
     └─────────────────────────────────┘ └─────────────┬─────────────┘
                                                       │
                                          DSR >= 0.95? │
                                         ┌─────────────┴─────────────┐
                                         │                           │
                                       [ NO ]                     [ YES ]
                                         │                           │
                                         ▼                           ▼
                       ┌───────────────────────────────────┐ ┌───────────────────────────────┐
                       │ Adjust Parameters & Re-Audit      │ │ 6. Emit Code & Deploy Options │ <-- Ref: references/tradingbot.md
                       │ Loop Back to Step 3               │ │    (User Chooses Deployment): │      Ref: references/signals_gateway.md
                       └───────────────────────────────────┘ │    - Emit Freqtrade Strategy   │      Ref: references/dashboard.md
                                                             │    - Launch Paper Trading Bot │      Ref: references/ui_management.md
                                                             │    - Activate Telegram Alerts │
                                                             │    - Spin Up Web Dashboard    │
                                                             └───────────────────────────────┘
```

---

## ⚙️ Environment Preparation & Prerequisites
*(Primary Reference: [`references/libs_clis.md`](file:///home/christonomous/Desktop/EdgeMiner/references/libs_clis.md))*

Before executing any tools, the AI agent **MUST verify and prepare the runtime environment**:

1. **Check & Install Python Dependencies:**
   Run the following command to ensure all required quantitative libraries (`polars`, `numpy`, `scipy`, `vectorbt`, `fastapi`, `python-telegram-bot`) are installed:
   ```bash
   pip install -r requirements.txt
   ```

2. **Check & Install Frontend Dependencies (If Web UI requested):**
   If launching the visual telemetry dashboard (`frontend_control.py`), ensure Node modules are installed:
   ```bash
   cd frontend && npm install && cd ..
   ```

---

## 🛠️ Step-by-Step Execution Contract

### Step 1: Feature Extraction & Regime Scan (Phase 1)
*(References: [`references/pricedataonly_edge_mining.md`](file:///home/christonomous/Desktop/EdgeMiner/references/pricedataonly_edge_mining.md) & [`references/thirdparty_edge_mining.md`](file:///home/christonomous/Desktop/EdgeMiner/references/thirdparty_edge_mining.md))*  
Extract bar geometry, VSA Volume Z-scores, Parkinson volatility, and rolling Hurst exponent proxy:
```bash
python tools/feature_miner.py --input data/candles_15m.csv --output data/features.csv
```

### Step 2: Out-of-the-Box Dialectic Ideation (Phase 2)
*(References: [`references/outofthebox_solutions_finding.md`](file:///home/christonomous/Desktop/EdgeMiner/references/outofthebox_solutions_finding.md) & [`references/indicator_usage.md`](file:///home/christonomous/Desktop/EdgeMiner/references/indicator_usage.md))*  
1. **Consensus Mapping:** Identify retail herd setup (e.g., buying Bollinger Band breakouts).
2. **Failure Dissection:** Pinpoint microstructure conditions where that setup fails (absorption, liquidity sweep).
3. **Lateral Synthesis:** Formulate entry/exit rule logic combining custom engineered features.

### Step 3: Fast Vectorized Coarse Filter (Phase 3)
*(References: [`references/edge.md`](file:///home/christonomous/Desktop/EdgeMiner/references/edge.md) & [`references/process.md`](file:///home/christonomous/Desktop/EdgeMiner/references/process.md))*  
Screen logic against In-Sample data with 5 bps fee and 2 bps slippage friction:
```bash
python tools/vectorized_screener.py \
  --data data/features.csv \
  --rules '{"entry_long": "close < lower_band and lower_wick > 0.55 and volume_zscore > 1.5", "exit": "bars >= 12"}' \
  --fee-bps 5.0 \
  --output data/candidate_returns.json
```
* **Check Results:** If Sharpe $< 1.3$, Trades $< 100$, or Net Expectancy $\le 2\times$ fees, **do not stop**—autonomously iterate with a refined hypothesis.

### Step 4: Adversarial Audit & DSR Gate (Phase 4)
*(References: [`references/statistic_edge.md`](file:///home/christonomous/Desktop/EdgeMiner/references/statistic_edge.md) & [`references/riskmanagement.md`](file:///home/christonomous/Desktop/EdgeMiner/references/riskmanagement.md))*  
Audit surviving returns against overfitting:
```bash
python tools/validation_cynic.py \
  --returns data/candidate_returns.json \
  --trials 120 \
  --param-grid '{"lower_wick": [0.45, 0.50, 0.55, 0.60], "volume_zscore": [1.2, 1.5, 1.8]}'
```
* **Gate Check:** DSR must be $\ge 0.95$, parameter surface must form a stable plateau, and OOS retention must be $\ge 65\%$. If failed, iterate logic.

### Step 5: Optional Deployment Features (User Selected)
Once a strategy passes all falsification gates, activate user-selected deployment features:

1. **Emit Freqtrade Production Code:** *(References: [`references/tradingbot.md`](file:///home/christonomous/Desktop/EdgeMiner/references/tradingbot.md) & [`references/libs_clis.md`](file:///home/christonomous/Desktop/EdgeMiner/references/libs_clis.md))*
   ```bash
   python tools/strategy_emitter.py --thesis "<THESIS>" --rules data/final_rules.json --framework freqtrade --out user_data/strategies/MyStrategy.py
   ```

2. **Activate 24/7 Telegram Signal Chatbot (Optional):** *(Reference: [`references/signals_gateway.md`](file:///home/christonomous/Desktop/EdgeMiner/references/signals_gateway.md))*
   ```bash
   python tools/server_control.py start --port 8000 --daemon
   python tools/ui_dispatcher.py --event SIGNAL_TRIGGERED --payload '<SIGNAL_JSON>'
   ```

3. **Launch Paper/Live Execution Bot (Optional):** *(Reference: [`references/tradingbot.md`](file:///home/christonomous/Desktop/EdgeMiner/references/tradingbot.md))*
   ```bash
   python tools/bot_control.py deploy --strategy MyStrategy --mode dry-run
   ```

4. **Spin Up Dual-Screen Web Dashboard (Optional):** *(References: [`references/dashboard.md`](file:///home/christonomous/Desktop/EdgeMiner/references/dashboard.md) & [`references/ui_management.md`](file:///home/christonomous/Desktop/EdgeMiner/references/ui_management.md))*
   ```bash
   python tools/frontend_control.py start --port 3000 --daemon
   ```

---

## 📚 Master Reference Knowledge Base

| Topic / Phase | Reference File | Focus & Guidelines |
| --- | --- | --- |
| **Strategy Profiles** | [`references/strategy_profiles.md`](file:///home/christonomous/Desktop/EdgeMiner/references/strategy_profiles.md) | Intent mapping, target constraints for Prop Firm, Swing, Conservative & News. |
| **Price Data Mining** | [`references/pricedataonly_edge_mining.md`](file:///home/christonomous/Desktop/EdgeMiner/references/pricedataonly_edge_mining.md) | Bar physics, volume Z-scores, Hurst regime metrics, Parkinson volatility. |
| **Third-Party Mining** | [`references/thirdparty_edge_mining.md`](file:///home/christonomous/Desktop/EdgeMiner/references/thirdparty_edge_mining.md) | External order book depth, social sentiment, and macro data integrations. |
| **Creative Ideation** | [`references/outofthebox_solutions_finding.md`](file:///home/christonomous/Desktop/EdgeMiner/references/outofthebox_solutions_finding.md) | Dialectic reasoning, retail consensus trap mapping, anti-fragile rules. |
| **Indicator Guidelines** | [`references/indicator_usage.md`](file:///home/christonomous/Desktop/EdgeMiner/references/indicator_usage.md) | Non-standard indicator usage, avoiding lagging signal traps. |
| **Edge Criteria** | [`references/edge.md`](file:///home/christonomous/Desktop/EdgeMiner/references/edge.md) | Mathematical edge formulation, trade expectancy, fee drag protection. |
| **Mining Process** | [`references/process.md`](file:///home/christonomous/Desktop/EdgeMiner/references/process.md) | End-to-end multi-phase workflow pipeline specification. |
| **Statistical Audit** | [`references/statistic_edge.md`](file:///home/christonomous/Desktop/EdgeMiner/references/statistic_edge.md) | Deflated Sharpe Ratio ($\text{DSR} \ge 0.95$), p-value evaluation, over-fitting audit. |
| **Risk Management** | [`references/riskmanagement.md`](file:///home/christonomous/Desktop/EdgeMiner/references/riskmanagement.md) | Position sizing, drawdown caps, stop-loss and trailing take-profit rules. |
| **Trading Bot Execution**| [`references/tradingbot.md`](file:///home/christonomous/Desktop/EdgeMiner/references/tradingbot.md) | Freqtrade/Jesse bot deployment, paper/dry-run execution, live safeguards. |
| **Libraries & CLIs** | [`references/libs_clis.md`](file:///home/christonomous/Desktop/EdgeMiner/references/libs_clis.md) | CLI dependency guidelines (`polars`, `vectorbt`, `fastapi`, `vite`). |
| **Signal Chatbot** | [`references/signals_gateway.md`](file:///home/christonomous/Desktop/EdgeMiner/references/signals_gateway.md) | 24/7 Telegram bot setup, Webhook ingestion, real-time alert dispatching. |
| **Visual Dashboard** | [`references/dashboard.md`](file:///home/christonomous/Desktop/EdgeMiner/references/dashboard.md) | Dual-screen UI architecture, TradingView canvas, agent deck stream. |
| **UI Management** | [`references/ui_management.md`](file:///home/christonomous/Desktop/EdgeMiner/references/ui_management.md) | Dashboard state machine, view hotkeys, background daemon controls. |
| **Simple Utilities** | [`references/simple_tools_ideas.md`](file:///home/christonomous/Desktop/EdgeMiner/references/simple_tools_ideas.md) | Lightweight helper script concepts and data formatting tools. |
| **Extended Tools** | [`references/extended_tools_ideas.md`](file:///home/christonomous/Desktop/EdgeMiner/references/extended_tools_ideas.md) | Future expansion blueprints (advanced ML models, multi-exchange routers). |

---

## CLI Tools Summary

| Tool Script | Responsibilities | Key Arguments |
| --- | --- | --- |
| `tools/feature_miner.py` | Bar geometry, VSA volume Z-score, Parkinson volatility, rolling Hurst proxy, AVWAP | `--input`, `--output`, `--window` |
| `tools/vectorized_screener.py` | Fast Vectorbt / Polars IS strategy coarse filter with taker fee friction | `--data`, `--rules`, `--fee-bps`, `--output` |
| `tools/validation_cynic.py` | DSR calculation, parameter stability surface grid, Monte Carlo, OOS audit | `--returns`, `--trials`, `--param-grid`, `--oos-data` |
| `tools/strategy_emitter.py` | Generates Freqtrade `IStrategy` or Jesse strategy Python code | `--thesis`, `--rules`, `--framework`, `--out` |
| `tools/ui_dispatcher.py` | Dispatches WebSocket widgets, chart markers, and Telegram alerts | `--event`, `--payload`, `--endpoint` |
| `tools/server_control.py` | CLI tool to start/stop FastAPI server & Telegram gateway | `start`, `stop`, `status`, `--port` |
| `tools/frontend_control.py` | CLI tool to build and serve the dual-screen React UI | `build`, `start`, `stop`, `status`, `--port` |
| `tools/bot_control.py` | CLI tool to launch and manage Freqtrade/Jesse paper trading bot | `deploy`, `stop`, `status`, `--strategy`, `--mode` |

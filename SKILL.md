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

### 2. Relentless Persistence Loop Directive & Dynamic Exit Mutation
> [!IMPORTANT]
> **Directive for AI Agent:** Never declare success or stop after 1 or 2 backtest trials. Fixed rules (such as arbitrary 6-bar hold exit caps) can cut off profitable trends early or exit prematurely during chop. The AI agent MUST relentlessly iterate across parameter spaces, mutating:
> 1. **Entry Rules & Filters:** Lower/upper wick thresholds, Volume Z-score, Hurst regime filters ($H < 0.45$ chop vs. $H > 0.55$ trend), AVWAP standard deviations.
> 2. **Directional Bias:** Test **LONG-only**, **SHORT-only**, or **Dual LONG+SHORT** based on structural market asymmetry.
> 3. **Exit Mechanics & Holding Windows:** Dynamically mutate max holding bars ($4 \le \text{bars} \le 48$), trailing stops, ATR volatility stops, and TP/SL risk-reward ratios.
> 4. **Iterative Goal:** Log failure causes, blacklist failed combinations, and **repeat the loop relentlessly until a genuinely profitable strategy matching the user's prompt requirements and passing DSR $\ge 0.95$ is discovered**.

### 3. Subagent Parallelization & Orchestration Pattern
If the execution environment supports subagents (e.g., Google Antigravity, OpenClaw, Hermes), the Orchestrator AI Agent SHOULD delegate tasks using a **Directed Acyclic Graph (DAG) pipeline**:

### 4. Directional Flexibility (Margin & Futures Openness)
> [!NOTE]
> **Directional Openness:** Strategies do NOT need to be strictly dual-directional nor strictly single-directional. The AI agent is directionally open—it autonomously tests **LONG-only**, **SHORT-only**, or **Dual LONG+SHORT** setups depending on market regime, structural asymmetry, and what yields the highest verified statistical edge (DSR $\ge 0.95$) for margin/futures markets according to the user's prompt requirements.

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

## 🚀 First-Time Initialization & Interactive Onboarding Protocol

When this skill is invoked for the first time (or when `.env` / system configuration is not yet established), the AI Agent SHOULD conduct a brief **Interactive Onboarding Interview** (or infer defaults from the user's initial prompt) to set up the system environment:

### 1. Initial Onboarding Interview Questions:
1. **Trading Objective & Risk Profile:**
   - 🎯 **Prop Firm Challenge Pass:** Max DD $\le 4.5\%$, Win Rate $\ge 55\%$, Net Sharpe $\ge 1.8$, DSR $\ge 0.96$, tight stop-loss.
   - 📈 **Crypto Swing Trading:** 15m/1h/4h multi-day trend capture, trailing stops, Hurst trend filter.
   - 🛡️ **Conservative Wealth Preservation:** Low turnover, capital preservation, Max DD $\le 8.0\%$.
   - ⚡ **News & Volatility Expansion:** Fading news spikes, wick rejections, fast holding windows.
2. **Target Asset & Timeframe:**
   - Default: `BTC/USDT 15m` (Binance REST API, zero mock data). Custom: `ETH/USDT`, `SOL/USDT`, etc.
3. **Telegram 24/7 Signal Broadcast Setup (Optional):**
   - *"Would you like live/paper signals streamed 24/7 to your Telegram app?"*
   - If YES: Prompt user for `TELEGRAM_BOT_TOKEN` (from `@BotFather`) and `TELEGRAM_CHAT_ID`.
   - Action: AI agent automatically saves these credentials to `.env`.
4. **Execution Mode & Exchange API Credentials (Optional):**
   - 📊 **Telemetry Dashboard & Backtest Preview Only** (default — zero risk, instant out-of-the-box backtests).
   - 🧪 **Paper Trading / Dry-Run** (simulated exchange execution).
   - ⚡ **Live Execution** (requires Exchange API Key & Secret written to `.env`).
5. **Telemetry & Dashboard Ports:**
   - API Server Port: `8000` (default)
   - Web Dashboard Port: `3000` (default)

### 2. Automated Env Setup & Out-of-the-Box Verification:
If credentials are provided during onboarding, the AI agent populates/patches `.env`:
```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ
TELEGRAM_CHAT_ID=-100123456789
EXCHANGE_NAME=binance
EXCHANGE_API_KEY=your_api_key_here
EXCHANGE_API_SECRET=your_api_secret_here
TELEMETRY_PORT=8000
DASHBOARD_PORT=3000
```
- **Zero-Key Verification:** The AI agent verifies that Binance public REST API (`https://api.binance.com`) is accessible for instant candle syncs without needing API keys.
- **Pre-Built UI Verification:** The AI agent checks that `frontend/dist/` is ready to serve immediately via `python3 tools/frontend_control.py start`.

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

2. **Pre-Built Production Dashboard (`frontend/dist/`):**
   The production UI bundle is pre-compiled and tracked directly in `frontend/dist/` within the git repository. The AI Agent can launch the visual telemetry dashboard instantly:
   ```bash
   python3 tools/frontend_control.py start --port 3000 --daemon
   ```
   If modifying frontend React components (`frontend/src/`), the AI Agent rebuilds the production bundle using:
   ```bash
   python3 tools/frontend_control.py build
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

### Step 3: Fast Vectorized Coarse Filter & Exit Mutation Loop (Phase 3)
*(References: [`references/edge.md`](file:///home/christonomous/Desktop/EdgeMiner/references/edge.md) & [`references/process.md`](file:///home/christonomous/Desktop/EdgeMiner/references/process.md))*  
Screen candidate rule combinations against In-Sample data with 5.0 bps fee and 2.0 bps slippage friction:
```bash
python tools/vectorized_screener.py \
  --data data/features.csv \
  --rules '{"entry_long": "close < lower_band and lower_wick > 0.55 and volume_zscore > 1.5", "exit": "bars >= 12"}' \
  --fee-bps 5.0 \
  --output data/candidate_returns.json
```
* **Iterative Screening Rule:** Do **NOT** rely on rigid exit rules (such as fixed 6-bar exits) that cut off profitable trends early. Mutate and test dynamic exit mechanics:
  - Extend/shorten holding periods ($4 \le \text{max\_bars} \le 48$).
  - Test trailing stop offsets ($0.5\% \le \text{trailing} \le 3.0\%$).
  - Test ATR volatility stops and trend-invalidation closes.
  - Test LONG-only, SHORT-only, or Dual LONG+SHORT directional setups.
* **Hurdle Check:** If Sharpe $< 1.8$, Win Rate $< 55\%$, Trades $< 60$, or Net Expectancy $\le 25\text{ bps}$, **do NOT stop**—autonomously mutate the hypothesis, entry filters, and exit rules and re-run screening until target profitability is reached.

### Step 4: Adversarial Audit & DSR Gate (Phase 4)
*(References: [`references/statistic_edge.md`](file:///home/christonomous/Desktop/EdgeMiner/references/statistic_edge.md) & [`references/riskmanagement.md`](file:///home/christonomous/Desktop/EdgeMiner/references/riskmanagement.md))*  
Audit surviving candidate returns against overfitting and parameter fragility:
```bash
python tools/validation_cynic.py \
  --returns data/candidate_returns.json \
  --trials 120 \
  --param-grid '{"lower_wick": [0.45, 0.50, 0.55, 0.60], "volume_zscore": [1.2, 1.5, 1.8]}'
```
* **Gate Check:** Deflated Sharpe Ratio must be $\text{DSR} \ge 0.95$, parameter surface must form a stable plateau (no cliff-edge spikes), and Out-Of-Sample Sharpe retention must be $\ge 65\%$. If the audit fails or returns unpromising metrics, loop back to Step 2, blacklist failed setups, and synthesize an alternative out-of-the-box hypothesis.

### Step 5: Optional Deployment Features (User Selected)
Once a strategy passes all falsification gates, activate user-selected deployment features:

1. **Emit Freqtrade Production Code:** *(References: [`references/tradingbot.md`](file:///home/christonomous/Desktop/EdgeMiner/references/tradingbot.md) & [`references/libs_clis.md`](file:///home/christonomous/Desktop/EdgeMiner/references/libs_clis.md))*
   ```bash
   python tools/strategy_emitter.py --thesis "<THESIS>" --rules data/final_rules.json --framework freqtrade --out strategies/MyStrategy.py
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
| **State Management** | [`references/state_management.md`](file:///home/christonomous/Desktop/EdgeMiner/references/state_management.md) | Single source of truth: `StateManager`, `SignalStore`, `state_control.py` CLI, state & signal schemas, file lock safety. |
| **Simple Utilities** | [`references/simple_tools_ideas.md`](file:///home/christonomous/Desktop/EdgeMiner/references/simple_tools_ideas.md) | Lightweight helper script concepts and data formatting tools. |
| **Extended Tools** | [`references/extended_tools_ideas.md`](file:///home/christonomous/Desktop/EdgeMiner/references/extended_tools_ideas.md) | Future expansion blueprints (advanced ML models, multi-exchange routers). |
| **Extend Frontend** | [`references/extending_frontend.md`](file:///home/christonomous/Desktop/EdgeMiner/references/extending_frontend.md) | How to add screens, WS events, chart overlays, TypeScript interfaces, and new REST consumers. Data flow, component anatomy, build workflow. |
| **Extend Backend** | [`references/extending_backend.md`](file:///home/christonomous/Desktop/EdgeMiner/references/extending_backend.md) | How to add REST endpoints, WS events, state fields, backtest metrics, strategy rules, and AI tools. Signal lifecycle, data fetching, golden rules. |

---

## 🔧 Tool Authoring Standard

All scripts in `tools/` follow one consistent pattern. When writing or extending a tool, match this exactly:

```python
#!/usr/bin/env python3
import argparse
import json
import urllib.request  # or numpy / polars for data tools
import sys

TOOL_NAME = "[MyTool]"  # prefix for all print() output — AI agent log readability

def action_name(arg1, arg2, ...):
    print(f"{TOOL_NAME} Doing action...")
    # logic here
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="One-line description for AI agent")
    parser.add_argument("action", choices=["a", "b", "c"], help="Action to execute")
    parser.add_argument("--arg", default="...", help="Description")
    args = parser.parse_args()

    if   args.action == "a": action_a(args.arg)
    elif args.action == "b": action_b(args.arg)
    elif args.action == "c": action_c(args.arg)
```

**Rules:**
- `#!/usr/bin/env python3` shebang on line 1
- Named functions per action — no `main()` wrapper
- `[ToolName]` prefix on **all** `print()` output so the AI can parse tool identity from logs
- `argparse` with a **flat positional `action` arg** and `choices=[]` — no subparsers
- Stdlib only (`urllib.request`, `json`, `os`, `sys`) or approved scientific libs (`numpy`, `polars`, `scipy`)
- No `logging.basicConfig` — use plain `print()` with prefix
- No third-party deps beyond what is in `requirements.txt`
- `if __name__ == "__main__":` entry point with flat `if/elif` dispatch

---

## 🛠️ CLI Tools Reference

| Tool Script | `[Prefix]` | Responsibilities | Key Arguments |
| --- | --- | --- | --- |
| `tools/feature_miner.py` | `[FeatureMiner]` | Bar geometry, VSA volume Z-score, Parkinson volatility, rolling Hurst proxy, AVWAP | `--input`, `--output`, `--window` |
| `tools/vectorized_screener.py` | `[VectorizedScreener]` | Fast Vectorbt / Polars IS strategy coarse filter with taker fee friction | `--data`, `--rules`, `--fee-bps`, `--output` |
| `tools/validation_cynic.py` | `[ValidationCynic]` | DSR calculation, parameter stability surface grid, Monte Carlo, OOS audit | `--returns`, `--trials`, `--param-grid`, `--oos-data` |
| `tools/run_backtest_audit.py` | `[BacktestAudit]` | Full backtest, equity curve, regime survival, 5-Gate Cynic matrix, saves state | `--strategy`, `--save-state`, `--json-output` |
| `tools/state_control.py` | `[StateControl]` | **AI State CLI:** read/patch state, deploy/stop strategies, manage signals | `get`, `patch`, `deploy`, `stop`, `signals`, `signal-stats`, `signal-add`, `schema` |
| `tools/strategy_emitter.py` | `[StrategyEmitter]` | Generates Freqtrade `IStrategy` or Jesse strategy Python code | `--thesis`, `--rules`, `--framework`, `--out` |
| `tools/ui_dispatcher.py` | `[UIDispatcher]` | Dispatches WebSocket widgets, chart markers, and Telegram alerts | `--event`, `--payload`, `--endpoint` |
| `tools/server_control.py` | `[ServerControl]` | Start/stop FastAPI telemetry server & Telegram gateway | `start`, `stop`, `status`, `--port` |
| `tools/frontend_control.py` | `[FrontendControl]` | Build and serve the dual-screen React UI | `build`, `start`, `stop`, `status`, `--port` |
| `tools/bot_control.py` | `[BotControl]` | Launch and manage Freqtrade/Jesse paper trading bot | `deploy`, `stop`, `status`, `--strategy`, `--mode` |


---

## 🌐 Backend REST API Reference

| Endpoint | Method | Description |
| --- | --- | --- |
| `/api/health` | GET | System health: bot status, WS connections |
| `/api/candles` | GET | Live or synthetic OHLCV candles (BTC/USDT 15m via Binance) |
| `/api/signals` | GET | All persisted signals + current active open signal |
| `/api/signals/stats` | GET | **Live performance stats since activation:** win rate, profit factor, Sharpe (annualized), total PnL %, avg win/loss, max consecutive losses |
| `/api/state` | GET | Single Source of Truth system state (active strategy, backtest summary) |
| `/api/strategies` | GET | List all strategy `.py` files in `strategies/` |
| `/api/strategies/select` | POST | Run real backtest preview for a strategy (no activation) |
| `/api/bot/deploy` | POST | Activate & deploy a strategy to paper trading + update state |
| `/api/bot/stop` | POST | Stop the active paper trading bot |
| `/api/backtest` | GET | Get backtest results for active or specified strategy |
| `/api/broadcast` | POST | Broadcast WebSocket event (signals, widgets, alerts) |
| `/ws` | WS | Real-time telemetry bus: `UPSERT_WIDGET`, `SIGNAL_TRIGGERED`, `STATE_UPDATED` |

---

## 📺 Dashboard Screen Architecture

| Screen | Hotkey | Purpose |
| --- | --- | --- |
| **Chart** (`ChartCanvas`) | F1 | Live BTC/USDT candlestick chart (Binance 15m WebSocket) with backtest trade markers overlay |
| **Signal Deck** (`SignalDeck`) | F2 | Live strategy telemetry: performance stats since activation (win rate, PF, Sharpe, PnL), active open signal with live unrealized PnL, and full signal history audit table |
| **Backtest** (`BacktestDeck`) | F3 | Full-width backtest analytics: equity growth curve, return distribution histogram, market regime survival (bull/bear/ranging), sequential trade log, and 5-Gate Cynic Audit |
| **Strategy Mega Menu** | Header | Header mega menu dropdown listing all strategies in `strategies/` with run backtest and activate actions |

> [!NOTE]
> **AI State Sharing:** All three screens read from the same `data/state.json` (Single Source of Truth). The AI agent writes to this file via CLI tools (`run_backtest_audit.py --save-state`) or via REST API. The frontend subscribes to changes via WebSocket `STATE_UPDATED` events.




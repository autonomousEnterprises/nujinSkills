# ⚡ NujinSkills: Autonomous Quant Edge Mining Engine & Signal Gateway

> **An agent-agnostic quantitative alpha discovery engine, 24/7 Telegram signal gateway, and interactive dual-screen telemetry dashboard for OHLCV market data.**

---

## 🌟 Key Capabilities

- 🔬 **Quantitative Research & Alpha Mining:** Multi-scale feature extraction across OHLCV datasets (bar geometry, VSA volume Z-scores, Parkinson volatility, Anchored VWAP, Hurst exponent regime classification).
- 💡 **Creative Strategy Development:** Dialectic ideation that invents non-standard, out-of-the-box trading rules tailored to specific objectives (*Prop Firm*, *BTC Swing*, *Conservative Investment*, *News Volatility*).
- 📊 **Rigorous Backtesting & Falsification:** Vectorized backtesting engine paired with an unyielding statistical audit hurdle (Deflated Sharpe Ratio $\text{DSR} \ge 0.95$, parameter grid stability, Monte Carlo drawdown risk checks).
- 🤖 **Automated Trading Bot Execution:** Emits production-ready Freqtrade/Jesse `IStrategy` code and deploys paper or live trading bots via `bot_control.py`.
- 💬 **24/7 Messenger Signal Gateway:** Integrated Telegram bot dispatcher broadcasting real-time trade signals, regime shifts, and PnL alerts to user messaging channels.
- 🔁 **Relentless Persistence Loop:** If a hypothesis fails backtesting or statistical hurdles, the AI automatically blacklists the setup, mutates parameters, and loops continuously until a statistically vetted, profitable trading strategy is discovered and deployed.
- 👥 **Multi-Subagent Parallelization:** Supports subagent delegation across parallel feature mining, exploration swarms (mean reversion vs. trend hypotheses), adversarial DSR auditing, and daemon operations.
- 🖥️ **Dual-Screen Telemetry & Visual Terminal:** Interactive Web UI (`frontend_control.py`) featuring TradingView Lightweight Charts and live agent execution telemetry.

---

## 🤖 Integration & Usage Guide Across AI Environments

NujinSkills is built around a standard agent-agnostic `SKILL.md` contract and local CLI tools.

### 1. Google Antigravity IDE

Antigravity automatically discovers and loads skills from customization roots:

- **Global Customizations Skill (Available in All Workspaces):**
  Place NujinSkills in `~/.gemini/config/skills/NujinSkills/` (containing `SKILL.md`).
  ```bash
  mkdir -p ~/.gemini/config/skills/NujinSkills
  cp -r * ~/.gemini/config/skills/NujinSkills/
  ```

- **Workspace-Scoped Skill (Project Specific):**
  Place NujinSkills in `.agents/skills/NujinSkills/` inside your project root.
  ```bash
  mkdir -p .agents/skills/NujinSkills
  cp -r * .agents/skills/NujinSkills/
  ```

---

### 2. OpenClaw / Hermes CLI Agents
Register the repository directly into your CLI agent's skill directory:
```bash
# Register skill into OpenClaw / Hermes
openclaw skill add ./
# Or symlink to global skills directory
ln -s $(pwd) ~/.openclaw/skills/NujinSkills
```

---

### 3. Claude Code / Cursor / Windsurf / VS Code Copilot
Open this project folder directly in your editor. The AI assistant ingests `SKILL.md` and `references/` when processing context.

---

## 💬 Simple User Prompts & Profiles

You do not need to specify technical formulas or command-line flags. Simply prompt the AI with your trading goal:

1. **Prop Firm Strategy:**
   > *"I need a prop firm trading strategy."*
   > *(AI sets strict Max DD $\le 4.5\%$, Sharpe $\ge 1.8$, DSR $\ge 0.96$, mines low-drawdown setups, emits Freqtrade code, and launches paper trading).*

2. **BTC Swing Trading Strategy:**
   > *"Make me a btc market cycle swing trade strategy."*
   > *(AI extracts multi-day trend/chop regimes using Hurst $H > 0.55$, filters false breakouts, and projects markers on the Lightweight Chart).*

3. **Longterm Conservative Investment:**
   > *"Make me a longterm conservative investment strategy."*
   > *(AI targets capital preservation, Parkinson volatility compression, Max DD $\le 8\%$, and low trade turnover).*

4. **News Volatility Strategy:**
   > *"How can news be traded effectively?"*
   > *(AI mines post-event V-Spread spikes and wick rejection fades, stress-tests with Monte Carlo reshuffling, and relays alerts to Telegram).*

---

## 🔄 Autonomous AI Agent Workflow Loop

```
                        [ USER PROMPT ]
  ("I need a prop firm strategy" / "Make me a BTC swing strategy")
                                │
                                ▼
                ┌───────────────────────────────┐
                │ 1. Map Strategy Profile &     │
                │    Set Target Constraints     │
                └───────────────┬───────────────┘
                                │
                                ▼
                ┌───────────────────────────────┐
                │ 2. Feature Extraction & Scan  │
                │    python tools/feature_...   │
                └───────────────┬───────────────┘
                                │
                                ▼
                ┌───────────────────────────────┐
                │ 3. Creative Dialectic         │
                │    Out-of-the-Box Ideation    │
                └───────────────┬───────────────┘
                                │
                                ▼
                ┌───────────────────────────────┐
                │ 4. Fast Vectorized Screen     │
                │    python tools/vectoriz...   │
                └───────────────┬───────────────┘
                                │
                  Pass Hurdles? │
                ┌───────────────┴───────────────┐
                │                               │
              [ NO ]                         [ YES ]
                │                               │
                ▼                               ▼
┌──────────────────────────────────┐ ┌───────────────────────────┐
│ Refine Rules / Blacklist Failed  │ │ 5. Adversarial DSR Audit  │
│ Setup & Loop Back to Step 3      │ │    python tools/valid...  │
└──────────────────────────────────┘ └─────────────┬─────────────┘
                                                   │
                                      DSR >= 0.95? │
                                     ┌─────────────┴─────────────┐
                                     │                           │
                                   [ NO ]                     [ YES ]
                                     │                           │
                                     ▼                           ▼
                   ┌───────────────────────────┐ ┌───────────────────────────────┐
                   │ Adjust Parameters & Loop  │ │ 6. Emit Code & Deploy Options │
                   │ Back to Step 3            │ │    (User Chooses Deployment): │
                   └───────────────────────────┘ │    - Emit Freqtrade Strategy   │
                                                 │    - Launch Paper Trading Bot │
                                                 │    - Activate Telegram Alerts │
                                                 │    - Spin Up Web Dashboard    │
                                                 └───────────────────────────────┘
```

---

## 📂 Repository Architecture

```
EdgeMiner/
├── SKILL.md                       <-- Master Skill Contract, tool standard & execution manual
├── README.md                      <-- This file
├── requirements.txt               <-- Python dependencies (polars, vectorbt, uvicorn, etc.)
├── data/
│   ├── state.json                 # ★ Single Source of Truth — read by all consumers
│   ├── signals.json               # Persisted live signals (managed by SignalStore)
│   ├── features.csv               # Extracted OHLCV feature matrix
│   ├── candles_15m.csv            # BTC/USDT 15m historical candles
│   └── candidate_returns.json     # Trade return arrays for DSR audit
├── references/                    <-- AI Agent Knowledge Base
│   ├── state_management.md        # Shared state: StateManager, SignalStore, CLI tool, schemas
│   ├── strategy_profiles.md       # Natural prompt intent mapping & risk targets
│   ├── dashboard.md               # UI architecture & telemetry schemas
│   ├── edge.md                    # Quantitative edge & counterparty trap principles
│   ├── statistic_edge.md          # DSR formula & statistical rejection hurdles
│   ├── riskmanagement.md          # Risk controls, ATR stops, invalidation rules
│   ├── signals_gateway.md         # 24/7 Telegram Signal Gateway integration
│   ├── tradingbot.md              # Freqtrade & Jesse strategy execution contracts
│   └── ...                        # (+ 8 more reference specs)
├── tools/                         <-- AI Agent CLI Tools (one consistent standard)
│   ├── feature_miner.py           # [FeatureMiner]    Bar geometry, Hurst, VSA, Parkinson, AVWAP
│   ├── vectorized_screener.py     # [VectorizedScreener] Vectorbt fast In-Sample filter
│   ├── validation_cynic.py        # [ValidationCynic] DSR gate, Monte Carlo, OOS audit
│   ├── run_backtest_audit.py      # [BacktestAudit]   Full backtest & 5-Gate Cynic report
│   ├── state_control.py           # [StateControl]    ★ Shared state CLI for AI agents
│   ├── strategy_emitter.py        # [StrategyEmitter] Freqtrade IStrategy code generator
│   ├── ui_dispatcher.py           # [UIDispatcher]    WebSocket event dispatcher
│   ├── server_control.py          # [ServerControl]   Start/stop FastAPI server
│   ├── frontend_control.py        # [FrontendControl] Build/serve frontend dashboard
│   └── bot_control.py             # [BotControl]      Deploy/manage paper trading bot
├── server/                        <-- Telemetry Backend & Telegram Gateway
│   ├── main.py                    # FastAPI app & REST API
│   ├── state_manager.py           # ★ StateManager & SignalStore — canonical file-locked writes
│   ├── backtest_engine.py         # Vectorized backtest & regime analysis engine
│   ├── websocket.py               # Real-time WebSocket event broadcaster
│   ├── telegram_bot.py            # Telegram signal gateway (24/7 alerts)
│   ├── bot_runner.py              # Freqtrade/Jesse paper-trading supervisor
│   └── data_manager.py            # OHLCV data loader & Binance live feed
├── strategies/                    <-- Strategy .py files (loaded by backtest engine)
└── frontend/                      <-- User Telemetry Dashboard
    └── src/
        ├── App.tsx                # Screen router, unified state via useWebSocket
        ├── components/
        │   ├── ChartCanvas.tsx    # F1 — Live BTC/USDT chart + backtest trade markers
        │   ├── SignalDeck.tsx     # F2 — Live signals, PnL, win rate, Sharpe since activation
        │   ├── BacktestDeck.tsx   # F3 — Equity curve, regime survival, 5-Gate Cynic audit
        │   └── Header.tsx         # Strategy mega-menu, WS status, screen switcher
        └── hooks/
            └── useWebSocket.ts    # Real-time WS client — surfaces liveSystemState
```


---

## ⚡ Quick Start

### 1. Installation
Clone the repository and install Python dependencies:
```bash
cd NujinSkills
pip install -r requirements.txt
```

### 2. Launch Telemetry Backend & Web Dashboard (Optional)
Use the CLI control tools to start services in background daemon mode:
```bash
# Start FastAPI Telemetry Backend & Telegram Signal Gateway (Port 8000)
python tools/server_control.py start --port 8000 --daemon

# Build and Start Dual-Screen Frontend Terminal (Port 3000)
python tools/frontend_control.py build
python tools/frontend_control.py start --port 3000 --daemon
```

### 3. Inspect & Manage Shared State
All three consumers share `data/state.json` through the `StateManager`:
```bash
python tools/state_control.py get                                  # full state as JSON
python tools/state_control.py get --key backtest_summary.sharpe   # read a nested value
python tools/state_control.py patch --patch '{"status":"STOPPED"}' # merge-patch
python tools/state_control.py signal-stats                         # live win rate, PF, Sharpe, PnL
```

---

## 🛠️ CLI Tools Reference

| Tool Script | `[Prefix]` | Responsibilities | Key Arguments |
| --- | --- | --- | --- |
| `tools/feature_miner.py` | `[FeatureMiner]` | Bar geometry, VSA volume Z-score, Parkinson volatility, rolling Hurst proxy, AVWAP | `--input`, `--output`, `--window` |
| `tools/vectorized_screener.py` | `[VectorizedScreener]` | Fast Vectorbt / Polars IS strategy coarse filter with taker fee friction | `--data`, `--rules`, `--fee-bps`, `--output` |
| `tools/validation_cynic.py` | `[ValidationCynic]` | DSR calculation, parameter stability surface grid, Monte Carlo, OOS audit | `--returns`, `--trials`, `--param-grid`, `--oos-data` |
| `tools/run_backtest_audit.py` | `[BacktestAudit]` | Full backtest, equity curve, regime survival, 5-Gate Cynic matrix, saves state | `--strategy`, `--save-state`, `--json-output` |
| `tools/state_control.py` | `[StateControl]` | **Shared state CLI:** read/patch state, deploy/stop strategies, manage signals | `get`, `patch`, `deploy`, `stop`, `signals`, `signal-stats`, `signal-add`, `schema` |
| `tools/strategy_emitter.py` | `[StrategyEmitter]` | Generates Freqtrade `IStrategy` or Jesse strategy Python code | `--thesis`, `--rules`, `--framework`, `--out` |
| `tools/ui_dispatcher.py` | `[UIDispatcher]` | Dispatches WebSocket widgets, chart markers, and Telegram alerts | `--event`, `--payload`, `--endpoint` |
| `tools/server_control.py` | `[ServerControl]` | Start/stop FastAPI server & Telegram gateway | `start`, `stop`, `status`, `--port` |
| `tools/frontend_control.py` | `[FrontendControl]` | Build and serve the dual-screen React UI | `build`, `start`, `stop`, `status`, `--port` |
| `tools/bot_control.py` | `[BotControl]` | Launch and manage Freqtrade/Jesse paper trading bot | `deploy`, `stop`, `status`, `--strategy`, `--mode` |

> All tools follow one consistent authoring standard — see `SKILL.md` § Tool Authoring Standard.

---

## 💻 Web Terminal Hotkeys

| Key | Screen |
|---|---|
| **`F1`** | Chart Canvas — live BTC/USDT candlestick chart with backtest trade markers |
| **`F2`** | Signal Deck — live signal feed, win rate, profit factor, Sharpe & PnL since activation |
| **`F3`** | Backtest — equity curve, return distribution, regime survival, 5-Gate Cynic Audit |
| **`Ctrl + Space`** | Cycle through all three screens |

---

## 🗄️ Shared State Architecture

All three consumers — **AI agent**, **server**, and **frontend** — read and write the same state.
No component accesses `data/state.json` or `data/signals.json` directly.

```
AI Agent CLI                 Server (FastAPI)             Frontend (React)
tools/state_control.py       server/main.py               useWebSocket hook
        │                          │                             │
        └──────── REST ───────────►│◄──────── REST GET ──────────┘
                            server/state_manager.py
                            (file-locked reads & writes)
                                   │
                           data/state.json
                           data/signals.json
                                   │
                     WS broadcast (STATE_UPDATED)
                       ┌───────────┘
                       ▼
             All open frontend screens
             update in real time
```

See [`references/state_management.md`](references/state_management.md) for the full schema, Python API, and CLI reference.

---

## 📜 License
MIT License. Built for autonomous quantitative research and strategy development.

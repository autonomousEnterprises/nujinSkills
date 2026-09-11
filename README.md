# ⚡ NujinAI: Autonomous Quant Trading Engine & Dual-Screen Cockpit

> **An agent-agnostic quantitative alpha discovery engine, self-improving strategy builder, 24/7 Telegram signal gateway, and interactive dual-screen telemetry Cockpit.**

---

## 🌟 Key Capabilities

- 🤖 **Nujin the Self-Improving Quant Agent:** An autonomous AI quant researcher that formulates non-consensus trading rules, runs vectorized backtests with taker friction, audits candidate returns via Deflated Sharpe Ratio ($\text{DSR} \ge 0.95$), and continually self-improves its hypotheses, tools, and research methodology.
- 🔁 **Continuous Autonomous Research Engine (`tools/nujin_miner.py`):** Persistent, disk-backed optimization loop (`.nujin/`) testing candidate rules against fixed historical regime slices (Bull, Bear, Range) with strict apples-to-apples validation scoring and confidence margins.
- 📐 **Strict Binary Evaluation Criteria:** 4–6 strict yes/no programmatic checks (`vectorized_screener.py`, `validation_cynic.py`, `run_backtest_audit.py`) eliminating subjective ratings (Net Sharpe $\ge 1.8$, MaxDD $\le 4.5\%$, Win Rate $\ge 50\%$, Expectancy $\ge 2\times$ fees, DSR $\ge 0.95$, parameter plateau stability).
- 🧬 **Structured Mutation Operators & Plateau Breakers:** Systematically mutates candidate rules via `add_constraint`, `add_negative_example`, `restructure_exit`, `tighten_thresholds`, `remove_bloat`, `directional_bias_flip`, and `plateau_break` (synthesizing fresh hypotheses from accumulated failure memory).
- 🛠️ **Meta-Tool Evolution:** Nujin audits, benchmarks, and evolves its own CLI tools (`python tools/nujin_miner.py improve-tool`), expands reference documentation with empirical discoveries, and refactors computational bottlenecks.
- 🖥️ **Dual-Screen Visual Cockpit:** High-speed Web UI (`frontend_control.py`) featuring TradingView Lightweight Charts, live execution telemetry, backtest analytics, and the Strategy Manager command deck.
- 💬 **24/7 Telegram Signal Gateway:** Integrated Telegram bot dispatcher broadcasting real-time trade signals, regime shifts, and PnL alerts to user messaging channels.
- 🚀 **Standard Bot Code Emission:** Emits production-ready Freqtrade/Jesse `IStrategy` code and deploys paper or live trading bots via `bot_control.py`.

---

## 🤖 Integration & Usage Guide Across AI Environments

**NujinSkills** is built around an agent-agnostic `SKILL.md` contract and local CLI tools.

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

## 💬 User Strategy Prompts & Profiles

Prompt Nujin naturally with your quantitative trading goal:

1. **Prop Firm Strategy:**
   > *"I need a prop firm trading strategy."*  
   > *(Nujin sets strict Max DD $\le 4.5\%$, Sharpe $\ge 1.8$, DSR $\ge 0.95$, executes the self-improving loop, emits Freqtrade code, and launches paper trading).*

2. **BTC Swing Trading Strategy:**
   > *"Make me a btc market cycle swing trade strategy."*  
   > *(Nujin extracts multi-day trend/chop regimes using Hurst $H > 0.55$, optimizes dynamic holding periods, and projects markers on the Lightweight Chart).*

3. **Conservative Wealth Preservation:**
   > *"Make me a longterm conservative investment strategy."*  
   > *(Nujin targets capital preservation, Parkinson volatility compression, Max DD $\le 6\%$, and low trade turnover).*

4. **News Volatility Strategy:**
   > *"How can news be traded effectively?"*  
   > *(Nujin mines post-event V-Spread spikes and wick rejection fades, stress-tests with Monte Carlo reshuffling, and relays alerts to Telegram).*

---

## 🔄 The Self-Improving Quant Workflow Funnel

```
                        [ USER PROMPT ]
  ("I need a prop firm strategy" / "Make me a BTC swing strategy")
                                │
                                ▼
                ┌───────────────────────────────┐
                │ 1. Scan Market & Features     │
                │    python tools/feature_...   │
                └───────────────┬───────────────┘
                                │
                                ▼
                ┌───────────────────────────────┐
                │ 2. Define Binary Evals (M=6)  │
                │    (Sharpe, MaxDD, DSR, etc.) │
                └───────────────┬───────────────┘
                                │
                                ▼
                ┌───────────────────────────────┐
                │ 3. Init Research Loop (.nujin)│
                │    python tools/nujin_miner.py│
                │    init                       │
                └───────────────┬───────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────┐
│              4. CONTINUOUS AUTONOMOUS ALPHA LOOP              │
│                                                               │
│   • Evaluate candidate rules on fixed validation slices       │
│   • Score binary criteria (0 to 6)                            │
│   • KEEP if validation_score > best by margin, else DISCARD   │
│   • Apply structured mutations (add_constraint, exit, etc.)  │
│   • Trigger plateau_break after 5 consecutive failures        │
│   • Dispatch real-time UI telemetry widget to Cockpit         │
└───────────────────────────────┬───────────────────────────────┘
                                │
                                ▼ (DSR >= 0.95 & Score 6/6)
                ┌───────────────────────────────┐
                │ 5. Emit Code & Live Deploy    │
                │    - Emit Freqtrade Strategy  │
                │    - Register in StrategyMgr  │
                │    - Launch Paper Bot         │
                │    - Stream Telegram Alerts   │
                └───────────────────────────────┘
```

---

## 📂 Repository Architecture

```
NujinSkills/
├── SKILL.md                       <-- Master Skill Contract, Nujin execution manual
├── README.md                      <-- This file
├── requirements.txt               <-- Python dependencies (polars, vectorbt, uvicorn, etc.)
├── .nujin/                        <-- Single Source of Truth for Autonomous Alpha Loop
│   ├── state.json                 # Live run counter, best scores, plateau counter
│   ├── rules.json                 # Current candidate rules
│   ├── best_rules.json            # Current champion rules
│   └── results.jsonl              # Append-only audit history of every research cycle
├── data/
│   ├── state.json                 # ★ Single Source of Truth — read by all consumers
│   ├── strategies.json            # Strategy registry (ACTIVE_LIVE, CRON_BACKTEST, DEACTIVATED)
│   ├── signals.json               # Persisted live signals (managed by SignalStore)
│   ├── features.csv               # Extracted OHLCV feature matrix
│   ├── candles_15m.csv            # BTC/USDT 15m historical candles
│   └── candidate_returns.json     # Trade return arrays for DSR audit
├── references/                    <-- Production-Grade Reference Manuals (Zero Bloat)
│   ├── alpha_ideation.md          # Dialectic ideation, 6 quant dimensions, strategy profiles, 7 mutations
│   ├── feature_engineering.md     # Bar physics, wicks, VSA, Parkinson, Hurst proxy, AVWAP
│   ├── statistical_validation.md  # Strict binary metrics, DSR formula, parameter plateau, ATR stops
│   ├── self_improving_loop.md     # Autonomous research engine, disk state, validation slicing, plateau breakers
│   ├── execution_and_signals.md   # Freqtrade/Jesse code emission, 24/7 Telegram signal gateway, bot supervisor
│   ├── state_architecture.md      # StateManager, SignalStore, atomic file locks, tri-state lifecycle, cron drift
│   ├── cockpit_telemetry.md       # Dual-screen Cockpit UI architecture, TradingView charts, WS bus, F1–F4 hotkeys
│   └── extending_nujin.md         # Developer guide: REST endpoints, WS events, React screens, tool authoring standard
├── tools/                         <-- Nujin AI CLI Tools (one consistent standard)
│   ├── nujin_miner.py             # [NujinMiner]      ★ Autonomous Alpha Loop & Tool Evolver
│   ├── feature_miner.py           # [FeatureMiner]    Bar geometry, Hurst, VSA, Parkinson, AVWAP
│   ├── vectorized_screener.py     # [VectorizedScreener] Vectorbt fast In-Sample filter
│   ├── validation_cynic.py        # [ValidationCynic] DSR gate, Monte Carlo, OOS audit
│   ├── run_backtest_audit.py      # [BacktestAudit]   Full backtest & 5-Gate Cynic report
│   ├── strategy_manager.py        # [StrategyManager] Lifecycle, portfolio & cron drift CLI
│   ├── state_control.py           # [StateControl]    Shared state CLI for AI agents
│   ├── strategy_emitter.py        # [StrategyEmitter] Freqtrade IStrategy code generator
│   ├── ui_dispatcher.py           # [UIDispatcher]    WebSocket event dispatcher
│   ├── server_control.py          # [ServerControl]   Start/stop FastAPI server
│   ├── frontend_control.py        # [FrontendControl] Build/serve Cockpit dashboard
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
└── frontend/                      <-- User Telemetry Cockpit
    └── src/
        ├── App.tsx                # Screen router, unified state via useWebSocket
        ├── components/
        │   ├── ChartCanvas.tsx    # F1 — Live BTC/USDT chart + backtest trade markers
        │   ├── SignalDeck.tsx     # F2 — Live signals, PnL, win rate, Sharpe since activation
        │   ├── BacktestDeck.tsx   # F3 — Equity curve, regime survival, 5-Gate Cynic audit
        │   ├── StrategyManagerDeck.tsx # F4 — Command center, leaderboard, drift trajectory
        │   └── Header.tsx         # Strategy mega-menu, WS status, screen switcher
        └── hooks/
            └── useWebSocket.ts    # Real-time WS client — surfaces liveSystemState
```

---

## ⚡ Quick Start

### 1. Installation
Clone the repository and install dependencies in virtualenv:
```bash
pip install -r requirements.txt
```

### 2. Run Autonomous Quant Alpha Discovery
```bash
# Initialize state and baseline rules
python tools/nujin_miner.py init --target "Prop Firm Dual Wick Rejection"

# Run 10 continuous research cycles
python tools/nujin_miner.py run --cycles 10

# Inspect status and recent mutations
python tools/nujin_miner.py status
```

### 3. Self-Audit Tools (Meta-Tool Evolution)
Audit and benchmark any tool in `tools/`:
```bash
python tools/nujin_miner.py improve-tool --tool feature_miner.py
```

### 4. Launch Cockpit & Telemetry Backend
Start services in background daemon mode:
```bash
# Start FastAPI Telemetry Backend & Telegram Signal Gateway (Port 8000)
python tools/server_control.py start --port 8000 --daemon

# Start Dual-Screen Frontend Cockpit (Port 3000)
python tools/frontend_control.py start --port 3000 --daemon
```

---

## 🛠️ CLI Tools Reference

| Tool Script | `[Prefix]` | Responsibilities | Key Arguments |
| --- | --- | --- | --- |
| `tools/nujin_miner.py` | `[NujinMiner]` | **Autonomous Alpha Loop & Tool Evolver:** hypothesis-eval-mutate cycles, binary scoring, disk state, and meta-tool auditing | `init`, `step`, `run`, `status`, `improve-tool`, `--target`, `--cycles`, `--tool` |
| `tools/feature_miner.py` | `[FeatureMiner]` | Bar geometry, VSA volume Z-score, Parkinson volatility, rolling Hurst proxy, AVWAP | `--input`, `--output`, `--window` |
| `tools/vectorized_screener.py` | `[VectorizedScreener]` | Fast Vectorbt / Polars IS strategy coarse filter with taker fee friction | `--data`, `--rules`, `--fee-bps`, `--output` |
| `tools/validation_cynic.py` | `[ValidationCynic]` | DSR calculation, parameter stability surface grid, Monte Carlo, OOS audit | `--returns`, `--trials`, `--param-grid`, `--oos-data` |
| `tools/run_backtest_audit.py` | `[BacktestAudit]` | Full backtest, equity curve, regime survival, 5-Gate Cynic matrix, saves state | `--strategy`, `--save-state`, `--json-output` |
| `tools/strategy_manager.py` | `[StrategyManager]` | Strategy lifecycle CLI: multi-bot execution, rankings, drift tracking | `list`, `status`, `portfolio`, `drift`, `signals`, `backtest`, `cron`, `rank` |
| `tools/state_control.py` | `[StateControl]` | Shared state CLI: read/patch state, deploy/stop strategies, manage signals | `get`, `patch`, `deploy`, `stop`, `signals`, `signal-stats`, `signal-add` |
| `tools/strategy_emitter.py` | `[StrategyEmitter]` | Generates Freqtrade `IStrategy` or Jesse strategy Python code | `--thesis`, `--rules`, `--framework`, `--out` |
| `tools/ui_dispatcher.py` | `[UIDispatcher]` | Dispatches WebSocket widgets, chart markers, and Telegram alerts | `--event`, `--payload`, `--endpoint` |
| `tools/server_control.py` | `[ServerControl]` | Start/stop FastAPI server & Telegram gateway | `start`, `stop`, `status`, `--port` |
| `tools/frontend_control.py` | `[FrontendControl]` | Build and serve the dual-screen React Cockpit | `build`, `start`, `stop`, `status`, `--port` |
| `tools/bot_control.py` | `[BotControl]` | Launch and manage Freqtrade/Jesse paper trading bot | `deploy`, `stop`, `status`, `--strategy`, `--mode` |

---

## 💻 Cockpit Hotkeys

| Key | Screen |
|---|---|
| **`F1`** | Chart Canvas — live BTC/USDT candlestick chart with backtest trade markers |
| **`F2`** | Signal Deck — live signal feed, win rate, profit factor, Sharpe & PnL since activation |
| **`F3`** | Backtest — equity curve, return distribution, regime survival, 5-Gate Cynic Audit |
| **`F4`** | Strategy Manager — command center, multi-bot execution, leaderboard, drift trajectory |
| **`Ctrl + Space`** | Cycle through all screens |

---

## 📜 License
MIT License. Built for autonomous quantitative research and strategy development.

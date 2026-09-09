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
NujinSkills/
├── SKILL.md                     <-- Master Skill Contract & Execution Manual
├── PROJECT.md                   <-- Master Development Roadmap & Checklist
├── requirements.txt             <-- Clean Python dependencies (polars, vectorbt, uvicorn, etc.)
├── references/                  <-- AI Agent Knowledge Base (16 canonical specs)
│   ├── strategy_profiles.md     # Natural prompt intent mapping & risk targets
│   ├── dashboard.md             # Dual-output event bus & UI telemetry schemas
│   ├── edge.md                  # Quantitative edge & counterparty trap principles
│   ├── extended_tools_ideas.md  # Advanced math feature extraction (Hurst, Parkinson, AVWAP)
│   ├── indicator_usage.md       # Non-consensus indicator principles
│   ├── libs_clis.md             # Python libraries & CLI tool contracts
│   ├── outofthebox_solutions_finding.md # Dialectic ideation engine (Consensus -> Failure -> Synthesis)
│   ├── pricedataonly_edge_mining.md    # Price auction footprints & bar geometry
│   ├── process.md               # 5-phase operational funnel specifications
│   ├── riskmanagement.md        # Risk controls, ATR stops, invalidation rules
│   ├── signals_gateway.md       # 24/7 Telegram Signal Gateway integration
│   ├── simple_tools_ideas.md    # Bar geometry & VSA volume Z-scores
│   ├── statistic_edge.md        # DSR formula & statistical rejection hurdles
│   ├── thirdparty_edge_mining.md# Order book proxies & funding rate dynamics
│   ├── tradingbot.md            # Freqtrade & Jesse strategy execution contracts
│   └── ui_management.md         # Hotkey viewport switching & Server-Driven UI
├── notes/                       <-- User Preparation Notes (READ-ONLY)
├── tools/                       <-- Executable CLI Tools for AI Agent
│   ├── feature_miner.py         # Bar geometry, Hurst, VSA, Parkinson Vol, AVWAP
│   ├── vectorized_screener.py   # Vectorbt fast In-Sample filter
│   ├── validation_cynic.py      # DSR gate, Parameter stability, Monte Carlo, OOS audit
│   ├── strategy_emitter.py      # Freqtrade IStrategy code generator
│   ├── ui_dispatcher.py         # WebSocket event dispatcher (Charts & Widgets)
│   ├── server_control.py        # CLI: start/stop FastAPI server & Telegram gateway
│   ├── frontend_control.py      # CLI: build/serve frontend dashboard UI
│   └── bot_control.py           # CLI: deploy/manage trading bot paper/live process
├── server/                      <-- Telemetry Backend & Telegram Gateway
│   ├── main.py                  # FastAPI application & REST API
│   ├── websocket.py             # Real-time WebSocket event broadcaster
│   ├── telegram_bot.py          # Telegram signal gateway (24/7 alerts)
│   ├── bot_runner.py            # Freqtrade / Jesse paper-trading supervisor
│   └── data_manager.py          # OHLCV data loader & feed server
└── frontend/                    <-- User Telemetry Dashboard (Dual-Screen UI)
    ├── package.json
    ├── vite.config.ts
    ├── index.html
    └── src/
        ├── App.tsx              # Dual-screen viewport layout & hotkey listener
        ├── components/
        │   ├── ChartCanvas.tsx  # TradingView Lightweight Charts canvas
        │   ├── AgentDeck.tsx    # Server-Driven UI Widget Grid
        │   └── Header.tsx       # Status pill & screen switcher
        └── hooks/
            └── useWebSocket.ts  # Real-time WS client hook
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

---

## 🛠️ CLI Tools Reference

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

---

## 💻 Web Terminal Hotkeys

- **`Ctrl + Space`** / **`Tab`**: Instantly swap between Screen 1 (TradingView Lightweight Chart Canvas) and Screen 2 (Agent Deck & Telemetry Report).
- **`F1`**: Direct focus to Lightweight Chart Canvas.
- **`F2`**: Direct focus to Agent Deck & Mining Telemetry.

---

## 📜 License
MIT License. Built for autonomous quantitative research and strategy development.

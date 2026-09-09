# NujinSkill: Autonomous Quant Edge Mining Engine & Signal Gateway

## Overview
NujinSkill is a complete, standalone quantitative alpha discovery engine, strategy execution package, 24/7 Telegram signal gateway, and dynamic dual-screen user terminal. This repository itself acts as an agent-agnostic skill through the root `SKILL.md` contract.

Everything is driven by executable CLI scripts in `tools/`:
- `python tools/feature_miner.py` (Bar geometry, VSA volume Z-scores, Hurst proxy, Parkinson volatility, AVWAP)
- `python tools/vectorized_screener.py` (Vectorbt / Polars fast In-Sample coarse filter)
- `python tools/validation_cynic.py` (Deflated Sharpe Ratio, parameter stability surface, Monte Carlo, OOS audit)
- `python tools/strategy_emitter.py` (Freqtrade & Jesse strategy code generator)
- `python tools/ui_dispatcher.py` (WebSocket event & Telegram alert dispatcher)
- `python tools/server_control.py` (Start/stop FastAPI server & Telegram gateway)
- `python tools/frontend_control.py` (Build/start React dual-screen terminal)
- `python tools/bot_control.py` (Deploy/manage Freqtrade dry-run / paper-trading instances)

---

## Directory Layout

```
NujinSkill/
├── SKILL.md                     <-- Master skill contract & CLI usage guide
├── PROJECT.md                   <-- Master project roadmap & checklist
├── requirements.txt             <-- Minimal Python dependencies
├── references/                  <-- AI Agent Canonical Reference Knowledge Base
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
├── tools/                       <-- Self-contained CLI Tools executed by AI Agent
│   ├── feature_miner.py         # Bar geometry, Hurst, VSA, Parkinson Vol, AVWAP
│   ├── vectorized_screener.py   # Vectorbt fast In-Sample filter
│   ├── validation_cynic.py      # DSR gate, Parameter stability, Monte Carlo, OOS audit
│   ├── strategy_emitter.py      # Freqtrade IStrategy code generator
│   ├── ui_dispatcher.py         # WebSocket event dispatcher (Charts & Widgets)
│   ├── server_control.py        # CLI tool: start/stop FastAPI server & Telegram gateway
│   ├── frontend_control.py      # CLI tool: build/serve frontend dashboard UI
│   └── bot_control.py           # CLI tool: deploy/manage trading bot paper/live process
├── server/                      <-- Telemetry Backend & Telegram Gateway
│   ├── main.py                  # FastAPI server & REST API
│   ├── websocket.py             # Real-time WebSocket event broadcaster
│   ├── telegram_bot.py          # Telegram signal gateway (24/7 alerts)
│   ├── bot_runner.py            # Freqtrade / Jesse paper-trading supervisor
│   └── data_manager.py          # OHLCV data loader & feed server
└── frontend/                    <-- User Telemetry Dashboard (Dual-Screen UI)
    ├── package.json
    ├── vite.config.ts
    ├── index.html
    └── src/
        ├── App.tsx
        ├── components/
        │   ├── ChartCanvas.tsx  # TradingView Lightweight Charts
        │   ├── AgentDeck.tsx    # Server-Driven UI Widget Grid
        │   ├── Header.tsx       # Hotkey Viewport Switcher (Ctrl + Space)
        │   └── widgets/         # MetricCard, HeatmapMatrix, HypothesisLog, etc.
        └── hooks/
            └── useWebSocket.ts  # Real-time WS client
```

---

## Development Roadmap & Status

### Phase 1: Knowledge Base & Skill Contract Setup
- [x] Create root `PROJECT.md` tracking document
- [x] Create dedicated AI Agent reference library in `references/` (15 structured files)
- [x] Keep user preparation `notes/` untouched
- [x] Create root `SKILL.md` master contract
- [x] Create root `requirements.txt`

### Phase 2: Core Mining & Falsification CLI Tools (`tools/`)
- [x] `tools/feature_miner.py`
- [x] `tools/vectorized_screener.py`
- [x] `tools/validation_cynic.py`
- [x] `tools/strategy_emitter.py`
- [x] `tools/ui_dispatcher.py`

### Phase 3: Telemetry Backend & Telegram Signal Gateway (`server/` + `tools/server_control.py`)
- [x] `server/main.py`
- [x] `server/websocket.py`
- [x] `server/telegram_bot.py`
- [x] `server/bot_runner.py`
- [x] `tools/server_control.py`

### Phase 4: User Telemetry Terminal (`frontend/` + `tools/frontend_control.py`)
- [x] React + Vite + Tailwind setup
- [x] `src/components/ChartCanvas.tsx`
- [x] `src/components/AgentDeck.tsx`
- [x] `src/components/Header.tsx`
- [x] `tools/frontend_control.py`

### Phase 5: Trading Bot Supervisor (`tools/bot_control.py`) & Verification
- [x] `tools/bot_control.py`
- [x] End-to-end integration test & verification (Pass)

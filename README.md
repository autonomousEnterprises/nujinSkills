# ⚡ NujinAI / EdgeMiner — Autonomous Quant Trading Agent Skill

[![System: NujinAI](https://img.shields.io/badge/System-NujinAI-blue.svg)](SKILL.md)
[![Year: 2026 Standard](https://img.shields.io/badge/Standard-2026%20Quant%20Agent-emerald.svg)](references/quant_strategies.md)
[![Cockpit: Dual--Screen Vue 3](https://img.shields.io/badge/Cockpit-Dual--Screen%20Vue%203-indigo.svg)](references/cockpit_telemetry.md)
[![Engine: VectorBT & DSR](https://img.shields.io/badge/Audit-DSR%20%E2%89%A5%200.95-amber.svg)](references/statistical_validation.md)
[![Signals: 24/7 Telegram](https://img.shields.io/badge/Signals-24%2F7%20Telegram-sky.svg)](references/execution_and_signals.md)

> **Unlock the trading world effortlessly.** You bring the creative vision and define your financial goals; your AI agent handles the heavy algorithmic grinding, statistical falsification, 24/7 live signaling, and tool self-evolution.

---

## 🎯 What is NujinAI?

**NujinAI (EdgeMiner)** is a self-evolving quantitative trading assistant and execution engine packaged as an open, agent-agnostic **AI Skill**. 

Instead of getting bogged down in boilerplate code, slippage modeling, or curve-fitted indicators:
1. **You stay creative:** State your market intuition, target asset, risk tolerance, and profit milestones in natural language.
2. **The Agent grinds:** Researches market microstructure, writes vectorized backtests, stress-tests against historical regimes, audits returns via the **Deflated Sharpe Ratio ($\text{DSR} \ge 0.95$)**, and verifies parameter stability.
3. **Deploys & Broadcasts:** Streams visual telemetry to a dual-screen Vue 3 Cockpit and broadcasts actionable 24/7 signals directly to your Telegram.
4. **Continuously Self-Improves:** Retains empirical memory on disk of what works and what fails, mutates trading hypotheses, refines its own Python tools, and records your personal financial objectives.

---

## ⚡ Quick Start: Zero to Alpha in Minutes

### Option 1: Direct Agent Execution (Easiest)
Simply clone or open this directory in **any AI agent or IDE** (Google Antigravity, Claude Code, Cursor, Windsurf, OpenClaw, Hermes):

```bash
git clone https://github.com/autonomousEnterprises/EdgeMiner.git
cd EdgeMiner
```

Initialize your virtual environment & dependencies:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Start the system engines:
```bash
# 1. Start FastAPI Telemetry & Signal Server (Port 8000)
python tools/server_control.py start --port 8000 --daemon

# 2. Start Dual-Screen Visual Cockpit (Port 3000)
python tools/frontend_control.py start --port 3000 --daemon
```

Now, **simply prompt your AI agent**:
> *"I want a prop-firm ready gold (XAU/USD) 1m scalping strategy targeting max 4% drawdown, minimum 1.8 Sharpe, with tight ATR trailing stops. Explore the market and build it."*

The agent reads [`SKILL.md`](SKILL.md), conducts feature extraction, runs adversarial backtests, and deploys it.

---

### Option 2: Install as a Reusable Agent Skill

Install NujinSkills globally across your favorite agentic frameworks:

```bash
# Google Antigravity (Workspace or Global Skill)
mkdir -p ~/.gemini/config/skills/nujinskills
cp -r ./* ~/.gemini/config/skills/nujinskills/

# OpenClaw / Hermes CLI Agents
openclaw skill add ./
# Or symlink directly
ln -s $(pwd) ~/.openclaw/skills/nujinskills

# Claude Code
claude skill add ./
```

---

## 🔁 The Autonomous Alpha Loop

```
  User Financial Goal & Thesis
              │
              ▼
┌────────────────────────────────────────────────────────┐
│               PHASE 1–4: DISCOVERY & BENCHMARK         │
│  • Microstructure features (VSA, wicks, Parkinson vol) │
│  • Strict Binary Criteria (Sharpe ≥ 1.8, MaxDD ≤ 4.5%) │
│  • Apples-to-apples baseline on historical regimes     │
└─────────────────────────────┬──────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────┐
│          PHASE 5: PERSISTENT ALPHA MINING LOOP         │
│  • Continuous trial mutations via structured operators │
│  • Keep/discard decisions backed by disk persistence   │
│  • Plateau breakers triggered on stalled alpha         │
└─────────────────────────────┬──────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌───────────────────────────────┐ ┌───────────────────────────────┐
│ 5-GATE CYNIC AUDIT (DSR≥0.95) │ │ TELEMETRY & LIVE EXECUTION    │
│  1. Deflated Sharpe Ratio     │ │  • Dual-Screen Cockpit (Vue 3)│
│  2. Parameter Plateau Surface │ │  • 24/7 Telegram Gateway      │
│  3. Monte Carlo Tail MDD99    │ │  • Freqtrade / Jesse Bots     │
│  4. Out-of-Sample Retention   │ │  • Dynamic Risk Sizing        │
│  5. Market Regime Breakdown   │ │  • Signal Conflict Guard      │
└───────────────────────────────┘ └───────────────────────────────┘
```

---

## 🖥️ The Dual-Screen Cockpit

Access the interactive trading cockpit at **`http://localhost:3000`**:

| Screen / Deck | Hotkey | Purpose & Telemetry |
|---|---|---|
| **Chart Canvas** | **`F1`** | High-performance TradingView candlestick chart overlaid with Level 3 visual primitives (multi-scale EMAs, Bollinger/Keltner bands), Fair Value Gap (FVG) imbalance boxes, liquidity sweeps, and execution markers. |
| **Signal Deck** | **`F2`** | Live execution telemetry: win rate, profit factor, annualized Sharpe, active open position card with real-time unrealized PnL, and manual position override button. |
| **Backtest Deck** | **`F3`** | Comprehensive backtest audit: authentic calendar time windows, equity growth curve, return distribution, regime breakdown (Bull, Bear, Range), and 5-Gate Cynic matrix. |
| **Strategy Manager** | **`F4`** | Institutional 4-pillar strategy leaderboard, global Live vs. Backtest toggle, equity trajectory curves, correlation matrices, and direct *View on Chart (F1)* action navigation. |
| **Cycle Screens** | **`Ctrl + Space`** | Seamlessly toggle focus between open decks. |

---

## 🛠️ CLI Toolkit Overview

All tools conform to the 2026 Nujin Agent Standard and execute directly in your terminal:

```bash
# Continuous quant alpha mining
python tools/nujin_miner.py run --archetype mean_reversion --cycles 10

# Screen strategies using fast vectorized VectorBT filter
python tools/vectorized_screener.py --data data/candles_15m.csv --strategy candidate.py

# Adversarial 5-Gate Cynic Audit (DSR >= 0.95)
python tools/validation_cynic.py --strategy candidate.py --strict

# Institutional 4-Pillar Ranking Leaderboard
python tools/strategy_manager.py rank

# Deep strategy quantitative breakdown & tier rationale
python tools/strategy_manager.py insights <strategy_name>

# Portfolio correlation matrix & regime orthogonality
python tools/portfolio_cynic.py --threshold 0.50

# Broadcast market updates or daily performance reports to Telegram
python tools/telegram_broadcast.py broadcast --type report --title "Daily Alpha" --message "PnL: +3.2%, Sharpe: 2.1"

# Supervise paper (dry-run) or live bot execution
python tools/bot_control.py deploy --strategy candidate --mode dry-run
```

---

## 🧠 Self-Improvement & Long-Term Adaptation

NujinAI does not stop at strategy generation:
- **Disk-Grounded Learning (`.nujin/`):** Preserves run counters, empirical failure patterns, and candidate rules across sessions. It never repeats discredited parameter combinations.
- **Goal-Aware Alignment:** Incorporates user-defined financial scope, drawdown constraints, and risk tolerances into its core binary acceptance matrix.
- **Meta-Tool Evolution:** Audits its own internal CLI scripts (`python tools/nujin_miner.py improve-tool --tool <name.py>`), updates documentation, vectorizes bottlenecks, and refines feature miners.

---

## 📚 Reference Knowledge Base

For in-depth mathematical derivations and architecture specifications:
- [`SKILL.md`](SKILL.md) — Master Autonomous Quant Engine Protocol & Instructions
- [`references/cockpit_telemetry.md`](references/cockpit_telemetry.md) — Dual-Screen Cockpit, WebSocket Bus & UI Controls
- [`references/quant_strategies.md`](references/quant_strategies.md) — 2026 Quant Landscape, SMC/ICT, 0DTE & Microstructure
- [`references/strategy_ranking_tiers.md`](references/strategy_ranking_tiers.md) — 4-Pillar Scoring Model & Tier Hurdles
- [`references/statistical_validation.md`](references/statistical_validation.md) — Deflated Sharpe Ratio & Adversarial Falsification
- [`references/feature_engineering.md`](references/feature_engineering.md) — Raw Auction Dynamics, Bar Physics & VSA
- [`references/execution_and_signals.md`](references/execution_and_signals.md) — Bot Supervisors & Telegram Signal Gateway
- [`references/extending_nujin.md`](references/extending_nujin.md) — Developer Guide: Adding REST endpoints, WS feeds & Vue 3 decks

---

## 📄 License

MIT License — Autonomous Enterprises. Built for systematic quantitative traders and autonomous agent swarms.

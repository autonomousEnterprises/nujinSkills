---
name: hummingbot-strategy
description: "Use when creating, structuring, validating, or optimizing trading strategies for Hummingbot. Provides code generators for strategy boilerplates, a Python script validator to avoid execution bugs, and a step-by-step framework to transition strategies from research to consistent live profitability."
risk: medium
source: nujinSkills
date_added: "2026-05-24"
---

# Hummingbot Strategy Framework

A comprehensive framework to help AI agents and human developers design, test, validate, and scale profitable trading strategies for the Hummingbot open-source high-frequency trading bot.

> [!NOTE]
> This skill focuses specifically on the development, boilerplate generation, validation, and profitability lifecycles of custom Python strategies. If you want to know more about how to install, configure, run, or manage the Hummingbot instance itself, please checkout the separate `hummingbot` skill.

## When to Use

- Generating boilerplate code for a new Hummingbot script strategy or Strategy V2 controller.
- Validating custom Python strategy scripts for common API usage mistakes, infinite execution loops, or dangerous floating-point math.
- Structuring indicators, risk management parameters, and order management.
- Looking for a systematic process to refine a trading edge from raw backtesting to live production.

## Scripts

Run from the repository root:

| Script | Purpose | Command Example |
|--------|---------|-----------------|
| `generate.ts` | Generate boilerplate Python strategy files | `npx tsx skills/hummingbot-strategy/scripts/generate.ts --name MyBot --type script` |
| `validate.ts` | Validate strategy files for common bugs | `npx tsx skills/hummingbot-strategy/scripts/validate.ts --file path/to/strategy.py` |

*Generator Options:*
- `--name`: Class and filename of the strategy (e.g. `MyRsiStrategy`).
- `--type`: `script` (for ScriptStrategyBase) or `v2` (for Strategy V2 Controller).
- `--pair`: Default trading pair (e.g. `BTC-USDT`).
- `--connector`: Default exchange/connector (e.g. `binance`).
- `--indicators`: Comma-separated list of indicators to stub out in the file.

*Validator checks:*
- **Structural Integrity:** Correct imports, class definition, inheritance, and presence of mandatory functions (`on_tick`, `markets`, etc.).
- **Floating-point check:** Flags dangerous `float` arithmetic for order sizes/prices and suggests using `Decimal`.
- **Order flooding:** Warns if orders are placed on tick without verification of current open orders or active cooldown flags.
- **Error handling:** Identifies if trade execution lacks try/catch or rate limit safety rails.

## Templates

Use these Python templates as dynamic starting points:

| Template | Type | Description |
|----------|------|-------------|
| [`script_strategy_base_template.py`](templates/script_strategy_base_template.py) | Script | Basic boilerplate for legacy `ScriptStrategyBase` scripts |
| [`directional_rsi_strategy.py`](templates/directional_rsi_strategy.py) | Script | Working RSI directional script with stop-loss/take-profit guards |
| [`strategy_v2_controller_template.py`](templates/strategy_v2_controller_template.py) | Controller | Boilerplate for Strategy V2 `ControllerBase` and configuration model |

## Reference Guides

Essential documentation to build robust, profitable strategies:

| Resource | Description |
|----------|-------------|
| [`profitable-strategy-process.md`](references/profitable-strategy-process.md) | **Strategy Profitability lifecycle:** 6-stage framework from hypothesis to scaling |
| [`hummingbot-v2-framework.md`](references/hummingbot-v2-framework.md) | V2 architecture details: market data providers, orchestrator, and position executors |
| [`common-pitfalls.md`](references/common-pitfalls.md) | Checklist of critical bugs: float precision errors, rate-limiting, and order flooding |

## Core Development Principles

### 1. Prevent Order Flooding
Hummingbot runs its clock event loop (typically `on_tick()`) every second. If your strategy executes buy/sell signals without tracking active orders or using dynamic cooldown states, the bot will flood the exchange with hundreds of orders. Always:
- Check `self.active_orders` before placing new entries.
- Use state variable boolean flags (e.g. `self.order_placed = True`).
- Use cooldown timers (e.g. tracking last trade execution timestamp).

### 2. Always Use Decimal Precision
Cryptocurrency exchanges require exact decimals for order sizing and price tick levels. Standard Python floating-point numbers (`float`) suffer from IEEE-754 binary representation errors (e.g., `0.1 + 0.2 = 0.30000000000000004`), leading to API order submission failures or unexpected execution sizing.
- Use `from decimal import Decimal`.
- Wrap all prices, sizes, and thresholds: `Decimal("0.001")`, `Decimal(str(price))`.

### 3. Handle Status Reporting Cleanly
Implement a clear `format_status()` method to display account balances, current market price, active positions, indicator values, and performance summaries in the Hummingbot CLI console.


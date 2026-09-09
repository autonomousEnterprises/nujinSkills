# Reference: Trading Bot Execution Contracts (Freqtrade & Jesse)

## Overview
NujinSkill emits strategy files for standardized trading bot frameworks that handle order routing, trailing stops, emergency cancellations, and exchange connectivity via CCXT.

---

## Target Framework Options

### Option A: Freqtrade (Recommended for Production)
- Single-file strategy class inheriting from `IStrategy`.
- Methods implemented:
  - `populate_indicators(dataframe, metadata)`
  - `populate_entry_trend(dataframe, metadata)`
  - `populate_exit_trend(dataframe, metadata)`
- Headless CLI commands:
  - Download data: `freqtrade download-data --pairs BTC/USDT -t 15m`
  - Run backtest: `freqtrade backtesting --strategy MyStrategy`
  - Deploy dry-run: `freqtrade trade --dry-run --strategy MyStrategy`

### Option B: Jesse (Cleanest Python Architecture)
- Clean OOP strategy class inheriting from `Strategy`.
- Methods implemented:
  - `should_long() -> bool`
  - `should_short() -> bool`
  - `go_long()`
- Headless CLI commands: `jesse backtest`, `jesse live`.

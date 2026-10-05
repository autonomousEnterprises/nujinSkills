# NujinSkills CLI Tools Reference Manual

This document details every tool available in `nujinSkills/tools/`.
Always invoke tools using the project virtualenv Python:
`nujinSkills/.venv/bin/python3 tools/<tool_name>.py [args]` (or `./.venv/bin/python3` if inside `nujinSkills/`).

---

## 1. Empirical Discovery & Feature Extraction

### `anomaly_scanner.py`
Empirical quantitative market anomaly & statistical discovery engine. Calculates Lo-MacKinlay Variance Ratios, Hurst exponent, conditional forward returns, and alpha decay curves.
- **Usage:**
  ```bash
  tools/anomaly_scanner.py [--data PATH] [--output PATH] [--json]
  ```
- **Arguments:**
  - `--data`: Path to OHLCV candle CSV (default: `data/candles_15m.csv`).
  - `--output`: Path to write empirical JSON briefing (default: `.nujin/empirical_briefing.json`).
  - `--json`: Output raw JSON to stdout.
- **Example:**
  ```bash
  tools/anomaly_scanner.py --data data/xauusd_candles_5m.csv --output .nujin/empirical_briefing.json
  ```

---

### `feature_miner.py`
Scalable multi-feature extractor. Computes rolling volatility, ATR, Bollinger Bands, Donchian channels, RSI, MACD, Volume Z-Scores, Fair Value Gaps (FVG), liquidity sweep rejections, and performs Higher-Timeframe (HTF) joins with zero lookahead bias.
- **Usage:**
  ```bash
  tools/feature_miner.py --input PATH --output PATH [--window INT] [--htf-data HTF_PATH] [--htf-prefix PREFIX]
  ```
- **Arguments:**
  - `--input`: Path to input OHLCV CSV file (required).
  - `--output`: Path for extracted features CSV (required).
  - `--window`: Rolling window size for baseline metrics (default: `20`).
  - `--htf-data`: Path to Higher Timeframe CSV (e.g. `data/xauusd_candles_5m.csv` or `data/candles_1h.csv`) to join HTF context via backward as-of merge.
  - `--htf-prefix`: Column prefix for HTF features (default: `htf_`).
- **Example:**
  ```bash
  tools/feature_miner.py --input data/xauusd_candles_1m.csv --output data/features.csv --htf-data data/xauusd_candles_5m.csv --window 20
  ```

---

## 2. Autonomous Search & Screening Loops

### `autoresearch_miner.py` (symlink: `nujin_miner.py`)
Complete autonomous research loop engine with state tracking in `.nujin/state.json`. Manages hypothesis iteration, automated mutations, plateau breakers, and tool self-improvement.
- **Usage:**
  ```bash
  tools/autoresearch_miner.py {init,scan,step,run,status,improve-tool} [options]
  ```
- **Actions:**
  - `init`: Initialize research state for a target and archetype.
    ```bash
    tools/autoresearch_miner.py init --target "BTC Volatility Breakout" --archetype momentum_breakout
    ```
    *(Archetypes: `mean_reversion`, `trend_following`, `momentum_breakout`, `price_action`, `smc_liquidity`, `custom`)*
  - `scan`: Run empirical anomaly scan on raw candles.
    ```bash
    tools/autoresearch_miner.py scan --data data/candles_15m.csv
    ```
  - `step`: Run a single iterative hypothesis mutation and backtest step.
    ```bash
    tools/autoresearch_miner.py step --features data/features.csv
    ```
  - `run`: Run $N$ continuous automated hypothesis discovery cycles.
    ```bash
    tools/autoresearch_miner.py run --cycles 10 --features data/features.csv
    ```
  - `status`: Display current research state, best rule, and plateau counter.
    ```bash
    tools/autoresearch_miner.py status
    ```
  - `improve-tool`: Self-audit and benchmark an internal tool script.
    ```bash
    tools/autoresearch_miner.py improve-tool --tool feature_miner.py
    ```

---

### `vectorized_screener.py`
Ultra-fast VectorBT coarse filter evaluating candidate entry/exit logic against feature datasets with realistic fee and slippage friction.
- **Usage:**
  ```bash
  tools/vectorized_screener.py [--data PATH] [--rules JSON_STR] [--fee-bps FLOAT] [--slippage-bps FLOAT] [--output PATH]
  ```
- **Arguments:**
  - `--data`: Input features CSV file path (default: `data/candles_15m.csv`).
  - `--rules`: Rule dict or JSON string specifying strategy entry/exit conditions.
  - `--fee-bps`: Taker fee in basis points (default: `5.0`).
  - `--slippage-bps`: Slippage in basis points (default: `2.0`).
  - `--output`: Output JSON path for trade return series.
- **Example:**
  ```bash
  tools/vectorized_screener.py --data data/features.csv --rules '{"entry_long": "ret_zscore < -2.0", "exit": "bars >= 6"}' --output data/candidate_returns.json
  ```

---

## 3. Adversarial Cynic Audit (Falsification)

### `cynic_auditor.py` (and `validation_cynic.py`)
Generic 5-Gate Adversarial Falsification Auditor. Verifies candidate strategy returns against real fee/slippage friction, Deflated Sharpe Ratio ($\text{DSR} \ge 0.95$), multi-regime slices, synthetic price noise jitter ($\ge 80\%$ Sharpe retention), and 1,000-run Monte Carlo trade order permutations ($\text{MDD}_{99}$ tail risk).
- **Usage:**
  ```bash
  tools/cynic_auditor.py [--returns PATH] [--strategy NAME] [--spec PATH] [--trials INT] [--strict] [--json]
  ```
- **Arguments:**
  - `--returns`: JSON file containing candidate trade returns series (array of floats).
  - `--strategy`: Strategy name in `strategies/` to run a real backtest audit on.
  - `--spec`: Strategy specification JSON path (default: `.nujin/best_rule.json`).
  - `--trials`: Cumulative trial count across discovery iterations (penalizes DSR).
  - `--strict`: Exit with non-zero exit code if any gate fails.
  - `--json`: Output raw JSON report instead of ASCII table.
- **Example:**
  ```bash
  tools/cynic_auditor.py --returns data/candidate_returns.json --trials 50 --strict
  ```

---

### `portfolio_cynic.py`
Portfolio-level correlation and regime orthogonality auditor. Rejects strategies correlated ($\rho \ge 0.50$) with currently active strategies to prevent portfolio crowding.
- **Usage:**
  ```bash
  tools/portfolio_cynic.py [--strategies NAMES] [--data PATH] [--threshold FLOAT] [--json]
  ```
- **Arguments:**
  - `--strategies`: Comma-separated strategy names (default: all strategies).
  - `--data`: Candle CSV dataset.
  - `--threshold`: Correlation rejection cutoff (default: `0.50`).
  - `--json`: Output raw JSON report.
- **Example:**
  ```bash
  tools/portfolio_cynic.py --data data/candles_15m.csv --threshold 0.50
  ```

---

## 4. Code Generation & Strategy Management

### `strategy_emitter.py`
Generates clean, production-ready standalone Python strategy classes compatible with both the live running bot's engine and standalone backtesting. Emitted classes include `populate_indicators`, `populate_entry_trend`, `populate_exit_trend`, and a self-contained `run_backtest(df)` method.
- **Usage:**
  ```bash
  tools/strategy_emitter.py --thesis "THESIS_TEXT" --rules RULES_JSON_OR_PATH [--framework {nujin,freqtrade,jesse}] [--out PATH]
  ```
- **Arguments:**
  - `--thesis`: Economic rationale and thesis description (required).
  - `--rules`: Rules JSON string or file path (e.g. `.nujin/best_rule.json`).
  - `--framework`: Target framework (`nujin` [default], `freqtrade`, `jesse`).
  - `--out`: Target output Python file path (defaults to `strategies/<StrategyName>.py`).
- **Example:**
  ```bash
  tools/strategy_emitter.py --thesis "XAUUSD Session Volatility Absorption" --rules .nujin/best_rule.json --framework nujin --out strategies/XauusdVolAbsorber.py
  ```

---

### `strategy_manager.py`
Central registry and lifecycle manager for all strategies across core and plugin directories.
- **Actions:**
  - `list`: List all discovered strategies with their operational status and metrics.
  - `plugins`: Discover and inspect strategies from dynamic plugins (in `plugins/`).
  - `status`: Update operational status of a strategy (`ACTIVE_LIVE`, `CRON_BACKTEST`, `DEACTIVATED`).
  - `rank`: Rank strategies by Sharpe ratio, win rate, and profit factor.
  - `insights`: Generate institutional performance insights for registered strategies.
  - `add`: Add and register a new strategy file.
  - `sync`: Synchronize strategy metadata with the live runtime state.
- **Examples:**
  ```bash
  tools/strategy_manager.py list
  tools/strategy_manager.py plugins
  tools/strategy_manager.py rank
  tools/strategy_manager.py status --strategy MyStrategy --status ACTIVE_LIVE
  ```

---

## 5. Live Bot Supervision & Telemetry

### `bot_control.py`
Non-disruptive supervisor CLI for the live trading bot.
- **Actions:**
  - `status`: Query live bot process, active strategies, broker connectivity, and execution mode.
  - `deploy`: Hot-deploy a strategy into execution without restarting the server.
  - `stop`: Deactivate a specific running strategy or stop execution.
  - `broker`: Inspect active broker account balances and open positions.
- **Examples:**
  ```bash
  tools/bot_control.py status
  tools/bot_control.py deploy --strategy MyStrategy --mode paper
  ```

---

### `state_control.py`
Unified state inspection and signal control CLI. Interfaces directly with the live server state.
- **Actions:**
  - `get`: Read state or a dotted key path (e.g. `backtest_summary.sharpe`).
  - `patch`: Merge-patch JSON updates into the live runtime state.
  - `signals`: List recently generated signals with timestamps and prices.
  - `signal-stats`: Query real-time win rate, Profit Factor, Sharpe ratio, and net PnL.
  - `signal-close`: Manually close an open position.
- **Examples:**
  ```bash
  tools/state_control.py get --key active_strategy
  tools/state_control.py signal-stats
  ```

---

### `ui_dispatcher.py` & `telegram_broadcast.py`
Live visual telemetry and notification dispatches.
- **UI Dispatcher:** Broadcasts events to the Cockpit frontend via WebSocket:
  ```bash
  tools/ui_dispatcher.py --event UPSERT_WIDGET --payload '{"widget_id": "cynic_card", "payload": {"status": "PASSED"}}'
  ```
- **Telegram Broadcast:** Sends reports and alerts to subscribed Telegram channels:
  ```bash
  tools/telegram_broadcast.py broadcast --type update -m "New alpha strategy promoted to paper trading."
  ```

# Reference: Python Libraries & CLI Tool Contracts

## Overview
NujinSkill uses deterministic Python scripts to decouple strategy mining logic from framework orchestration.

---

## Tool Contracts & CLI Executables

### 1. Feature Extraction: `tools/feature_miner.py`
- **Library Stack:** `polars`, `numpy`
- **Command:** `python tools/feature_miner.py --input data/candles.csv --output data/features.csv`
- **Output:** Enhanced CSV with geometry, VSA volume Z-score, Parkinson volatility, and Hurst proxy.

### 2. Fast In-Sample Coarse Filter: `tools/vectorized_screener.py`
- **Library Stack:** `pandas`, `vectorbt`, `polars`
- **Command:** `python tools/vectorized_screener.py --data data/features.csv --rules '<JSON>' --fee-bps 5.0 --output data/returns.json`
- **Hurdles:** Net Sharpe $\ge 1.3$, Trades $\ge 100$, Profit Factor $\ge 1.4$, Expectancy $> 2\times$ fees.

### 3. Adversarial Audit Cynic: `tools/validation_cynic.py`
- **Library Stack:** `scipy.stats`, `numpy`
- **Command:** `python tools/validation_cynic.py --returns data/returns.json --trials 120`
- **Gates:** Deflated Sharpe Ratio (DSR $\ge 0.95$), Parameter Stability Surface, Monte Carlo trade reshuffling, OOS retention ($\ge 65\%$).

### 4. Production Strategy Emitter: `tools/strategy_emitter.py`
- **Command:** `python tools/strategy_emitter.py --thesis "..." --rules '<JSON>' --framework freqtrade --out strategies/MyStrategy.py`
- **Generates:** Production Freqtrade `IStrategy` script or Jesse strategy class.

### 5. Telemetry Dispatcher: `tools/ui_dispatcher.py`
- **Command:** `python tools/ui_dispatcher.py --event UPSERT_WIDGET --payload '<JSON>'`
- **Dispatches:** Telemetry events to local server HTTP broadcast endpoint and Telegram gateway.

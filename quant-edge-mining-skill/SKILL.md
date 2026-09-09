# Skill: Quant Edge Mining Engine

## Metadata
- **Name:** `NujinSkills`
- **Version:** `1.0.0`
- **Runtime:** Python 3.10+ & Node.js 18+
- **Execution:** Direct CLI execution via `python tools/<tool_name>.py [args]`

## Description
Autonomous quantitative alpha discovery engine and strategy execution package for OHLCV candlestick data. Generates non-consensus, out-of-the-box trading edges, stress-tests them with Deflated Sharpe Ratio (DSR) and parameter stability audits, emits production Freqtrade & Jesse strategies, dispatches dynamic telemetry to a dual-screen UI and 24/7 Telegram signal gateway, and manages paper/live execution bots.

---

## Operational Funnel & Execution Commands

Follow these 5 phases sequentially when executing an edge-mining cycle. Consult `references/` for theoretical principles.

### Service Setup & Telemetry Infrastructure
Before running mining pipelines, start the embedded telemetry server and UI dashboard:
```bash
# 1. Start FastAPI Telemetry Server & Telegram Signal Gateway
python tools/server_control.py start --port 8000

# 2. Build and Start Dual-Screen Frontend UI Dashboard
python tools/frontend_control.py start --port 3000
```

---

### Phase 1: Feature Extraction & Regime Scan
*References: `references/pricedataonly_edge_mining.md`, `references/simple_tools_ideas.md`*

Extract bar geometry, Volume-Spread Analysis (VSA) volume Z-scores, Parkinson volatility, rolling Hurst exponent, Anchored VWAP Z-scores, and fractional differentiation from In-Sample (IS: 60%) OHLCV candles:
```bash
python tools/feature_miner.py --input data/candles_15m.csv --output data/features.csv
```

---

### Phase 2: Out-of-the-Box Ideation
*References: `references/outofthebox_solutions_finding.md`, `references/edge.md`*

Synthesize entry/exit rules based on market regime and trapped counterparty capital:
1. **Consensus Mapping:** Identify retail herd setup (e.g., buying Bollinger Band breakouts).
2. **Failure Dissection:** Pinpoint microstructure conditions where that setup fails (absorption, liquidity sweep).
3. **Lateral Synthesis:** Formulate rule logic using custom features rather than standard thresholds.
   - Restrict degrees of freedom to $\le 3$.
   - Require regime filters (e.g., `hurst_proxy < 0.45`).

---

### Phase 3: Fast Vectorized Coarse Filter
*References: `references/process.md`, `references/libs_clis.md`*

Run vectorized backtest on In-Sample (IS) dataset with 5 bps taker fee and 2 bps slippage friction:
```bash
python tools/vectorized_screener.py \
  --data data/features.csv \
  --rules '{"entry_long": "close < lower_band and lower_wick > 0.55 and volume_zscore > 1.5", "exit": "bars >= 12"}' \
  --fee-bps 5.0 \
  --output data/candidate_returns.json
```

* **Rejection Hurdles:** Net Sharpe $< 1.3$, Trades $< 100$, Profit Factor $< 1.4$, Expectancy $\le 2\times$ fees.

---

### Phase 4: Adversarial Audit & Falsification
*References: `references/riskmanagement.md`, `references/statistic_edge.md`*

Audit surviving candidate strategy against overfitting and tail risk:
```bash
python tools/validation_cynic.py \
  --returns data/candidate_returns.json \
  --trials 140 \
  --param-grid '{"lower_wick": [0.45, 0.50, 0.55, 0.60], "volume_zscore": [1.2, 1.5, 1.8]}' \
  --oos-data data/features_oos.csv
```

* **Gate 1 (DSR):** Deflated Sharpe Ratio must be $\ge 0.95$ given cumulative trials.
* **Gate 2 (Stability):** Parameter surface matrix must show a smooth plateau, not an isolated cliff spike.
* **Gate 3 (Monte Carlo):** 99th percentile maximum drawdown $MDD_{99} \le 2.5 \times MDD_{\text{backtest}}$.
* **Gate 4 (OOS Walk-Forward):** $Sharpe_{OOS} \ge 0.65 \times Sharpe_{IS}$.

---

### Phase 5: Production Strategy Emission & Telemetry Dispatch
*References: `references/tradingbot.md`, `references/ui_management.md`, `references/signals_gateway.md`*

1. **Emit Freqtrade Production Strategy:**
```bash
python tools/strategy_emitter.py \
  --thesis "Fade Asian Liquidity Sweeps" \
  --rules data/final_rules.json \
  --framework freqtrade \
  --out user_data/strategies/TrapFade_v1.py
```

2. **Dispatch Dynamic UI Widgets & Chart Markers:**
```bash
python tools/ui_dispatcher.py --event UPSERT_WIDGET --payload '{
  "id": "dsr_score",
  "component": "MetricCard",
  "title": "Deflated Sharpe Ratio (DSR)",
  "props": {"value": "0.964", "target": "> 0.950", "status": "PASS", "subtitle": "Audited over 140 trials"}
}'

python tools/ui_dispatcher.py --event CHART_MARKER --payload '{
  "time": 1773295200,
  "action": "BUY",
  "price": 64250.0,
  "stop_loss": 63400.0,
  "take_profit": 65950.0,
  "annotation": "Absorption Sweep (Hurst < 0.42, Wick > 60%)"
}'
```

3. **Deploy Trading Bot Execution (Paper / Live):**
```bash
python tools/bot_control.py deploy --strategy TrapFade_v1 --mode dry-run
```

---

## CLI Tools Reference Table

| Tool Script | Responsibilities | Key Arguments |
| --- | --- | --- |
| `tools/feature_miner.py` | Bar geometry, VSA volume Z-score, Parkinson volatility, rolling Hurst proxy, AVWAP | `--input`, `--output`, `--window` |
| `tools/vectorized_screener.py` | Fast Vectorbt / Polars IS strategy coarse filter with taker fee friction | `--data`, `--rules`, `--fee-bps`, `--output` |
| `tools/validation_cynic.py` | DSR calculation, parameter stability surface grid, Monte Carlo, OOS audit | `--returns`, `--trials`, `--param-grid`, `--oos-data` |
| `tools/strategy_emitter.py` | Generates Freqtrade `IStrategy` or Jesse strategy Python code | `--thesis`, `--rules`, `--framework`, `--out` |
| `tools/ui_dispatcher.py` | Dispatches WebSocket widgets, chart markers, and Telegram alerts | `--event`, `--payload`, `--endpoint` |
| `tools/server_control.py` | CLI tool to start/stop FastAPI server & Telegram gateway | `start`, `stop`, `status`, `--port` |
| `tools/frontend_control.py` | CLI tool to build and serve the dual-screen React UI | `build`, `start`, `status`, `--port` |
| `tools/bot_control.py` | CLI tool to launch and manage Freqtrade/Jesse paper trading bot | `deploy`, `stop`, `status`, `--strategy`, `--mode` |

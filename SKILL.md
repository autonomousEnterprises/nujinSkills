# Skill: NujinSkills Quant Agent Engine

## Metadata
- **Name:** `NujinSkills`
- **Version:** `1.0.0`
- **Runtime:** Python 3.10+ & Node.js 18+
- **Execution:** Direct CLI tool calls via `python tools/<tool_name>.py [args]`

## Description
Autonomous quantitative alpha discovery engine, strategy builder, 24/7 Telegram signal chatbot, and dual-screen telemetry dashboard for OHLCV market data.

When a user prompts for a strategy (e.g., *"I need a prop firm strategy"*, *"Make me a BTC swing strategy"*, *"Make me a conservative strategy"*), the AI agent autonomously runs an **Unconstrained Out-of-the-Box Alpha Discovery Loop**. It is NOT limited to fixed templates or standard textbook indicators. Instead, it uses lateral dialectic reasoning to invent unique feature combinations, test them with vectorized backtesting, audit them with Deflated Sharpe Ratio (DSR $\ge 0.95$), and **relentlessly iterate until a genuinely profitable, statistically vetted strategy is discovered**.

---

## 💡 Creative Out-of-the-Box Reasoning & Persistence Contract

### 1. Unconstrained Feature & Rule Synthesis
The AI agent is encouraged to invent non-consensus strategy logic combining orthogonal metrics engineered by `tools/feature_miner.py`:
- **Bar Physics & Geometry:** `upper_wick`, `lower_wick`, `body_ratio`, `buying_pressure`, `selling_pressure`, `v_spread`.
- **Effort vs. Result (VSA):** `volume_zscore` (Volume Z-score relative to 20-period rolling average).
- **Volatility Regimes:** `parkinson_vol` (High/Low intra-bar dispersion) and ATR compression ratios.
- **Time Series Memory:** `hurst_proxy` ($H < 0.45$ anti-persistent chop vs. $H > 0.55$ persistent trend).
- **Fair Value Anchors:** `avwap_zscore` (Anchored VWAP standard deviation distance).

### 2. Relentless Persistence Loop Directive
> [!IMPORTANT]
> **Directive for AI Agent:** Never declare failure or stop after 1 or 2 backtest trials. If a candidate hypothesis fails `vectorized_screener.py` hurdles or `validation_cynic.py` DSR audits:
> 1. Log the failure cause (e.g., low trade count, negative expectancy, isolated cliff spike).
> 2. Blacklist the failed feature/threshold combination in working memory.
> 3. Formulate an alternative out-of-the-box hypothesis (mutating regime filters, altering counterparty trap triggers, or adjusting holding periods).
> 4. **Repeat the loop relentlessly until a profitable strategy meeting the user's profile and passing DSR $\ge 0.95$ is found.**

---

## 🎯 User Intent & Strategy Profile Mapping

| User Request | Target Strategy Profile | Mining & Risk Constraints |
| --- | --- | --- |
| *"I need a prop firm trading strategy"* | **Prop Firm Challenge** | **Strict Drawdown:** Max DD $\le 4.5\%$, Net Sharpe $\ge 1.8$, Win Rate $\ge 55\%$, DSR $\ge 0.96$, tight stop-loss. |
| *"Make me a btc market cycle swing trade strategy"* | **BTC Market Cycle Swing** | **Multi-Day Trend/Chop:** 15m/1h/4h timeframes, Hurst Exponent regime filter ($H > 0.55$ for trend, $H < 0.45$ for chop), trailing stop. |
| *"Make me a longterm conservative investment strategy"* | **Conservative Investment** | **Low Turnover & Preservation:** Max DD $\le 8.0\%$, Profit Factor $\ge 1.8$, Parkinson Volatility compression filters. |
| *"How can news be traded effectively"* | **News Volatility Expansion** | **Liquidity Sweep & Fade:** V-Spread spike absorption, post-news upper/lower wick rejection fades, short holding time. |

---

## 🔄 Autonomous Iterative Discovery & Execution Loop

```
                                [ USER PROMPT ]
       ("I need a prop firm strategy" / "Make me a BTC swing strategy")
                                       │
                                       ▼
                       ┌───────────────────────────────┐
                       │  1. Map Strategy Profile &    │
                       │     Set Target Constraints    │
                       └───────────────┬───────────────┘
                                       │
                                       ▼
                       ┌───────────────────────────────┐
                       │  2. Feature Extraction &      │
                       │     Regime Scan (Phase 1)     │
                       │     python tools/feature_...  │
                       └───────────────┬───────────────┘
                                       │
                                       ▼
                       ┌───────────────────────────────┐
                       │  3. Creative Dialectic        │
                       │     Out-of-the-Box Ideation   │
                       └───────────────┬───────────────┘
                                       │
                                       ▼
                       ┌───────────────────────────────┐
                       │  4. Fast Vectorized Screen    │
                       │     python tools/vectoriz...  │
                       └───────────────┬───────────────┘
                                       │
                         Pass Hurdles? │
                       ┌───────────────┴───────────────┐
                       │                               │
                     [ NO ]                         [ YES ]
                       │                               │
                       ▼                               ▼
     ┌─────────────────────────────────┐ ┌───────────────────────────┐
     │ Refine Rules / Blacklist Failed │ │ 5. Adversarial DSR Audit  │
     │ Setup & Loop Back to Step 3     │ │    python tools/valid...  │
     └─────────────────────────────────┘ └─────────────┬─────────────┘
                                                       │
                                          DSR >= 0.95? │
                                         ┌─────────────┴─────────────┐
                                         │                           │
                                       [ NO ]                     [ YES ]
                                         │                           │
                                         ▼                           ▼
                       ┌───────────────────────────────────┐ ┌───────────────────────────────┐
                       │ Adjust Parameters & Re-Audit      │ │ 6. Emit Code & Deploy Options │
                       │ Loop Back to Step 3               │ │    (User Chooses Deployment): │
                       └───────────────────────────────────┘ │    - Emit Freqtrade Strategy   │
                                                             │    - Launch Paper Trading Bot │
                                                             │    - Activate Telegram Alerts │
                                                             │    - Spin Up Web Dashboard    │
                                                             └───────────────────────────────┘
```

---

## 🛠️ Step-by-Step Execution Contract

### Step 1: Feature Extraction (Phase 1)
Extract bar geometry, VSA Volume Z-scores, Parkinson volatility, and rolling Hurst exponent proxy:
```bash
python tools/feature_miner.py --input data/candles_15m.csv --output data/features.csv
```

### Step 2: Out-of-the-Box Dialectic Ideation (Phase 2)
Consult `references/outofthebox_solutions_finding.md`:
1. **Consensus Mapping:** Identify retail herd setup (e.g., buying Bollinger Band breakouts).
2. **Failure Dissection:** Pinpoint microstructure conditions where that setup fails (absorption, liquidity sweep).
3. **Lateral Synthesis:** Formulate entry/exit rule logic combining custom engineered features.

### Step 3: Fast Vectorized Coarse Filter (Phase 3)
Screen logic against In-Sample data with 5 bps fee and 2 bps slippage friction:
```bash
python tools/vectorized_screener.py \
  --data data/features.csv \
  --rules '{"entry_long": "close < lower_band and lower_wick > 0.55 and volume_zscore > 1.5", "exit": "bars >= 12"}' \
  --fee-bps 5.0 \
  --output data/candidate_returns.json
```
* **Check Results:** If Sharpe $< 1.3$, Trades $< 100$, or Net Expectancy $\le 2\times$ fees, **do not stop**—autonomously iterate with a refined hypothesis.

### Step 4: Adversarial Audit & DSR Gate (Phase 4)
Audit surviving returns against overfitting:
```bash
python tools/validation_cynic.py \
  --returns data/candidate_returns.json \
  --trials 120 \
  --param-grid '{"lower_wick": [0.45, 0.50, 0.55, 0.60], "volume_zscore": [1.2, 1.5, 1.8]}'
```
* **Gate Check:** DSR must be $\ge 0.95$, parameter surface must form a stable plateau, and OOS retention must be $\ge 65\%$. If failed, iterate logic.

### Step 5: Optional Deployment Features (User Selected)
Once a strategy passes all falsification gates, activate user-selected deployment features:

1. **Emit Freqtrade Production Code:**
   ```bash
   python tools/strategy_emitter.py --thesis "<THESIS>" --rules data/final_rules.json --framework freqtrade --out user_data/strategies/MyStrategy.py
   ```

2. **Activate 24/7 Telegram Signal Chatbot (Optional):**
   ```bash
   python tools/server_control.py start --port 8000 --daemon
   python tools/ui_dispatcher.py --event SIGNAL_TRIGGERED --payload '<SIGNAL_JSON>'
   ```

3. **Launch Paper/Live Execution Bot (Optional):**
   ```bash
   python tools/bot_control.py deploy --strategy MyStrategy --mode dry-run
   ```

4. **Spin Up Dual-Screen Web Dashboard (Optional):**
   ```bash
   python tools/frontend_control.py start --port 3000 --daemon
   ```

---

## CLI Tools Summary

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

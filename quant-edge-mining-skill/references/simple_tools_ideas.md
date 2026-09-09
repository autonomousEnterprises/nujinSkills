For an AI edge-mining agent to produce non-consensus, statistically robust solutions, its toolset cannot just be a basic price API. It needs tools that allow it to **probe market microstructure, evaluate mathematical relationships, and rapidly stress-test hypotheses** against friction.

Organize the agent's toolset into four functional layers:

---

### 1. Microstructure & Order Flow Query Tools

Standard OHLCV feeds push the agent toward retail TA. Giving it tools that query liquidity dynamics and trade aggressor distribution opens up completely different hypothesis spaces.

* **`query_orderbook_depth(symbol, depth_levels=50)`**:
* Returns bid/ask depth distributions, slope of the book, and liquidity imbalance ratios.
* *Why it enables out-of-the-box ideas:* Lets the agent detect spoofing, liquidity absorption, and where large limit orders are defending levels.


* **`query_delta_and_cvd(symbol, timeframe, lookback)`**:
* Computes Cumulative Volume Delta, buy/sell taker volume ratios, and volume at price (Volume Profile / VPVR).
* *Why it enables out-of-the-box ideas:* Allows the agent to look for absorption—e.g., aggressive buyers slamming into a passive wall with zero price advancement.


* **`query_derivatives_state(symbol)`**:
* Pulls real-time funding rates, predicted funding, open interest (OI) changes, and liquidation cluster maps.
* *Why it enables out-of-the-box ideas:* Bridges spot/perp dislocations, letting the model spot crowded long/short squeezes and mechanical liquidations.



---

### 2. Mathematical & Statistical Exploration Tools

Rather than letting the LLM estimate correlations or distributions in text, give it deterministic analytical tools to inspect the mathematical properties of a dataset.

* **`compute_regime_metrics(series, lookback)`**:
* Calculates statistical distribution properties: Hurst Exponent (mean-reverting vs. trending vs. random walk), rolling Shannon entropy, realized volatility clustering, and skewness/kurtosis.
* *Use case:* The agent can use this as a pre-condition filter (e.g., "Only fire this mean-reversion rule if Hurst $< 0.45$").


* **`calculate_cross_feature_divergence(feature_a, feature_b, window)`**:
* Computes rolling z-score spreads, dynamic cointegration, or rank correlation (Spearman) between two disparate series (e.g., RSI velocity vs. CVD acceleration).


* **`orthogonalize_features(feature_list)`**:
* Runs PCA (Principal Component Analysis) or Gram-Schmidt orthogonalization to tell the agent whether a proposed combination of indicators is actually offering new information or just duplicating variance.



---

### 3. Rapid Execution & Backtest Sandboxing

The agent must be able to test its own hypotheses immediately, fail fast, and refine without human intervention.

* **`run_vectorized_backtest(logic_definition, params, friction_model)`**:
* Wraps an ultra-fast engine (such as `vectorbt` or Polars-based backtesters).
* Takes concise execution rules and applies realistic friction: taker fees, maker rebates, and slippage based on book depth.


* **`run_robustness_audit(strategy_id)`**:
* Automatically executes:
* **Deflated Sharpe Ratio (DSR):** Corrects for data snooping and multiple testing bias.
* **Walk-Forward In-Sample / Out-of-Sample (IS/OOS) split.**
* **Monte Carlo trade shuffling:** Shuffles trade sequences to test if returns were driven by a few lucky outliers.





---

### 4. Agent Architecture: Recommended Tool Definition (JSON Schema)

Expose tools using strict functional schemas that force the agent to categorize its logic.

```json
{
  "name": "mine_hybrid_microstructure_signal",
  "description": "Evaluates a non-linear combination of a classic indicator and an order-flow/structural metric to test for structural alpha.",
  "parameters": {
    "type": "object",
    "properties": {
      "asset": { "type": "string" },
      "regime_condition": {
        "type": "string",
        "description": "Statistical environment required (e.g., 'hurst < 0.45', 'oi_expansion_above_2sd')"
      },
      "classic_primitive": {
        "type": "object",
        "properties": {
          "name": { "type": "string", "enum": ["RSI", "BB_WIDTH", "ATR_RATIO", "STOCH"] },
          "transform": { "type": "string", "enum": ["raw", "velocity", "acceleration", "z_score"] }
        },
        "required": ["name", "transform"]
      },
      "order_flow_primitive": {
        "type": "object",
        "properties": {
          "metric": { "type": "string", "enum": ["cvd_divergence", "book_imbalance", "funding_skew", "liquidation_exhaustion"] },
          "threshold": { "type": "number" }
        },
        "required": ["metric", "threshold"]
      },
      "counterparty_thesis": {
        "type": "string",
        "description": "Brief explanation of who is trapped or forced to trade against this signal."
      }
    },
    "required": ["asset", "regime_condition", "classic_primitive", "order_flow_primitive", "counterparty_thesis"]
  }
}

```

---

### Recommended Tool Stack

| Layer | Recommended Library / Source | Agent Use |
| --- | --- | --- |
| **Backtesting Engine** | `vectorbt` or `numba` vectorized pipelines | Millisecond iteration cycles so the agent can test 50 variations in seconds. |
| **Statistical Analysis** | `scipy.stats`, `arch`, `statsmodels` | Autocorrelation, stationary checks, Hurst exponent, and cointegration. |
| **Order Flow / Tick Data** | `Tardis.dev`, local Parquet ticks, or exchange L2/L3 feeds | Level 2 order book snapshots, trade agressor delta, and liquidations. |
| **Standard Indicators** | `ta-lib` or `pandas-ta` | Computing baseline primitives before applying non-linear derivatives. |
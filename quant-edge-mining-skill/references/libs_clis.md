Even with only raw OHLCV candlestick data, an agent can extract non-consensus edges if its tools deconstruct the **geometry, physics, and statistical properties of candles** rather than relying solely on lagging indicator lines.

Candlestick data contains price action, liquidity discovery, intra-bar volatility, and relative volume. Below is the standard tool suite an edge-mining agent should have in a zero-third-party setup.

---

### 1. Bar Microstructure & Price-Volume Geometry Tools

These tools unpack what happened *inside* the OHLC boundaries and how volume interacted with price travel.

* **`calc_bar_geometry(ohlcv_df)`**
* Computes intra-candle components: upper/lower wick ratios, body-to-range ratio, and range-to-ATR ratio.
* *Why it finds edge:* Distinguishes pure price rejection (long wick, small body) from aggressive directional continuation (large body, zero wicks) without needing complex L2 order books.


* **`calc_volume_effort_vs_result(ohlcv_df, window=20)`**
* Evaluates Volume Spread Analysis (VSA) relationships: Volume Z-score divided by normalized True Range.
* *Why it finds edge:* High volume + narrow spread signals absorption/exhaustion (someone is capping price). Low volume + wide spread signals an artificial vacuum (liquidity void).


* **`detect_liquidity_sweeps_and_gaps(ohlcv_df, lookback=50)`**
* Identifies rolling swing highs/lows that price briefly breached and closed back inside (false breakouts/turtle soups), plus Fair Value Gaps (FVGs / 3-bar imbalances).
* *Why it finds edge:* Formalizes institutional trap setups and liquidity pools programmatically using standard OHLC math.



---

### 2. Time, Dispersion & Statistical Regime Tools

Markets cycle between mean-reverting chop and directional trend. Feeding the agent raw price without regime metrics leads to curve-fitting.

* **`calc_trend_roughness_and_regime(close_series, window=50)`**
* Computes the **Hurst Exponent** ($H < 0.5$ mean-reverting, $H > 0.5$ trending) or Fractal Dimension index over rolling windows.
* *Why it finds edge:* Prevents the agent from applying mean-reverting oscillator logic when the price series is exhibiting persistent memory/trend.


* **`calc_volatility_dispersion(ohlcv_df, window=20)`**
* Computes Parkinsons Volatility (which uses High/Low instead of Close/Close) or Yang-Zhang Volatility (handles overnight gaps and drift).
* *Why it finds edge:* Extreme compression in Yang-Zhang volatility reliably precedes asymmetric explosive breakouts, giving the agent a clean volatility-expansion trigger.


* **`calc_session_and_temporal_bias(ohlcv_df)`**
* Tags bars with cyclical metrics: day-of-week, hour-of-day, and elapsed bars since the daily high/low was set.
* *Why it finds edge:* Many edges in liquid markets are structural time-of-day phenomena (e.g., London open expansion, New York lunch chop, Asian range sweeps).



---

### 3. Indicator Transformation Tools

When the agent uses classic indicators, it must not treat them as static thresholds.

* **`compute_indicator_derivative(series, method='velocity' | 'acceleration' | 'zscore', window=20)`**
* Computes the 1st/2nd derivative or rolling z-score of an indicator (e.g., $\Delta \text{RSI} / \Delta t$ or Z-score of Bollinger Bandwidth).
* *Why it finds edge:* Catches momentum shifts well before standard overbought/oversold boundaries or moving average crossovers fire.


* **`detect_indicator_price_divergence(price_series, indicator_series, lookback=30)`**
* Scans local extrema to find regular and hidden divergences across any classic indicator against price.



---

### 4. Fast Vectorized Backtesting & Reality Check

To iterate autonomously, the agent needs an internal evaluation tool with built-in execution reality checks.

* **`run_vectorized_test(entry_rules, exit_rules, fee_bps=5.0, slippage_ticks=1)`**
* Executes a vectorized simulation (e.g., using `vectorbt` or pure NumPy arrays).
* *Mandatory output returned to the agent:*
* Expectancy per trade vs. fee drag (to immediately kill high-turnover noise).
* Profit Factor, Maximum Drawdown, and Win Rate.
* Trade count (rejecting ideas with $< 30$ samples).




* **`run_deflated_sharpe_test(strategy_returns, total_trials_attempted)`**
* Runs Bailey & López de Prado’s Deflated Sharpe Ratio calculation based on how many iterations the agent has run.
* *Why it finds edge:* Flags data snooping; if the agent tested 100 variations to get a Sharpe of 1.8, the tool penalizes the score to warn that the result is statistically likely to be random luck.



---

### Standard Tool Spec Overview

| Tool Name | Input Data | Output / What the Agent Learns |
| --- | --- | --- |
| `calc_bar_geometry` | OHLCV dataframe | Wick rejections, expansion body ratios, structural sweeps |
| `calc_volume_effort_vs_result` | OHLCV dataframe | Volume/spread divergence, absorption, liquidity exhaustion |
| `calc_trend_roughness_and_regime` | Price series | Hurst exponent, trend persistence vs. mean-reverting chop |
| `calc_volatility_dispersion` | OHLCV dataframe | Parkinson/Yang-Zhang volatility squeeze & expansion cycles |
| `compute_indicator_derivative` | Indicator series | Velocity, acceleration, and dynamic z-score of classic tools |
| `run_vectorized_test` | Logic + Costs | Net Sharpe, profit factor, fee drag, and drawdown profile |
| `run_deflated_sharpe_test` | Returns + Trials | Statistically discounted Sharpe to check for overfitting |
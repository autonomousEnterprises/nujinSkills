When limited strictly to exchange price data (OHLCV candles or tick-level price/volume), classic indicators fail because they treat price as an abstract curve.

To build an edge with pure price action, you must treat OHLCV not as a line graph, but as a **footprint of volume auction mechanics and volatility regimes**.

---

### 1. The Core Flaw in Off-the-Shelf Indicators

Standard indicators make mathematical assumptions that financial markets break constantly:

* **Non-Stationarity:** Markets alternate between low-variance mean-reverting states and high-variance directional trends. An RSI with a fixed lookback of 14 assumes the underlying distribution of price variance is constant—which is why it gets pinned at extremes during strong moves.
* **Information Loss from Equal-Time Sampling:** A 5-minute bar during market open might contain 20,000 transactions and huge capital turnover, while a 5-minute bar at 03:00 UTC might contain 40 transactions. Standard indicators weight both bars equally, blending high-signal institutional activity with overnight noise.
* **Redundant Linear Transformations:** MACD, Bollinger Bands, and Stochastics are all different combinations of moving averages and standard deviations. Stacking them together compounds lag without adding new information.

---

### 2. Custom Feature Engineering from Pure Price & Volume

Instead of relying on standard formulas, engineer custom mathematical features directly from the raw OHLCV bar geometry and volume distribution.

```
                  ┌────────────────────────┐
                  │ High                   │  Upper Shadow: Rejected Price Discovery
                  │                        │
       Open ──────┼────────────────────────┤
                  │                        │
                  │ Body (Spread)          │  Realized Advance: Net Buying / Selling
                  │                        │
      Close ──────┼────────────────────────┤
                  │                        │
                  │ Low                    │  Lower Shadow: Absorbed Selling Pressure
                  └────────────────────────┘

```

#### A. Fractionally Differentiated Prices (Preserving Memory & Stationarity)

* **The Problem:** Raw prices are non-stationary (they wander with trends), which causes machine learning algorithms to overfit. Taking standard integer differences (returns: $\Delta p = p_t - p_{t-1}$) achieves stationarity, but completely erases long-term historical memory.
* **Custom Metric:** Use **fractional differentiation** (e.g., $d \approx 0.35 - 0.45$). This yields a stationary time series that an algorithmic miner can train on without wiping out structural support and resistance memory.

#### B. Volume-Synchronized Volatility (Replacing Fixed-Period ATR)

* **Custom Metric:** Instead of rolling 14-period ATR, calculate range expansion weighted by volume participation:

$$\text{V-Spread}_t = \frac{\text{High}_t - \text{Low}_t}{\text{Volume}_t}$$


* **The Signal:** When $\text{V-Spread}$ is unusually low while volume is in the 90th percentile, large passive volume is absorbing the range. When $\text{V-Spread}$ spikes on dry volume, the book is thin, indicating potential exhaustion or false breakouts.

#### C. Microstructure Proxy: Tick Imbalance & Bar Geometry

Without Level 2 order books, bar wicks approximate the battle between aggressive takers and resting limits:


$$\text{Buying Pressure Proxy} = \frac{\text{Close} - \text{Low}}{\text{High} - \text{Low}}, \quad \text{Selling Pressure Proxy} = \frac{\text{High} - \text{Close}}{\text{High} - \text{Low}}$$

* **The Signal:** Measure the rolling velocity of wick rejection ratios at structural swing points. Consecutive large lower shadows accompanied by elevated volume reflect passive buyers soaking up market sells.

#### D. Anchored VWAP Dispersion (Fair Value Distance)

* **Custom Metric:** Calculate Volume-Weighted Average Price (VWAP) anchored to specific structural inflection points (e.g., weekly open, major swing high, or highest volume spike of the month) rather than an arbitrary rolling window.

$$\text{Z-VWAP}_t = \frac{\text{Price}_t - \text{AVWAP}_t}{\sigma_{\text{VWAP}}}$$


* **The Signal:** Price deviations beyond $2\sigma$ from Anchored VWAP tend to mean-revert during balanced regimes, while a break and retest of the anchored level confirms structural regime change.

---

### 3. Turning Price Data into Strategy Blueprints

| Category | Custom Feature Setup | Execution Logic |
| --- | --- | --- |
| **Volatility Compression Breakout** | Ratio of Short-Term ATR (5) to Long-Term ATR (50) drops below the 10th historical percentile. | **Entry:** Place bracket stop orders outside the multi-bar range. <br>

<br>**Logic:** Volatility clusters; prolonged compression mathematically precedes rapid expansion. |
| **Auction Range Rejection (Liquidity Sweeps)** | Price prints a new 20-bar high, but closes in the bottom 25% of the bar's range on volume $> 1.5\times$ average. | **Entry:** Fade the break (short). <br>

<br>**Stop:** Placed just above the wick. <br>

<br>**Logic:** Aggressive breakout buyers were completely absorbed by passive sellers, trapping breakout traders. |
| **Dynamic Mean Reversion** | Rolling Hurst Exponent ($H < 0.45$ indicating anti-persistence) + Anchored VWAP deviation $> 2\sigma$. | **Entry:** Mean reversion back to AVWAP. <br>

<br>**Condition:** Automatically disabled whenever the Hurst Exponent crosses $> 0.55$ (trending regime). |

---

### 4. Structuring Your Edge Miner Pipeline

To discover these patterns systematically without manual chart watching:

```
[ Raw OHLCV Data ]
        │
        ▼
[ Transform to Volume / Dollar Bars ]  (Removes dead-hours noise)
        │
        ▼
[ Compute Orthogonal Custom Features ]
   ├── Volatility Regime (Hurst Exponent or ATR Ratio)
   ├── Auction Geometry (Wick Rejection Ratio, V-Spread)
   └── Structural Anchors (Anchored VWAP Z-Score)
        │
        ▼
[ Rule-Induction Miner ]
   Finds conditional rules: IF Regime == MeanReverting AND Z-Score > 2.0 AND WickRatio > 0.75
        │
        ▼
[ Triple-Barrier Validation ] (ATR Take-Profit, ATR Stop-Loss, Max Holding Bars)

```

1. **Resample to Volume Bars:** Rebuild your dataset so each bar represents a constant unit of volume (e.g., every 5,000 contracts) rather than 5 minutes of time. This immediately normalizes volatility and makes statistical signals cleaner.
2. **Mine Asymmetric Confluences:** Don't search for a single magic indicator. Mine combinations where a **regime metric** (is the market currently trending or mean-reverting?) acts as a hard filter before testing a **structural rejection trigger**.
3. **Validate with Strict Walk-Forward Analysis:** Ensure any discovered rule set remains profitable across multiple non-overlapping market periods to confirm you aren't simply curve-fitting past volatility.

---
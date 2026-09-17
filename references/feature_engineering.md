# Reference: Feature Engineering, Information Domains & Alpha Half-Life

## 1. Overview: The 4 Open Information Domains

Standard technical indicators (simple moving averages, raw RSI, MACD) smooth historical prices over fixed rolling windows, introducing severe mathematical lag and collinearity. In **NujinAI**, features are not limited to pre-packaged retail indicators. Features can be drawn from **4 open, orthogonal information domains**:

```
┌────────────────────────────────────────────────────────────────────────┐
│                      THE 4 OPEN INFORMATION DOMAINS                     │
├────────────────────────────────────────────────────────────────────────┤
│ 1. SPATIAL & GEOMETRIC DOMAIN                                          │
│    • Swing highs/lows, break of structure (BOS/CHoCH), FVGs            │
│    • Wick rejection ratios, consolidation box boundaries, trendlines   │
├────────────────────────────────────────────────────────────────────────┤
│ 2. STATISTICAL & DISTRIBUTIONAL DOMAIN                                 │
│    • Lo-MacKinlay Variance Ratios, rolling Hurst exponent estimates    │
│    • Normalized Z-scores, empirical returns skewness & kurtosis        │
│    • Parkinson / Garman-Klass intra-bar volatility estimators          │
├────────────────────────────────────────────────────────────────────────┤
│ 3. AUCTION & MICROSTRUCTURE DOMAIN                                     │
│    • Volume-Spread Analysis (VSA), Volume Absorption (V_abs)           │
│    • Cumulative Volume Delta (CVD), order book bid/ask imbalances      │
│    • Session time-of-day killzones (London, NY Open, Asian range)     │
├────────────────────────────────────────────────────────────────────────┤
│ 4. EXTERNAL & ALTERNATIVE DOMAIN                                       │
│    • Intermarket lead-lag (e.g. US500 futures leading BTC; DXY / Gold)│
│    • Scheduled economic calendar prints (CPI, FOMC, NFP volatility)    │
│    • LLM sentiment scoring of real-time financial news feeds           │
└────────────────────────────────────────────────────────────────────────┘
```

### The Orthogonality Law: $\text{Feature}_A \perp \text{Feature}_B$
Stacking features from the same mathematical family (e.g. 14 RSI + 9 Stochastic + 12/26 MACD) increases parameters without adding new information. Every robust edge must combine **features from disjoint domains**.

All native features can be computed with `tools/feature_miner.py` and statistically verified with `tools/anomaly_scanner.py`.

---

## 2. Core Feature Formulations & Python Implementations

### A. Bar Geometry & Wick Physics
Measures the battle between buyers and sellers within individual candlestick bars:

```python
# Total bar height with epsilon protection against division by zero
total_range = (high - low).clip(1e-6, None)

# Bar body proportion relative to full range
body_ratio = (close - open).abs() / total_range

# Upper wick (selling pressure / absorption of buyers)
upper_wick = (high - np.maximum(close, open)) / total_range

# Lower wick (buying pressure / absorption of sellers)
lower_wick = (np.minimum(close, open) - low) / total_range

# Intra-bar auction dominance
buying_pressure = (close - low) / total_range
selling_pressure = (high - close) / total_range
```

**Interpretation:**
- `lower_wick > 0.45`: Aggressive market sell orders were fully absorbed by passive institutional bids; price rejected the lows.
- `upper_wick > 0.45`: Aggressive market buy orders were absorbed by passive institutional asks; price rejected the highs.
- `body_ratio > 0.75`: Strong momentum bar with minimal rejection wicks.

---

### B. Volume-Spread Analysis (VSA)
Relates volume participation (effort) to bar range expansion (result):

```python
# Volume Z-score relative to 20-bar baseline
vol_mean = volume.rolling(20).mean()
vol_std = volume.rolling(20).std().clip(1e-6, None)
volume_zscore = (volume - vol_mean) / vol_std

# Volume-weighted range expansion (V-Spread)
v_spread = (high - low) / (volume + 1e-6)
```

**Interpretation Matrix:**
- **High `volume_zscore` ($> 1.5$) + Low `v_spread`:** Passive limit absorption (institutional accumulation or distribution).
- **High `v_spread` + Low `volume_zscore` ($< 0.0$):** Liquidity vacuum (thin order book; high likelihood of false breakout).
- **High `volume_zscore` ($> 1.5$) + Elongated Wick (`lower_wick > 0.45`):** High-conviction liquidity sweep reversal.

---

### C. Parkinson High/Low Volatility Dispersion
Unlike standard deviation of closing prices, the Parkinson Volatility metric uses the high/low range to estimate continuous price variance with $5\times$ higher statistical efficiency:

$$\sigma_{\text{PV}} = \sqrt{\frac{1}{4 \ln 2} \cdot \ln\left(\frac{\text{High}}{\text{Low}}\right)^2}$$

```python
ratio = (high / low.clip(1e-6, None)).clip(1.0 + 1e-6, None)
parkinson_vol = np.sqrt((np.log(ratio) ** 2) / (4.0 * np.log(2.0)))
```

**Usage:** Detects volatility compression prior to directional expansion. When rolling Parkinson volatility reaches cyclical lows, prepare for breakout trend setups.

---

### D. Rolling Hurst Exponent Proxy (Variance Ratio)
Identifies the memory characteristics of the asset to prevent deploying mean-reversion strategies into strong secular trends:

$$\text{Hurst Proxy} \approx \frac{\text{Var}(r_{5t})}{5 \cdot \text{Var}(r_t)}$$

```python
ret1 = np.log(close / close.shift(1))
ret5 = np.log(close / close.shift(5))
hurst_proxy = (ret5.rolling(50).var() / (5.0 * ret1.rolling(50).var())).clip(0.1, 0.9)
```

**Regime Classification:**
- **$H < 0.45$ (Anti-Persistent / Mean-Reverting):** High-frequency chop. Ideal for wick rejection fades and range scalping.
- **$H \approx 0.50$ (Geometric Random Walk):** Unpredictable noise. Reduce risk exposure.
- **$H > 0.55$ (Persistent / Trending):** Directional autocorrelation. Disable mean-reversion fades; trade breakouts and pullbacks with trailing stops.

---

### E. Anchored VWAP Dispersion ($Z_{\text{VWAP}}$)
Measures the standard deviation distance of current price from volume-weighted fair value anchors:

```python
# Rolling 100-bar VWAP approximation
cum_vol = volume.rolling(100).sum()
cum_vol_price = (close * volume).rolling(100).sum()
avwap = cum_vol_price / cum_vol.clip(1e-6, None)
rolling_std = close.rolling(100).std().clip(1e-6, None)

avwap_zscore = (close - avwap) / rolling_std
```

**Usage:** When price reaches $|Z_{\text{VWAP}}| > 2.0$ in a mean-reverting regime ($H < 0.45$), high probability of snapback toward the VWAP anchor.

---

## 3. Order Book & Derivative Micro-Proxies

When derivative or order book feeds are available, Nujin incorporates these high-signal proxies:
1. **Funding Rate Imbalance:** Persistent high positive funding ($> 0.03\%$) coupled with stalling price signals crowded retail long leverage vulnerable to a long-liquidation cascade.
2. **Open Interest (OI) Divergence:** Price reaching a new high while OI declines indicates short covering rather than fresh spot accumulation.
3. **Liquidation Volume Spikes:** Forced liquidations trigger sharp wick rejections, marking temporary local price exhaustion.

---

## 4. Indicator Anti-Patterns (What NOT to Do)

1. **Avoid Collinear Indicator Stacking:** Never combine multiple indicators that measure the exact same derivative (e.g. RSI + Stochastics + MACD). They generate false confidence without adding new statistical dimensions.
2. **Avoid Naked Moving Average Crossovers:** MA crossovers are pure lag. In ranging regimes ($H < 0.45$), they buy tops and sell bottoms.
3. **Avoid Static RSI Overbought/Oversold Thresholds:** In a trending regime ($H > 0.55$), RSI can remain "overbought" ($> 70$) for hundreds of bars while price doubles.
4. **Enforce Parameter Parsimony:** Never combine more than 3 continuous numerical parameters in an entry expression to prevent catastrophic curve-fitting.

---

## 5. Custom Indicator Synthesis & Complementary Engineering

Nujin is not restricted to standard pre-packaged indicators. It synthesizes custom mathematical signals by combining auction physics across orthogonal domains:

### A. Volume Absorption Ratio ($V_{\text{abs}}$)
Identifies institutional limit absorption where high volume fails to expand price range:
```python
true_range = np.maximum(high - low, np.maximum((high - close.shift(1)).abs(), (low - close.shift(1)).abs()))
volume_absorption_ratio = (volume / (true_range + 1e-6)) / volume.rolling(50).mean()
```
- **High $V_{\text{abs}} > 2.5$ at support/resistance:** Institutions are absorbing all market orders; imminent sharp reversal.

### B. Dynamic Volatility Squeeze ($S_v$)
Ratios Bollinger Band width against Keltner Channel width to time explosive momentum expansions:
```python
bb_std = close.rolling(20).std()
bb_width = 4.0 * bb_std
atr20 = true_range.rolling(20).mean()
keltner_width = 3.0 * atr20
volatility_squeeze = bb_width / (keltner_width + 1e-6)
```
- **$S_v < 0.85$:** Extreme volatility compression (coiled spring). Breakout entry triggered when price breaches Donchian or EMA boundary.

### C. Liquidity Imbalance Ratio ($L_{\text{imb}}$)
Measures the directional asymmetry of rejection wicks relative to bar progress:
```python
candle_body = (close - open).abs()
wick_imbalance = (upper_wick - lower_wick) / (candle_body + 1e-6)
```
- **$L_{\text{imb}} > 2.0$:** Severe upper rejection; trapped breakout buyers. Ideal short entry trigger.
- **$L_{\text{imb}} < -2.0$:** Severe lower rejection; trapped breakdown sellers. Ideal long entry trigger.

### D. The 4-Pillar Orthogonal Strategy Recipe
When designing a strategy, select exactly ONE indicator from each pillar:
1. **Pillar 1 (Trend Baseline):** EMA Ribbon (13/34/50), Donchian Channel, or SuperTrend.
2. **Pillar 2 (Volatility Regime):** Parkinson Volatility, ATR Trailing Band, or Volatility Squeeze $S_v$.
3. **Pillar 3 (Momentum Speed):** ADX trend strength, RSI exhaustion, or Linear Regression Slope.
4. **Pillar 4 (Microstructure / Volume):** Volume Z-Score, Wick Imbalance $L_{\text{imb}}$, or Fair Value Gap.

---

## 6. Alpha Decay & Optimal Half-Life Horizon ($h^*$)

Every market inefficiency has an ephemeral shelf-life. An aggressive order flow imbalance or liquidity sweep does not produce edge indefinitely; its predictive power decays rapidly as the market digests the imbalance:

```
Predictive Alpha (t-statistic)
  ▲
  │       Peak Alpha (h*)
  │           ▲
  │          ╱ ╲
  │         ╱   ╲
  │        ╱     ╲
  │       ╱       ╲__________ Baseline Noise / Random Walk
  └──────┼────────┼───────────► Forward Holding Horizon (k bars)
         0        h*          24+
```

### Mathematical Formulation
For any entry signal event $E_t$, compute the forward cumulative return distribution across horizons $k \in \{1, 2, \dots, K\}$:
$$R_{t, k} = \frac{P_{t+k} - P_t}{P_t}$$
Compute the $t$-statistic against $H_0: \mu_k = 0$:
$$t_k = \frac{\bar{R}_k}{\sigma_k / \sqrt{N}}$$

### The Golden Rule of Exit Timing
$$\text{Max Hold Bars} \le h^* = \arg\max_k |t_k|$$
- If an agent sets `max_bars_held = 40` on a micro-scalp whose alpha decays at $k = 8$, **$80\%$ of the holding time is uncompensated exposure to market risk and fee drag**.
- `tools/anomaly_scanner.py` automatically evaluates the decay curve and sets the empirical half-life cutoff.


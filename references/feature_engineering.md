# Reference: Feature Engineering, Bar Physics & Auction Microstructure

## 1. Overview: Raw Auction Dynamics vs. Lagging Indicators

Standard technical analysis tools (simple moving averages, raw RSI, MACD) smooth historical prices over fixed rolling windows, introducing unavoidable mathematical lag. In contrast, **NujinAI** extracts orthogonal features directly from raw OHLCV price auction dynamics:
- **Intra-bar geometry:** Footprints of aggressive takers vs. passive limit absorption.
- **Volume participation (VSA):** Relative effort vs. observed price progress.
- **Time series memory & regimes:** Differentiating anti-persistent mean reversion from persistent trend expansion.
- **Dispersion anchors:** Distance from volume-weighted fair value levels.

All features are engineered by `tools/feature_miner.py` and output to `data/features.csv`.

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

1. **Avoid Naked Moving Average Crossovers:** MA crossovers are pure lag. In ranging regimes ($H < 0.45$), they buy tops and sell bottoms.
2. **Avoid Static RSI Overbought/Oversold Thresholds:** In a trending regime ($H > 0.55$), RSI can remain "overbought" ($> 70$) for hundreds of bars while price doubles.
3. **Enforce Parameter Parsimony:** Never combine more than 3 continuous numerical parameters in an entry expression to prevent catastrophic curve-fitting.

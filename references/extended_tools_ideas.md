# Reference: Advanced Mathematical Feature Extraction

## Overview
Standard indicators treat price as a continuous linear curve, losing critical information about volatility regimes and market memory. The AI agent engineers orthogonal features directly from raw OHLCV price auction mechanics.

---

## Key Features & Formulas

### 1. Rolling Hurst Exponent Proxy (Variance Ratio)
Measures time series memory and regime persistence:
- $H < 0.45$: Anti-persistent (mean-reverting chop).
- $H > 0.55$: Persistent (trending expansion).

```python
ret1 = np.log(close / close.shift(1))
ret5 = np.log(close / close.shift(5))
hurst_proxy = (ret5.rolling(50).var() / (5.0 * ret1.rolling(50).var())).clip(0.1, 0.9)
```

### 2. Parkinson Volatility (Intra-Bar High/Low Dispersion)
Superior to closing-price standard deviation because it incorporates intra-bar price range:
$$\sigma_{PV} = \sqrt{\frac{1}{4 \ln 2} \ln\left(\frac{\text{High}}{\text{Low}}\right)^2}$$

### 3. Volume-Synchronized Volatility (V-Spread)
Weighted range expansion by volume participation:
$$\text{V-Spread}_t = \frac{\text{High}_t - \text{Low}_t}{\text{Volume}_t + 1e-6}$$
- **Low V-Spread + High Volume Z-score:** Passive limit absorption (range accumulation).
- **High V-Spread + Low Volume:** Thin order book (liquidity vacuum / false breakout).

### 4. Anchored VWAP Z-Score Proxy
Measures price dispersion from volume-weighted anchor levels:
$$\text{Z-VWAP}_t = \frac{\text{Price}_t - \text{AVWAP}_t}{\sigma_{\text{Rolling}}}$$

### 5. Fractional Differentiation
Preserves long-term structural memory while transforming non-stationary price series into stationary inputs ($d \approx 0.35 - 0.45$).

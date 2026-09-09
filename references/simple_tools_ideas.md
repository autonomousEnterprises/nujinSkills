# Reference: Simple Geometric & VSA Feature Extraction Ideas

## Overview
Simple tools compute deterministic bar geometry and volume metrics directly from raw OHLCV inputs without heavy third-party dependencies.

---

## Feature Formulas & Implementations

### 1. Bar Body & Wick Ratios
```python
total_range = (high - low).clip(1e-6, None)
body_ratio = (close - open).abs() / total_range
upper_wick = (high - np.maximum(close, open)) / total_range
lower_wick = (np.minimum(close, open) - low) / total_range
```

### 2. Buying vs. Selling Pressure Proxies
```python
buying_pressure = (close - low) / total_range
selling_pressure = (high - close) / total_range
```

### 3. Volume Z-Score (Effort vs. Result)
```python
vol_mean = volume.rolling(20).mean()
vol_std = volume.rolling(20).std().clip(1e-6, None)
volume_zscore = (volume - vol_mean) / vol_std
```

### 4. Interpretation Matrix
- **`lower_wick > 0.55` and `volume_zscore > 1.5`:** Aggressive selling was absorbed by passive limit bids (Bullish Reversal / Liquidity Sweep).
- **`upper_wick > 0.55` and `volume_zscore > 1.5`:** Aggressive buying was absorbed by passive limit asks (Bearish Reversal / Liquidity Sweep).

# Reference: Price-Data-Only Edge Mining

## Overview
When mining edges strictly from OHLCV candlestick data without order book feeds, treat OHLCV bars as footprints of volume auction mechanics and volatility dispersion rather than simple price lines.

---

## Microstructure Proxies from Raw OHLCV

### 1. Wick Rejection & Absorption Ratios
Bar wicks approximate the battle between aggressive takers and passive limits:
$$\text{Lower Wick Ratio} = \frac{\min(\text{Close}, \text{Open}) - \text{Low}}{\text{High} - \text{Low}}$$
$$\text{Upper Wick Ratio} = \frac{\text{High} - \max(\text{Close}, \text{Open})}{\text{High} - \text{Low}}$$

- **Signal:** Large lower wick ($> 55\%$) on elevated Volume Z-score ($> 1.5$) reflects aggressive market sellers absorbed by passive limit buyers.

### 2. Volume-Spread Analysis (VSA)
- **High Volume + Small Bar Body:** Passive absorption (accumulation / distribution).
- **Low Volume + Large Bar Body:** Lack of participation (liquidity vacuum / potential false break).

### 3. Volatility Compression Preceding Expansion
- Ratio of Short-Term ATR (5) to Long-Term ATR (50) falling below 10th percentile indicates energy buildup prior to expansion.

# Reference: Principles for Non-Consensus Indicator Usage

## Overview
Off-the-shelf indicators (RSI 14, MACD 12/26/9, Bollinger Bands 20/2) fail when used in standard textbook fashion because they assume stationary market distributions and introduce compounding lag.

---

## Guidelines for AI Agent Strategy Formulation

### 1. Avoid Indicator Stacking
Do not combine MACD, RSI, and Stochastics simultaneously. They are all linear combinations of moving averages and momentum; stacking them compounds lag without adding orthogonal information.

### 2. Use Indicator Derivatives & Geometry
Instead of testing `RSI < 30`, evaluate:
- **Wick Rejection Ratio:** Ratio of upper/lower wick to total bar range.
- **Volume Z-Score:** Standard deviation units of current volume relative to 20-period rolling average.
- **Regime Filters:** Conditionally enable mean-reversion rules only when `hurst_proxy < 0.45`.

### 3. Normalize Thresholds by Volatility
Scale fixed thresholds by ATR or Parkinson volatility so parameters adapt automatically to changing market regimes.

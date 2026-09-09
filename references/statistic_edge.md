# Reference: Statistical Edge Validation & Sample Size Rejection

## Overview
Statistical validation ensures strategy performance is not the result of random chance or data dredging.

---

## Statistical Rejection Hurdles

1. **Minimum Trade Count ($N \ge 100$):** Rejects statistical noise and small sample sizes.
2. **Net Sharpe Ratio ($\ge 1.3$):** Measured across In-Sample (60%) dataset including taker fee & slippage.
3. **Profit Factor ($\ge 1.4$):** Gross profit divided by gross loss.
4. **Trade Expectancy ($E > 2\times \text{Fees}$):** Average trade return in basis points must exceed double total transaction costs.

---

## Deflated Sharpe Ratio (DSR) Formula

$$DSR = \Phi \left( \frac{(\hat{SR} - SR_0)\sqrt{T-1}}{\sqrt{1 - \hat{\gamma}_3 \hat{SR} + \frac{\hat{\gamma}_4 - 1}{4}\hat{SR}^2}} \right)$$

- $\hat{SR}$: Observed annualized Sharpe Ratio.
- $SR_0$: Expected maximum Sharpe Ratio under pure chance across $N$ trials.
- $\hat{\gamma}_3$: Skewness of returns.
- $\hat{\gamma}_4$: Kurtosis of returns.
- **Threshold:** DSR $\ge 0.95$ (95% confidence of genuine skill).

# Reference: Quantitative Risk Management & Invalidation Rules

## Overview
Proper risk management separates profitable strategies from account blowups. Every strategy emitted by NujinSkill must enforce hard invalidation stop-losses, profit targets, and trailing stop rules.

---

## 1. Core Risk Principles

### A. Dynamic ATR Stop-Loss
Position stop-loss levels based on market volatility rather than fixed percentage distances:
$$\text{Stop Distance} = \text{Entry Price} \pm (\text{ATR}_{14} \times \text{Multiplier})$$
- Default multiplier: $1.5 \times \text{ATR}_{14}$.

### B. Fixed holding Period Timeout
If price does not reach target or stop within a maximum bar window (e.g., 12 bars on 15m timeframe), exit at market to free up capital and avoid extended chop risk.

### C. Trailing Stop Loss
- Enable trailing stops only after price moves into profit by $+1.0\%$.
- Trailing offset: $1.5\%$ behind peak price.

---

## 2. Falsification Gates for Overfitting

1. **Deflated Sharpe Ratio (DSR):** Penalizes observed Sharpe for multiple testing ($N$ trials). Requires DSR $\ge 0.95$.
2. **Parameter Stability Surface:** Evaluates neighbor cells ($\pm 10\%, \pm 20\%$). Rejects isolated cliff spikes.
3. **Monte Carlo Reshuffling:** Measures 99th percentile maximum drawdown ($MDD_{99}$). Requires $MDD_{99} \le 2.5\times MDD_{\text{backtest}}$.

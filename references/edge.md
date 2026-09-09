# Reference: Quantitative Edge & Counterparty Inefficiency

## Overview
A quantitative trading edge is a statistical expectation of positive net returns after deducting all transaction costs, taker fees, and execution slippage. In modern markets, sustainable edges do not come from standard technical analysis indicators; they derive from structural market mechanics and counterparty capital trapping.

---

## 1. Pillars of Genuine Alpha

### A. Non-Consensus Market Mechanics
Retail momentum setups (such as buying simple moving average crosses or Bollinger Band breakouts) are heavily crowded. Institutional passive limit orders frequently absorb aggressive retail takers at key session highs and lows, causing immediate mean reversion.

### B. Microstructure Liquidity Sweeps
When price breaks above a well-defined swing high, breakout traders buy with market orders while resting stop-losses of short sellers get triggered. If large passive participants absorb this liquidity without price expanding further, price reverses aggressively—trapping the breakout capital.

### C. Regime-Dependent Dynamics
Markets shift between mean-reverting (anti-persistent) chop and trending (persistent) expansion. Strategies must include explicit regime filters (e.g., rolling Hurst Exponent proxy $H < 0.45$) to ensure mean-reversion trades are disabled during trending regimes.

---

## 2. Edge Mining Rules for the AI Agent

1. **Restrict Degrees of Freedom:** Maximum of 3 numerical parameters per strategy to prevent curve-fitting.
2. **Combine Orthogonal Features:** Pair a **regime metric** (Hurst, Parkinson Volatility) with a **bar geometry trigger** (Wick ratio, VSA Volume Z-score).
3. **Target Trapped Counterparties:** Define explicitly who is on the opposite side of the trade and why their position is mathematically forced into invalidation.

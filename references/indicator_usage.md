# Reference: Quantitative Strategy Formulation & Feature Engineering

## 1. System Design Rules: Orthogonality & Anti-Collinearity

Every feature ingested by an automated trading engine must provide an independent source of informational entropy. Stacking correlated indicators compounds lag and guarantees overfitted noise.

* **Max 1 Feature per Informational Category:** Never combine metrics from the same family within a single sub-system.
* **Trend / Vector:** SMA, EMA, KAMA, Supertrend.
* **Momentum / Velocity:** RSI, MACD, Stochastic, ROC, CCI.
* **Volatility / Dispersion:** ATR, Bollinger Bands, Keltner, Historical Volatility.
* **Liquidity / Participation:** VWAP, CVD, OBV, Volume Profile, Order Book Imbalance.


* **The Complementary Baseline Triad:** Valid multi-factor alphas must span 3 distinct axes:

$$\text{Valid Alpha} = \text{Structural Baseline} \times \text{Dispersion / Regime Filter} \times \text{Microstructure / Trigger}$$


* *Example:* Anchored VWAP (Structure) + Parkinson Volatility (Regime) + CVD Absorption (Microstructure).


* **Correlation Ceiling:** Run rolling correlation checks on all inputs:

$$\vert{}\rho(\text{Feature}_A, \text{Feature}_B)\vert{} < 0.55$$



Drop any feature exceeding this threshold during training or walk-forward windows.

---

## 2. Standard Industry Archetypes (Reference Only)

Use standard setups only as modular baselines before engineering non-consensus edges:

* **Volatility Squeeze (Expansion):**
* *Setup:* Bollinger Bands contract inside Keltner Channels.
* *Directional Bias:* Linear regression slope of momentum $> 0$ or session VWAP polarity.


* **Dynamic Mean Reversion (Fair Value Drift):**
* *Setup:* Anchor to session VWAP with $\pm 2.0\sigma$ to $\pm 3.0\sigma$ bands.
* *Trigger:* Extreme deviation fading into local volume absorption.


* **Multi-Timeframe Trend Capture (Regime Alignment):**
* *Setup:* Higher timeframe (HTF) directional bias (e.g., 200 SMA / 50 EMA).
* *Trigger:* Lower timeframe (LTF) pullback into dynamic equilibrium (e.g., 21 EMA or Anchored VWAP from prior swing).



---

## 3. Engineering Non-Consensus Features

Standard indicator signals are crowded and subject to severe alpha decay. Strip textbook indicators into raw mathematical derivatives or replace them with microstructure-aware features.

### A. Intracandle & Bar Geometry (Replaces Static Overbought/Oversold)

Discard binary thresholds like `RSI < 30`. Compute physical auction dynamics directly:

* **Wick Rejection Ratio:**

$$\text{Wick Rejection}_{\text{Lower}} = \frac{\min(\text{Open}, \text{Close}) - \text{Low}}{\text{High} - \text{Low} + \epsilon}$$



*Trigger:* Value $> 0.65$ at structural inflection signals aggressive passive limit absorption.
* **Candle Efficiency:**

$$\text{Efficiency}_{\text{Bar}} = \frac{\vert{}\text{Close} - \text{Open}\vert{}}{\text{High} - \text{Low} + \epsilon}$$



Differentiates strong directional displacement from high-churn indecision.

### B. Adaptive Lookbacks (Replaces Fixed Windows)

Never use fixed lookback lengths ($N=14, 20, 50$). Dynamically scale lookbacks using Kaufman’s Efficiency Ratio (ER):

$$\text{ER}_t = \frac{\vert{}\text{Price}_t - \text{Price}_{t-N}\vert{}}{\sum_{i=0}^{N-1} \vert{}\text{Price}_{t-i} - \text{Price}_{t-i-1}\vert{}}$$

* **Trend Expansion ($\text{ER} \to 1$):** Shorten lookbacks (e.g., $N \to 5$) to track breakout momentum closely without lag.
* **Noisy Consolidation ($\text{ER} \to 0$):** Widen lookbacks (e.g., $N \to 60$) or deactivate directional execution entirely.

### C. Synthetic MWAP (When Centralized Volume Is Absent/Unreliable)

On decentralized perps, FX, or fragmented feeds, substitute traded volume with price velocity to build a Momentum-Weighted Average Price:

$$\text{MWAP}_t = \frac{\sum_{i=1}^{k} \left( \text{TypicalPrice}_i \times \text{Weight}_i \right)}{\sum_{i=1}^{k} \text{Weight}_i}$$

* $\text{Weight}_i = \text{True Range}_i \times \vert{}\text{ROC}_i\vert{}$.
* Filters out low-velocity chop; anchors equilibrium strictly to bars with rapid directional displacement.

### D. Volatility Normalization via Z-Scores

Never feed unscaled, dimensional metrics into an execution engine. Standardize all indicator derivatives:

$$Z_t = \frac{\text{Feature}_t - \mu_{N}(\text{Feature})}{\sigma_{N}(\text{Feature})}$$

Define trigger boundaries in standard deviations (e.g., $\vert{}Z\vert{} \ge 2.0$) so signals dynamically scale to macro volatility expansions and contractions.

---

## 4. Agent Validation & Execution Constraints

Before promoting an engineered strategy to paper trading or live deployment, ensure it passes these mechanical constraints:

1. **Phase Lag Budget:** Total execution confirmation logic must not exceed 2 bars after a market structure break.
2. **Hard Regime Gates:** Deactivate all mean-reversion sub-routines unless a trend-efficiency gate confirms a non-trending state ($\text{ADX} < 20$ or $\text{ER} < 0.30$).
3. **Execution Friction Reality:** Model fills using conservative taker fees and an adverse selection slippage buffer. High-turnover indicator signals must achieve an edge that survives exchange fee tiers $\ge 0.05\%$ per side.
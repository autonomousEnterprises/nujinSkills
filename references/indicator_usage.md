# Reference: Principles for Quantitative Indicator Synergy, Orthogonality & Edge Mining

## Overview

Off-the-shelf indicators (RSI 14, MACD 12/26/9, Bollinger Bands 20/2) fail when applied in textbook fashion because they assume stationary price distributions, introduce compounding phase lag, and lack statistical orthogonality.

For an autonomous quantitative strategy engine, an indicator is not a trigger; it is a **lossy dimensionality reduction function** that compresses non-stationary time-series data into scalar features. Every indicator in a system must provide an independent source of informational entropy.

---

## 1. Indicator Taxonomy & Orthogonal Complementarity Matrix

To avoid redundant multi-collinearity, indicators must be grouped into distinct mathematical categories. Combining indicators within the same family compounds phase distortion and curves over-fitting. Valid systems pair indicators across orthogonal domains.

### Core Mathematical Categories

| Category | Primary Metric | Common Implementations | Underlying Signal Bias |
| --- | --- | --- | --- |
| **Trend / Drift** | Low-frequency price vector | SMA, EMA, KAMA, HMA, Supertrend | Tracks directional displacement; vulnerable to whipsaws |
| **Momentum / Velocity** | 1st/2nd derivative of price | RSI, MACD, Stochastic, ROC, CCI | Measures speed of change; susceptible to mean-reversion saturation |
| **Volatility / Dispersion** | Variance / True Range | ATR, Bollinger Bands, Keltner, Historical Volatility | Measures regime expansion/compression; non-directional |
| **Volume / Liquidity** | Participation density | OBV, VWAP, CVD, Volume Profile, Chaikin Money Flow | Tracks capital commitment; filters low-liquidity drift |
| **Market Microstructure** | Order book & aggressor flow | Order Book Imbalance (OBI), Delta divergence, Liquidation pools | Captures real-time auction mechanics and passive limit absorption |

---

### Indicator Synergy & Conflict Reference

```
[ Trend / Baseline ]  <==== Orthogonal ====>  [ Volatility Regime ]
          ▲                                            ▲
          │                 COMPLEMENTARY              │
          ▼                    TRIAD                   ▼
[ Microstructure / CVD ] <=================> [ Dynamic Momentum / ROC ]

```

* **Fully Complementary Combinations (Orthogonal Information):**
* `Anchored VWAP + Historical Volatility Bands + Cumulative Volume Delta (CVD)`: Price baseline + structural dispersion limits + order flow absorption.
* `Kaufman Adaptive Moving Average (KAMA) + Parkinson Volatility + Order Book Imbalance`: Noise-filtered trend + clean regime bounds + execution pressure.
* `Donchian Channels + Volume Z-Score + Hurst Exponent`: Trend breakout tracking + liquidity confirmation + statistical regime filtering.


* **Correlated / Redundant Stacks (Banned):**
* `RSI + Stochastic + MACD`: Pure momentum redundancy. All measure velocity over recent windows; stacking guarantees lagging multi-collinearity.
* `SMA + EMA + WMA`: Stacking multiple moving averages without functional differentiation produces delayed curve-fitting.
* `Bollinger Bands + Keltner Channels + ATR Bands`: All capture dispersion; choose one volatility proxy and optimize the lookback adaptively.



---

## 2. Industry-Standard Strategy Archetypes & Implementations

### Archetype A: Volatility Compression & Breakout (Squeeze)

* **Underlying Logic:** Markets rotate between high and low volatility regimes. Prolonged compression signals impending non-directional energy release.
* **Orthogonal Components:**
* *Volatility Filter:* Bollinger Bands inside Keltner Channels (John Carter Squeeze).
* *Momentum Confirmation:* Linear Regression Slope of Momentum (or ROC).
* *Execution Anchor:* Volume-Weighted Average Price (VWAP) as directional polarity bias.


* **Standard Parameterization:**
* BB: Length 20, Mult 2.0.
* KC: Length 20, ATR Mult 1.5.
* Trigger: Enter long when BB expands outside KC AND Regression Slope $> 0$ AND Price $>$ Session VWAP.



### Archetype B: Intraday VWAP Mean Reversion (Statistical Arbitrage)

* **Underlying Logic:** High-frequency capital deployment centers around institutional volume-weighted cost bases. Extreme deviations revert unless met with order flow continuation.
* **Orthogonal Components:**
* *Central Tendency:* Session VWAP (or Anchored VWAP from daily open/session turnover).
* *Dispersion Bands:* $\pm 2.0$ and $\pm 3.0$ standard deviation bands.
* *Microstructure Trigger:* CVD absorption or aggressive limit order absorption at extremes.


* **Standard Parameterization:**
* Enter short when `Price > VWAP + 2.5σ` AND `Delta (CVD) makes a lower high` (exhaustion/absorption) AND `M1/M5 bar shows upper wick rejection > 50%`.



### Archetype C: Multi-Timeframe Trend Following (Macro Filter + Micro Pullback)

* **Underlying Logic:** Align lower-timeframe execution with higher-timeframe capital drift.
* **Orthogonal Components:**
* *Regime Filter (HTF):* 200 SMA or 50 EMA on 1D/4H chart.
* *Oscillator (LTF):* 14-period RSI or Stochastic normalized against ATR.
* *Trigger:* Pullback into structural support (Dynamic EMA 21 or Anchored VWAP from prior swing).



---

## 3. When to Break Consensus: Asymmetric & Custom Indicator Engineering

Textbook indicator combinations are heavily crowded. Alpha decays when thousands of automated systems compute the exact same mathematical outputs. Autonomous strategy formulation must construct custom features that capture mechanics rather than chart patterns.

### Transition Triggers: Off-the-Shelf vs. Engineered Indicators

| Market Condition | Textbook Metric (Fails) | Engineered Alternative (Captures Edge) |
| --- | --- | --- |
| **Flash Liquidity Sweeps** | RSI Oversold (`< 30`) | **Wick Rejection Ratio + Delta Absorption** |
| **Volatile Chop / Range** | Moving Average Crossovers | **Efficiency Ratio (ER) + Hurst Exponent Thresholding** |
| **High-Impact News / Releases** | Standard Daily VWAP | **Event-Anchored Momentum-Weighted Average (MWAP)** |
| **Thin Order Books / Spreads** | Static Bollinger Bands | **Parkinson Volatility or Garman-Klass Volatility Bands** |

---

## 4. Engineering Custom Non-Consensus Features: Step-by-Step

### Step 1: Replace Raw Price Inputs with Microstructure-Aware Inputs

Standard closes discard intraday/intra-candle mechanical auctions.

* **Bar Anatomy Metrics:**

$$\text{Wick Rejection Ratio}_{\text{Lower}} = \frac{\min(\text{Open}, \text{Close}) - \text{Low}}{\text{High} - \text{Low} + \epsilon}$$



A ratio $> 0.60$ at an intraday support level indicates passive buy-side absorption regardless of what the standard RSI displays.
* **Weighted Energy Price:**

$$\text{Energy Price} = \frac{\text{Close} \times \text{Volume} + \frac{\text{High} + \text{Low}}{2} \times \text{Traded Contracts}}{\text{Total Volume}}$$



### Step 2: Transform Static Windows into Adaptive Dynamic Engines

Replace fixed lookback lengths ($N = 14, 20, 50$) with dynamic market speed inputs:

* **Kaufman Efficiency Ratio (ER) Scaling:**

$$\text{ER}_t = \frac{\vert{}\text{Price}_t - \text{Price}_{t-N}\vert{}}{\sum_{i=0}^{N-1} \vert{}\text{Price}_{t-i} - \text{Price}_{t-i-1}\vert{}}$$


* When $\text{ER} \to 1$: Trend is smooth and efficient. Automatically collapse lookbacks to short lengths (e.g., $N=5$) to hug breakout momentum.
* When $\text{ER} \to 0$: Market is random noise/chop. Expand lookback lengths ($N \to 60$) or freeze trend signals completely.



### Step 3: Implement Momentum-Weighted Average Price (MWAP)

Where centralized volume data is unreliable, noisy, or absent (FX, fragmented decentralized perpetual swaps), reconstruct structural baselines using price velocity:


$$\text{MWAP}_t = \frac{\sum_{i=1}^{k} \left( \text{TypicalPrice}_i \times \text{Weight}_i \right)}{\sum_{i=1}^{k} \text{Weight}_i}$$


Where $\text{Weight}_i = \text{True Range}_i \times \vert{}\text{ROC}_i\vert{}$. This anchors baseline valuation strictly to high-displacement momentum bars while ignoring drift and sideways churn.

### Step 4: Normalization via Volatility Z-Scores

Never feed raw indicator deltas into decision engines. Standardize features into dimensionless variance units:


$$Z_{\Delta \text{Indicator}} = \frac{\Delta \text{Indicator}_t - \mu_{N}}{\sigma_{N}}$$


Define trade execution conditions only when $\vert{}Z\vert{} \ge 2.0$, ensuring signals adapt seamlessly across shifts in baseline market volatility.

---

## 5. System Optimization & Validation Checklist for Agents

1. **Orthogonality Check:** Ensure Pearson correlation matrix across all active features satisfies $\vert{}\rho(F_i, F_j)\vert{} < 0.60$ across rolling 90-day samples.
2. **Phase Lag Minimization:** Reject any indicator combination whose combined signal confirmation requires more than 3 trailing candles after physical structure break.
3. **Regime Gating:** Mean-reversion indicators must be hard-disabled unless a market-wide trend efficiency metric verifies non-trending conditions ($\text{Hurst} < 0.45$ or $\text{ADX} < 20$).
4. **Execution Feasibility:** Factor in slippage, fee tiers, and fill ratios. High-frequency indicator crossovers fail entirely once exchange fees exceed 0.05% of trade notional value.
# Quant Protocol — Generic Edge Mining & Strategy Synthesis Engine

This document outlines the standard, domain-agnostic protocol for quantitative research, edge discovery, iterative optimization, and strategy code generation.

---

## 🏛️ The 4-Stage Quant Methodology

```
┌────────────────────────────────────────────────────────────────────────┐
│ STAGE 1: EMPIRICAL DISCOVERY & ANOMALY SCANNING                       │
│   • Analyze raw inputs (OHLCV, orderbook, funding rates, macro, etc.)   │
│   • Calculate variance ratios, autocorrelation, Hurst exponents, drift │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ STAGE 2: HYPOTHESIS & ITERATIVE EXPRESSION SEARCH LOOP                │
│   • Define binary targets (Sharpe, MaxDD, DSR >= 0.95, WinRate)        │
│   • Mutate candidate rules & expression trees autonomously             │
│   • Track history in `.nujin/state.json` and `.nujin/results.jsonl`   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ STAGE 3: CYNIC AUDIT & STRESS TESTING                                 │
│   • 5-Gate Cynic Audit: Friction, Noise, Regimes, Parameter Stability  │
│   • Calculate Deflated Sharpe Ratio (DSR) & Combinatorial Purged CV   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ STAGE 4: CODE EMISSION & DEPLOYMENT                                   │
│   • Generate clean, production-ready standalone Python strategy class   │
│   • Register in StrategyManager and stream telemetry to Cockpit        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 🔬 Stage 1: Empirical Anomaly Discovery

Before building any strategy, inspect the underlying empirical distribution of the target asset class/timeframe without forcing pre-baked indicator assumptions.

1. **Statistical Characterization:**
   - **Lo-MacKinlay Variance Ratio Test:** Determines if price returns exhibit mean-reversion ($VR < 1$), random walk ($VR \approx 1$), or momentum ($VR > 1$).
   - **Hurst Exponent ($H$):** Measure of long-memory persistence ($H > 0.5 \Rightarrow$ trending, $H < 0.5 \Rightarrow$ mean-reverting).
   - **Conditional Forward Return Matrix:** $P(R_{t+k} \mid X_t)$, evaluating return expectations given feature states.
   - **Alpha Half-Life Decay:** Estimating expected signal decay duration to set proper holding period bounds.

2. **Generic Feature Space:**
   Features can be synthesized dynamically from raw series:
   - **Normalized Return Shocks:** $Z(R_t) = \frac{R_t - \mu}{\sigma}$
   - **Rolling Quantiles & Volatility Ratios:** Dynamic normalized bounds.
   - **Volume/Order Flow Imbalances:** Relative buying/selling absorption.
   - **Cross-Series / Basis Spreads:** Relative value differentials across assets or timeframes.

---

## 🔄 Stage 2: Autonomous Iterative Search Loop

Nujin operates autonomously to find edges that satisfy user criteria or self-generated targets.

### The Search Process:
1. **Target Criteria (Binary Thresholds):**
   - Annualized Sharpe Ratio $\ge 1.5$ (or user target)
   - Max Drawdown $\le 10\%$
   - Deflated Sharpe Ratio ($\text{DSR}$) $\ge 0.95$
   - Minimum Trades Count $\ge 100$ (to avoid sample size bias)
2. **Rule Expression Trees:**
   - Strategies are formulated as logical condition sets:
     $\text{Long Trigger} = C_1 \land C_2 \land \dots \land C_n$
     $\text{Exit Trigger} = E_1 \lor E_2 \lor \text{Timeout}$
3. **Autonomous Mutation & Reversion:**
   - Evaluate performance on fixed validation slices.
   - If `score > best_score`, **PROMOTE** rule parameters.
   - If `score <= best_score`, **REVERT** and increment plateau counter.
   - If `plateau_counter >= 5`, apply **Plateau Breaker** (expand feature space, alter regime filters, or mutate holding periods).

---

## 🛡️ Stage 3: Cynic Audit & Stress Verification

No strategy is accepted based solely on in-sample performance. Every candidate must pass the **5-Gate Cynic Audit**:

1. **Friction Gate:** Enforce realistic fee + slippage (e.g., 5 bps fees + 2 bps slippage per trade side).
2. **Deflated Sharpe Ratio (DSR) Gate:** Adjust Sharpe ratio for multiple testing trial count ($N_{trials}$) and non-normal return skewness/kurtosis ($\text{DSR} \ge 0.95$).
3. **Regime Survival Gate:** Test across explicit Bull, Bear, and Side-Range market slices.
4. **Noise Perturbation Gate:** Inject Gaussian noise into price series; strategy performance must remain robust ($\Delta \text{Sharpe} < 20\%$).
5. **Parameter Stability Gate:** Evaluate neighboring hyperparameter grids; eliminate narrow "cliff" anomalies.

---

## 🚀 Stage 4: Clean Strategy Emission

Once a candidate passes Stage 3:
1. Emit clean, self-contained Python code in `strategies/`.
2. Strategy class must inherit from standard interface (`BaseStrategy`).
3. Must include entry, exit, stop loss, take profit, and position sizing logic.
4. Stream activation signal to Strategy Manager & Cockpit UI.

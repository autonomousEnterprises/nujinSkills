# Institutional Quant Protocol — Universal Alpha Discovery & Strategy Engineering

This document establishes the end-to-end standard for quantitative research, hypothesis formulation, multi-timeframe architecture, and strategy engineering in NujinAI.

---

## 🏛️ 1. Core Quantitative Principles

A strategy is accepted for production only if it demonstrates **positive mathematical expectancy**, **economic causality**, and **statistical resilience** across changing market environments.

### 1.1 Universal Hypothesis Modeling
Nujin is designed to build and optimize strategies for **any concept, market, or hypothesis requested by the user** (or discovered through data exploration). 

Regardless of the underlying trading philosophy—whether Price Action, Market Structure, Order Flow, Statistical Arbitrage, Trend Following, Scalping, Volatility Models, Macro Dynamics, or novel mathematical formulations—the protocol standardizes how that concept is translated into a systematic system:

1. **Formalize the Core Mechanism:** Clearly articulate the market dynamic or economic inefficiency being targeted.
2. **Translate to Objective Conditions:** Convert subjective or qualitative notions into unambiguous, mathematically verifiable rules and features.
3. **Multi-Timeframe Structure:** Embed the rules into a hierarchical Higher/Mid/Lower timeframe structure for context, confirmation, and precision.
4. **Enforce Execution Realism:** Account for spread, taker fees, slippage, and latency from day one.
5. **Adversarial Falsification:** Subject the candidate to the 5-Gate Cynic Audit before deployment.

### 1.2 Mathematical Expectancy & Risk Asymmetry
Every strategy must produce positive mathematical expectancy after all execution friction:

$$E = (P_{\text{win}} \times \overline{\text{Win Size}}) - (P_{\text{loss}} \times \overline{\text{Loss Size}}) - \text{Friction}$$

- **Asymmetric Risk-to-Reward ($R:R$):** Prioritize setups with favorable payoff ratios ($\frac{\overline{\text{Win}}}{\overline{\text{Loss}}} \ge 1.5$ to $3.0+$).
- **Structural Invalidation:** Invalidation points (stop losses) must be defined by objective market structure (swing extremes, structural boundaries, volatility thresholds), never arbitrary percentage or fixed-dollar stops.
- **Avoid Negative Skew:** High win-rate systems with small gains and fat-tailed, catastrophic losses are strictly rejected.

---

## 🔭 2. Institutional Multi-Timeframe (MTF) Architecture

Professional systematic strategies integrate multiple horizons to avoid trading noise in isolation. Nujin standardizes a 3-tier confluence framework:

```
┌────────────────────────────────────────────────────────────────────────┐
│ 1. HIGHER TIMEFRAME (HTF) — Context, Macro Regime & Dominant Bias     │
│    • Horizons: Daily, 4-Hour, or 1-Hour                                │
│    • Purpose: Establish overall market regime (Bull, Bear, Range),     │
│      dominant structural direction, major liquidity boundaries, or     │
│      macro volatility states.                                          │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Condition: Trade only in alignment
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 2. MID TIMEFRAME (MTF) — Structural Setup & Key Interaction Zone      │
│    • Horizons: 15-Minute or 5-Minute                                   │
│    • Purpose: Identify structural shifts, value area retests, key      │
│      level interactions, pattern completions, or dynamic conditions.   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Condition: Setup confirmed
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 3. LOWER TIMEFRAME (LTF) — Execution Trigger & Precise Invalidation    │
│    • Horizons: 1-Minute, 15-Second, or Tick Series                     │
│    • Purpose: Fine-tune entry timing, capture local confirmation,      │
│      and anchor a tight structural stop loss for high R:R execution.   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 🔬 3. Stage-by-Stage Alpha Discovery Pipeline

### Stage 1: Empirical Anomaly Discovery & Statistical Profiling
Examine underlying series behavior before finalizing rule parameters:
1. **Variance Ratio Test ($VR$):**
   - $VR < 0.95$: Mean-reverting behavior (boundary interaction / reversal mechanics).
   - $VR > 1.05$: Trending persistence (breakout and trend-following mechanics).
   - $VR \approx 1.00$: Random walk characteristics.
2. **Hurst Exponent ($H$):**
   - $H < 0.45$: Anti-persistent (mean-reverting).
   - $H > 0.55$: Persistent (momentum / trend).
3. **Conditional Forward Returns:**
   - Verify that conditional states yield statistically significant forward returns ($t\text{-stat} > 2.0, p < 0.05$).
4. **Alpha Half-Life Decay:**
   - Measure the duration over which the predictive edge decays to establish optimal holding bounds (`max_bars_held`).

### Stage 2: Hypothesis Synthesis & Iterative Optimization Loop
1. **Rule Formulation:**
   - Construct precise entry triggers, structural invalidation (stop loss), profit targets, and exit rules.
2. **Sample Size & Multi-Year Historical Depth:**
   - Require statistically meaningful sample sizes (**$N \ge 100$ to $500+$ trades**) evaluated across multi-year data.
   - Must cover diverse market regimes: Trending (Bull and Bear), Volatility Shocks, and Extended Low-Volatility Consolidation.
3. **In-Sample (IS) vs. Out-of-Sample (OOS) Partitioning:**
   - Partition data into In-Sample (for search/optimization) and Out-of-Sample (blind testing).
   - Alternatively apply Combinatorial Purged Cross-Validation (CPCV) with purging and embargoing to eliminate lookahead leakage.
4. **Iterative Autonomous Search:**
   - Execute vectorized screening via `tools/vectorized_screener.py` or continuous cycles via `tools/autoresearch_miner.py`.
   - If progress halts ($N \ge 5$ iterations without improvement), trigger the **Plateau Breaker** to expand the feature space, mutate rules, or adjust timeframes.

### Stage 3: Adversarial Cynic Audit (Falsification)
Every candidate strategy must pass all 5 gates before code generation:
1. **Execution Friction:** Realistic fee (e.g., 5 bps taker fee) + slippage (e.g., 2 bps per side) + spread friction.
2. **Deflated Sharpe Ratio (DSR):** DSR $\ge 0.95$ accounting for total trial count ($N_{trials}$) and non-normal return skewness/kurtosis.
3. **Market Regime Survival:** Positive expectancy across distinct market slices (Trending, Choppy, Volatility shock).
4. **Noise Perturbation Jitter:** Price series perturbed with synthetic noise; Sharpe retention must exceed $80\%$.
5. **Parameter Stability Surface:** Hyperparameter grid must form a stable plateau, rejecting narrow parameter spikes.
6. **Monte Carlo Permutation:** 1,000+ trade order permutations verifying 99th percentile drawdown ($\text{MDD}_{99} \le 3.0\%$) and zero ruin probability.

### Stage 4: Code Emission, Portfolio Orthogonality & Live Hot-Deployment
1. **Code Generation:** Emit production-ready Python strategy classes inheriting standard interface (`tools/strategy_emitter.py`).
2. **Portfolio Correlation Audit:** Ensure the candidate strategy has low pairwise return correlation ($< 0.50$) with existing active strategies (`tools/portfolio_cynic.py`).
3. **Hot Deployment:** Register into `strategy_manager.py` and deploy via `tools/bot_control.py` in paper mode before live capital allocation.

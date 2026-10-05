# Cynic Audit & Stress Verification Specification

The **Cynic Audit** is Nujin's rigorous, non-negotiable verification suite designed to eliminate overfitted backtests, data-mining bias, and unrealistic execution assumptions.

---

## 🏛️ The 5 Cynic Verification Gates

```
┌────────────────────────────────────────────────────────────────────────┐
│                        5-GATE CYNIC AUDIT MATRIX                       │
├─────────────────────────┬──────────────────────────────────────────────┤
│ Gate                    │ Verification Standard                        │
├─────────────────────────┼──────────────────────────────────────────────┤
│ 1. Execution Friction   │ Fees: >= 5 bps | Slippage: >= 2 bps per side │
│ 2. Deflated Sharpe      │ DSR >= 0.95 (Corrects for N_trials & skew)   │
│ 3. Market Regime        │ Must maintain Positive Expectancy in Bull,  │
│    Survival             │ Bear, and Ranging regime slices              │
│ 4. Noise Perturbation   │ Sharpe retention >= 80% under price jitter   │
│ 5. Parameter Surface    │ No sharp peaks/cliffs in adjacent parameters │
└─────────────────────────┴──────────────────────────────────────────────┘
```

---

## 📐 Mathematical Definitions

### 1. Deflated Sharpe Ratio (DSR)
The Deflated Sharpe Ratio computes the probability that an estimated Sharpe ratio ($\hat{SR}$) exceeds zero after accounting for the number of backtest iterations ($N$) and distribution non-normality (skewness $\gamma_3$, kurtosis $\gamma_4$):

$$\text{DSR} = Z\left( \frac{(\hat{SR} - SR^*) \sqrt{T - 1}}{\sqrt{1 - \gamma_3 \hat{SR} + \frac{\gamma_4 - 1}{4} \hat{SR}^2}} \right)$$

Where $SR^*$ is the expected maximum Sharpe ratio under the null hypothesis of zero true edge across $N$ trials:

$$SR^* = \sqrt{2 \ln N} \left(1 - \frac{\gamma}{2 \ln N}\right) + \frac{\gamma}{\sqrt{2 \ln N}}$$

---

### 2. Combinatorial Purged Cross-Validation (CPCV)
To eliminate leakage across time-series observations, training and testing splits are partitioned into $N$ groups with:
- **Purging:** Removing training samples whose labels overlap with test samples.
- **Embargoing:** Removing training samples immediately following test samples to eliminate autoregressive leakage.

---

### 3. Noise Sensitivity Ratio
Tests strategy resilience against synthetic micro-structure noise:

$$\text{Noise Resilience} = \frac{SR_{\text{perturbed}}}{SR_{\text{original}}}$$

Where $P_{perturbed} = P \times (1 + \epsilon), \quad \epsilon \sim \mathcal{N}(0, \sigma_{noise}^2)$.
If $\text{Noise Resilience} < 0.80$, the edge is rejected as fragile noise fitting.

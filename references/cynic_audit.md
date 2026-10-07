# Cynic Audit & Adversarial Verification Specification

The **Cynic Audit** is NujinAI's adversarial falsification suite designed to reject overfitted backtests, data-mining bias, survivorship bias, and unrealistic execution assumptions.

---

## 🏛️ The 5 Cynic Verification Gates

```
┌────────────────────────────────────────────────────────────────────────┐
│                       5-GATE ADVERSARIAL AUDIT MATRIX                  │
├─────────────────────────┬──────────────────────────────────────────────┤
│ Gate                    │ Verification Standard                        │
├─────────────────────────┼──────────────────────────────────────────────┤
│ 1. Execution Friction   │ Taker fee: >= 5 bps | Slippage: >= 2 bps/side│
│                         │ Realistic bid-ask spread deducted per trade  │
├─────────────────────────┼──────────────────────────────────────────────┤
│ 2. Deflated Sharpe      │ DSR >= 0.95 (Corrects for N_trials, skewness │
│    Ratio (DSR)          │ gamma_3, and excess kurtosis gamma_4)        │
├─────────────────────────┼──────────────────────────────────────────────┤
│ 3. Market Regime        │ Positive expectancy maintained in Bull,      │
│    Survival             │ Bear, and Choppy/Ranging regime slices       │
├─────────────────────────┼──────────────────────────────────────────────┤
│ 4. Noise Perturbation   │ Sharpe retention >= 80% under synthetic      │
│                         │ Gaussian price jitter (sigma = 0.05 * ATR)   │
├─────────────────────────┼──────────────────────────────────────────────┤
│ 5. Parameter Surface    │ Stable plateau across adjacent parameters;   │
│    Stability            │ zero tolerance for isolated "cliff" spikes   │
└─────────────────────────┴──────────────────────────────────────────────┘
```

---

## 📐 Mathematical Formulations

### 0. Gate 1: Execution Friction & Microstructure Noise Floor
Every trade return must account for physical broker/exchange friction before performance metrics are evaluated:
1. **Physical Fill Offsets (Bid-Ask Spread & Slippage):**
   $$\text{Fill}_{\text{Buy}} = P + \frac{1}{2} S + \text{Slippage}, \quad \text{Fill}_{\text{Sell}} = P - \frac{1}{2} S - \text{Slippage}$$
   Where $S$ is typical asset bid-ask spread (e.g. \$0.40 on Gold, 5 bps on Crypto, 1 pip on Forex).
2. **Microstructure Floor Rule:**
   Any strategy with an invalidation stop or trailing stop tighter than $\max(3.0 \times S, \; 1.5 \times \text{ATR})$ fails Gate 1 immediately (`FAIL_NOISE_FLOOR`), as it is mathematically trading inside bid-ask noise.
3. **Net Friction Hurdle:**
   Net expectancy per trade after all round-trip frictions must remain positive ($E > 0$) with an expectancy-to-friction ratio $\ge 2.0$.

### 1. Deflated Sharpe Ratio (DSR)
Following Bailey & López de Prado (2014), DSR calculates the probability that an estimated Sharpe ratio ($\widehat{SR}$) exceeds zero after discounting for selection bias from multiple testing ($N$ trials) and non-normal return distributions:

$$\text{DSR} = \Phi\left( \frac{(\widehat{SR} - SR^*) \sqrt{T - 1}}{\sqrt{1 - \gamma_3 \widehat{SR} + \frac{\gamma_4 - 1}{4} \widehat{SR}^2}} \right)$$

Where:
- $\Phi(\cdot)$ is the standard normal cumulative distribution function (CDF).
- $T$ is the number of return observations (sample length).
- $\gamma_3$ is the skewness of the return distribution.
- $\gamma_4$ is the Pearson kurtosis of the return distribution ($\gamma_4 = 3$ for normal distributions).
- $SR^*$ is the expected maximum Sharpe ratio under the null hypothesis of zero true edge across $N$ trials:

$$SR^* = \sqrt{2 \ln N} \left(1 - \frac{\gamma_E}{2 \ln N}\right) + \frac{\gamma_E}{\sqrt{2 \ln N}}$$

($\gamma_E \approx 0.5772156649$ is the Euler-Mascheroni constant).

**Threshold:** The strategy passes Gate 2 **only if $\text{DSR} \ge 0.95$** (95% statistical confidence that observed performance is not spurious data snooping).

---

### 2. Monte Carlo Permutation Analysis (MDD Tail Risk)
Backtest paths represent only one historical realization. The Cynic applies 1,000+ trade order permutations to stress-test path dependency and tail risk:

1. Shuffle observed trade return series randomly across $K = 1,000$ iterations.
2. Calculate the simulated equity curve and maximum drawdown for each permutation:
   $$\text{MDD}_k = \max_{t} \left( \max_{s \le t} W_s - W_t \right)$$
3. Compute the 99th percentile maximum drawdown:
   $$\text{MDD}_{99} = \text{Percentile}_{99}(\{\text{MDD}_1, \dots, \text{MDD}_K\})$$
4. Compute the Drawdown Tail Ratio:
   $$\text{Tail Ratio} = \frac{\text{MDD}_{99}}{\text{MDD}_{\text{original}}}$$

**Passing Standard:**
- $\text{MDD}_{99} \le 3.0\%$ (or within user drawdown constraints).
- $\text{Tail Ratio} \le 2.5$ (verifying drawdown distribution has thin tails).

---

### 3. Noise Sensitivity Ratio
Tests strategy resilience against microstructure noise and execution jitter:

$$\text{Noise Resilience} = \frac{SR_{\text{perturbed}}}{SR_{\text{original}}}$$

Where prices are perturbed with Gaussian noise:
$$P_{\text{perturbed}} = P \times (1 + \epsilon), \quad \epsilon \sim \mathcal{N}(0, \sigma_{\text{noise}}^2)$$

**Passing Standard:**
- $\text{Noise Resilience} \ge 0.80$ (retaining at least 80% of original Sharpe ratio).

---

### 4. Parameter Stability & Plateau Surface
Strategies must reside on broad parameter plateaus rather than fragile, overfitted parameter spikes:

1. Construct an $n \times m$ grid varying critical hyperparameters by $\pm 10\%$ to $\pm 30\%$.
2. Compute the metric matrix $M_{i,j}$.
3. Evaluate the coefficient of variation and worst-case drop:
   $$\min(M) \ge 0.40 \times \widehat{SR} \quad \text{and} \quad \text{mean}(M) \ge 0.70 \times \widehat{SR}$$

**Classification:**
- `STABLE_PLATEAU`: Robust across parameter neighbors (PASS).
- `ISOLATED_CLIFF`: Performance collapses immediately when parameters shift slightly (REJECT).

---

### 5. Portfolio Correlation & Regime Orthogonality
When evaluating a strategy for portfolio deployment, test cross-strategy correlation:

$$\rho_{i,j} = \frac{\text{Cov}(R_i, R_j)}{\sigma_i \sigma_j} < 0.50$$

Any strategy exhibiting pairwise return correlation $\rho \ge 0.50$ with an existing active strategy is rejected or assigned reduced capital allocation to prevent risk crowding.

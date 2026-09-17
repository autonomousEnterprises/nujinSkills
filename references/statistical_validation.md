# Reference: Statistical Validation, Binary Metrics & Risk Controls

## 1. Mathematical Edge & Friction Reality

A quantitative trading strategy possesses a genuine edge **only if its net expectancy is statistically positive after deducting realistic transaction costs**:
$$\text{Net Expectancy} = (\text{Win Rate} \times \text{Avg Win}) - (\text{Loss Rate} \times \text{Avg Loss}) - \text{Friction}$$

In NujinAI, all backtests and coarse filters programmatically enforce:
- **Taker Fee:** $5.0\text{ bps}$ ($0.05\%$) per trade.
- **Slippage Drag:** $2.0\text{ bps}$ ($0.02\%$) per trade.
- **Hurdle:** Average trade expectancy must exceed $2.0\times$ total transaction costs ($14.0\text{ bps}$).

---

## 2. Strict Binary Evaluation Criteria Matrix

Nujin uses unambiguous **binary (yes/no)** pass/fail criteria to evaluate candidate strategies:

| Metric / Criterion | Type | Strict Hurdle | Programmatic Command Evaluator |
| --- | --- | --- | --- |
| **`sharpe_gte_1_8`** | `command` | Net Annualized Sharpe Ratio $\ge 1.80$ | `python tools/vectorized_screener.py` |
| **`drawdown_lte_4_5`** | `command` | Maximum Peak-to-Trough Drawdown $\le 4.5\%$ | `python tools/vectorized_screener.py` |
| **`sample_trades_gte_60`**| `command` | Trade count $\ge 60$ trades & Win Rate $\ge 50.0\%$ | `python tools/vectorized_screener.py` |
| **`fee_drag_protected`** | `command` | Trade Expectancy $\ge 14.0\text{ bps}$ ($2\times \text{fees}$) | `python tools/vectorized_screener.py` |
| **`dsr_gte_0_95`** | `command` | Deflated Sharpe Ratio $\text{DSR} \ge 0.95$ | `python tools/validation_cynic.py` |
| **`parameter_plateau`** | `command` | Status == `STABLE_PLATEAU` (no isolated spikes) | `python tools/validation_cynic.py` |
| **`monte_carlo_mdd99`** | `command` | Reshuffled 99th percentile $MDD_{99} \le 2.5\times \text{MaxDD}$ | `python tools/validation_cynic.py` |
| **`oos_retention`** | `command` | $\text{Sharpe}_{\text{OOS}} \ge 0.65 \times \text{Sharpe}_{\text{IS}}$ | `python tools/validation_cynic.py` |
| **`microstructure_trap`** | `llm-judge` | Logic identifies trapped counterparty capital | Adversarial review prompt |

---

## 3. Deflated Sharpe Ratio (DSR) Formulation

When searching parameter spaces over multiple trials, standard Sharpe ratios are naturally inflated by selection bias under the maximum. The **Deflated Sharpe Ratio** (Bailey & López de Prado, 2014) penalizes the observed Sharpe for the number of tested variations ($N$):

$$DSR = \Phi \left( \frac{(\hat{SR} - SR_0)\sqrt{T-1}}{\sqrt{1 - \hat{\gamma}_3 \hat{SR} + \frac{\hat{\gamma}_4 - 1}{4}\hat{SR}^2}} \right)$$

Where:
- $\hat{SR}$: Observed annualized Sharpe Ratio.
- $SR_0$: Expected maximum Sharpe Ratio under pure random chance across $N$ trials:
  $$SR_0 \approx \sqrt{2 \ln N} \left( 1 - \frac{\gamma}{2 \ln N} \right) + \frac{\gamma}{\sqrt{2 \ln N}}$$
  ($\gamma \approx 0.5772$ is the Euler-Mascheroni constant).
- $T$: Total number of trade return observations.
- $\hat{\gamma}_3$: Sample skewness of trade returns.
- $\hat{\gamma}_4$: Sample kurtosis of trade returns (Pearson kurtosis, normal = 3).
- **Hurdle:** $\text{DSR} \ge 0.95$ (95% statistical confidence that observed outperformance is genuine).

---

## 4. Parameter Stability: Plateau vs. Cliff

A strategy passes the parameter stability test if performance forms a **broad plateau** rather than an isolated cliff:
```
   STABLE PLATEAU (PASS)             ISOLATED CLIFF (FAIL)
        ┌──────┐                              ▲
     ┌──┘      └──┐                          ╱ ╲
  ───┘            └───                 ─────┘   └─────
Neighboring cells retain >=70%        Tiny change causes collapse
```
- **Plateau Condition:** All neighboring parameter cells ($\pm 10\%, \pm 20\%$) retain $\ge 70\%$ of the central Sharpe ratio.

---

## 5. Dynamic Volatility Risk Management

Every strategy emitted by Nujin enforces strict risk controls:

### A. Dynamic ATR Stop-Loss
Stops are positioned based on local market volatility rather than arbitrary fixed percentages:
$$\text{Stop Distance} = \text{Entry Price} \pm (\text{ATR}_{14} \times \text{Multiplier})$$
- Default: $1.2\times - 1.8\times \text{ATR}_{14}$.

### B. Bar Holding Timeouts
If a trade neither reaches Take-Profit nor Stop-Loss within a predetermined maximum holding window ($4 \le \text{bars} \le 24$), exit at market immediately. This prevents capital stagnation during prolonged consolidation.

### C. Trailing Stops & Breakeven Locks
- Once price reaches $+1.0\times \text{Risk}$ ($1\text{R}$ profit), move Stop-Loss to Breakeven $+ \text{fee buffer}$.
- Trail stop $1.5\times \text{ATR}$ behind trailing peaks during trending regimes ($H > 0.55$).

---

## 6. Combinatorially Purged Cross-Validation (CPCV & Embargoing)

Standard K-Fold cross-validation is fatally flawed for financial time series because of **information leakage** across the train-test boundary:
1. **Label Overlap:** If a trade initiated at bar $t$ closes at $t+8$, training on $t+2$ leaks the forward outcome.
2. **Feature Lookback Leakage:** Rolling indicators (e.g. 50 EMA, 20 ATR) computed across the split point contaminate out-of-sample data with in-sample information.

### The Two De Prado Protections (López de Prado, 2018)

```
[ Train Partition ] ──► [ Purged Buffer ] ──► [ Test Partition ] ──► [ Embargo Buffer ] ──► [ Train Partition ]
```

1. **Purging:** Removing all training observations whose evaluation window overlaps with the test slice.
2. **Embargoing:** Imposing a temporal cooling-off window (default: $1.0\times$ max holding bars) immediately following the test partition to eliminate serial autocorrelation bleed.

All validation runs in Nujin programmatically purge overlapping bar spans to ensure that historical backtest alpha accurately reflects live out-of-sample execution.

---

## 7. Dynamic Strategy Lifecycle & Decommissioning Gates

A strategy is never permanent. Because market microstructures evolve, edges decay:

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  CANDIDATE   │ ──► │   DRY-RUN    │ ──► │  PRIME LIVE  │ ──► │ DECOMMISSION │
│ Vector Screener    │ Paper Bot    │     │  Production  │     │ Decay Gate   │
│ DSR >= 0.95  │     │ Zero Slip    │     │ Capital Allocation │ Prune File   │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

### Decommissioning Triggers (Automatic Demotion / Removal)
1. **Drawdown Breach:** Live cumulative drawdown exceeds $1.5\times$ the maximum historical drawdown observed during backtesting.
2. **Sharpe Decay:** Rolling 30-day realized Sharpe Ratio drops below $1.00$.
3. **Expectancy Inversion:** Realized average trade pnl drops below $2\times$ taker fees ($< 14\text{ bps}$).

When any of these triggers fire, Nujin's supervisor halts execution, shifts risk allocation to $0$, and automatically decommissions the strategy file via `tools/strategy_manager.py remove <StrategyName>`.


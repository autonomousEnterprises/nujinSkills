An end-to-end edge-mining pipeline is an automated, statistical assembly line designed to convert unstructured market data into mathematically vetted execution code. It takes raw OHLCV inputs, uses structured divergent prompts to discover non-consensus relationships, and subjects them to rigorous quantitative filtering.

---

### Phase 1: Data Preprocessing & Statistical Profiling

Before attempting to generate trading signals, the agent partitions the historical data and calculates fundamental statistical properties to classify market behavior.

* **Split the Data Immediately:**
* Partition data into **In-Sample (IS: 60%)** for exploration and **Out-of-Sample (OOS: 40%)** locked in an isolated partition. The agent is never permitted to touch OOS during exploration.


* **Feature Extraction via Local Tools:**
* The agent executes deterministic calculation tools on the IS dataset to extract geometric and statistical signals:
* **Bar Geometry:** Body-to-wick ratios, candle range expansion vs. ATR.
* **Effort vs. Result (VSA):** Ratio of Volume Z-score to True Range Z-score (identifies absorption vs. liquidity vacuums).
* **Volatility Regimes:** Rolling Parkinson and Yang-Zhang volatility to detect volatility compression phases.
* **Regime Memory:** Rolling Hurst Exponent ($H < 0.45$ for mean-reverting chop, $H > 0.55$ for trending persistence).





---

### Phase 2: Divergent Ideation (The Out-of-the-Box Engine)

Instead of asking for a generic strategy, the agent orchestrates a 3-step dialectic reasoning flow using high-temperature sampling (`temp=0.9`, `presence_penalty=0.4`).

```
[ Step A: Consensus Mapping ]
  Identify how 90% of retail traders use the tools on this regime.
         ↓
[ Step B: Failure Dissection ]
  Pinpoint the exact microstructure conditions where that setup fails and traps capital.
         ↓
[ Step C: Lateral Synthesis ]
  Formulate an entry rule that exploits the trapped capital, combining standard
  indicators in an orthogonal, non-textbook manner.

```

#### Operational Output Schema

The LLM must emit a structured JSON payload containing its rationale and execution logic:

```json
{
  "thesis": {
    "economic_rationale": "Retail traders buy upper Bollinger band breakouts during low-volatility Asian sessions. We fade the sweep when upper wick > 60% of candle range and Volume Z-score > 2.0 with Hurst < 0.45.",
    "trapped_counterparty": "Breakout buyers trapped by passive liquidity walls at session highs."
  },
  "rules": {
    "regime_filter": "hurst_50 < 0.45 and rolling_entropy_20 > 1.2",
    "entry_long": "close < lower_band and lower_wick_ratio > 0.55 and volume_zscore > 1.5",
    "entry_short": "close > upper_band and upper_wick_ratio > 0.55 and volume_zscore > 1.5",
    "exit_rule": "crosses_mean or max_bars_held == 12",
    "stop_loss_atr_mult": 1.5
  },
  "degrees_of_freedom": 3
}

```

---

### Phase 3: High-Throughput Coarse Filter (Vectorized In-Sample)

The agent feeds the emitted logic directly into an internal execution tool built on `vectorbt`.

* **Execution Constraints:**
* Subtract $5\text{ bps}$ taker fee and $1\text{ tick}$ slippage per trade.
* Evaluate across the full IS timeframe.


* **Automated Kill-Switches (IS Rejection Criteria):**
* Number of trades $< 100$ (rejects statistical noise).
* Net Sharpe Ratio $< 1.3$.
* Profit Factor $< 1.4$.
* Average trade expectancy $\le 2 \times$ total transaction costs.



If the strategy fails any threshold, the agent logs the failure reason and re-enters Phase 2 with the failed setup blacklisted in context.

---

### Phase 4: Adversarial Audit & Anti-Overfitting Stress Tests

Strategies that pass Phase 3 enter the validation sandbox, where the agent systematically attempts to falsify the edge.

#### 1. Parameter Stability Surface (Plateau vs. Cliff)

The agent executes a local grid search varying the numerical parameters by $\pm 10\%$ and $\pm 20\%$.

* **Pass:** Performance degrades gracefully across adjacent cells (a wide stability plateau).
* **Fail:** Performance drops to negative expectancy on neighboring values (flags an overfitted parameter spike).

#### 2. Deflated Sharpe Ratio (DSR) Check

Using Bailey and López de Prado's framework, the agent calculates its DSR by penalizing the observed Sharpe based on how many strategy variations ($N$) were attempted during Phase 2 and 3:

$$DSR = \Phi \left( \frac{(\widehat{SR} - SR_0)\sqrt{T-1}}{\sqrt{1 - \hat{\gamma}_3 \widehat{SR} + \frac{\hat{\gamma}_4 - 1}{4}\widehat{SR}^2}} \right)$$

* Where $SR_0$ is the expected maximum Sharpe under pure random chance across $N$ trials, $\hat{\gamma}_3$ is skewness, and $\hat{\gamma}_4$ is kurtosis.
* **Threshold:** $DSR \ge 0.95$ (95% probability the result is genuine skill rather than selection bias).

#### 3. Monte Carlo Trade Reshuffling

The trade returns are permuted randomly 1,000 times without replacement to break temporal clustering.

* The 99th percentile maximum drawdown ($MDD_{99}$) is computed. If $MDD_{99} > 2.5 \times$ the backtested drawdown, the strategy is discarded due to tail risk.

#### 4. Out-of-Sample (OOS) Walk-Forward Verification

Only now is the code run against the untouched 40% OOS data block.

* **Criterion:** $Sharpe_{OOS} \ge 0.65 \times Sharpe_{IS}$. If performance decays more than 35%, the hypothesis is labeled overfit and discarded.

---

### Phase 5: Production Emission & Live Incubation

When a strategy passes Phase 4, the agent promotes it from raw research code into a deployable asset.

1. **Stateful Execution Code Generation:** The agent translates the vectorized signals into an event-driven class implementing entry limits, dynamic sizing, execution timeouts, and hard risk invalidation levels.
2. **Telemetry Logging:** It writes monitoring hooks tracking:
* Realized slippage vs. modeled backtest slippage.
* Rolling win rate vs. theoretical backtest distribution.


3. **Paper Forward Incubation:** The code is deployed to a live forward environment (paper trading) for 100 trades or 3 weeks. If the live execution delta remains within historical confidence intervals, it is promoted to production capital allocation.

---

### Complete Python Implementation: The Autonomous Engine

Save this script as `quant_agent_pipeline.py`. It implements the computational engine for the agent, covering geometric feature extraction, vectorized backtesting, and the Deflated Sharpe Ratio gate.

```python
import numpy as np
import pandas as pd
from scipy.stats import norm, skew, kurtosis
import vectorbt as vbt

# ==========================================
# 1. CANDLESTICK FEATURE TOOLS
# ==========================================

def compute_market_features(df: pd.DataFrame) -> pd.DataFrame:
    """Extracts bar geometry, VSA metrics, and volatility regime."""
    out = df.copy()
    high, low, close, open_p, vol = out['high'], out['low'], out['close'], out['open'], out['volume']
    
    # Geometry
    total_range = high - low
    total_range = np.where(total_range == 0, 1e-6, total_range)
    out['body_ratio'] = np.abs(close - open_p) / total_range
    out['upper_wick'] = (high - np.maximum(close, open_p)) / total_range
    out['lower_wick'] = (np.minimum(close, open_p) - low) / total_range
    
    # Effort vs. Result (VSA)
    vol_mean = vol.rolling(20).mean()
    vol_std = vol.rolling(20).std().replace(0, 1e-6)
    out['volume_zscore'] = (vol - vol_mean) / vol_std
    
    # Parkinson Volatility (Intra-candle dispersion)
    pv = np.sqrt((1.0 / (4.0 * np.log(2.0))) * (np.log(high / low) ** 2))
    out['parkinson_vol'] = pv.rolling(20).mean()
    
    # Hurst Exponent Proxy (Variance ratio across scales)
    ret1 = np.log(close / close.shift(1))
    ret5 = np.log(close / close.shift(5))
    var1 = ret1.rolling(50).var()
    var5 = ret5.rolling(50).var()
    out['hurst_proxy'] = (var5 / (5.0 * var1.replace(0, 1e-6))).clip(0.1, 0.9)
    
    return out

# ==========================================
# 2. STATISTICAL VALIDATION & DSR GATE
# ==========================================

def calculate_dsr(returns: np.ndarray, num_trials: int) -> float:
    """Computes Deflated Sharpe Ratio given total trials attempted."""
    clean_ret = returns[~np.isnan(returns)]
    if len(clean_ret) < 30:
        return 0.0
    
    mean_r = np.mean(clean_ret)
    std_r = np.std(clean_ret, ddof=1)
    if std_r == 0:
        return 0.0
        
    sr = (mean_r / std_r) * np.sqrt(252) # Annualized
    t_obs = len(clean_ret)
    sk = skew(clean_ret)
    kt = kurtosis(clean_ret, fisher=False) # Pearson kurtosis (normal = 3)
    
    # Expected maximum Sharpe under null hypothesis
    emc = 0.5772156649  # Euler-Mascheroni constant
    z = np.sqrt(2.0 * np.log(max(num_trials, 2)))
    sr_0 = (z * (1.0 - emc / (2.0 * np.log(max(num_trials, 2)))) + emc / z) * 1.0
    
    denom = np.sqrt((1.0 - sk * sr + ((kt - 1.0) / 4.0) * (sr ** 2)) / (t_obs - 1))
    if denom <= 0:
        return 0.0
        
    dsr_stat = (sr - sr_0) / denom
    return float(norm.cdf(dsr_stat))

# ==========================================
# 3. VECTORIZED EVALUATION SANDBOX
# ==========================================

def run_agent_backtest(df: pd.DataFrame, entries: pd.Series, exits: pd.Series, fee_bps: float = 5.0):
    """Executes vectorized backtest with realistic taker friction."""
    fees = fee_bps / 10000.0
    portfolio = vbt.Portfolio.from_signals(
        close=df['close'],
        entries=entries,
        exits=exits,
        fees=fees,
        slippage=0.0002, # 2 bps slippage
        freq='15m'
    )
    
    daily_returns = portfolio.daily_returns().dropna().values
    stats = {
        "trades": portfolio.trades.count(),
        "sharpe": portfolio.sharpe_ratio(),
        "win_rate": portfolio.trades.win_rate(),
        "profit_factor": portfolio.trades.profit_factor(),
        "max_drawdown": portfolio.max_drawdown(),
        "returns": daily_returns
    }
    return stats

```
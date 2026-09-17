# Reference: Non-Consensus Alpha Ideation & Strategy Profiles

## 1. Quantitative Rationale: First-Principles Edge vs Indicator Dogmatism

Sustainable quantitative trading edges do not derive from arbitrary technical indicators (moving averages, simple RSI levels, or MACD crossovers). An indicator is **never the edge**; it is merely a lossy mathematical compression of past price/volume data. 

**Core Neutrality vs. Dynamic Injection:**
1. **The Core Engine is 100% Neutral:** The foundational mining and anomaly scanning kernel computes only scale-invariant mathematical primitives (variance ratios, normalized shocks, Markov runs, volume dispersion) and tests any user columns dynamically without lookahead. It presumes zero indicators.
2. **The AI Dynamically Injects Fitting Indicators:** When the user specifies an objective or domain (e.g. crypto funding arbitrage, FX order flow, equities mean reversion, news NLP), the AI agent dynamically synthesizes and injects whatever specific indicators, features, or math formulations fit the user's request.
3. **The Result:** The AI is never trapped in a hardcoded bubble; it can mine *any* edge across *any* domain.

**Nujin's Core Alpha Thesis:** Every profitable trading strategy must exploit a verifiable **structural market asymmetry** where an identifiable counterparty is forced into an economically disadvantageous action.

### The 4 Invariant Sources of Market Edge

| Inefficiency Class | Market Mechanism | Systematic Exploitation |
| :--- | :--- | :--- |
| **1. Behavioral & Psychological Traps** | Retail FOMO breakout chasing, panic stop runs, forced margin liquidations, disposition effect. | Liquidity sweep rejections, capitulation volume absorption, false breakout fades. |
| **2. Structural & Institutional Constraints** | Pension/index rebalancing (e.g. 16:00 London fix), ETF creation/redemption, options dealer gamma hedging. | Session killzone drift, anchored VWAP mean reversion, volatility compression breakouts. |
| **3. Risk & Liquidity Premium** | Market makers & liquidity providers require compensation for absorbing aggressive inventory risk during expansions. | Mean-reversion envelope scalping, volatility selling/fading during range regimes. |
| **4. Information & Lead-Lag Asymmetry** | Macro releases (CPI, FOMO), cross-market lead-lag (e.g. US500 futures leading BTC; DXY leading Gold). | Intermarket divergence triggers, high-frequency event momentum, news volatility fades. |

---

## 2. The Two-Tiered Empirical Discovery Pipeline

Rather than relying on ungrounded LLM text guessing, Nujin couples **empirical statistical numbers** with **causal economic reasoning**:

```
┌────────────────────────────────────────────────────────────────────────┐
│ TIER 1: EMPIRICAL ANOMALY SCANNER (tools/anomaly_scanner.py)           │
│   • Vectorized calculation of Lo-MacKinlay Variance Ratios & Hurst     │
│   • Hourly session volatility and directional drift t-statistics       │
│   • Conditional forward return distributions P(R_{t+k} | Condition)    │
│   • Alpha Decay Half-Life curve estimation (h*)                        │
│   • Emits: .nujin/empirical_briefing.json                              │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ TIER 2: LLM ECONOMIC REASONER (Hypothesis Formulation)                 │
│   • Ingests empirical anomalies with p < 0.05 and |t| >= 2.0           │
│   • Connects empirical statistical advantage to 1 of 4 Edge Classes    │
│   • Defines structural invalidation anchor (where thesis fails)        │
│   • Restricts maximum holding horizon to Alpha Half-Life (h*)          │
└────────────────────────────────────────────────────────────────────────┘
```

### The 3-Step Dialectic Ideation Engine

```
[ Step 1: Consensus Mapping ]
  Identify how the retail herd or naive algorithms trade this asset/timeframe.
         ↓
[ Step 2: Failure Dissection ]
  Pinpoint the exact microstructure conditions where that consensus setup fails and traps capital.
         ↓
[ Step 3: Lateral Synthesis ]
  Formulate non-consensus entry & exit rules combining orthogonal auction features.
```

### Multi-Horizon Fractal Alignment
Lower-timeframe execution triggers must always be conditioned on higher-timeframe market structure:
$$\text{Strategy Rules} = \text{Macro Context (HTF)} \times \text{Local Regime (MTF)} \times \text{Precision Trigger (LTF)}$$
- **Higher Timeframe (1h–4h):** Locates structural liquidity pools, trend bias, and institutional fair value.
- **Medium Timeframe (15m):** Quantifies volatility expansion state and volume absorption ($V_{\text{abs}}$).
- **Lower Timeframe (1m–5m):** Pinpoints the precise execution trigger with minimal structural stop distance.

### Step 1: Consensus Mapping
- **Retail Setup:** Buying Bollinger Band upper-band breakouts, buying oversold RSI ($< 30$), or chasing momentum on high-volume expansion bars.

### Step 2: Failure Dissection
- **Microstructure Trap:** When price attempts to expand beyond resistance with a high Volume Z-score ($> 1.5$) but creates an elongated upper wick (`upper_wick > 0.45`), aggressive buyers have been absorbed by institutional limit sellers. Price fails to follow through, leaving late breakout takers trapped off-balance.

### Step 3: Lateral Synthesis
- **Non-Consensus Rule:** Fade the failed breakout immediately with dynamic invalidation placed just beyond the wick extreme:
  ```python
  entry_short = "upper_wick > 0.42 and volume_zscore > 1.2 and hurst_proxy < 0.45"
  invalidation = high + 0.15% buffer
  ```

---

## 3. Six Quantitative Quality Dimensions

When ideating or suggesting alpha targets, systematically explore these 6 orthogonal dimensions:

1. **Mean Reversion & Liquidity Sweeps:**
   - Capitalize on absorbed aggressive participants around session extremes (e.g. Asian session liquidity sweeps, previous day highs/lows).
   - *Key Features:* `lower_wick`, `upper_wick`, `volume_zscore`, `hurst_proxy < 0.45`.
2. **Trend Expansion & Momentum:**
   - Enter persistent directional momentum after verified volatility expansion.
   - *Key Features:* `hurst_proxy > 0.55`, `sma_50` slope, EMA alignment (`ema_9 > ema_21 > ema_100`).
3. **Volatility Regimes & Compression:**
   - Detect pre-breakout energy accumulation using intra-bar volatility metrics.
   - *Key Features:* `parkinson_vol`, ATR compression ratio ($\text{ATR}_5 / \text{ATR}_{50} < 0.10$).
4. **Volume-Spread Analysis (VSA):**
   - Identify "effort vs. result" anomalies where high volume produces narrow range (absorption) or wide range occurs on low volume (liquidity vacuum).
   - *Key Features:* `volume_zscore`, `v_spread`, `body_ratio`.
5. **Structural Session Inefficiencies:**
   - Exploit institutional order-flow schedule imbalances (London Open 08:00 UTC, NY Open 13:30 UTC, Asian range fade 00:00–06:00 UTC).
6. **Multi-Timeframe Confluence:**
   - Anchor macro regime on higher timeframe (e.g. 1h/4h Anchored VWAP distance) and execute precise timing on lower timeframe (1m/15m wick rejection).

---

## 4. User Strategy Profiles & Constraint Mapping

Nujin maps natural language user prompts to standardized quantitative profiles:

| User Prompt Intent | Profile Name | Target Constraints & Risk Rules | Preferred Mechanics |
| --- | --- | --- | --- |
| *"I need a prop firm trading strategy"* | **Prop Firm Challenge** | Max DD $\le 4.5\%$, Net Sharpe $\ge 1.8$, Win Rate $\ge 52\%$, DSR $\ge 0.95$, Strict 1:1.5+ Risk/Reward | Low-drawdown wick rejection, tight hard stops, zero overnight holding risk. |
| *"Make me a BTC swing strategy"* | **BTC Market Cycle Swing** | 15m/1h/4h timeframes, Profit Factor $\ge 1.8$, Max DD $\le 10\%$, Hurst Trend Filter ($H > 0.55$) | Trend riding, dynamic ATR trailing stops, multi-day holding capacity ($12 \le \text{bars} \le 48$). |
| *"Make me a conservative strategy"* | **Conservative Investment** | Max DD $\le 6.0\%$, Profit Factor $\ge 1.6$, Low trade turnover ($< 30$ trades/month), Preservation focus | Volatility compression filters (`parkinson_vol`), wide fair-value anchor bands (`avwap_zscore`). |
| *"How can news/volatility be traded?"* | **News Volatility Fade** | Short holding periods ($2 \le \text{bars} \le 8$), Expectancy $\ge 25\text{ bps}$, Monte Carlo MDD99 $\le 2.0\times$ | Post-announcement wick rejection, V-spread spike absorption, liquidity grab fades. |

---

## 5. Seven Structured Mutation Operators

When a strategy fails backtesting or statistical validation gates, Nujin mutates the hypothesis using explicit operators:

| Operator | Transformation Logic | Practical Application |
| --- | --- | --- |
| **`add_constraint`** | Adds an orthogonal regime or volume filter to eliminate false signals during choppy conditions. | Add `and hurst_proxy < 0.45` or `and volume_zscore > 1.4` |
| **`add_negative_example`** | Inserts an anti-trap prohibition preventing entry into exhausted bars. | Add `and body_ratio < 0.65` (reject solid breakout bars without wicks) |
| **`restructure_exit`** | Modifies trade holding caps ($4 \le \text{bars} \le 48$), trailing stops, or Take-Profit multipliers. | Mutate `max_bars_held` from 6 to 12; adjust Take-Profit from $3.0\%$ to $4.2\%$ |
| **`tighten_thresholds`** | Increases selectivity on entry criteria to filter out marginal setups. | Change `lower_wick > 0.38` to `0.45`; reduce Stop-Loss from $2.0\%$ to $1.4\%$ |
| **`remove_bloat`** | Strips collinear or low-impact indicators to reduce parameter degrees of freedom ($\le 3$). | Prune secondary RSI clause; retain only primary wick + VSA volume trigger |
| **`directional_bias_flip`** | Tests directional asymmetry (LONG-only vs. SHORT-only vs. Dual). | Flip from DUAL to LONG-only during secular bull regimes |
| **`plateau_break`** | Triggered after 5 consecutive failures: discards current lineage and synthesizes an orthogonal hypothesis. | Switch completely from mean-reversion scalp to volatility expansion breakout |

---

## 6. Empirical Failure Memory

Nujin records every failed parameter set, rule combination, and rejection reason on disk (`.nujin/results.jsonl`). When mutating rules or executing a `plateau_break`, Nujin queries the failure history to ensure no discredited parameter cell or indicator trap is ever repeated.

# Reference: Out-of-the-Box Ideation Engine & Creative Rule Generation

## Overview
To discover genuine alpha, the AI agent must **never rely on static indicator templates or standard textbook rules**. The system is built around generic, high-throughput feature calculation and vectorized screening tools that allow the AI to invent unconstrained, creative mathematical expressions.

---

## 1. The 3-Step Dialectic Ideation Engine

```
[ Step A: Consensus Mapping ]
  Identify how 90% of retail traders use indicators in this regime.
         ↓
[ Step B: Failure Dissection ]
  Pinpoint exact microstructure conditions where that setup fails and traps capital.
         ↓
[ Step C: Lateral Synthesis ]
  Formulate an entry rule combining orthogonal custom features.
```

### Step A: Consensus Mapping
- *Goal:* Map retail herd behavior (e.g. buying BB breakouts, buying RSI $< 30$ oversold, MACD bullish cross).

### Step B: Failure Dissection
- *Goal:* Identify where large institutional liquidity absorbs aggressive takers, creating temporary liquidity traps.

### Step C: Lateral Synthesis
- *Goal:* Invent non-consensus entry/exit rules using custom feature combinations rather than simple thresholds.

---

## 2. Creative Feature Combinations

The AI agent can evaluate any custom boolean expression using features extracted by `tools/feature_miner.py`:

| Feature Name | Description | Creative Usage Example |
| --- | --- | --- |
| `upper_wick` / `lower_wick` | Bar wick rejection ratio | Fade breakouts when `upper_wick > 0.60` |
| `volume_zscore` | Volume participation relative to 20-period mean | Require `volume_zscore > 1.8` for absorption |
| `hurst_proxy` | Time series memory ($H < 0.45$ chop vs $H > 0.55$ trend) | Enable mean reversion ONLY when `hurst_proxy < 0.45` |
| `parkinson_vol` | Intra-bar high/low volatility dispersion | Detect volatility compression prior to breakout |
| `avwap_zscore` | Dispersion distance from Anchored VWAP | Mean revert when `avwap_zscore > 2.0` |
| `v_spread` | Range expansion per volume unit | Filter dry-volume false breakouts |

---

## 3. Relentless Discovery Directive
- The AI agent MUST NOT stop if trial 1 fails.
- The AI logs the failure cause, blacklists the failed parameter cell, mutates the hypothesis, and **persistently loops until a candidate passes DSR $\ge 0.95$, parameter stability, and OOS walk-forward falsification**.

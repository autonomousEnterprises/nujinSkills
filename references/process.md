# Reference: End-to-End Edge Mining Operational Process

## Overview
The NujinSkill mining process is an automated, 5-phase statistical assembly line designed to transform raw market data into mathematically vetted execution code.

---

## The 5-Phase Funnel

```
[ Phase 1: Feature Extraction & Regime Scan ]  <-- tools/feature_miner.py
                       │
                       ▼
[ Phase 2: Out-of-the-Box Dialectic Ideation ]  <-- AI Agent Dialectic Prompting
                       │
                       ▼
[ Phase 3: Fast Vectorized Coarse Filter ]     <-- tools/vectorized_screener.py
                       │
                       ▼
[ Phase 4: Adversarial Audit & Falsification ]  <-- tools/validation_cynic.py
                       │
                       ▼
[ Phase 5: Code Generation & UI Telemetry ]    <-- tools/strategy_emitter.py & ui_dispatcher.py
```

### Phase 1: Data Partitioning & Feature Extraction
- Immediately partition data: **In-Sample (IS: 60%)** for exploration and **Out-of-Sample (OOS: 40%)** locked in isolation.
- Run `python tools/feature_miner.py --input data/candles.csv --output data/features.csv`.

### Phase 2: Divergent Ideation
- Formulate hypothesis targeting trapped counterparty capital.
- Enforce parameter limit $\le 3$.

### Phase 3: Fast Vectorized Coarse Filter
- Screen logic on IS dataset using `python tools/vectorized_screener.py`.
- Deduct 5 bps taker fee and 2 bps slippage friction.
- Reject if Sharpe $< 1.3$, Trades $< 100$, Profit Factor $< 1.4$, or Expectancy $\le 2\times$ fees.

### Phase 4: Adversarial Audit & Anti-Overfitting
- Audit surviving candidates using `python tools/validation_cynic.py`.
- Require **DSR $\ge 0.95$**, **Stable Parameter Plateau**, **$MDD_{99} \le 2.5\times MDD$**, and **$Sharpe_{OOS} \ge 0.65 \times Sharpe_{IS}$**.

### Phase 5: Production Emission & Live Incubation
- Emit Freqtrade `IStrategy` using `python tools/strategy_emitter.py`.
- Dispatch telemetry to UI and Telegram via `python tools/ui_dispatcher.py`.
- Deploy paper trading supervisor via `python tools/bot_control.py`.

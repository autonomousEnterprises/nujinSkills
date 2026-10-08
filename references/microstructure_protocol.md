# Market Microstructure & Auction Imbalance Protocol

This document formalizes the quantitative analysis of **trapped inventory, passive absorption, and auction failure dynamics** within NujinAI.

---

## 🏛️ 1. Theoretical Foundation: Auction Market Theory & Forced Liquidity

Markets do not move randomly; they operate as continuous double auctions designed to facilitate trade.
Price discovery functions via an essential invariant:
> **Price moves until two-sided trade is facilitated, or until aggressive market orders encounter passive limit exhaustion.**

Systematic traders do not need access to private competitor strategies to exploit this mechanic. All discretionary and systematic strategies leave predictable structural footprints at structural extremes:
1. **Entry Clustering:** Aggressive market orders cluster at obvious technical levels (range breakouts, session highs/lows, macro levels).
2. **Defensive Clustering:** Protective stop-loss orders are placed immediately beyond those levels.
3. **Liquidity Conversion:** Because a stop-loss is an aggressive market order when triggered (e.g., stop-loss on a long position is a market sell), trapped participants become **forced fuel** for rapid, asymmetric reversals.

---

## 🔬 2. The 4-Stage Trapped Inventory Sequence

Any systematic strategy targeting auction imbalance or trapped liquidity follows an objective sequence:

```
[ 1. Level Interaction / Breakout Attempt ]
  Price expands into a key structural boundary (HTF extreme, Value Area, MTF Zone).
                    │
                    ▼
[ 2. Passive Absorption / Effort vs. Result ]
  Volume or CVD spikes aggressively, but price fails to progress (Limit orders absorb market orders).
                    │
                    ▼
[ 3. Structural Reclaim / Invalidation of Breakout ]
  Price fails to hold and slips back inside the prior range (Chasers are now trapped offside).
                    │
                    ▼
[ 4. Cascading Liquidity Run (The Asymmetric Trade) ]
  Price accelerates toward the opposing liquidity pool as trapped stops trigger.
```

---

## 📐 3. Mathematical Formulations & Feature Proxies

When raw Level 3 (DOM / Market Depth) or full tick-level CVD data is not available, these dynamics are reliably captured from OHLCV series via scale-invariant proxies:

### 3.1 Effort vs. Result (Absorption Index)
Measures the divergence between aggressive volume effort and price displacement:
$$\text{Effort-to-Result Ratio} = \frac{\text{Volume Z-Score}}{\text{Normalized True Range}}$$
- **High Ratio ($> 2.0$):** Massive volume effort producing negligible price expansion. This indicates large passive institutional limit orders absorbing retail market sweeps.

### 3.2 Auction Rejection / Wick Asymmetry
$$\text{Upper Rejection} = \frac{\text{High} - \max(\text{Open}, \text{Close})}{\text{High} - \text{Low}}, \quad \text{Lower Rejection} = \frac{\min(\text{Open}, \text{Close}) - \text{Low}}{\text{High} - \text{Low}}$$
- An upper rejection $\ge 0.38$ accompanied by above-average volume ($\text{Vol Z-score} > 1.0$) confirms buyers attempted an auction higher, met immediate liquidity replenishment, and were rejected back into value.

### 3.3 Trapped Inventory Signatures (Offside Clustering)
- **Trapped Long Signature:**
  $$\text{High}_t \ge \max_{1 \le i \le 20}(\text{High}_{t-i}) \quad \land \quad \text{Volume Z-Score} > 1.0 \quad \land \quad \text{Close}_t < \text{Open}_t$$
  Aggressive buyers chased a new 20-bar high with elevated volume, yet the bar closed bearish. Those market-buy orders are now trapped at a loss.
- **Trapped Short Signature:**
  $$\text{Low}_t \le \min_{1 \le i \le 20}(\text{Low}_{t-i}) \quad \land \quad \text{Volume Z-Score} > 1.0 \quad \land \quad \text{Close}_t > \text{Open}_t$$
  Aggressive sellers pushed a new 20-bar low with elevated volume, yet the bar closed bullish. Those short orders are offside.

---

## 🛡️ 4. Neutrality & Scientific Guardrails

To prevent strategy bias:
1. **Hypothesis Neutrality:** Auction imbalance is one valid hypothesis family alongside Momentum Continuation, Mean Reversion, and Structural Breakouts. The engine **never mandates** using absorption or traps.
2. **Falsification Gate Compliance:** Any trapped-inventory strategy must strictly pass all **6 Cynic Audit Gates**, particularly:
   - **Gate 1 (Microstructure Noise Floor):** Stops must reside $\ge \max(3\times \text{Spread}, 1.5\times \text{ATR})$ away from the entry to avoid trading inside random spread noise.
   - **Gate 6 (Equity Linearity):** Payoffs must compound smoothly ($R^2 \ge 0.85$, $K\text{-Ratio} \ge 1.5$) rather than relying on rare, sporadic liquidation cascades.

# Reference: Institutional Strategy Ranking & Quantitative Tier System

## 1. Overview & Problem Formulation

In systematic quantitative trading, ranking strategies purely by **alpha drift** or unadjusted **raw return** creates fatal biases:
1. **Sample Size Blindness:** A strategy with 5 trades and a Sharpe of 9.0 may rank above a battle-tested strategy with 120 trades, positive expectancy, and Deflated Sharpe Ratio (DSR) $\ge 0.98$.
2. **Overfitting Sensitivity:** High raw Sharpe without falsification testing (Monte Carlo $MDD_{99}$, parameter drift surfaces) exposes capital to curve-fitted illusions.
3. **Downside Neglect:** A strategy with a high win rate but an unmanaged $12\%$ drawdown tail risk can ruin a prop firm or portfolio account.

NujinAI implements an **Institutional 4-Pillar Composite Scoring Model** ($0.0 \dots 100.0$) coupled with **Programmatic Falsification Gates** and **Strict Tier Classifications**.

---

## 2. The 4-Pillar Composite Scoring Model

Every strategy registered in `data/strategies.json` is scored across four independent quantitative pillars:

$$\text{Composite Score} = (0.35 \times \text{Edge}) + (0.30 \times \text{Robustness}) + (0.25 \times \text{Risk}) + (0.10 \times \text{Drift})$$

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                    INSTITUTIONAL QUANTITATIVE COMPOSITE SCORE                 │
├───────────────────────┬────────────────────────┬───────────────┬──────────────┤
│ Edge Strength (35%)   │ Robustness (30%)       │ Risk (25%)    │ Drift (10%)  │
├───────────────────────┼────────────────────────┼───────────────┼──────────────┤
│ • Net Annual Sharpe   │ • Deflated Sharpe DSR  │ • Max Drawdown│ • Trajectory │
│ • Profit Factor (PF)  │ • Sample Trades (N)    │ • Win Rate    │ • Snapshots  │
│ • Trade Expectancy bps│ • 5-Gate Cynic Ratio   │ • Tail Risk   │ • Decay Test │
└───────────────────────┴────────────────────────┴───────────────┴──────────────┘
```

### Pillar 1: Edge Strength ($W_E = 35\%$)
Measures net profitability after accounting for execution friction (5 bps taker fee + 2 bps slippage):
- **Net Annualized Sharpe ($50\text{ pts}$):** Scaled linearly up to a Sharpe of $3.50$ (capped at 50 pts). Strategies with Sharpe $\le 0.0$ receive 0 pts.
- **Profit Factor ($35\text{ pts}$):** Scaled linearly from $PF = 1.0$ (break-even) to $PF \ge 2.0$ (35 pts). $PF < 1.0$ receives 0 pts.
- **Trade Expectancy ($15\text{ pts}$):** Positive average return per trade in basis points ($\text{bps}$). $15\text{ bps}$ awards the full 15 pts.

$$\text{Score}_{\text{Edge}} = \min\left(50, \max\left(0, \frac{\text{Sharpe}}{3.5} \times 50\right)\right) + \min\left(35, \max\left(0, \frac{PF - 1.0}{1.0} \times 35\right)\right) + \min\left(15, \max\left(0, \frac{\text{Expectancy}_{\text{bps}}}{15.0} \times 15\right)\right)$$

### Pillar 2: Statistical Robustness & Falsification ($W_{\text{Rob}} = 30\%$)
Protects against p-hacking, selection bias, and sample insignificance:
- **Deflated Sharpe Ratio ($50\text{ pts}$):** Based on Bailey & López de Prado (2014), penalizing Sharpe for trial counts ($N$). Full 50 pts awarded if $\text{DSR} \ge 0.95$. Partial credit scaled down to $\text{DSR} = 0.50$.
- **Sample Trade Count Significance ($30\text{ pts}$):**
  - $N \ge 60$ trades: Full $30\text{ pts}$.
  - $30 \le N < 60$: $20\text{ pts}$.
  - $15 \le N < 30$: $10\text{ pts}$.
  - $N < 15$: $0\text{ pts}$ (statistically underpowered).
- **5-Gate Cynic Pass Ratio ($20\text{ pts}$):** Awards up to $20\text{ pts}$ proportional to the number of gates passed (DSR, Parameter Plateau, Monte Carlo $MDD_{99}$, OOS Walk-Forward Retention, Regime Survival).

### Pillar 3: Downside Risk & Capital Preservation ($W_{\text{Risk}} = 25\%$)
Penalizes capital volatility and asymmetric fat-tail risk:
- **Maximum Drawdown Curve ($60\text{ pts}$):**
  - $\text{MaxDD} \le 1.0\%$: $60\text{ pts}$ (exceptional control).
  - $1.0\% < \text{MaxDD} \le 2.5\%$: $50\text{ pts}$.
  - $2.5\% < \text{MaxDD} \le 4.5\%$: $35\text{ pts}$.
  - $4.5\% < \text{MaxDD} \le 8.0\%$: $15\text{ pts}$.
  - $\text{MaxDD} > 8.0\%$: $0\text{ pts}$ (severe prop-firm violation).
- **Win Rate Consistency ($40\text{ pts}$):**
  - $\text{Win Rate} \ge 55\%$: $40\text{ pts}$.
  - $50\% \le \text{Win Rate} < 55\%$: $30\text{ pts}$.
  - $40\% \le \text{Win Rate} < 50\%$: $15\text{ pts}$.
  - $\text{Win Rate} < 40\%$: $0\text{ pts}$.

### Pillar 4: Drift Stability ($W_{\text{Drift}} = 10\%$)
Tracks stability across cron snapshots and live execution:
- Trajectory evaluation: `IMPROVING` ($100\text{ pts}$), `STABLE` ($80\text{ pts}$), `NEW` ($75\text{ pts}$), `DECAYING` ($35\text{ pts}$).

---

## 3. Strict Quantitative Tier Hurdles

Composite score alone is insufficient: strategies must also satisfy **hard binary hurdles** to attain higher tiers.

| Tier | Category | Composite Score | Mandatory Binary Hurdles | Purpose & Execution Status |
|---|---|---|---|---|
| **S-Tier** | **Superior Edge** | $\ge 80.0$ | $\text{Sharpe} \ge 2.50$, $\text{DSR} \ge 0.95$, $\text{MaxDD} \le 4.5\%$, $\text{Win Rate} \ge 50\%$, $PF \ge 1.50$, Trades $\ge 25$ | Institutional production alpha ready for live prop capital. |
| **A-Tier** | **Robust Edge** | $\ge 65.0$ | $\text{Sharpe} \ge 1.80$, $\text{DSR} \ge 0.90$, $\text{MaxDD} \le 5.0\%$, $PF \ge 1.30$, Trades $\ge 20$ | Proven alpha; qualified for live multi-bot deployment. |
| **B-Tier** | **Incubation Alpha**| $\ge 45.0$ | Core positive expectancy ($\text{Sharpe} > 1.0$, $PF > 1.1$) | Candidates accumulating trade sample size or running cron walk-forward tests. |
| **C-Tier** | **Sub-Hurdle / Decayed** | $< 45.0$ | Failed primary risk gates ($\text{MaxDD} > 8\%$, negative Sharpe, or collapsing trajectory) | Quarantined; requires parameter mutation or retirement. |

---

## 4. Agent CLI Commands

The quant engine exposes two primary workflows via `tools/strategy_manager.py`:

### Leaderboard & Ranking Recalculation
```bash
python tools/strategy_manager.py rank
```
Calculates scores across all strategies in `data/strategies.json`, synchronizes with the running server via WebSocket, updates persistent state, and displays the formatted leaderboard:
```text
============================================================================================================
[StrategyManager] INSTITUTIONAL QUANTITATIVE LEADERBOARD & TIERS (🟢 Live WebSocket Synced)
============================================================================================================
Rank  Tier                     Score  E/Rob/Rsk/Drf    Strategy Name                Sharpe   DSR      Win%     MaxDD    PF     Gates
------------------------------------------------------------------------------------------------------------
#1    S-Tier (Superior Edge)   95.7   95/100/100/75    PropFirmAtrHybridScalperXa   4.17     1.00     60.7%    0.33%    1.80   5/5
#2    S-Tier (Superior Edge)   92.4   94/90/100/75     GoldLiquiditySweepAtrScalp   4.07     1.00     60.0%    0.33%    1.77   5/5
#3    S-Tier (Superior Edge)   92.0   99/90/92/75      XauMtfEngulfingScalper       4.16     0.98     54.5%    0.33%    1.95   5/5
#4    B-Tier (Incubation Alpha) 73.5  100/20/100/75    XauMtfEngulfingScalper5m     8.83     0.00     60.0%    0.09%    3.40   3/5
------------------------------------------------------------------------------------------------------------
  TIER DISTRIBUTION: S-Tier: 3 | A-Tier: 0 | B-Tier: 6 | C-Tier: 5
============================================================================================================
```

For programmatic machine consumption:
```bash
python tools/strategy_manager.py rank --json
```

### In-Depth Strategy Insights
```bash
python tools/strategy_manager.py insights PropFirmAtrHybridScalperXauusd
```
Provides the full quantitative audit breakdown, including 4-pillar sub-scores, Cynic audit gates, and the tier qualification rationale:
```text
====================================================================================
[StrategyManager] STRATEGY QUANTITATIVE INSIGHTS & TIER RATIONALE
====================================================================================
  Strategy Name:    Trader MNQ ATR Scalper on Gold (PropFirmAtrHybridScalperXauusd.py)
  Rank & Tier:      Rank #1 — S-Tier (Superior Edge)
  Status / Profile: CRON_BACKTEST | Prop Firm Gold ATR Envelope Scalper (1m-5m)
  Asset Scope:      XAU/USD (1m)
  Thesis:           Trader MNQ volatility envelope limit dip buying & exhaustion fading
  --------------------------------------------------------------------------------
  COMPOSITE SCORE:  95.7 / 100.0
    • Edge Strength (35%):           94.9 / 100  (Sharpe 4.17, PF 1.80)
    • Statistical Robustness (30%): 100.0 / 100  (DSR 1.00, Trades 61)
    • Downside Risk & MDD (25%):    100.0 / 100  (Max DD 0.33%, Win Rate 60.7%)
    • Drift Stability (10%):         75.0 / 100  (Snapshots: 1)
  --------------------------------------------------------------------------------
  CYNIC AUDIT GATES (5/5 PASSED):
    [Gate 1] Net Annualized Sharpe >= 1.80 : ✅ PASS (4.17)
    [Gate 2] Max Drawdown <= 4.50%         : ✅ PASS (0.33%)
    [Gate 3] Trades >= 30 & Win Rate >= 50%: ✅ PASS (61 trades, 60.7%)
    [Gate 4] Profit Factor >= 1.30         : ✅ PASS (1.80)
    [Gate 5] Deflated Sharpe DSR >= 0.95   : ✅ PASS (1.00)
  --------------------------------------------------------------------------------
  TIER RATIONALE:   Elite Production Alpha: 5/5 Gates Passed, DSR 1.00 >= 0.95, Sharpe 4.17
====================================================================================
```

With `--json`:
```bash
python tools/strategy_manager.py insights PropFirmAtrHybridScalperXauusd --json
```

---

## 5. Telemetry REST API & WebSocket Real-Time Synchronization

The telemetry server (`server/main.py`) provides endpoints and events:

### REST Endpoints
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/strategies/manage/rank` | Triggers immediate re-scoring of all strategies, persists to `data/strategies.json`, and broadcasts WebSocket event. |
| `GET` | `/api/strategies/manage/rankings` | Returns sorted strategies list with `ranking_breakdown`, composite scores, and tier distribution counts. |

### WebSocket Event
Whenever strategies are recalculated or modified:
```json
{
  "event": "STRATEGIES_UPDATED",
  "data": [ ...list of ManagedStrategy with ranking_breakdown... ]
}
```
All connected Cockpit clients (`StrategyLeaderboard.vue`) update immediately with zero page refresh required.

---

## 6. Frontend Cockpit Experience

In `frontend/src/components/strategy/StrategyLeaderboard.vue`:
1. **Tier Filter Dropdown:** Filter by `ALL`, `S-Tier`, `A-Tier`, `B-Tier`, or `C-Tier`.
2. **Interactive Sorting:** Sort by `Rank (Score)`, `Sharpe Ratio`, `Win Rate`, `Profit Factor`, `Max Drawdown`, or `Alpha Drift`.
3. **Score & Sub-Score Badges:** Distinct visual badges for S-Tier (emerald), A-Tier (blue), B-Tier (amber), and C-Tier (slate/rose) with composite score and sub-score metrics.
4. **Preserved Drift Analysis:** All baseline-to-current metrics, drift percentages, and Sharpe sparklines remain intact.
5. **Expandable 4-Pillar Breakdown:** Clicking any row reveals a scorecard displaying the 4-pillar breakdown, Cynic gate pass counter, tier rationale, and snapshot history.

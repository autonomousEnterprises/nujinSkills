To find non-obvious statistical edges using free, publicly available APIs, you must avoid downloading standard OHLCV price bars to run classic formulas. When data is easy to access in bar format, thousands of retail bots are already executing the exact same calculations.

The blueprint for mining edges on public data is **multi-stream data synthesis**: pairing price action with a secondary or tertiary public data stream that reflects structural pressure, inventory stress, or institutional constraints.

---

### Phase 1: High-Signal Free & Public Data Feeds

You do not need an expensive Bloomberg or Databento subscription. Free tiers and public endpoints provide massive structural depth if you know where to tap:

| Category | Free / Public Endpoints | What Informational Alpha It Holds |
| --- | --- | --- |
| **Microstructure & Derivatives** | **Binance / Bybit / OKX Public Endpoints** (No API key needed for market data: `/fapi/v1/fundingRate`, `/openInterest`, `/trades`, `/depth`) | Aggressive market-order delta, liquidation events, resting order book depth, historical funding rates. |
| **On-Chain & DeFi** | **DeFiLlama API** (`/v2/chains`, `/protocols`), **Etherscan / Solscan APIs**, Public RPC nodes | Large token unlocking schedules, TVL flows across bridges, lending pool health factors (monitoring liquidation walls). |
| **Macro & Rates** | **FRED API** (Federal Reserve Economic Data) | Yield curve inversions (10Y minus 2Y), Overnight Reverse Repo facility usage, Fed balance sheet adjustments, liquidity drain. |
| **Institutional Position Shifts** | **CFTC CoT API** (Commitment of Traders via Quandl/Nasdaq Data Link or CFTC public CSVs) | Commercial hedgers vs. non-commercial speculative positioning in FX, commodities, and index futures. |
| **Alternative & Sentiment** | **SEC EDGAR API** (Form 4 insider trading, 13F filings), **Finnhub Free Tier**, Social APIs (Reddit/X rate-limited scrapers) | Executive insider buying/selling relative to float, retail sentiment clustering. |

---

### Phase 2: Formulating Cross-Domain Hypotheses (The "Niche" Generator)

Instead of testing technical indicators in isolation, your edge miner should search for **imbalances between two disconnected datasets**:

#### Niche 1: The Liquidity Squeeze Divergence (Perp Derivatives Data)

* **Data Sources:** Public REST endpoints from crypto derivatives exchanges (Open Interest + Aggressive Trades / CVD + Spot Index).
* **Structural Anomaly:** When price drops to a prior low, but Open Interest (OI) surges drastically while Cumulative Volume Delta (CVD) is violently negative, yet price fails to push further down.
* **The Constraint:** Aggressive late-shorters are hitting massive passive limit orders. The moment aggressive selling stops, those short positions are trapped with nowhere to exit except buying back into thin books.

#### Niche 2: Macro Liquidity Absorption Lag (FRED API + Equity/Index ETF)

* **Data Sources:** FRED API (Reverse Repo volume + Treasury General Account balances) fetched weekly vs. SPY/QQQ daily volume profile.
* **Structural Anomaly:** Net liquidity injection (Fed balance sheet minus TGA minus RRP) often leads equity market liquidity expansion with a measurable multi-day lag.
* **The Constraint:** Money-market funds shift capital based on mechanical rate adjustments, creating a multi-day wave of passive institutional inflows that systematically cushions market drawdowns.

#### Niche 3: Extreme Speculative Crowding & Mean Reversion (CFTC CoT Data)

* **Data Sources:** Weekly CFTC CoT reports (Free via public data feeds) + Daily FX/Commodity futures data.
* **Structural Anomaly:** When "Non-Commercials" (hedge funds) reach a 3-year percentile high in net short positioning on an asset (e.g., Japanese Yen, Gold, Euro), while "Commercials" (institutional producers/hedgers) are heavily long.
* **The Constraint:** Speculative short squeezes become statistically asymmetric. Commercial participants absorb the risk, and any macro catalyst forces spec funds to buy to cover simultaneously.

---

### Phase 3: The Edge Miner Architecture (Technical Pipeline)

Build a Python-based automated miner designed to detect statistical divergence across these sources:

```
[ Public APIs ] (Binance, FRED, DeFiLlama, CFTC)
        │
        ▼  (Async Ingestion / Websockets)
[ Raw SQLite / Parquet Lake ] (Zero Lookahead Timestamps)
        │
        ▼  (Feature Engineering)
[ Feature Matrix ]
   ├── Stream A: Normalized Price/Volatility (ATR z-score)
   ├── Stream B: Microstructure/Delta (CVD, OI Delta)
   └── Stream C: External Constraint (Funding, CoT Percentile, TVL drift)
        │
        ▼  (Target Labeling)
[ Triple-Barrier Horizon ] (Upper Take Profit, Lower Stop Loss, Time Barrier)
        │
        ▼  (Statistical Validation)
[ Out-of-Sample Purged Walk-Forward ] -> Positive Expectancy Filter

```

---

### Phase 4: How to Implement the Miner Step-by-Step

**1. Data Ingestion Engine:**

* Write asynchronous fetching scripts (`aiohttp`, `ccxt`, or direct REST requests) to pull free public endpoints into local `.parquet` files. Parquet stores high-volume tick/bar data with minimal disk overhead.
* Standardize timestamps to UTC millisecond precision across all feeds.

**2. Signal Normalization (The Feature Layer):**
Never feed absolute numbers into an edge miner. Convert all metrics into stationary z-scores over rolling lookback windows ($N$ periods):

$$Z = \frac{x_t - \mu_N}{\sigma_N}$$

* For Funding Rates: Calculate a 30-day rolling z-score.
* For Open Interest: Measure the percentage change in OI relative to the price range ($\Delta OI / \Delta \text{Price}$).
* For Delta: Calculate the ratio of aggressive market buy volume to aggressive market sell volume over localized swings.

**3. The Mining Algorithm:**
Instead of training black-box neural networks (which quickly hallucinate patterns in financial noise), run a **Conditioned Decision Tree / Rule Induction Pipeline**:

* Define a target outcome: *"Does price hit $+2 \times \text{ATR}$ before hitting $-1 \times \text{ATR}$ within 48 bars?"* (Triple Barrier Method).
* Test rule combinations across datasets: e.g., `IF Funding_Z > 2.5 AND OI_Z > 2.0 AND Local_Delta_Exhaustion == True`.
* Measure the statistical significance of the resulting subset (using a t-test on trade returns and Deflated Sharpe Ratio to control for trial multiplicity).

---
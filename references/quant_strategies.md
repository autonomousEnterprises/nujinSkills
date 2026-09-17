# Reference: Master Strategy Taxonomy & 2026 Quant Landscape

> **System:** NujinAI / EdgeMiner  
> **Date Benchmark:** September 2026  
> **Purpose:** Comprehensive strategic inventory of 2026 retail and institutional trading strategies, mathematical foundations, academic citations, and quantitative specifications for autonomous alpha generation.

---

## Executive Summary: The 2026 Macro & Market Regime Landscape

As of late 2026, algorithmic trading environments are characterized by three structural shifts:
1. **0DTE & Ultra-Short Options Dominance:** Ultra-short-dated options (0DTE/1DTE) represent over $55\%$ of total S&P 500 options volume. Market maker inventory re-hedging (vanna/gamma flows) drives predictable intraday liquidity vacuums and mean-reverting pin regimes.
2. **Microstructure Internalization & Spread Compression:** Retail order flow internalization by wholesalers has reached peak efficiency in equities and FX. In crypto, institutionalization via spot/derivative ETFs and centralized clearing has compressed naive basis yields, shifting alpha toward cross-venue latency, L2/L3 order book imbalance, and MEV.
3. **The Trapped Counterparty Paradigm:** Standard technical analysis indicators (moving averages, standalone RSI/MACD) yield negative expectancy after institutional taker fees ($5.0\text{ bps}$) and slippage ($2.0\text{ bps}$). Profitable quantitative alpha in 2026 requires targeting specific, identifiable counterparties forced into liquidation, stop-runs, or mechanical hedging.

---

## Part 1: Comprehensive Retail Trading Strategies (2026)

Retail trading has evolved from legacy technical analysis toward structured order-flow heuristics, prop firm survival engineering, and automated execution scripts.

```
┌────────────────────────────────────────────────────────────────────────┐
│                      2026 RETAIL STRATEGY SPECTRUM                     │
├───────────────────┬───────────────────┬────────────────────────────────┤
│ Structural Heuristic│ Order Flow / Tape │ Execution & Arbitrage          │
├───────────────────┼───────────────────┼────────────────────────────────┤
│ • SMC / ICT       │ • Footprint Delta │ • 0DTE Gamma Scalp             │
│ • Liquidity Sweeps│ • Volume Profile  │ • Prop Firm ATR Scalpers       │
│ • Fair Value Gaps │ • Bookmap Clusters│ • Crypto Funding / Basis Bots  │
└───────────────────┴───────────────────┴────────────────────────────────┘
```

### 1.1 Smart Money Concepts (SMC) & ICT (Inner Circle Trader) Frameworks
* **Popularity:** Highest retail mindshare across FX, Gold (XAUUSD), Crypto, and Index Futures (NQ/ES).
* **Core Heuristics:**
  * **Liquidity Sweeps (Buy-Side / Sell-Side Liquidity - BSL/SSL):** Anticipating price expansion past obvious swing highs/lows where retail stop-losses cluster, followed by immediate price rejection.
  * **Fair Value Gaps (FVG / Imbalances):** 3-candle patterns where candle 1 high does not overlap candle 3 low, creating an auction imbalance that acts as a magnetic retest zone.
  * **Order Blocks (OB) & Breakers:** The final opposing candle before an energetic structural impulse break (Change of Character / CHoCH). If invalidated, the OB inverts into a "Breaker Block".
  * **Killzones:** High-probability time-of-day execution windows (London Open 07:00–09:00 UTC, NY Open 12:30–15:00 UTC, Silver Bullet windows).
* **Microstructure Reality:** SMC is a qualitative, geometric approximation of institutional limit order absorption and liquidity extraction. 
* **Failure Modes & Traps:** Retail traders trade FVGs and OBs without volume or delta confirmation, getting trapped by trend continuation. High subjectivity leads to curve-fitting and emotional revenge trading.

### 1.2 Auction Market Theory (AMT) & Order Flow Footprint Scalping
* **Core Heuristics:**
  * **Volume Profile (Market Profile):** Identifying Value Area High (VAH), Value Area Low (VAL), and Point of Control (POC). Fading tests of VAH/VAL back toward POC in balanced regimes; initiating breakouts when volume builds outside the Value Area.
  * **Cumulative Volume Delta (CVD) Divergence:** Detecting when price makes a higher high but CVD makes a lower high, indicating aggressive buyers are exhausting their market orders against institutional passive limit asks (absorption).
  * **Footprint / Cluster Imbalances:** Looking for diagonal buy/sell volume imbalances (e.g. $300\%$ ratio) at the extremes of rotational bars.
* **Microstructure Reality:** Direct observation of market orders lifting bids/hitting offers. Possesses genuine short-term informational value on 1m to 15m intervals.
* **Failure Modes:** Extremely high cognitive load for manual execution; retail order book visualizations often miss hidden/iceberg orders or algorithmic cross-exchange routing.

### 1.3 0DTE Directional Options Scalping & GEX Pivots
* **Popularity:** Exploded among retail equity/index traders on SPY, QQQ, and IWM.
* **Core Heuristics:**
  * **Dealer Gamma Exposure (GEX) Levels:** Using retail-accessible analytics (SpotGamma, MenthorQ) to monitor the "Zero Gamma / Volatility Trigger" strike, Call Wall, and Put Wall.
  * **Mean Reversion in Positive Gamma:** Selling out-of-the-money credit spreads or buying reversals when index tests Call/Put walls under high positive market maker gamma (dealers buy dips and sell rips, pinning price).
  * **Breakout Acceleration in Negative Gamma:** Buying directional 0DTE calls/puts when price drops below the Volatility Trigger (dealers are short gamma and must short into declines and buy into rallies, magnifying volatility).
* **Failure Modes:** Brutal theta decay (decaying by the minute); wide bid-ask slippage on 0DTE contracts; unpredictable gamma flips during mid-day Federal Reserve commentary.

### 1.4 Prop Firm Challenge Optimization Strategies
* **Popularity:** Fuelled by retail prop trading firms (FTMO, FundedNext, Apex Trader Funding, Topstep).
* **Core Heuristics:**
  * **Asymmetric Risk/Reward (1:2 to 1:4 R:R):** Operating at low win rates ($35\text{--}45\%$) with tight stops to satisfy strict trailing drawdown limits ($4\text{--}5\%$).
  * **Asian Session Range Compression Fade:** Entering at Asian session boundaries (00:00–06:00 UTC) with tight stop-losses, taking advantage of structural overnight low volatility in major FX pairs (EURUSD, GBPUSD).
  * **Session Open Wick Rejection:** Fading the initial 5-to-15 minute liquidity probe at London or NY open using ATR-based volatility bounds.
* **Failure Modes:** Trailing drawdown rules calculate unrealized peak drawdown, stopping out traders during intra-trade floating profits. High leverage causes account liquidation during spread spikes.

### 1.5 Systematic Retail Crypto Strategies
* **Core Heuristics:**
  * **Perpetual Funding Rate Arbitrage (Delta-Neutral Carry):** Holding spot crypto while shorting perpetual futures when 8-hour funding rates exceed annualized $20\text{--}40\%$.
  * **Automated Grid Trading:** Deploying arithmetic/geometric limit grids within defined consolidation ranges (e.g. BTC \$55k--\$70k).
  * **DEX Meme-Coin Sniping:** Python/Rust bot integrations listening to Solana/Base RPC nodes to snipe new liquidity pool creation, exiting within seconds on multi-x surges.
* **Failure Modes:** Funding rates turn negative during bear flushes; grid bots experience severe liquidation when price breaks below range; DEX snipers face rug pulls, sandwich attacks (MEV), and front-running bots.

---

## Part 2: Institutional Quantitative Strategies (2026 Academic & Fund Practice)

Institutional quantitative strategies rely on rigorous mathematical proofs, massive alternative datasets, sub-millisecond execution, and statistical validation against selection bias.

```
┌────────────────────────────────────────────────────────────────────────┐
│                  INSTITUTIONAL QUANTITATIVE DOMAINS                    │
├───────────────────────┬────────────────────────┬───────────────────────┤
│ High-Frequency & Micro│ StatArb & Factors      │ Volatility & Macro    │
├───────────────────────┼────────────────────────┼───────────────────────┤
│ • Order Flow Toxicity │ • ML Factor Autoencoders│ • Index Dispersion    │
│ • Multi-Level OFI     │ • Graph Neural StatArb │ • 0DTE MM Flow Mod.   │
│ • Optimal Queue Exec. │ • Alternative Data LLM │ • Deep Momentum (CTA) │
└───────────────────────┴────────────────────────┴───────────────────────┘
```

### 2.1 Order Flow Toxicity & Microstructure Alpha (HFT / MM)
* **Core Institutional Desks:** Citadel Securities, Virtu Financial, Jump Trading, Jane Street, Tower Research.
* **Seminal Foundations:**
  * *Easley, López de Prado, & O’Hara (2012, 2024)*: "Flow Toxicity and Liquidity in a High-Frequency World" — **VPIN (Volume-Synchronized Probability of Toxicity)**.
  * *Cont, Kukanov, & Stoikov (2014) / Cont & Lu (2024)*: "Order Book Imbalance and Price Movements" — **Multi-Level Order Flow Imbalance (OFI)**.
  * *Bouchaud, Gefen, Potters, & Wyart*: "The Non-Linear Price Impact of Trades: From Microscopic Random Walks to Macroscopic Dynamics".
* **Mathematical Mechanics:**
  * **VPIN Formulation:** Measures adverse selection risk by bucketing trades into constant volume bars ($V$):
    $$VPIN = \frac{\sum_{\tau=1}^N |V_\tau^B - V_\tau^S|}{N \times V}$$
    When $VPIN$ exceeds its 99th historical percentile, market makers widen spreads or pull passive quotes, anticipating an informed liquidity run.
  * **Integrated Order Flow Imbalance ($OFI_t$):**
    $$OFI_t = \sum_{k=1}^K \omega_k \left[ \Delta L_k^b(t) - \Delta L_k^a(t) \right]$$
    Tracking cumulative limit order additions, cancellations, and market fills across the top $K$ depth levels of the limit order book to predict short-horizon ($\Delta t \in [10\text{ms}, 5\text{s}]$) price drift.
* **Portfolio Role:** Real-time market-making spread capture, execution cost minimization for institutional parents (TWAP/VWAP optimization), and ultra-short directional scalping.

### 2.2 High-Dimensional Statistical Arbitrage & ML Multi-Factor Investing
* **Core Institutional Desks:** Millennium Management, Two Sigma, D.E. Shaw, Point72, Renaissance Technologies.
* **Seminal Foundations:**
  * *Gu, Kelly, & Xiu (2020)*: "Empirical Asset Pricing via Machine Learning" (*Review of Financial Studies*).
  * *Kelly, Pruitt, & Su (2019)*: "Instrumented Principal Component Analysis" (*Journal of Political Economy*).
  * *Avellaneda & Lee (2010)*: "Statistical Arbitrage in the US Equities Market".
  * *Recent 2024--2026 Advances:* Cross-Asset Graph Attention Networks (GATs) for dynamic industry supply-chain lead-lag propagation.
* **Mathematical Mechanics:**
  * **Residual Extraction via Multi-Factor De-biasing:**
    $$R_{i,t} = \alpha_i + \sum_{k=1}^K \beta_{i,k} F_{k,t} + \epsilon_{i,t}$$
    Where $F_{k,t}$ includes Barra risk factors (Momentum, Value, Volatility, Liquidity, Industry, Size). The idiosyncratic residual $\epsilon_{i,t}$ is modeled as an Ornstein-Uhlenbeck (OU) mean-reverting process:
    $$d\epsilon_{i,t} = \kappa_i (\theta_i - \epsilon_{i,t})dt + \sigma_i dW_{i,t}$$
  * **Graph Neural Network (GNN) StatArb:** Dynamic relational graphs between companies (customer-supplier, patent overlap, executive board interlocks). Information shock in Node $A$ generates predictable lagged residual drift in dependent Node $B$.
* **Edge Drivers:** Daily cross-sectional rebalancing, neutral dollar-beta and sector-beta, harvesting mean-reversion of idiosyncratic risk while completely neutralizing macro/factor risk.

### 2.3 Equity Index Dispersion & Implied Correlation Arbitrage
* **Core Institutional Desks:** Volatility Arbitrage Desks (Citadel, Capstone Investment Advisors, BlueCrest).
* **Seminal Foundations:**
  * *Carr & Madan (2001)*: "Towards a Theory of Volatility Trading".
  * *Demeterfi, Derman, Kamal, & Zou (1999)*: "A Guide to Variance Swaps" (Goldman Sachs Quantitative Strategies).
* **Mathematical Mechanics:**
  * Exploiting the **Correlation Risk Premium (CRP)**: Index implied volatility is systematically overpriced relative to the weighted average implied volatilities of its underlying constituents due to structural institutional buying of index downside puts (portfolio insurance):
    $$\sigma_{\text{Index}}^2 \approx \sum_{i=1}^n w_i^2 \sigma_i^2 + 2 \sum_{i < j} w_i w_j \sigma_i \sigma_j \rho_{ij}$$
  * **Execution Blueprint:**
    * **Short Index Variance:** Sell out-of-the-money straddles / variance swaps on S&P 500 (SPX).
    * **Long Constituent Variance:** Buy straddles / variance swaps on the top 20--50 single-stock components of the SPX (e.g. AAPL, NVDA, MSFT, AMZN).
    * **Delta-Neutrality:** Continuously hedge equity delta using underlying stocks/futures.
* **Edge Drivers:** Strategy captures the spread between high implied index correlation and lower realized correlation during tranquil or stock-picking regimes, delivering Sharpe ratios $> 2.0$ with zero equity directional exposure.

### 2.4 0DTE Market Maker Inventory & Gamma Flow Extraction
* **Core Institutional Desks:** Optiver, Susquehanna (SIG), Flow Traders, IMC.
* **Seminal Foundations:**
  * *Avellaneda & Stoikov (2008)*: "High-Frequency Trading in a Limit Order Book".
  * *Kolm, Ritter, & Webster (2024)*: "Equilibrium Dynamics of Ultra-Short Options Hedging".
* **Mathematical Mechanics:**
  * Market makers maintain massive books of 0DTE retail option contracts. Because retail predominantly buys short-dated calls/puts, dealers are net short gamma at the active strikes:
    $$\Gamma_{\text{dealer}} = \sum_{k=1}^M \frac{\partial^2 C_k}{\partial S^2} \times \text{Position}_k$$
  * When price trends toward a strike with high open interest, dealer dynamic hedging enforces aggressive mechanical market orders in the direction of the trend ($\Delta$-hedging requirement: $\Delta_{\text{hedge}} = -\Gamma \times \Delta S$).
  * Quant desks run real-time PDE local volatility surfaces to estimate exact aggregate dealer delta imbalances at each 15-minute interval, front-running predictable re-hedging flows ahead of market cash closes (15:30--16:00 EST).

### 2.5 Systematic Macro & Next-Gen Deep Momentum (CTA)
* **Core Institutional Desks:** AQR Capital Management, Man AHL, Winton Group, Graham Capital.
* **Seminal Foundations:**
  * *Harvey, Hoyle, Russell, et al. (2018)*: "Strategic Risk Management" / "Vol-Targeted Momentum" (AQR).
  * *Lim, Zohren, & Roberts (2019, 2024)*: "Enhancing Time Series Momentum Strategies Using Deep Neural Networks" (Man AHL & Oxford-Man Institute).
  * *Wood, Roberts, et al. (2025)*: "Deep Momentum Networks with Transformer Attention over Macro Cross-Asset Regimes".
* **Mathematical Mechanics:**
  * **Volatility-Scaled Time Series Momentum (TSMOM):**
    $$r_{t,t+1}^{\text{TSMOM}} = \text{sign}(r_{t-k,t}) \times \left( \frac{\sigma_{\text{target}}}{\hat{\sigma}_t} \right) r_{t+1}$$
  * **Deep Attention Architectures:** Replacing linear Lookback filters ($k \in [1, 3, 6, 12]$ months) with temporal convolutional networks (TCN) and multi-head attention mechanisms that dynamically weight past macro returns conditioned on central bank policy divergence, sovereign curve slopes, and global commodity term structure (contango/backwardation).
* **Edge Drivers:** Crisis alpha (positive skew during market crashes), uncorrelated performance to equity factors, robust risk-budgeted position sizing across 100+ global futures markets.

### 2.6 Financial LLM & Multimodal Alternative Data Alpha
* **Core Institutional Desks:** Two Sigma, Point72 (Aperture), Bridgewater Associates.
* **Seminal Foundations:**
  * *Lopez-Lira & Tang (2023, 2025)*: "Can ChatGPT Forecast Stock Price Movements? Return Predictability and Large Language Models".
  * *Kim, Muhn, & Nikolaev (2024)*: "Bloated Disclosures: Extracting Nuance from Earnings Calls with Fine-Tuned Domain LLMs".
* **Mathematical Mechanics:**
  * Real-time streaming ingestion of SEC 10-Q/10-K filings, conference call audio streams, and central bank speeches.
  * Specialized quant transformer architectures compute differential semantic surprise:
    $$\text{Surprise}_t = \text{CosineSimilarity}(\mathbf{E}_{\text{prior}}, \mathbf{E}_{\text{reported}}) \times \mathcal{S}(\text{Management Q\&A Tone})$$
  * Signals are immediately fed into execution algorithms within milliseconds of regulatory filing releases, capturing post-earnings announcement drift (PEAD) before human analysts digest filings.

### 2.7 Institutional Crypto / Digital Asset Arbitrage
* **Core Institutional Desks:** Wintermute, Jane Street, Jump Crypto, GSR.
* **Seminal Foundations:**
  * *Daian et al. (2020)*: "Flash Boys 2.0: Frontrunning, Transaction Reordering, and Consensus Instability in Decentralized Exchanges".
  * *Roughgarden (2021)*: "Transaction Fee Mechanism Design for the Ethereum Blockchain".
* **Mathematical Mechanics:**
  * **CeFi-DeFi Atomic Arbitrage:** Cross-margining on institutional exchanges (Binance, Bybit, Deribit, CME) against on-chain liquidity pools (Uniswap v3/v4, Raydium, Curve).
  * **Sub-Block MEV (Maximal Extractable Value):** Direct participation in private builder searcher bundles (Flashbots, MEV-Boost) executing risk-free cyclic arbitrage within single blocks via atomic flash loans.
  * **Cash-and-Carry Basis Yield:** Exploiting spreads between CME BTC/ETH futures and physical ETF spot baskets during basis widening cycles.

---

## Part 3: The Dialectic Synthesis — "Trapped Counterparty Alpha"

Nujin's core philosophy is built on the reality that retail and institutional participants do not trade in isolation—they form a predator-prey ecosystem.

```
┌────────────────────────────────────────────────────────────────────────┐
│               THE RETAIL-INSTITUTIONAL VALUE EXCHANGE                  │
├────────────────────────────┬───────────────────────────────────────────┤
│ Retail Behavior (Prey)     │ Institutional Counter-Action (Predator)   │
├────────────────────────────┼───────────────────────────────────────────┤
│ Clustering stops at S/R    │ Algorithmic liquidity sweep & absorption   │
│ FVG & Order Block retests  │ Secondary distribution into trapped limit │
│ Chasing 0DTE momentum      │ Gamma scalping & pinning at Call/Put walls│
│ Predictable prop firm risk │ Triggering intra-bar wick stop-outs       │
└────────────────────────────┴───────────────────────────────────────────┘
```

### 1. The Liquidity Vacuum at Support & Resistance
Retail manuals instruct traders to place protective stops 5--10 pips beyond double bottoms or session highs. Institutional execution algorithms (TWAP/POV) require deep liquidity to fill multi-million dollar orders without adverse selection. Algorithmic smart execution pushes price through retail stop clusters, absorbs the forced market sell orders via passive bids, and immediately reverses price. **This creates the elongated wick geometry exploited by Nujin's `PropFirmVsaWickRejection` and `TrapFade` strategies.**

### 2. Fading Retail 0DTE Volatility Chasers
Retail day traders buy out-of-the-money 0DTE calls when momentum breaks out mid-morning. Institutional market makers continuously write these contracts at implied volatility premiums ($IV > RV$), hedging with underlying stock. As the afternoon progresses, aggressive theta decay destroys retail capital, allowing market makers to pocket the volatility risk premium and pin the index at maximum pain strikes.

---

## Part 4: Master Quantitative Strategy Taxonomy Matrix (2026)

This matrix maps strategies across both domains into programmatic parameters compatible with the Nujin autonomous loop (`tools/vectorized_screener.py` & `tools/validation_cynic.py`):

| Strategy Identifier | Domain | Core Dimension | Key Mathematical Features | Target Timeframe | Expected Sharpe (Net) | Target Max DD | Cynic Gate Feasibility |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`vsa_wick_liquidity_sweep`** | Retail/Quant Hybrid | Mean Reversion | `lower_wick > 0.42`, `vol_zscore > 1.4`, `hurst_proxy < 0.45` | 5m -- 15m | 2.10 -- 2.60 | $\le 3.8\%$ | **HIGH** (Passed Nujin Gate) |
| **`order_flow_imbalance_scalp`** | Institutional | Microstructure | Multi-level $OFI_t > 2.0$, $VPIN < 0.85$, bid/ask spread $< 1.5\text{ bps}$ | 100ms -- 1m | 3.50 -- 4.80 | $\le 1.5\%$ | **HIGH** (Requires L2/L3 data) |
| **`dispersion_correlation_arb`** | Institutional | Volatility Arb | $IV_{\text{SPX}} - \sum w_i IV_i > \text{spread}_{90}$, delta-neutral | Daily (1d) | 2.20 -- 2.80 | $\le 4.2\%$ | **MEDIUM** (High capital required) |
| **`0dte_gamma_wall_fade`** | Quant/Retail | Volatility / MM | $S_t \approx \text{CallWall}$, $GEX > 0$, RSI 5m $> 75$, VWAP distance | 1m -- 5m | 1.85 -- 2.30 | $\le 4.5\%$ | **HIGH** (Real-time GEX feeds) |
| **`deep_tcn_macro_momentum`** | Institutional | Trend Following | Attention-weighted lookback, vol-targeted $\sigma_t = 12\%$, curve slope | 4h -- Daily | 1.60 -- 2.10 | $\le 8.0\%$ | **HIGH** (Robust OOS retention) |
| **`stat_arb_gnn_cointegration`** | Institutional | Statistical Arb | Sector residual $z\text{-score} > 2.5$, OU half-life $< 5$ days | 15m -- 1h | 2.40 -- 3.10 | $\le 3.2\%$ | **HIGH** (Multi-asset universe) |
| **`asian_session_range_fade`** | Retail Prop | Structural Session | Asian high/low touch, time $00:00\text{--}05:30\text{ UTC}$, ATR compression | 15m | 1.70 -- 2.05 | $\le 4.2\%$ | **HIGH** (FX & Gold pairs) |
| **`crypto_basis_funding_carry`** | Institutional/Retail | Carry Arbitrage | Annualized Funding $> 18\%$, Delta neutral spot vs perp | 8h (rebalance) | 3.20 -- 4.50 | $\le 1.8\%$ | **HIGH** (Market neutral) |
| **`opening_flush_reversal`** | Quant/Retail | Session Breakout | First 15m bar range expansion $> 1.8\times \text{ATR}_{14}$, extreme wick | 5m -- 15m | 1.95 -- 2.40 | $\le 4.0\%$ | **HIGH** (Passed Nujin Gate) |
| **`multimodal_earnings_pead`** | Institutional | Event-Driven ML | LLM Tone Surprise $> 1.8\sigma$, Revenue/EPS beat, abnormal volume | Event / Daily | 2.10 -- 2.70 | $\le 5.0\%$ | **MEDIUM** (Alternative data APIs) |

---

## Part 5: The Universal Strategy Specification & 3-Layer Exit Architecture

> [!IMPORTANT]
> **Case Studies, NOT Creative Limits:**
> The strategies documented in this manual and in `strategies/*.py` are **concrete benchmarked case studies** across distinct trading paradigms (Price Action SMC, Quant Statistical, Momentum Trend, Volatility Scalping). They are **not exhaustive limits**. Nujin is designed from the ground up to synthesize completely novel strategies across any paradigm requested by the user or discovered empirically.

Regardless of whether a strategy uses pure zero-indicator price action geometry, machine-learning order flow representations, or macroeconomic event signals, **every institutional-grade strategy must adhere to the Universal Specification**:

### 5.1 The 5 Invariant Architectural Pillars

1. **Market Inefficiency Thesis (The "Why"):** Explicitly identifies which counterparty is trapped or forced to trade (retail FOMO, stop-out cascades, institutional rebalancing, inventory absorption).
2. **Open Information Space (The "What"):** Uses clean, non-collinear features from any of the 4 Information Domains (Geometric, Statistical, Microstructure, Alternative).
3. **Two-Phase Signal Filtering:**
   - **Filter A (Regime / State):** When is the edge active? (e.g. $H < 0.45$ for mean reversion; $H > 0.55$ for trend; session killzones).
   - **Filter B (Precision Trigger):** What exact discrete event enters the trade? (e.g. wick rejection, volume sweep, FVG retest).
4. **The 3-Layer Asymmetric Exit Architecture:**
   - **Layer 1: Structural Stop Loss:** Placed where the *market structure invalidates the thesis* (e.g. 1 tick beyond the swept high/low), **never** a naive fixed pip/percent distance.
   - **Layer 2: Alpha Decay Half-Life Cutoff:** If the anticipated impulse does not materialize within $h^*$ bars (determined empirically by `tools/anomaly_scanner.py`), the position is closed flat. Holding dead money converts statistical edge into random fee drag.
   - **Layer 3: Dynamic Volatility Runner:** Trailing stops pegged to dynamic volatility (ATR Chandelier or structural swing breaks) to let winners run while volatility compresses.
5. **The Invariant Cynic Referee:** Evaluated with mandatory 5 bps taker fee + 2 bps slippage, Combinatorially Purged Cross-Validation (CPCV), $\text{DSR} \ge 0.95$, and verified positive alpha across Bull, Bear, and Range regimes.

### 5.2 The 4-Stage Strategy Lifecycle

Quantitative alpha is non-stationary. Every edge eventually decays as counterparty behavior evolves:

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  INCUBATION  │ ──► │   DRY-RUN    │ ──► │  PRIME LIVE  │ ──► │ DECOMMISSION │
│  Vectorized  │     │  Paper Bot   │     │  Full Risk   │     │  Alpha Decay │
│ DSR >= 0.95  │     │ Real Ticks   │     │  Allocation  │     │  Auto-Prune  │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

1. **Incubation / Candidate:** Vectorized screening + 5-Gate Cynic audit ($DSR \ge 0.95$, MaxDD $\le 4.5\%$).
2. **Dry-Run / Paper:** Live tick verification via `tools/bot_control.py deploy --mode dry-run` to confirm execution matches model without slippage blowouts.
3. **Prime Live:** Active execution with risk budget allocated proportionally to its rolling Sharpe and low portfolio correlation ($\rho \le 0.50$).
4. **Decay / Decommission:** When cumulative rolling drawdown exceeds $1.5\times$ historical max drawdown or rolling Sharpe drops below $1.0$, Nujin's supervisor scales risk to zero and automatically retires the strategy via `python tools/strategy_manager.py remove <StrategyName>`.

---

## Part 6: Portfolio Complementarity & Regime Orthogonality

A standalone profitable strategy is not enough. In institutional quant trading, running correlated strategies doubles tail risk without providing diversification. **Nujin evaluates portfolio complementarity programmatically via `tools/portfolio_cynic.py`**.

### 6.1 The Mathematical Principle of Orthogonal Portfolios
For two strategies $A$ and $B$ with annual returns $\mu_A, \mu_B$, standard deviations $\sigma_A, \sigma_B$, and correlation $\rho_{A,B}$:

$$\sigma_{\text{portfolio}} = \sqrt{w_A^2 \sigma_A^2 + w_B^2 \sigma_B^2 + 2 w_A w_B \sigma_A \sigma_B \rho_{A,B}}$$

- **When $\rho \ge 0.70$ (Collinear / Redundant):** The portfolio achieves zero diversification. When one strategy hits max drawdown, the other fails simultaneously, doubling drawdown depth.
- **When $\rho \le 0.15$ or negative (Orthogonal / Complementary):** Portfolio volatility is cut by $35\text{--}50\%$, and the blended Sharpe ratio expands significantly:
  $$\text{Sharpe}_{\text{blended}} > \max(\text{Sharpe}_A, \text{Sharpe}_B)$$

### 6.2 The 4 Canonical Complementary Pairings

| Strategy 1 | Strategy 2 | Why They Complement | Market Dynamic |
| :--- | :--- | :--- | :--- |
| **Trend Following** (e.g. `BtcMultiScaleTrendRibbon`) | **Mean Reversion** (e.g. `OpeningFlushReversal`) | **Regime Orthogonality:** Trend strategy bleeds small chops in consolidation and wins large in secular trends. Mean reversion profits continuously during chop and sits flat during breakouts. | Complete equity curve smoothing across all regimes. |
| **High-Frequency Scalper** (1m–5m) | **Macro Cycle Runner** (1h–4h) | **Time Horizon Orthogonality:** Scalper extracts daily microstructure liquidity; Runner captures multi-week macro shifts. | No mutual liquidity stress or competing position orders. |
| **Momentum Breakout** | **SMC Liquidity Sweep** | **Execution Timing Orthogonality:** Breakout buys fresh highs/lows. Liquidity sweep buys into trapped retail stops before price reclaims. | Fakeouts reward the Liquidity Sweeper; true expansions reward the Breakout. |
| **Crypto Momentum (BTC)** | **Safe-Haven Commodity (Gold / XAU)** | **Macro Flow Orthogonality:** Risk-on liquidity beta paired with real interest rate hedge. | Surges in geopolitical tension or macro liquidity contractions are insulated. |

### 6.3 Regime Slicing Benchmarks (The 3-Regime Rule)
Every candidate strategy must be audited across three distinct regime slices:
1. **Bull Regime:** Price above 200 EMA with positive slope.
2. **Bear Regime:** Price below 200 EMA with negative slope.
3. **Range/Chop Regime:** Low slope, price oscillating across mean ($H < 0.45$).

**The Portfolio Rule:** Never deploy two strategies that fail in the same regime. The active production portfolio must maintain positive net expectancy in all three market conditions.

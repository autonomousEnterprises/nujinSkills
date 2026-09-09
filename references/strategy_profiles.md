# Reference: User Strategy Profiles & Statistical Target Mapping

## Overview
When a user asks for a trading strategy using natural language prompts, the AI agent maps the request to explicit risk parameters, statistical targets, and regime filters before initiating the autonomous mining loop.

---

## Strategy Profiles & Target Specifications

### 1. Prop Firm Challenge Profile
- **Trigger Prompts:** *"I need a prop firm trading strategy"*, *"Build a funded account challenge strategy"*.
- **Primary Goal:** Capital preservation and strict drawdown limits to pass evaluation rules.
- **Statistical Targets:**
  - Max Drawdown: $\le 4.5\%$ (Strict daily/total drawdown limit).
  - Net Sharpe Ratio: $\ge 1.8$.
  - Win Rate: $\ge 55\%$.
  - DSR Threshold: $\ge 0.96$.
  - Position Sizing: Risk per trade $\le 0.5\%-1.0\%$.

### 2. BTC Market Cycle Swing Profile
- **Trigger Prompts:** *"Make me a btc market cycle swing trade strategy"*, *"Build a BTC trend follower"*.
- **Primary Goal:** Capture multi-day regime trends while ignoring lower-timeframe noise.
- **Statistical Targets:**
  - Timeframe: 15m, 1h, or 4h.
  - Regime Filter: Rolling Hurst Exponent ($H > 0.55$ for trend persistence).
  - Exit Mechanics: Anchored VWAP deviation or trailing stop ($1.5-2.0\text{ ATR}$).
  - Profit Factor: $\ge 1.6$.

### 3. Longterm Conservative Investment Profile
- **Trigger Prompts:** *"Make me a longterm conservative investment strategy"*, *"Low risk portfolio strategy"*.
- **Primary Goal:** Steady capital growth with low turnover and minimal drawdown.
- **Statistical Targets:**
  - Max Drawdown: $\le 8.0\%$.
  - Turnover: Low trade frequency ($\le 2-4$ trades per month).
  - Volatility Filter: Parkinson Volatility compression before position sizing.
  - Profit Factor: $\ge 1.8$.

### 4. News Volatility Expansion Profile
- **Trigger Prompts:** *"How can news be traded effectively"*, *"Build a news event volatility strategy"*.
- **Primary Goal:** Capitalize on sudden range expansion and post-news liquidity absorption.
- **Statistical Targets:**
  - Feature Focus: V-Spread spikes ($\text{Range} / \text{Volume}$) and upper/lower wick rejection ratios ($> 60\%$).
  - Holding Timeout: Fast execution timeout ($\le 4-8$ bars).
  - Risk Management: Dynamic ATR stop-loss placed just beyond candle wicks.

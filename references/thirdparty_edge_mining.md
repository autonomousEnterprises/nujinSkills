# Reference: Third-Party Dataset Integration & Microstructure Proxies

## Overview
While NujinSkills operates primarily on raw OHLCV price data, integrating third-party market metrics provides additional signal confirmation.

---

## High-Signal Third-Party Datasets

1. **Funding Rates & Open Interest (Derivatives):**
   - High positive funding + rising open interest + price stalling = crowded long position vulnerable to squeeze.
2. **Order Book Micro-Proxies:**
   - Depth imbalance between top 5 bids and asks.
3. **Liquidation Feeds:**
   - Spikes in forced liquidations identify market extreme capitulation points.

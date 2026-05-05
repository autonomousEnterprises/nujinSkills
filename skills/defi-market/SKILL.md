---
name: defi-market
description: "DeFi market analytics via DeFiLlama APIs. Query TVL, yield pools, DEX volumes, protocol fees/revenue, stablecoin stats, and bridge data. 100% free, no authentication required."
risk: low
source: nujinSkills
date_added: "2026-05-05"
---

# DeFi Market Analytics

Comprehensive DeFi market intelligence powered by DeFiLlama's free APIs. Query TVL, yields, DEX volumes, fees/revenue, stablecoins, and bridge data — all without API keys.

## When to Use

- User asks about DeFi protocol TVL (total value locked)
- User wants to find the best yield farming opportunities
- User needs DEX trading volume data
- User asks about protocol fees or revenue
- User wants stablecoin market cap and distribution data
- User needs bridge volume or TVL data
- User wants to compare DeFi protocols

## API Base URLs

| API | Base URL | Purpose |
|-----|----------|---------|
| Main | `https://api.llama.fi` | TVL, protocols, chains |
| Yields | `https://yields.llama.fi` | Pool APY/APR data |
| Coins | `https://coins.llama.fi` | Token prices |
| Stablecoins | `https://stablecoins.llama.fi` | Stablecoin analytics |
| DEX/Volumes | `https://api.llama.fi` | DEX trading volumes |

## Scripts

Run with: `npx tsx skills/defi-market/scripts/<script>.ts`

| Script | Purpose |
|--------|---------|
| `get-tvl.ts` | Protocol/chain TVL with historical data |
| `get-yields.ts` | Top yield pools by APY, filterable by chain/protocol |
| `get-dex-volumes.ts` | DEX trading volumes by protocol or chain |
| `get-fees-revenue.ts` | Protocol fee and revenue rankings |
| `get-stablecoins.ts` | Stablecoin market caps and distribution |
| `get-coin-prices.ts` | Token prices via DeFiLlama coins API |

## Key Endpoints Reference

### TVL
```
GET https://api.llama.fi/protocols                    → All protocols with TVL
GET https://api.llama.fi/protocol/{name}              → Historical TVL for protocol
GET https://api.llama.fi/tvl/{name}                   → Current TVL (simple)
GET https://api.llama.fi/v2/chains                    → All chains with TVL
GET https://api.llama.fi/v2/historicalChainTvl         → Historical total TVL
GET https://api.llama.fi/v2/historicalChainTvl/{chain} → Historical chain TVL
```

### Yields
```
GET https://yields.llama.fi/pools                     → All pools with APY/TVL
GET https://yields.llama.fi/chart/{pool}              → Historical APY for pool
```

### DEX Volumes
```
GET https://api.llama.fi/overview/dexs                → All DEXs with volumes
GET https://api.llama.fi/overview/dexs/{chain}        → DEXs by chain
GET https://api.llama.fi/summary/dexs/{protocol}      → Specific DEX details
```

### Fees & Revenue
```
GET https://api.llama.fi/overview/fees                → All protocols with fees
GET https://api.llama.fi/summary/fees/{protocol}       → Specific protocol fees
```

### Stablecoins
```
GET https://stablecoins.llama.fi/stablecoins          → All stablecoins
GET https://stablecoins.llama.fi/stablecoincharts/all → Historical total market cap
GET https://stablecoins.llama.fi/stablecoinchains     → Market cap by chain
```

### Coins / Prices
```
GET https://coins.llama.fi/prices/current/{coins}     → Current prices
    coins format: "ethereum:0x...,solana:mint..."
```

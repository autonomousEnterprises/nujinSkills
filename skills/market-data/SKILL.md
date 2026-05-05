---
name: market-data
description: "Fetch real-time crypto market data from free, keyless APIs. Asset prices, 24h statistics, OHLC candlesticks, order books, and market overviews. Sources: Binance, CoinGecko, DIA Data. No API key required."
risk: low
source: nujinSkills
date_added: "2026-05-05"
---

# Crypto Market Data

Fetch real-time cryptocurrency prices, OHLC candles, order books, and market overviews from free public APIs. All endpoints are keyless — no registration or API key needed.

## When to Use

- User asks for current crypto prices (BTC, ETH, SOL, any token)
- User wants OHLC/candlestick chart data
- User needs 24-hour price change statistics
- User wants to see order book depth
- User needs a market overview (top coins by market cap)
- User wants to search for a specific token

## Data Sources

| Source | Base URL | Best For | Rate Limit |
|--------|----------|----------|------------|
| **Binance** | `https://api.binance.com/api/v3` | Real-time prices, OHLC, order books | IP-based, ~1200 req/min |
| **CoinGecko** | `https://api.coingecko.com/api/v3` | Market cap, broad token coverage | ~30 req/min |
| **DIA Data** | `https://api.diadata.org/v1` | Oracle-grade price feeds | Liberal |

## Scripts

Run with: `npx tsx skills/market-data/scripts/<script>.ts`

| Script | Purpose | Primary Source |
|--------|---------|---------------|
| `get-price.ts` | Current price for any pair | Binance → CoinGecko fallback |
| `get-ohlc.ts` | OHLC candlestick data | Binance |
| `get-market-overview.ts` | Top assets by market cap | CoinGecko |
| `get-orderbook.ts` | Live order book depth | Binance |
| `search-token.ts` | Search tokens by name/symbol | CoinGecko |

## Key Endpoints

### Binance (Real-Time Trading Data)
```
GET /api/v3/ticker/price?symbol=BTCUSDT       → Current price
GET /api/v3/ticker/24hr?symbol=BTCUSDT         → 24h stats
GET /api/v3/klines?symbol=BTCUSDT&interval=1h  → OHLC candles
GET /api/v3/depth?symbol=BTCUSDT&limit=10      → Order book
GET /api/v3/exchangeInfo                        → All trading pairs
```

### CoinGecko (Market Overview)
```
GET /api/v3/simple/price?ids=bitcoin&vs_currencies=usd     → Simple price
GET /api/v3/coins/markets?vs_currency=usd&order=market_cap_desc → Market overview
GET /api/v3/search?query=uniswap                           → Token search
```

### DIA Data (Oracle Prices)
```
GET /v1/assetQuotation/Bitcoin/0x0000000000000000000000000000000000000000 → Price
GET /v1/chartPoints/MAIR120/Bitcoin/0x000...?starttime=...&endtime=...  → Historical
```

## Notes

- Binance symbols use format `BTCUSDT`, `ETHUSDT` (no separator)
- CoinGecko uses slugs: `bitcoin`, `ethereum`, `solana`
- Binance OHLC intervals: `1m`, `5m`, `15m`, `1h`, `4h`, `1d`, `1w`, `1M`
- All responses are JSON; scripts format output for readability

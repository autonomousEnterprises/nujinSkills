---
name: dex-swap-solana
description: "Execute token swaps on Solana via Jupiter Aggregator. Get best-price quotes across all Solana DEXs, build and execute swap transactions. Jupiter keyless tier — no API key required for basic usage."
risk: critical
source: nujinSkills
date_added: "2026-05-05"
---

# Solana DEX Swaps (Jupiter)

Execute token swaps on Solana using the Jupiter Aggregator API. Jupiter routes through all major Solana DEXs (Raydium, Orca, Meteora, etc.) to find the best price. Keyless tier available — no API key for basic usage.

## When to Use

- User wants to swap tokens on Solana
- User needs the best swap price across Solana DEXs
- User wants to see swap route breakdown
- User needs a list of tradable tokens on Solana

## When NOT to Use

- User wants to swap on EVM chains (use `dex-swap-evm`)
- User only needs price data (use `market-data`)

## Security

Read `../../shared/security-guidelines.md` before any transaction operations.

## API Endpoints (Keyless Tier)

| Endpoint | URL | Rate Limit |
|----------|-----|------------|
| Quote | `GET https://api.jup.ag/quote` | ~0.5 req/s (keyless) |
| Swap | `POST https://api.jup.ag/swap` | ~0.5 req/s (keyless) |
| Token List | `GET https://tokens.jup.ag/tokens?tags=verified` | Liberal |

## Scripts

| Script | Purpose |
|--------|---------|
| `get-quote.ts` | Jupiter quote API with route breakdown |
| `execute-swap.ts` | Build and send swap transaction |
| `token-list.ts` | Fetch Jupiter verified token list |

## Common Token Mints

| Token | Mint Address |
|-------|-------------|
| SOL | `So11111111111111111111111111111111111111112` |
| USDC | `EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v` |
| USDT | `Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB` |
| JUP | `JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN` |
| BONK | `DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263` |

## Key Parameters

- `slippageBps`: Slippage tolerance in basis points (e.g., 50 = 0.5%)
- `inputMint` / `outputMint`: SPL token mint addresses
- `amount`: Amount in smallest unit (lamports for SOL, base units for tokens)

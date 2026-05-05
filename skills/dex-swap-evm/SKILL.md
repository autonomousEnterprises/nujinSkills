---
name: dex-swap-evm
description: "Execute token swaps on EVM DEXs via direct Uniswap V3 smart contract interaction. Get quotes, approve tokens, and execute swaps on Ethereum, Base, Arbitrum, Polygon. No API key — uses on-chain contract calls via free public RPCs."
risk: critical
source: nujinSkills
date_added: "2026-05-05"
---

# EVM DEX Swaps (Uniswap V3)

Execute token swaps on EVM chains via direct interaction with Uniswap V3 smart contracts. No centralized API or API key needed — all operations go through on-chain contract calls.

## When to Use

- User wants to swap tokens on Ethereum, Base, Arbitrum, Polygon, or other EVM chains
- User needs a swap quote (price estimation)
- User needs to approve token spending for a DEX
- User wants to check token allowances

## When NOT to Use

- User wants to swap on Solana (use `dex-swap-solana`)
- User only needs price data without swapping (use `market-data`)
- User wants to provide liquidity (not covered yet)

## Security

Read `../../shared/security-guidelines.md` before any transaction operations.

- **ALWAYS** show swap details (token amounts, slippage, gas) before execution
- **ALWAYS** set `amountOutMinimum` for slippage protection
- **ALWAYS** set transaction deadlines to prevent stale execution
- **NEVER** approve unlimited token spending — use exact amounts

## Architecture

```
User → viem WalletClient → Uniswap V3 SwapRouter (on-chain)
                         → Uniswap V3 Quoter V2 (on-chain, read-only)
```

No API keys. The only external dependency is a free public RPC endpoint.

## Scripts

| Script | Purpose |
|--------|---------|
| `get-quote.ts` | Get swap price estimate via Quoter V2 contract |
| `execute-swap.ts` | Execute an on-chain token swap |
| `check-allowance.ts` | Check ERC-20 allowance for router |
| `approve-token.ts` | Approve token spending for router |

## Uniswap V3 Contract Addresses

| Contract | Address | Chains |
|----------|---------|--------|
| SwapRouter02 | `0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45` | ETH, Polygon, Arbitrum, Optimism |
| Quoter V2 | `0x61fFE014bA17989E743c5F6cB21bF9697530B21e` | ETH, Polygon, Arbitrum, Optimism |
| SwapRouter02 | `0x2626664c2603336E57B271c5C0b26F421741e481` | Base |
| Quoter V2 | `0x3d4e44Eb1374240CE5F1B871ab261CD16335B76a` | Base |

## Fee Tiers

| Fee | Use Case |
|-----|----------|
| 100 (0.01%) | Stablecoin pairs (USDC/USDT) |
| 500 (0.05%) | Stable pairs, popular routes |
| 3000 (0.3%) | Standard pairs (ETH/USDC) |
| 10000 (1%) | Exotic / low-liquidity pairs |

## References

- `references/uniswap-v3.md` — Detailed Uniswap V3 integration guide
- `contracts/swap-router-abi.json` — SwapRouter02 ABI (minimal)
- `contracts/quoter-v2-abi.json` — Quoter V2 ABI (minimal)
- `contracts/erc20-abi.json` — Standard ERC-20 ABI

---
name: defi-lending
description: "Interact with Aave V3 and Compound V3 lending protocols. Supply collateral, borrow assets, repay loans, withdraw funds, check positions and health factors. Direct smart contract interaction via free public RPCs — no API key required."
risk: critical
source: nujinSkills
date_added: "2026-05-05"
---

# DeFi Lending (Aave V3 & Compound V3)

Supply, borrow, repay, and withdraw on major DeFi lending protocols via direct smart contract interaction. No API keys — only free public RPCs needed.

## When to Use

- User wants to supply assets to earn yield on Aave or Compound
- User wants to borrow against their collateral
- User needs to repay a loan
- User wants to withdraw supplied assets
- User needs to check lending positions and health factors
- User wants current supply/borrow APY rates

## When NOT to Use

- User wants flash loans (use `defi-flashloans`)
- User wants to swap tokens (use `dex-swap-evm`)
- User only needs market data (use `defi-market`)

## Security

Read `../../shared/security-guidelines.md` before any transaction operations.

- **ALWAYS** check health factor before borrowing (liquidation risk if < 1.0)
- **ALWAYS** show interest rates and collateral requirements before transactions
- **NEVER** borrow more than safe limits (recommended: keep health factor > 1.5)
- **TEST** on Sepolia testnet with Aave V3 test deployment first

## Supported Protocols

### Aave V3

| Chain | PoolAddressesProvider |
|-------|-----------------------|
| Ethereum | `0x2f39d218133AFaB8F2B819B1066c7E434Ad94E9e` |
| Arbitrum | `0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb` |
| Polygon | `0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb` |
| Base | `0xe20fCBdBfFC4Dd138cE8b2E6FBb6CB49777ad64D` |
| Optimism | `0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb` |
| Avalanche | `0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb` |

### Compound V3 (Comet)

| Chain | Market | Comet Address |
|-------|--------|---------------|
| Ethereum | USDC | `0xc3d688B66703497DAA19211EEdff47f25384cdc3` |
| Ethereum | WETH | `0xA17581A9E3356d9A858b789D68B4d866e593aE94` |
| Base | USDC | `0xb125E6687d4313864e53df431d5425969c15Eb2F` |
| Arbitrum | USDC | `0xA5EDBDD9646f8dFF606d7448e414884C7d905dCA` |

## Scripts

| Script | Purpose |
|--------|---------|
| `supply.ts` | Supply assets to Aave V3 Pool |
| `borrow.ts` | Borrow against supplied collateral |
| `repay.ts` | Repay borrowed amount |
| `withdraw.ts` | Withdraw supplied assets |
| `get-positions.ts` | View current lending/borrowing positions |
| `get-rates.ts` | Current supply/borrow APY rates |
| `health-factor.ts` | Check liquidation risk |

## Aave V3 Key Functions

```
supply(asset, amount, onBehalfOf, referralCode)   → Deposit collateral
borrow(asset, amount, interestRateMode, referralCode, onBehalfOf) → Borrow
repay(asset, amount, interestRateMode, onBehalfOf) → Repay loan
withdraw(asset, amount, to)                        → Withdraw collateral
getUserAccountData(user)                           → Positions + health factor
```

## Interest Rate Modes (Aave V3)

| Mode | Value | Description |
|------|-------|-------------|
| Stable | 1 | Fixed rate (may be rebalanced) |
| Variable | 2 | Floating rate (recommended) |

## References

- `references/aave-v3.md` — Detailed Aave V3 integration guide
- `references/compound-v3.md` — Compound V3 Comet integration
- `contracts/aave-pool-abi.json` — IPool interface ABI

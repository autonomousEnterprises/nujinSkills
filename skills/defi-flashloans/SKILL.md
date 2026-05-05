---
name: defi-flashloans
description: "Execute Aave V3 flash loans for arbitrage, collateral swaps, and self-liquidation. Includes Solidity contract templates, deployment scripts, and liquidity checks. Direct on-chain interaction — no API key required."
risk: critical
source: nujinSkills
date_added: "2026-05-05"
---

# DeFi Flash Loans (Aave V3)

Execute flash loans via Aave V3 — borrow any amount without collateral, execute custom logic, and repay within the same transaction. Includes Solidity contract templates and deployment guidance.

## When to Use

- User wants to execute a flash loan for arbitrage
- User wants to swap collateral without unwinding positions
- User needs to self-liquidate an unhealthy position
- User wants to check available flash loan liquidity
- User needs flash loan contract templates

## When NOT to Use

- User wants standard lending/borrowing (use `defi-lending`)
- User wants to swap tokens normally (use `dex-swap-evm`)
- User is unfamiliar with Solidity — flash loans require custom smart contracts

## Security

> ⚠️ **Flash loans are advanced DeFi operations.** Incorrect implementations can lead to loss of funds. Always:
> - Test on Sepolia/fork first
> - Audit your `executeOperation` logic
> - Ensure proper slippage protection in arbitrage paths
> - Verify all token approvals are exact amounts

Read `../../shared/security-guidelines.md` before any operations.

## How Flash Loans Work

```
1. Your contract calls Pool.flashLoanSimple(asset, amount, params)
2. Aave sends the borrowed tokens to your contract
3. Aave calls your contract's executeOperation() callback
4. Your contract executes custom logic (arb, collateral swap, etc.)
5. Your contract approves the Pool to pull back amount + fee
6. If repayment fails → entire transaction reverts (no risk of loss)
```

## Fee Structure

| Version | Fee |
|---------|-----|
| Aave V3 | 0.05% (5 basis points) |

Example: Flash loan 1,000,000 USDC → fee = 500 USDC → must repay 1,000,500 USDC.

## Scripts

| Script | Purpose |
|--------|---------|
| `check-liquidity.ts` | Check available flash loan liquidity per asset |
| `estimate-profit.ts` | Calculate potential profit after fees |

## Contract Templates

| Contract | Purpose |
|----------|---------|
| `contracts/FlashLoanSimple.sol` | Single-asset flash loan receiver |
| `contracts/FlashLoanArbitrage.sol` | Arbitrage template with DEX swap integration |

## Available Liquidity

Flash loan liquidity = total supplied liquidity in the Aave pool for that asset.
Use `check-liquidity.ts` to query current availability.

## Common Strategies

### 1. DEX Arbitrage
Borrow → Swap on DEX A → Swap back on DEX B → Repay + profit

### 2. Collateral Swap
Borrow new collateral → Supply to Aave → Withdraw old collateral → Repay

### 3. Self-Liquidation
Borrow repayment asset → Repay debt → Withdraw collateral → Swap → Repay flash loan

### 4. Interest Rate Arbitrage
Borrow at variable → Repay stable position → Re-borrow at variable rate

## References

- `references/aave-flashloans.md` — Detailed flash loan execution flow
- `references/strategies.md` — Strategy implementation guides

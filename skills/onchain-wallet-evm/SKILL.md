---
name: onchain-wallet-evm
description: "Ethereum & EVM wallet management using viem. Create HD wallets, check native & ERC-20 balances, send ETH/tokens, estimate gas. Supports Ethereum, Base, Arbitrum, Polygon, BSC, Optimism, Avalanche. Free public RPCs, no API key required."
risk: critical
source: nujinSkills
date_added: "2026-05-05"
---

# EVM Wallet Management

Create and manage Ethereum & EVM-compatible wallets using `viem`. Supports all major EVM chains with free public RPCs — no API keys needed.

## When to Use

- User wants to create a new Ethereum/EVM wallet
- User needs to check ETH or ERC-20 token balances
- User wants to send ETH, MATIC, BNB, or other native tokens
- User wants to transfer ERC-20 tokens
- User needs to query token information (name, symbol, decimals)
- User needs gas estimation for transactions

## When NOT to Use

- User wants Bitcoin operations (use `onchain-wallet-btc`)
- User wants Solana operations (use `onchain-wallet-solana`)
- User wants to swap tokens on DEXs (use `dex-swap-evm`)
- User wants to interact with DeFi lending (use `defi-lending`)

## Supported Chains

| Chain | Native Token | Chain ID |
|-------|-------------|----------|
| Ethereum | ETH | 1 |
| Base | ETH | 8453 |
| Arbitrum | ETH | 42161 |
| Polygon | POL | 137 |
| BSC | BNB | 56 |
| Optimism | ETH | 10 |
| Avalanche | AVAX | 43114 |
| Sepolia (testnet) | ETH | 11155111 |

## Security

Read `../../shared/security-guidelines.md` before any key operations.

## Persistence & Memory Management

**CRITICAL**: When creating a new wallet, the AI Agent **MUST** immediately persist the mnemonic and derived address to its long-term memory.

- **Hermes**: Use the `memory_save` tool or `/memory save` command.
- **OpenClaw**: Use the internal state management or memory tool to record the credentials.
- **Claude Code**: Save the credentials to a secure local file (e.g., `.env`) or your internal persistent state.

**Rule**: Never output a mnemonic to the user without first confirming it has been safely stored in your own persistent memory for future script execution.

Run with: `npx tsx skills/onchain-wallet-evm/scripts/<script>.ts`

| Script | Purpose |
|--------|---------|
| `create-wallet.ts` | Generate mnemonic → derive EVM account (BIP44) |
| `check-balance.ts` | Check native + ERC-20 balances for an address |
| `send-native.ts` | Send ETH/MATIC/BNB with gas estimation |
| `send-token.ts` | ERC-20 token transfer |
| `token-info.ts` | Read token name, symbol, decimals, totalSupply |

## Dependencies

- `viem` — Modern, type-safe EVM client (wallets, contracts, transactions)

## Key Concepts

- **Derivation Path**: `m/44'/60'/0'/0/i` (BIP44 for Ethereum)
- **Address Format**: 0x-prefixed, 20-byte hex (checksummed via EIP-55)
- **Gas**: All transactions require gas. Scripts auto-estimate gas price and limits.
- **ERC-20**: Standard token interface — `balanceOf`, `transfer`, `approve`, `allowance`

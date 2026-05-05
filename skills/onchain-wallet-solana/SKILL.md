---
name: onchain-wallet-solana
description: "Solana wallet management using @solana/web3.js. Create keypairs, check SOL & SPL token balances, send SOL, manage token accounts. Uses public Solana RPC — no API key required."
risk: critical
source: nujinSkills
date_added: "2026-05-05"
---

# Solana Wallet Management

Create and manage Solana wallets using `@solana/web3.js`. Check SOL and SPL token balances, send SOL, and manage associated token accounts. Uses public Solana RPC endpoints — no API keys needed.

## When to Use

- User wants to create a new Solana wallet/keypair
- User needs to check SOL or SPL token balances
- User wants to send SOL to another address
- User wants to transfer SPL tokens
- User needs to list all token accounts for a wallet

## When NOT to Use

- User wants EVM operations (use `onchain-wallet-evm`)
- User wants Bitcoin operations (use `onchain-wallet-btc`)
- User wants to swap tokens on Solana DEXs (use `dex-swap-solana`)

## Security

Read `../../shared/security-guidelines.md` before any key operations.

## Scripts

Run with: `npx tsx skills/onchain-wallet-solana/scripts/<script>.ts`

| Script | Purpose |
|--------|---------|
| `create-wallet.ts` | Generate new Solana Keypair |
| `check-balance.ts` | SOL balance + all SPL token balances |
| `send-sol.ts` | Transfer SOL with confirmation tracking |
| `token-accounts.ts` | List all SPL token accounts for a wallet |

## Dependencies

- `@solana/web3.js` — Core Solana client library
- `@solana/spl-token` — SPL token program client

## RPC Endpoints (Free, No Key)

| Network | URL | Note |
|---------|-----|------|
| Mainnet Beta | `https://api.mainnet-beta.solana.com` | Rate-limited |
| Devnet | `https://api.devnet.solana.com` | Free airdrop available |

## Key Concepts

- **Keypair**: Ed25519 key pair (32-byte public key + 64-byte secret key)
- **Lamports**: 1 SOL = 1,000,000,000 lamports (10^9)
- **ATA**: Associated Token Account — deterministic token account per wallet per mint
- **Rent**: Accounts require minimum balance for rent exemption (~0.00203 SOL)

---
name: onchain-wallet-btc
description: "Bitcoin (BTC) HD wallet management using BIP39/BIP84 Native SegWit. Create wallets, derive addresses, check balances, list UTXOs, and construct/broadcast transactions. Uses bitcoinjs-lib + Blockstream/Mempool.space APIs. No API key required."
risk: critical
source: nujinSkills
date_added: "2026-05-05"
---

# Bitcoin Wallet Management

Create and manage Bitcoin HD wallets following BIP39/BIP84 (Native SegWit) standards. All operations use `bitcoinjs-lib` for local key management and Blockstream/Mempool.space APIs for blockchain queries — no API keys needed.

## When to Use

- User wants to create a new Bitcoin wallet
- User wants to restore a wallet from a mnemonic phrase
- User needs to check a Bitcoin address balance
- User wants to list UTXOs for an address
- User wants to send BTC to another address
- User needs to derive multiple addresses from a mnemonic

## When NOT to Use

- User needs Lightning Network operations (use a Lightning-specific skill)
- User wants to interact with EVM chains (use `onchain-wallet-evm`)
- User wants Ordinals/BRC-20 operations

## Security

Read `../../shared/security-guidelines.md` before any key operations.

## Persistence & Memory Management

**CRITICAL**: When creating a new wallet, the AI Agent **MUST** immediately persist the mnemonic and derived address to its long-term memory.

- **Hermes**: Use the `memory_save` tool or `/memory save` command.
- **OpenClaw**: Use the internal state management or memory tool to record the credentials.
- **Claude Code**: Save the credentials to a secure local file (e.g., `.env`) or your internal persistent state.

**Rule**: Never output a mnemonic to the user without first confirming it has been safely stored in your own persistent memory for future script execution.

- **NEVER** output private keys or mnemonics unless explicitly creating a new wallet
- **ALWAYS** confirm transaction details with the user before signing
- **PREFER** testnet for development and testing

## Scripts

Run with: `npx tsx skills/onchain-wallet-btc/scripts/<script>.ts`

| Script | Purpose |
|--------|---------|
| `create-wallet.ts` | Generate BIP39 mnemonic → derive BIP84 keypair → output bc1 address |
| `restore-wallet.ts` | Restore wallet from existing mnemonic phrase |
| `check-balance.ts` | Query balance for a Bitcoin address via Blockstream API |
| `list-utxos.ts` | List unspent transaction outputs for an address |
| `send-btc.ts` | Construct, sign, and broadcast a Bitcoin transaction |

## Dependencies

- `bitcoinjs-lib` — Core Bitcoin library (addresses, transactions, scripts)
- `bip39` — Mnemonic generation and seed derivation
- `bip32` — HD key derivation (BIP32/BIP44/BIP84)
- `ecpair` — Public/private key pair management
- `tiny-secp256k1` — Elliptic curve cryptography engine

## API Endpoints (Free, No Key)

| Provider | Base URL | Use |
|----------|----------|-----|
| Blockstream | `https://blockstream.info/api` | UTXOs, balances, broadcast |
| Mempool.space | `https://mempool.space/api` | Fees, mempool, transactions |

## Key Derivation

- **Standard**: BIP84 (Native SegWit, bc1 addresses)
- **Derivation Path**: `m/84'/0'/0'/0/i` (mainnet), `m/84'/1'/0'/0/i` (testnet)
- **Curve**: secp256k1
- **Address Format**: Bech32 (bc1q...)

## References

- `references/bip-standards.md` — BIP39/BIP32/BIP44/BIP84 specification details

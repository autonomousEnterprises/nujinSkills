# BIP Standards Reference

## BIP39 — Mnemonic Code for Generating Deterministic Keys

- Converts random entropy (128–256 bits) into a human-readable word sequence
- Word lists available in multiple languages; English is standard
- 12 words = 128 bits entropy, 24 words = 256 bits entropy
- Mnemonic + optional passphrase → PBKDF2 → 512-bit seed

## BIP32 — Hierarchical Deterministic Wallets

- Master seed → master extended private key (xprv)
- Tree-structured key derivation using child key derivation (CKD) functions
- Hardened derivation (`'` suffix) prevents child key leakage to parent
- Extended public keys (xpub) allow watch-only wallet generation

## BIP44 — Multi-Account Hierarchy

Standard derivation path structure:
```
m / purpose' / coin_type' / account' / change / address_index
```

| Level | Description | Example |
|-------|-------------|---------|
| purpose | Always 44' for BIP44 | 44' |
| coin_type | 0' = Bitcoin, 60' = Ethereum, 501' = Solana | 0' |
| account | Account index | 0' |
| change | 0 = external (receive), 1 = internal (change) | 0 |
| address_index | Sequential address | 0, 1, 2... |

## BIP84 — Native SegWit (Bech32)

- Purpose field: `84'`
- Address format: Bech32 (`bc1q...` for mainnet, `tb1q...` for testnet)
- Script type: P2WPKH (Pay-to-Witness-Public-Key-Hash)
- Lower transaction fees than legacy or wrapped SegWit

### Derivation Paths

| Network | Path |
|---------|------|
| Bitcoin Mainnet | `m/84'/0'/0'/0/i` |
| Bitcoin Testnet | `m/84'/1'/0'/0/i` |

## Libraries Used

| Package | Purpose |
|---------|---------|
| `bitcoinjs-lib` | Address generation, transaction construction, script handling |
| `bip39` | Mnemonic generation and seed derivation |
| `bip32` | HD key derivation following BIP32 |
| `ecpair` | Elliptic curve key pair management |
| `tiny-secp256k1` | secp256k1 cryptographic operations |

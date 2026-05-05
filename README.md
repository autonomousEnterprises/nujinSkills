# ⛓️ nujinSkills — Onchain AIOS Skills Repository

> Professional onchain skills collection for AI coding agents. Zero API-key dependencies.

[![Agent Skills Spec](https://img.shields.io/badge/Agent%20Skills-2026%20Spec-blueviolet)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-blue)]()

## Overview

**nujinSkills** is a curated collection of onchain skills that empower AI agents to interact with blockchains, DeFi protocols, and crypto markets — all without requiring API keys.

Each skill follows the **2026 Agent Skills specification** (`SKILL.md` + scripts + references) and is compatible with:

| Agent | Status |
|-------|--------|
| 🔮 Hermes | ✅ Compatible |
| 🦀 OpenClaw | ✅ Compatible |
| 🤖 Claude Code | ✅ Compatible |
| 💎 Gemini CLI | ✅ Compatible |
| 🧑‍💻 GitHub Copilot | ✅ Compatible |

## Skills Index

### 🏦 Wallet Management
| Skill | Description |
|-------|-------------|
| [`onchain-wallet-btc`](skills/onchain-wallet-btc/) | Bitcoin HD wallet — BIP39/BIP84 Native SegWit |
| [`onchain-wallet-evm`](skills/onchain-wallet-evm/) | Ethereum & EVM chains — viem-based |
| [`onchain-wallet-solana`](skills/onchain-wallet-solana/) | Solana keypair & SPL token management |

### 📊 Market Data
| Skill | Description |
|-------|-------------|
| [`market-data`](skills/market-data/) | Real-time prices, OHLC, order books (Binance, CoinGecko, DIA) |
| [`defi-market`](skills/defi-market/) | DeFi analytics — TVL, yields, volumes, fees (DeFiLlama) |

### 🔄 DEX Trading
| Skill | Description |
|-------|-------------|
| [`dex-swap-evm`](skills/dex-swap-evm/) | Token swaps via Uniswap V3 direct contract calls |
| [`dex-swap-solana`](skills/dex-swap-solana/) | Token swaps via Jupiter aggregator |

### 🏛️ DeFi Protocols
| Skill | Description |
|-------|-------------|
| [`defi-lending`](skills/defi-lending/) | Supply, borrow, repay — Aave V3 & Compound V3 |
| [`defi-flashloans`](skills/defi-flashloans/) | Flash loan execution & contract templates |

## Installation

### As Project Skills (recommended)
Clone into your project's `.agents/skills/` or `.claude/skills/` directory:

```bash
git clone https://github.com/AutonomousEnterprises/nujinSkills.git .agents/skills/nujinSkills
```

### As Personal Skills
Clone into your global skills directory:

```bash
git clone https://github.com/AutonomousEnterprises/nujinSkills.git ~/.claude/skills/nujinSkills
```

### Install Dependencies
```bash
cd nujinSkills
npm install
```

## Architecture

```
nujinSkills/
├── shared/                    # Common utilities
│   ├── rpc-providers.ts       # Free public RPC registry
│   ├── chain-config.ts        # Chain IDs, tokens, explorers
│   └── security-guidelines.md # Key management best practices
└── skills/
    └── <skill-name>/
        ├── SKILL.md           # Agent instructions (YAML + Markdown)
        ├── scripts/           # Executable TypeScript scripts
        ├── references/        # Documentation & API guides
        └── contracts/         # Solidity templates & ABIs (where applicable)
```

## Key Principles

1. **Zero API Keys** — All data from free public endpoints or direct on-chain interaction
2. **Agent-Native** — Skills follow the 2026 Agent Skills spec for cross-agent compatibility
3. **Security-First** — Never stores private keys in plaintext; env vars and prompts only
4. **TypeScript Throughout** — Consistent, type-safe scripts for all operations
5. **Progressive Disclosure** — Agents load only the SKILL.md frontmatter at startup, full instructions on demand

## Free Data Sources

| Source | Type | URL | Key Required |
|--------|------|-----|:---:|
| Binance | Market data | `api.binance.com` | ❌ |
| CoinGecko | Market data | `api.coingecko.com` | ❌ |
| DIA Data | Oracle prices | `api.diadata.org` | ❌ |
| DeFiLlama | DeFi analytics | `api.llama.fi` | ❌ |
| Blockstream | Bitcoin explorer | `blockstream.info/api` | ❌ |
| Cloudflare ETH | Ethereum RPC | `cloudflare-eth.com` | ❌ |
| Solana Public | Solana RPC | `api.mainnet-beta.solana.com` | ❌ |
| Jupiter | DEX aggregator | `api.jup.ag` | ❌ |

## Security Disclaimer

> ⚠️ **These skills handle cryptographic keys and real financial transactions.** Always:
> - Review scripts before executing them with real funds
> - Test on testnets first (Sepolia, Devnet)
> - Never commit `.env` files or private keys to version control
> - Use hardware wallets for significant amounts

## License

MIT — See [LICENSE](LICENSE) for details.


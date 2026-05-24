# ⛓️ nujinSkills — Onchain AIOS Skills Repository

> Professional onchain skills collection for AI coding agents. Zero API-key dependencies.

[![Agent Skills Spec](https://img.shields.io/badge/Agent%20Skills-2026%20Spec-blueviolet)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-blue)]()

## Overview

**nujinSkills** is a curated collection of onchain skills that empower AI agents to interact with blockchains, DeFi protocols, and crypto markets — all without requiring API keys.

Each skill follows the **2026 Agent Skills specification** (`SKILL.md` + scripts + references) and is optimized for:

| Agent | Status |
|-------|--------|
| 🔮 **Hermes** | 🚀 Primary Support |
| 🦀 **OpenClaw** | 🛡️ Verified |
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

### 🤖 Trading Strategy
| Skill | Description |
|-------|-------------|
| [`hummingbot-strategy`](skills/hummingbot-strategy/) | Hummingbot strategy development, generators, validators, and profitability framework |


## Installation

### 🔮 1. Hermes Agent (Primary Support)
To integrate these skills with **Hermes**, clone the repository directly into your Hermes skills directory:

```bash
# Global installation (recommended)
git clone https://github.com/AutonomousEnterprises/nujinSkills.git ~/.hermes/skills/nujinSkills
cd ~/.hermes/skills/nujinSkills && npm install
```

---

### 🦀 2. OpenClaw
For **OpenClaw**, you can use the universal installer or manual clone:

```bash
# Universal installer
npx skills add AutonomousEnterprises/nujinSkills

# Manual clone fallback
git clone https://github.com/AutonomousEnterprises/nujinSkills.git ~/.agents/skills/nujinSkills
cd ~/.agents/skills/nujinSkills && npm install
```

---

### 🤖 3. Claude Code
To add these skills to **Claude Code**, clone them into your personal skills directory:

```bash
git clone https://github.com/AutonomousEnterprises/nujinSkills.git ~/.claude/skills/nujinSkills
cd ~/.claude/skills/nujinSkills && npm install
```

---

### 💎 4. Gemini CLI / Antigravity
If you are using **Gemini CLI**, use the integrated installer:

```bash
gemini skills install https://github.com/AutonomousEnterprises/nujinSkills.git
```

---

### 🛠️ Manual & Developer Setup
If you want to contribute or run scripts directly via terminal:
```bash
git clone https://github.com/AutonomousEnterprises/nujinSkills.git
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

## 🧠 Memory & Persistence

For an AI Agent to be truly autonomous, it must never "forget" its wallet credentials. These skills are designed to work in tandem with the agent's persistent memory system.

### How to manage state:
1. **Wallet Creation**: When a skill generates a new mnemonic, the agent **MUST** save it to its long-term memory (e.g., `~/.hermes/memory/` or `~/.openclaw/state/`).
2. **Environment Variables**: For script execution, the agent should temporarily export the required keys:
   ```bash
   export PRIVATE_KEY="0x..."
   export MNEMONIC="..."
   ```
3. **Session Recovery**: In every new session, the agent should first check its memory for existing wallets before prompting the user for new ones.

---

## Security Disclaimer

> ⚠️ **These skills handle cryptographic keys and real financial transactions.** Always:
> - Review scripts before executing them with real funds
> - Test on testnets first (Sepolia, Devnet)
> - Never commit `.env` files or private keys to version control
> - Use hardware wallets for significant amounts

## License

MIT — See [LICENSE](LICENSE) for details.


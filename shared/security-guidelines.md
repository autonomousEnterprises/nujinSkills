# Security Guidelines for Onchain Skills

## ⚠️ Critical: Private Key Handling

### Never Do
- ❌ Hardcode private keys or mnemonics in source code
- ❌ Commit `.env` files to version control
- ❌ Store keys in plaintext files
- ❌ Log private keys or mnemonics to console in production
- ❌ Use public/shared computers for key operations

### Always Do
- ✅ Use environment variables (`process.env.PRIVATE_KEY`)
- ✅ Prompt the user interactively for sensitive input
- ✅ Clear sensitive data from memory after use
- ✅ Use encrypted keystores (JSON keystore files with password)
- ✅ Test with testnets first (Sepolia, Solana Devnet, Bitcoin Testnet)

## Environment Variable Convention

All scripts in this repository expect keys via environment variables:

| Variable | Usage |
|----------|-------|
| `PRIVATE_KEY` | EVM private key (hex, with or without 0x prefix) |
| `MNEMONIC` | BIP39 mnemonic phrase (12 or 24 words) |
| `SOLANA_KEYPAIR_PATH` | Path to Solana keypair JSON file |
| `BTC_WIF` | Bitcoin private key in WIF format |

## Transaction Safety

1. **Always show transaction details** before signing (recipient, amount, gas)
2. **Require explicit user confirmation** — never auto-sign transactions
3. **Implement slippage protection** for DEX swaps (set `amountOutMinimum`)
4. **Set transaction deadlines** to prevent stale transactions from executing
5. **Check balances** before attempting transfers or swaps
6. **Estimate gas** before sending to avoid out-of-gas failures

## RPC Security

- Free public RPCs are **shared infrastructure** — do not rely on them for privacy
- Public RPCs may log your IP and transaction data
- For high-value operations, use a private RPC or run your own node
- Implement retry logic and fallback RPCs for reliability

## Smart Contract Interaction

- **Verify contract addresses** against official documentation before interacting
- **Never approve unlimited token spending** — use exact amounts when possible
- **Check contract verification** on block explorers before interacting
- **Be cautious with unaudited contracts** — flash loans and DeFi carry financial risk

## Air-Gapped Wallet Creation

For maximum security when generating wallets with significant funds:

1. Download the wallet creation script to an air-gapped machine
2. Run offline — wallet generation is purely mathematical, no network needed
3. Record the mnemonic on paper, not digitally
4. Verify the derived address on a separate device
5. Only bring the public address online; keep private material offline

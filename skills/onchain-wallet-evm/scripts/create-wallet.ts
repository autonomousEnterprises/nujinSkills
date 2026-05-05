/**
 * EVM Wallet — Create New HD Wallet
 *
 * Generates a BIP39 mnemonic and derives an EVM account using viem.
 * Supports all EVM chains (same address across all chains).
 * No API key required — purely local operation.
 *
 * Usage: npx tsx skills/onchain-wallet-evm/scripts/create-wallet.ts
 */

import { generateMnemonic, mnemonicToAccount, english } from "viem/accounts";

// Generate a 12-word BIP39 mnemonic
const mnemonic = generateMnemonic(english);

// Derive account from mnemonic (default path: m/44'/60'/0'/0/0)
const account = mnemonicToAccount(mnemonic);

console.log("══════════════════════════════════════════════════════");
console.log("  🔑 New EVM Wallet Created");
console.log("══════════════════════════════════════════════════════════");
console.log(`  Address:    ${account.address}`);
console.log(`  Path:       m/44'/60'/0'/0/0`);
console.log(`  Mnemonic:   ${mnemonic}`);
console.log("══════════════════════════════════════════════════════════");
console.log("");
console.log("  ✅ This address works on ALL EVM chains:");
console.log("     Ethereum, Base, Arbitrum, Polygon, BSC, Optimism, Avalanche");
console.log("");
console.log("  ⚠️  WRITE DOWN YOUR MNEMONIC AND STORE IT SAFELY");
console.log("  ⚠️  NEVER SHARE IT WITH ANYONE");
console.log("══════════════════════════════════════════════════════════");

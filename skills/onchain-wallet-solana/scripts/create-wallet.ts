/**
 * Solana Wallet — Create New Keypair
 *
 * Generates a new Solana Keypair and outputs the public key (address).
 * Optionally saves the keypair to a JSON file (same format as Solana CLI).
 * No API key required — purely local operation.
 *
 * Usage:
 *   npx tsx create-wallet.ts
 *   npx tsx create-wallet.ts --save wallet.json
 */

import { Keypair } from "@solana/web3.js";
import { writeFileSync } from "fs";

const saveFlag = process.argv.indexOf("--save");
const savePath = saveFlag !== -1 ? process.argv[saveFlag + 1] : undefined;

// Generate new keypair
const keypair = Keypair.generate();

console.log("══════════════════════════════════════════════════");
console.log("  🔑 New Solana Wallet Created");
console.log("══════════════════════════════════════════════════");
console.log(`  Public Key: ${keypair.publicKey.toBase58()}`);
console.log(`  Secret Key: [${keypair.secretKey.toString()}]`);

if (savePath) {
  // Save in Solana CLI compatible format (JSON array of bytes)
  writeFileSync(savePath, JSON.stringify(Array.from(keypair.secretKey)));
  console.log(`  Saved to:   ${savePath}`);
}

console.log("══════════════════════════════════════════════════");
console.log("");
console.log("  ⚠️  SAVE YOUR SECRET KEY SECURELY");
console.log("  ⚠️  ANYONE WITH IT CAN ACCESS YOUR FUNDS");
console.log("══════════════════════════════════════════════════");

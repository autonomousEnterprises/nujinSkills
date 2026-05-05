/**
 * Bitcoin Wallet — Create New HD Wallet (BIP84 Native SegWit)
 *
 * Generates a new BIP39 mnemonic and derives a BIP84 (bc1) address.
 * No API key required — all operations are local.
 *
 * Usage: npx tsx skills/onchain-wallet-btc/scripts/create-wallet.ts [--testnet]
 */

import * as bitcoin from "bitcoinjs-lib";
import * as bip39 from "bip39";
import { BIP32Factory } from "bip32";
import * as ecc from "tiny-secp256k1";

const bip32 = BIP32Factory(ecc);

const isTestnet = process.argv.includes("--testnet");
const network = isTestnet ? bitcoin.networks.testnet : bitcoin.networks.bitcoin;
const coinType = isTestnet ? "1'" : "0'";

// 1. Generate mnemonic
const mnemonic = bip39.generateMnemonic(256); // 24 words for maximum security
const seed = await bip39.mnemonicToSeed(mnemonic);

// 2. Derive master key
const root = bip32.fromSeed(seed, network);

// 3. Derive BIP84 path: m/84'/0'/0'/0/0
const path = `m/84'/${coinType}/0'/0/0`;
const child = root.derivePath(path);

// 4. Generate Native SegWit address (P2WPKH)
const { address } = bitcoin.payments.p2wpkh({
  pubkey: Buffer.from(child.publicKey),
  network,
});

// 5. Output
console.log("══════════════════════════════════════════════════");
console.log("  🔑 New Bitcoin Wallet Created (BIP84 SegWit)");
console.log("══════════════════════════════════════════════════");
console.log(`  Network:    ${isTestnet ? "Testnet" : "Mainnet"}`);
console.log(`  Address:    ${address}`);
console.log(`  Path:       ${path}`);
console.log(`  Mnemonic:   ${mnemonic}`);
console.log("══════════════════════════════════════════════════");
console.log("");
console.log("  ⚠️  WRITE DOWN YOUR MNEMONIC AND STORE IT SAFELY");
console.log("  ⚠️  NEVER SHARE IT WITH ANYONE");
console.log("  ⚠️  THIS IS THE ONLY WAY TO RECOVER YOUR WALLET");
console.log("══════════════════════════════════════════════════");

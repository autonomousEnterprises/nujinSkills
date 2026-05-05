export {};
/**
 * Solana Wallet — Send SPL Token
 *
 * Sends SPL tokens (e.g., USDC, BONK) to another address.
 * Automatically handles associated token account (ATA) creation if needed.
 *
 * Usage:
 *   export PRIVATE_KEY="[1,2,3...]"
 *   npx tsx send-token.ts <mint_address> <to_address> <amount> [--devnet]
 */

import { Connection, Keypair, PublicKey } from "@solana/web3.js";
import { getOrCreateAssociatedTokenAccount, transfer, getMint } from "@solana/spl-token";

async function main() {
  const mint = process.argv[2];
  const to = process.argv[3];
  const amount = parseFloat(process.argv[4]);
  const isDevnet = process.argv.includes("--devnet");
  const privateKeyString = process.env.PRIVATE_KEY;

  if (!mint || !to || isNaN(amount) || !privateKeyString) {
    console.error("Usage: export PRIVATE_KEY='[...]' && npx tsx send-token.ts <mint> <to> <amount> [--devnet]");
    process.exit(1);
  }

  const rpcUrl = isDevnet ? "https://api.devnet.solana.com" : "https://api.mainnet-beta.solana.com";
  const connection = new Connection(rpcUrl, "confirmed");

  const secretKey = Uint8Array.from(JSON.parse(privateKeyString));
  const fromKeypair = Keypair.fromSecretKey(secretKey);
  const mintPubkey = new PublicKey(mint);
  const toPubkey = new PublicKey(to);

  console.log("══════════════════════════════════════════════════");
  console.log(`  ☀️ Sending SPL Token (${isDevnet ? "Devnet" : "Mainnet"})`);
  console.log("══════════════════════════════════════════════════");
  console.log(`  From:     ${fromKeypair.publicKey.toBase58()}`);
  console.log(`  To:       ${toPubkey.toBase58()}`);
  console.log(`  Mint:     ${mintPubkey.toBase58()}`);

  try {
    // 1. Get mint info to find decimals
    const mintInfo = await getMint(connection, mintPubkey);
    const amountInLamports = Math.floor(amount * Math.pow(10, mintInfo.decimals));

    console.log(`  Amount:   ${amount} (Raw: ${amountInLamports})`);

    // 2. Get/Create source ATA
    const fromTokenAccount = await getOrCreateAssociatedTokenAccount(
      connection,
      fromKeypair,
      mintPubkey,
      fromKeypair.publicKey
    );

    // 3. Get/Create destination ATA
    const toTokenAccount = await getOrCreateAssociatedTokenAccount(
      connection,
      fromKeypair,
      mintPubkey,
      toPubkey
    );

    // 4. Transfer
    const signature = await transfer(
      connection,
      fromKeypair,
      fromTokenAccount.address,
      toTokenAccount.address,
      fromKeypair.publicKey,
      amountInLamports
    );

    console.log("  ✅ Transaction Sent!");
    console.log(`  Signature: ${signature}`);
    console.log(`  Explorer:  https://solscan.io/tx/${signature}${isDevnet ? "?cluster=devnet" : ""}`);
  } catch (error: any) {
    console.error("  ❌ Transaction Failed:");
    console.error(`  ${error.message}`);
  }
  console.log("══════════════════════════════════════════════════");
}

main();

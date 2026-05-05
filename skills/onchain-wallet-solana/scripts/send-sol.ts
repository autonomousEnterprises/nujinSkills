export {};
/**
 * Solana Wallet — Send SOL
 *
 * Sends native SOL to another address.
 *
 * Usage:
 *   export PRIVATE_KEY="[1,2,3...]"
 *   npx tsx send-sol.ts <to_address> <amount_sol> [--devnet]
 */

import { Connection, Keypair, PublicKey, Transaction, SystemProgram, LAMPORTS_PER_SOL, sendAndConfirmTransaction } from "@solana/web3.js";

async function main() {
  const to = process.argv[2];
  const amount = parseFloat(process.argv[3]);
  const isDevnet = process.argv.includes("--devnet");
  const privateKeyString = process.env.PRIVATE_KEY;

  if (!to || isNaN(amount) || !privateKeyString) {
    console.error("Usage: export PRIVATE_KEY='[...]' && npx tsx send-sol.ts <to> <amount> [--devnet]");
    process.exit(1);
  }

  const rpcUrl = isDevnet ? "https://api.devnet.solana.com" : "https://api.mainnet-beta.solana.com";
  const connection = new Connection(rpcUrl, "confirmed");

  const secretKey = Uint8Array.from(JSON.parse(privateKeyString));
  const fromKeypair = Keypair.fromSecretKey(secretKey);
  const toPubkey = new PublicKey(to);

  console.log("══════════════════════════════════════════════════");
  console.log(`  ☀️ Sending SOL (${isDevnet ? "Devnet" : "Mainnet"})`);
  console.log("══════════════════════════════════════════════════");
  console.log(`  From:   ${fromKeypair.publicKey.toBase58()}`);
  console.log(`  To:     ${toPubkey.toBase58()}`);
  console.log(`  Amount: ${amount} SOL`);

  try {
    const transaction = new Transaction().add(
      SystemProgram.transfer({
        fromPubkey: fromKeypair.publicKey,
        toPubkey: toPubkey,
        lamports: amount * LAMPORTS_PER_SOL,
      })
    );

    const signature = await sendAndConfirmTransaction(connection, transaction, [fromKeypair]);

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

export {};
/**
 * Solana DEX Swap — Execute Swap (Jupiter)
 *
 * Executes a token swap on Solana using Jupiter Aggregator.
 *
 * Usage:
 *   export PRIVATE_KEY="[1,2,3...]"
 *   npx tsx execute-swap.ts <inputMint> <outputMint> <amount> [--slippage 50]
 */

import { Connection, Keypair, VersionedTransaction } from "@solana/web3.js";
import axios from "axios";

async function main() {
  const inputMint = process.argv[2];
  const outputMint = process.argv[3];
  const amount = process.argv[4]; // in raw units (lamports for SOL, or adjusted for token decimals)
  const slippageBps = parseInt(process.argv.find(a => a.startsWith("--slippage"))?.split(" ")[1] || "50");
  const privateKeyString = process.env.PRIVATE_KEY;

  if (!inputMint || !outputMint || !amount || !privateKeyString) {
    console.error("Usage: export PRIVATE_KEY='[...]' && npx tsx execute-swap.ts <inputMint> <outputMint> <amount> [--slippage 50]");
    process.exit(1);
  }

  const connection = new Connection("https://api.mainnet-beta.solana.com", "confirmed");
  const secretKey = Uint8Array.from(JSON.parse(privateKeyString));
  const keypair = Keypair.fromSecretKey(secretKey);

  console.log("══════════════════════════════════════════════════");
  console.log("  🪐 Jupiter Swap Execution");
  console.log("══════════════════════════════════════════════════");
  console.log(`  Account: ${keypair.publicKey.toBase58()}`);

  try {
    // 1. Get Quote
    console.log("  🔍 Fetching quote...");
    const quoteResponse = await axios.get(
      `https://quote-api.jup.ag/v6/quote?inputMint=${inputMint}&outputMint=${outputMint}&amount=${amount}&slippageBps=${slippageBps}`
    );
    const quote = quoteResponse.data;

    // 2. Get Swap Transaction
    console.log("  📦 Preparing swap transaction...");
    const swapResponse = await axios.post("https://quote-api.jup.ag/v6/swap", {
      quoteResponse: quote,
      userPublicKey: keypair.publicKey.toBase58(),
      wrapAndUnwrapSol: true,
    });
    const { swapTransaction } = swapResponse.data;

    // 3. Sign and Execute
    console.log("  ✍️  Signing transaction...");
    const swapTransactionBuf = Buffer.from(swapTransaction, "base64");
    const transaction = VersionedTransaction.deserialize(swapTransactionBuf);
    transaction.sign([keypair]);

    console.log("  🛰️  Broadcasting...");
    const rawTransaction = transaction.serialize();
    const txid = await connection.sendRawTransaction(rawTransaction, {
      skipPreflight: true,
      maxRetries: 2,
    });

    console.log("  ✅ Swap Transaction Sent!");
    console.log(`  Signature: ${txid}`);
    console.log(`  Explorer:  https://solscan.io/tx/${txid}`);

    // Wait for confirmation (optional, but good for feedback)
    console.log("  ⏳ Confirming...");
    await connection.confirmTransaction(txid);
    console.log("  🎉 Transaction Confirmed!");

  } catch (error: any) {
    console.error("  ❌ Swap Failed:");
    console.error(`  ${error.response?.data || error.message}`);
  }
  console.log("══════════════════════════════════════════════════");
}

main();

/**
 * Solana Wallet — Check Balance
 *
 * Checks SOL balance and all SPL token balances for a given address.
 * Uses public Solana RPC — no API key required.
 *
 * Usage:
 *   npx tsx check-balance.ts <public-key> [--devnet]
 */

import { Connection, PublicKey, LAMPORTS_PER_SOL } from "@solana/web3.js";

const pubkeyStr = process.argv[2];
const isDevnet = process.argv.includes("--devnet");

if (!pubkeyStr) {
  console.error("Usage: npx tsx check-balance.ts <public-key> [--devnet]");
  process.exit(1);
}

const rpcUrl = isDevnet
  ? "https://api.devnet.solana.com"
  : "https://api.mainnet-beta.solana.com";

const connection = new Connection(rpcUrl, "confirmed");
const publicKey = new PublicKey(pubkeyStr);

// Fetch SOL balance
const lamports = await connection.getBalance(publicKey);
const solBalance = lamports / LAMPORTS_PER_SOL;

console.log("══════════════════════════════════════════════════");
console.log("  ◎ Solana Balance");
console.log("══════════════════════════════════════════════════");
console.log(`  Address:  ${pubkeyStr}`);
console.log(`  Network:  ${isDevnet ? "Devnet" : "Mainnet Beta"}`);
console.log(`  SOL:      ${solBalance.toFixed(9)} SOL (${lamports} lamports)`);

// Fetch SPL token accounts
try {
  const tokenAccounts = await connection.getParsedTokenAccountsByOwner(publicKey, {
    programId: new PublicKey("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"),
  });

  if (tokenAccounts.value.length > 0) {
    console.log("──────────────────────────────────────────────────");
    console.log("  SPL Tokens:");

    for (const { account } of tokenAccounts.value) {
      const parsed = account.data.parsed as {
        info: {
          mint: string;
          tokenAmount: { uiAmount: number; uiAmountString: string; decimals: number };
        };
      };
      const { mint, tokenAmount } = parsed.info;

      if (tokenAmount.uiAmount && tokenAmount.uiAmount > 0) {
        console.log(`    ${mint}`);
        console.log(`      Balance: ${tokenAmount.uiAmountString} (decimals: ${tokenAmount.decimals})`);
      }
    }
  } else {
    console.log("  No SPL tokens found.");
  }
} catch (error) {
  console.log("  SPL token fetch failed (rate limit or network issue)");
}

console.log("══════════════════════════════════════════════════");

export {};
/**
 * Bitcoin Wallet — List UTXOs
 *
 * Lists all unspent transaction outputs for a Bitcoin address.
 * Uses Blockstream API (free, no API key).
 *
 * Usage: npx tsx skills/onchain-wallet-btc/scripts/list-utxos.ts <address> [--testnet]
 */

const address = process.argv[2];
const isTestnet = process.argv.includes("--testnet");

if (!address) {
  console.error("Usage: npx tsx list-utxos.ts <bitcoin-address> [--testnet]");
  process.exit(1);
}

const baseUrl = isTestnet
  ? "https://blockstream.info/testnet/api"
  : "https://blockstream.info/api";

interface Utxo {
  txid: string;
  vout: number;
  status: { confirmed: boolean; block_height?: number };
  value: number;
}

try {
  const response = await fetch(`${baseUrl}/address/${address}/utxo`);

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }

  const utxos = (await response.json()) as Utxo[];

  const totalSats = utxos.reduce((sum, u) => sum + u.value, 0);
  const satsToBtc = (sats: number) => (sats / 1e8).toFixed(8);

  console.log("══════════════════════════════════════════════════");
  console.log("  ₿ UTXOs for", address);
  console.log("══════════════════════════════════════════════════");
  console.log(`  Network: ${isTestnet ? "Testnet" : "Mainnet"}`);
  console.log(`  Count:   ${utxos.length}`);
  console.log(`  Total:   ${satsToBtc(totalSats)} BTC`);
  console.log("──────────────────────────────────────────────────");

  if (utxos.length === 0) {
    console.log("  No UTXOs found.");
  } else {
    for (const utxo of utxos) {
      console.log(`  ${utxo.txid}:${utxo.vout}`);
      console.log(`    Value:     ${satsToBtc(utxo.value)} BTC (${utxo.value} sats)`);
      console.log(`    Confirmed: ${utxo.status.confirmed ? `Yes (block ${utxo.status.block_height})` : "No (mempool)"}`);
      console.log("");
    }
  }

  console.log("══════════════════════════════════════════════════");
} catch (error) {
  console.error("Failed to fetch UTXOs:", (error as Error).message);
  process.exit(1);
}

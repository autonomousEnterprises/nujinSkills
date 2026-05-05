export {};
/**
 * Bitcoin Wallet — Check Balance
 *
 * Queries the Blockstream API for the confirmed and unconfirmed balance
 * of a given Bitcoin address. No API key required.
 *
 * Usage: npx tsx skills/onchain-wallet-btc/scripts/check-balance.ts <address> [--testnet]
 */

const address = process.argv[2];
const isTestnet = process.argv.includes("--testnet");

if (!address) {
  console.error("Usage: npx tsx check-balance.ts <bitcoin-address> [--testnet]");
  process.exit(1);
}

const baseUrl = isTestnet
  ? "https://blockstream.info/testnet/api"
  : "https://blockstream.info/api";

try {
  const response = await fetch(`${baseUrl}/address/${address}`);

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }

  const data = (await response.json()) as {
    address: string;
    chain_stats: {
      funded_txo_count: number;
      funded_txo_sum: number;
      spent_txo_count: number;
      spent_txo_sum: number;
      tx_count: number;
    };
    mempool_stats: {
      funded_txo_count: number;
      funded_txo_sum: number;
      spent_txo_count: number;
      spent_txo_sum: number;
      tx_count: number;
    };
  };

  const confirmedBalance = data.chain_stats.funded_txo_sum - data.chain_stats.spent_txo_sum;
  const unconfirmedBalance = data.mempool_stats.funded_txo_sum - data.mempool_stats.spent_txo_sum;
  const totalBalance = confirmedBalance + unconfirmedBalance;

  const satsToBtc = (sats: number) => (sats / 1e8).toFixed(8);

  console.log("══════════════════════════════════════════════════");
  console.log("  ₿ Bitcoin Balance");
  console.log("══════════════════════════════════════════════════");
  console.log(`  Address:     ${address}`);
  console.log(`  Network:     ${isTestnet ? "Testnet" : "Mainnet"}`);
  console.log(`  Confirmed:   ${satsToBtc(confirmedBalance)} BTC (${confirmedBalance} sats)`);
  console.log(`  Unconfirmed: ${satsToBtc(unconfirmedBalance)} BTC (${unconfirmedBalance} sats)`);
  console.log(`  Total:       ${satsToBtc(totalBalance)} BTC`);
  console.log(`  Tx Count:    ${data.chain_stats.tx_count}`);
  console.log("══════════════════════════════════════════════════");
} catch (error) {
  console.error("Failed to fetch balance:", (error as Error).message);
  process.exit(1);
}

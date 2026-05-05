export {};
/**
 * Bitcoin Wallet — Send BTC
 *
 * Sends Bitcoin (Native SegWit) to another address.
 *
 * Usage:
 *   export MNEMONIC="..."
 *   npx tsx send-btc.ts <to_address> <amount_sats> [--testnet]
 */

import * as bitcoin from "bitcoinjs-lib";
import { BIP32Factory } from "bip32";
import * as ecc from "tiny-secp256k1";
import { mnemonicToSeedSync } from "bip39";
import axios from "axios";

const bip32 = BIP32Factory(ecc);

async function main() {
  const toAddress = process.argv[2];
  const amountSats = parseInt(process.argv[3]);
  const isTestnet = process.argv.includes("--testnet");
  const mnemonic = process.env.MNEMONIC;

  if (!toAddress || isNaN(amountSats) || !mnemonic) {
    console.error("Usage: export MNEMONIC='...' && npx tsx send-btc.ts <to> <amount_sats> [--testnet]");
    process.exit(1);
  }

  const network = isTestnet ? bitcoin.networks.testnet : bitcoin.networks.bitcoin;
  const path = isTestnet ? "m/84'/1'/0'/0/0" : "m/84'/0'/0'/0/0";

  const seed = mnemonicToSeedSync(mnemonic);
  const root = bip32.fromSeed(seed, network);
  const keyPair = root.derivePath(path);

  const { address } = bitcoin.payments.p2wpkh({ pubkey: keyPair.publicKey, network });
  if (!address) throw new Error("Could not derive address");

  const apiBase = isTestnet ? "https://blockstream.info/testnet/api" : "https://blockstream.info/api";

  console.log("══════════════════════════════════════════════════");
  console.log(`  ₿ Sending Bitcoin (${isTestnet ? "Testnet" : "Mainnet"})`);
  console.log("══════════════════════════════════════════════════");
  console.log(`  From:   ${address}`);
  console.log(`  To:     ${toAddress}`);
  console.log(`  Amount: ${amountSats} sats (${(amountSats / 1e8).toFixed(8)} BTC)`);

  try {
    // 1. Fetch UTXOs
    const { data: utxos } = await axios.get(`${apiBase}/address/${address}/utxo`);
    if (utxos.length === 0) throw new Error("No UTXOs found for address");

    // 2. Select UTXOs (Simple FIFO)
    let totalInput = 0;
    const selectedUtxos = [];
    for (const utxo of utxos) {
      totalInput += utxo.value;
      selectedUtxos.push(utxo);
      if (totalInput >= amountSats + 1000) break; // Basic 1000 sat fee buffer
    }

    if (totalInput < amountSats + 1000) throw new Error("Insufficient balance (including fee)");

    // 3. Build Transaction
    const psbt = new bitcoin.Psbt({ network });
    for (const utxo of selectedUtxos) {
      const { data: txHex } = await axios.get(`${apiBase}/tx/${utxo.txid}/hex`);
      psbt.addInput({
        hash: utxo.txid,
        index: utxo.vout,
        witnessUtxo: {
          script: bitcoin.payments.p2wpkh({ pubkey: keyPair.publicKey, network }).output!,
          value: utxo.value,
        },
      });
    }

    psbt.addOutput({ address: toAddress, value: amountSats });
    const change = totalInput - amountSats - 1000; // Fixed 1000 sat fee for simplicity
    if (change > 546) { // Dust limit
      psbt.addOutput({ address, value: change });
    }

    // 4. Sign and Finalize
    psbt.signAllInputs(keyPair);
    psbt.finalizeAllInputs();
    const tx = psbt.extractTransaction();
    const txHex = tx.toHex();

    // 5. Broadcast
    console.log("  🛰️  Broadcasting...");
    const { data: txid } = await axios.post(`${apiBase}/tx`, txHex);

    console.log("  ✅ Transaction Sent!");
    console.log(`  TXID: ${txid}`);
    console.log(`  Explorer: ${isTestnet ? "https://blockstream.info/testnet/tx/" : "https://blockstream.info/tx/"}${txid}`);

  } catch (error: any) {
    console.error("  ❌ Transaction Failed:");
    console.error(`  ${error.response?.data || error.message}`);
  }
  console.log("══════════════════════════════════════════════════");
}

main();

export {};
/**
 * EVM Wallet — Send Native Token
 *
 * Sends native tokens (ETH/MATIC/BNB) on any supported EVM chain.
 *
 * Usage:
 *   export PRIVATE_KEY=0x...
 *   npx tsx send-native.ts <to_address> <amount> [--chain ethereum|base|...]
 */

import { createWalletClient, http, fallback, parseEther, type Address } from "viem";
import { privateKeyToAccount } from "viem/accounts";
import { mainnet, base, arbitrum, polygon, bsc, optimism, avalanche, sepolia } from "viem/chains";
import { EVM_RPCS } from "../../../shared/rpc-providers";

const CHAIN_MAP = { ethereum: mainnet, base, arbitrum, polygon, bsc, optimism, avalanche, sepolia } as const;

async function main() {
  const to = process.argv[2] as Address | undefined;
  const amount = process.argv[3];
  const chainFlag = process.argv.indexOf("--chain");
  const chainName = chainFlag !== -1 ? (process.argv[chainFlag + 1] as keyof typeof CHAIN_MAP) : "ethereum";

  const privateKey = process.env.PRIVATE_KEY as `0x${string}` | undefined;

  if (!to || !amount || !privateKey) {
    console.error("Usage: export PRIVATE_KEY=0x... && npx tsx send-native.ts <to> <amount> [--chain <chain>]");
    process.exit(1);
  }

  const chain = CHAIN_MAP[chainName];
  if (!chain) {
    console.error(`Unknown chain: ${chainName}`);
    process.exit(1);
  }

  const account = privateKeyToAccount(privateKey);
  const rpcConfig = EVM_RPCS[chainName];
  const transports = rpcConfig.rpcs.map((rpc) => http(rpc.url));

  const client = createWalletClient({
    account,
    chain,
    transport: fallback(transports),
  });

  console.log("══════════════════════════════════════════════════");
  console.log(`  🚀 Sending Native Token on ${chain.name}`);
  console.log("══════════════════════════════════════════════════");
  console.log(`  From:   ${account.address}`);
  console.log(`  To:     ${to}`);
  console.log(`  Amount: ${amount} ${chain.nativeCurrency.symbol}`);

  try {
    const hash = await client.sendTransaction({
      to,
      value: parseEther(amount),
    });

    console.log("  ✅ Transaction Sent!");
    console.log(`  Hash:   ${hash}`);
    console.log(`  Explorer: ${chain.blockExplorers?.default.url}/tx/${hash}`);
  } catch (error: any) {
    console.error("  ❌ Transaction Failed:");
    console.error(`  ${error.message}`);
  }
  console.log("══════════════════════════════════════════════════");
}

main();

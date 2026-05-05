export {};
/**
 * EVM Wallet — Send ERC-20 Token
 *
 * Sends ERC-20 tokens on any supported EVM chain.
 *
 * Usage:
 *   export PRIVATE_KEY=0x...
 *   npx tsx send-token.ts <token_address> <to_address> <amount> [--chain ethereum|base|...]
 */

import { createWalletClient, createPublicClient, http, fallback, parseUnits, type Address } from "viem";
import { privateKeyToAccount } from "viem/accounts";
import { mainnet, base, arbitrum, polygon, bsc, optimism, avalanche, sepolia } from "viem/chains";
import { EVM_RPCS } from "../../../shared/rpc-providers";

const CHAIN_MAP = { ethereum: mainnet, base, arbitrum, polygon, bsc, optimism, avalanche, sepolia } as const;

async function main() {
  const tokenAddress = process.argv[2] as Address | undefined;
  const to = process.argv[3] as Address | undefined;
  const amount = process.argv[4];
  const chainFlag = process.argv.indexOf("--chain");
  const chainName = chainFlag !== -1 ? (process.argv[chainFlag + 1] as keyof typeof CHAIN_MAP) : "ethereum";

  const privateKey = process.env.PRIVATE_KEY as `0x${string}` | undefined;

  if (!tokenAddress || !to || !amount || !privateKey) {
    console.error("Usage: export PRIVATE_KEY=0x... && npx tsx send-token.ts <token> <to> <amount> [--chain <chain>]");
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

  const publicClient = createPublicClient({
    chain,
    transport: fallback(transports),
  });

  const walletClient = createWalletClient({
    account,
    chain,
    transport: fallback(transports),
  });

  const ERC20_ABI = [
    { name: "transfer", type: "function", stateMutability: "nonpayable", inputs: [{ name: "recipient", type: "address" }, { name: "amount", type: "uint256" }], outputs: [{ name: "", type: "bool" }] },
    { name: "decimals", type: "function", stateMutability: "view", inputs: [], outputs: [{ name: "", type: "uint8" }] },
    { name: "symbol", type: "function", stateMutability: "view", inputs: [], outputs: [{ name: "", type: "string" }] },
  ] as const;

  try {
    const [decimals, symbol] = await Promise.all([
      publicClient.readContract({ address: tokenAddress, abi: ERC20_ABI, functionName: "decimals" }),
      publicClient.readContract({ address: tokenAddress, abi: ERC20_ABI, functionName: "symbol" }),
    ]);

    const amountInUnits = parseUnits(amount, decimals);

    console.log("══════════════════════════════════════════════════");
    console.log(`  🚀 Sending ERC-20 Token on ${chain.name}`);
    console.log("══════════════════════════════════════════════════");
    console.log(`  From:     ${account.address}`);
    console.log(`  To:       ${to}`);
    console.log(`  Amount:   ${amount} ${symbol}`);
    console.log(`  Contract: ${tokenAddress}`);

    const hash = await walletClient.writeContract({
      address: tokenAddress,
      abi: ERC20_ABI,
      functionName: "transfer",
      args: [to, amountInUnits],
    });

    console.log("  ✅ Transaction Sent!");
    console.log(`  Hash:     ${hash}`);
    console.log(`  Explorer: ${chain.blockExplorers?.default.url}/tx/${hash}`);
  } catch (error: any) {
    console.error("  ❌ Transaction Failed:");
    console.error(`  ${error.message}`);
  }
  console.log("══════════════════════════════════════════════════");
}

main();

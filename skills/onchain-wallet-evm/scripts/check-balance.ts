/**
 * EVM Wallet — Check Balance
 *
 * Checks native token (ETH/MATIC/BNB) and optionally ERC-20 token balances.
 * Uses free public RPCs — no API key required.
 *
 * Usage:
 *   npx tsx check-balance.ts <address> [--chain ethereum|base|arbitrum|polygon|bsc]
 *   npx tsx check-balance.ts <address> --chain base --token 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913
 */

import { createPublicClient, http, fallback, formatEther, formatUnits, type Address } from "viem";
import { mainnet, base, arbitrum, polygon, bsc, optimism, avalanche, sepolia } from "viem/chains";
import { EVM_RPCS } from "../../../shared/rpc-providers";

const CHAIN_MAP = { ethereum: mainnet, base, arbitrum, polygon, bsc, optimism, avalanche, sepolia } as const;

// ─── Parse Args ──────────────────────────────────────────────────────────────

const address = process.argv[2] as Address | undefined;
const chainFlag = process.argv.indexOf("--chain");
const chainName = chainFlag !== -1 ? (process.argv[chainFlag + 1] as keyof typeof CHAIN_MAP) : "ethereum";
const tokenFlag = process.argv.indexOf("--token");
const tokenAddress = tokenFlag !== -1 ? (process.argv[tokenFlag + 1] as Address) : undefined;

if (!address) {
  console.error("Usage: npx tsx check-balance.ts <address> [--chain <chain>] [--token <contract>]");
  console.error("Chains: ethereum, base, arbitrum, polygon, bsc, optimism, avalanche, sepolia");
  process.exit(1);
}

const chain = CHAIN_MAP[chainName];
if (!chain) {
  console.error(`Unknown chain: ${chainName}`);
  process.exit(1);
}

const rpcConfig = EVM_RPCS[chainName];
const transports = rpcConfig.rpcs.map((rpc) => http(rpc.url));

const client = createPublicClient({
  chain,
  transport: fallback(transports),
});

// ─── Fetch Balances ──────────────────────────────────────────────────────────

const nativeBalance = await client.getBalance({ address });

console.log("══════════════════════════════════════════════════");
console.log(`  💰 Balance on ${chain.name}`);
console.log("══════════════════════════════════════════════════");
console.log(`  Address:  ${address}`);
console.log(`  Native:   ${formatEther(nativeBalance)} ${chain.nativeCurrency.symbol}`);

// ERC-20 balance check
if (tokenAddress) {
  const ERC20_ABI = [
    { name: "balanceOf", type: "function", stateMutability: "view", inputs: [{ name: "account", type: "address" }], outputs: [{ name: "", type: "uint256" }] },
    { name: "symbol", type: "function", stateMutability: "view", inputs: [], outputs: [{ name: "", type: "string" }] },
    { name: "decimals", type: "function", stateMutability: "view", inputs: [], outputs: [{ name: "", type: "uint8" }] },
    { name: "name", type: "function", stateMutability: "view", inputs: [], outputs: [{ name: "", type: "string" }] },
  ] as const;

  const [balance, symbol, decimals, name] = await Promise.all([
    client.readContract({ address: tokenAddress, abi: ERC20_ABI, functionName: "balanceOf", args: [address] }),
    client.readContract({ address: tokenAddress, abi: ERC20_ABI, functionName: "symbol" }),
    client.readContract({ address: tokenAddress, abi: ERC20_ABI, functionName: "decimals" }),
    client.readContract({ address: tokenAddress, abi: ERC20_ABI, functionName: "name" }),
  ]);

  console.log(`  Token:    ${name} (${symbol})`);
  console.log(`  Balance:  ${formatUnits(balance, decimals)} ${symbol}`);
  console.log(`  Contract: ${tokenAddress}`);
}

console.log("══════════════════════════════════════════════════");

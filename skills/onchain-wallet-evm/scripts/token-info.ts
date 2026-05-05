/**
 * EVM Wallet — Token Info
 *
 * Read ERC-20 token metadata: name, symbol, decimals, totalSupply.
 * Uses free public RPCs — no API key required.
 *
 * Usage: npx tsx token-info.ts <contract-address> [--chain ethereum|base|...]
 */

import { createPublicClient, http, formatUnits, type Address } from "viem";
import { mainnet, base, arbitrum, polygon, bsc, optimism, avalanche } from "viem/chains";

const CHAIN_MAP = { ethereum: mainnet, base, arbitrum, polygon, bsc, optimism, avalanche } as const;
const RPC_URLS: Record<string, string> = {
  ethereum: "https://cloudflare-eth.com",
  base: "https://mainnet.base.org",
  arbitrum: "https://arb1.arbitrum.io/rpc",
  polygon: "https://polygon-rpc.com",
  bsc: "https://bsc-dataseed.binance.org",
  optimism: "https://mainnet.optimism.io",
  avalanche: "https://api.avax.network/ext/bc/C/rpc",
};

const contractAddress = process.argv[2] as Address | undefined;
const chainFlag = process.argv.indexOf("--chain");
const chainName = chainFlag !== -1 ? (process.argv[chainFlag + 1] as keyof typeof CHAIN_MAP) : "ethereum";

if (!contractAddress) {
  console.error("Usage: npx tsx token-info.ts <contract-address> [--chain <chain>]");
  process.exit(1);
}

const chain = CHAIN_MAP[chainName];
if (!chain) {
  console.error(`Unknown chain: ${chainName}`);
  process.exit(1);
}

const client = createPublicClient({
  chain,
  transport: http(RPC_URLS[chainName]),
});

const ERC20_ABI = [
  { name: "name", type: "function", stateMutability: "view", inputs: [], outputs: [{ name: "", type: "string" }] },
  { name: "symbol", type: "function", stateMutability: "view", inputs: [], outputs: [{ name: "", type: "string" }] },
  { name: "decimals", type: "function", stateMutability: "view", inputs: [], outputs: [{ name: "", type: "uint8" }] },
  { name: "totalSupply", type: "function", stateMutability: "view", inputs: [], outputs: [{ name: "", type: "uint256" }] },
] as const;

try {
  const [name, symbol, decimals, totalSupply] = await Promise.all([
    client.readContract({ address: contractAddress, abi: ERC20_ABI, functionName: "name" }),
    client.readContract({ address: contractAddress, abi: ERC20_ABI, functionName: "symbol" }),
    client.readContract({ address: contractAddress, abi: ERC20_ABI, functionName: "decimals" }),
    client.readContract({ address: contractAddress, abi: ERC20_ABI, functionName: "totalSupply" }),
  ]);

  console.log("══════════════════════════════════════════════════");
  console.log("  🪙 ERC-20 Token Info");
  console.log("══════════════════════════════════════════════════");
  console.log(`  Name:         ${name}`);
  console.log(`  Symbol:       ${symbol}`);
  console.log(`  Decimals:     ${decimals}`);
  console.log(`  Total Supply: ${formatUnits(totalSupply, decimals)} ${symbol}`);
  console.log(`  Contract:     ${contractAddress}`);
  console.log(`  Chain:        ${chain.name}`);
  console.log("══════════════════════════════════════════════════");
} catch (error) {
  console.error("Failed to read token info:", (error as Error).message);
  console.error("Make sure the address is a valid ERC-20 contract on", chain.name);
  process.exit(1);
}

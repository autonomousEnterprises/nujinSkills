/**
 * EVM DEX Swap — Get Quote
 *
 * Gets a swap price estimate from Uniswap V3 Quoter V2 contract (on-chain read).
 * No API key required — uses free public RPC.
 *
 * Usage:
 *   npx tsx get-quote.ts --from 0xA0b8...eB48 --to 0xC02a...Cc2 --amount 1000 --chain ethereum
 *   npx tsx get-quote.ts --from USDC --to WETH --amount 1000 --chain ethereum
 */

import { createPublicClient, http, parseUnits, formatUnits, type Address } from "viem";
import { mainnet, base, arbitrum, polygon } from "viem/chains";

// ─── Quoter V2 ABI (minimal) ────────────────────────────────────────────────

const QUOTER_ABI = [
  {
    name: "quoteExactInputSingle",
    type: "function",
    stateMutability: "nonpayable",
    inputs: [{
      name: "params",
      type: "tuple",
      components: [
        { name: "tokenIn", type: "address" },
        { name: "tokenOut", type: "address" },
        { name: "amountIn", type: "uint256" },
        { name: "fee", type: "uint24" },
        { name: "sqrtPriceLimitX96", type: "uint160" },
      ],
    }],
    outputs: [
      { name: "amountOut", type: "uint256" },
      { name: "sqrtPriceX96After", type: "uint160" },
      { name: "initializedTicksCrossed", type: "uint32" },
      { name: "gasEstimate", type: "uint256" },
    ],
  },
] as const;

// ─── Contract Addresses ─────────────────────────────────────────────────────

const QUOTER_ADDRESSES: Record<string, Address> = {
  ethereum: "0x61fFE014bA17989E743c5F6cB21bF9697530B21e",
  arbitrum: "0x61fFE014bA17989E743c5F6cB21bF9697530B21e",
  polygon: "0x61fFE014bA17989E743c5F6cB21bF9697530B21e",
  base: "0x3d4e44Eb1374240CE5F1B871ab261CD16335B76a",
};

const CHAIN_MAP = { ethereum: mainnet, base, arbitrum, polygon } as const;
const RPC_URLS: Record<string, string> = {
  ethereum: "https://cloudflare-eth.com",
  base: "https://mainnet.base.org",
  arbitrum: "https://arb1.arbitrum.io/rpc",
  polygon: "https://polygon-rpc.com",
};

// Well-known token shortcuts
const TOKEN_SHORTCUTS: Record<string, Record<string, { address: Address; decimals: number }>> = {
  ethereum: {
    WETH: { address: "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2", decimals: 18 },
    USDC: { address: "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", decimals: 6 },
    USDT: { address: "0xdAC17F958D2ee523a2206206994597C13D831ec7", decimals: 6 },
    DAI: { address: "0x6B175474E89094C44Da98b954EedeAC495271d0F", decimals: 18 },
    WBTC: { address: "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599", decimals: 8 },
  },
};

// ─── Parse Args ──────────────────────────────────────────────────────────────

function getArg(flag: string): string | undefined {
  const idx = process.argv.indexOf(flag);
  return idx !== -1 ? process.argv[idx + 1] : undefined;
}

const fromArg = getArg("--from");
const toArg = getArg("--to");
const amountArg = getArg("--amount");
const chainName = (getArg("--chain") || "ethereum") as keyof typeof CHAIN_MAP;
const fee = parseInt(getArg("--fee") || "3000");

if (!fromArg || !toArg || !amountArg) {
  console.error("Usage: npx tsx get-quote.ts --from <token> --to <token> --amount <amount> [--chain ethereum] [--fee 3000]");
  console.error("Token can be an address or shortcut: WETH, USDC, USDT, DAI, WBTC");
  process.exit(1);
}

// Resolve token addresses
function resolveToken(input: string, chain: string): { address: Address; decimals: number } {
  const shortcuts = TOKEN_SHORTCUTS[chain] || {};
  const shortcut = shortcuts[input.toUpperCase()];
  if (shortcut) return shortcut;
  // Assume it's an address with 18 decimals (user can override)
  return { address: input as Address, decimals: 18 };
}

const tokenIn = resolveToken(fromArg, chainName);
const tokenOut = resolveToken(toArg, chainName);
const amountIn = parseUnits(amountArg, tokenIn.decimals);

const chain = CHAIN_MAP[chainName];
const quoterAddress = QUOTER_ADDRESSES[chainName];

if (!chain || !quoterAddress) {
  console.error(`Chain "${chainName}" not supported for DEX quotes`);
  process.exit(1);
}

const client = createPublicClient({
  chain,
  transport: http(RPC_URLS[chainName]),
});

// ─── Get Quote ───────────────────────────────────────────────────────────────

try {
  const result = await client.simulateContract({
    address: quoterAddress,
    abi: QUOTER_ABI,
    functionName: "quoteExactInputSingle",
    args: [{
      tokenIn: tokenIn.address,
      tokenOut: tokenOut.address,
      amountIn,
      fee,
      sqrtPriceLimitX96: 0n,
    }],
  });

  const [amountOut, , , gasEstimate] = result.result;

  console.log("══════════════════════════════════════════════════");
  console.log("  🔄 Swap Quote (Uniswap V3)");
  console.log("══════════════════════════════════════════════════");
  console.log(`  Chain:       ${chain.name}`);
  console.log(`  From:        ${fromArg} (${tokenIn.address})`);
  console.log(`  To:          ${toArg} (${tokenOut.address})`);
  console.log(`  Amount In:   ${amountArg}`);
  console.log(`  Amount Out:  ${formatUnits(amountOut, tokenOut.decimals)}`);
  console.log(`  Fee Tier:    ${fee / 10000}%`);
  console.log(`  Gas Est:     ${gasEstimate.toString()}`);
  console.log("══════════════════════════════════════════════════");
} catch (error) {
  console.error("Quote failed:", (error as Error).message);
  console.error("This may mean no pool exists for this pair/fee tier.");
  process.exit(1);
}

/**
 * DeFi Flash Loans — Check Available Liquidity
 *
 * Queries Aave V3 Pool to check how much liquidity is available
 * for flash loans per asset. Uses free public RPC — no API key.
 *
 * Usage:
 *   npx tsx check-liquidity.ts [--chain ethereum]
 *   npx tsx check-liquidity.ts --chain arbitrum
 */

import { createPublicClient, http, formatUnits, type Address } from "viem";
import { mainnet, base, arbitrum, polygon } from "viem/chains";

const CHAIN_MAP = { ethereum: mainnet, base, arbitrum, polygon } as const;
const RPC_URLS: Record<string, string> = {
  ethereum: "https://cloudflare-eth.com",
  base: "https://mainnet.base.org",
  arbitrum: "https://arb1.arbitrum.io/rpc",
  polygon: "https://polygon-rpc.com",
};

// Major assets to check per chain
const ASSETS: Record<string, Array<{ symbol: string; address: Address; decimals: number }>> = {
  ethereum: [
    { symbol: "WETH", address: "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2", decimals: 18 },
    { symbol: "USDC", address: "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", decimals: 6 },
    { symbol: "USDT", address: "0xdAC17F958D2ee523a2206206994597C13D831ec7", decimals: 6 },
    { symbol: "DAI", address: "0x6B175474E89094C44Da98b954EedeAC495271d0F", decimals: 18 },
    { symbol: "WBTC", address: "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599", decimals: 8 },
  ],
  arbitrum: [
    { symbol: "WETH", address: "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1", decimals: 18 },
    { symbol: "USDC", address: "0xaf88d065e77c8cC2239327C5EDb3A432268e5831", decimals: 6 },
    { symbol: "USDT", address: "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9", decimals: 6 },
  ],
  polygon: [
    { symbol: "WETH", address: "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619", decimals: 18 },
    { symbol: "USDC", address: "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359", decimals: 6 },
  ],
  base: [
    { symbol: "WETH", address: "0x4200000000000000000000000000000000000006", decimals: 18 },
    { symbol: "USDC", address: "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913", decimals: 6 },
  ],
};

// Aave V3 Pool addresses
const AAVE_POOL: Record<string, Address> = {
  ethereum: "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
  arbitrum: "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
  polygon: "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
  base: "0xA238Dd80C259a72e81d7e4664a9801593F98d1c5",
};

const ERC20_BALANCE_ABI = [
  {
    name: "balanceOf",
    type: "function",
    stateMutability: "view",
    inputs: [{ name: "account", type: "address" }],
    outputs: [{ name: "", type: "uint256" }],
  },
] as const;

const chainFlag = process.argv.indexOf("--chain");
const chainName = (chainFlag !== -1 ? process.argv[chainFlag + 1] : "ethereum") as keyof typeof CHAIN_MAP;

const chain = CHAIN_MAP[chainName];
const poolAddress = AAVE_POOL[chainName];
const assets = ASSETS[chainName];

if (!chain || !poolAddress || !assets) {
  console.error(`Chain "${chainName}" not supported. Available: ethereum, arbitrum, polygon, base`);
  process.exit(1);
}

const client = createPublicClient({
  chain,
  transport: http(RPC_URLS[chainName]),
});

console.log("══════════════════════════════════════════════════════════════════");
console.log(`  ⚡ Flash Loan Liquidity — Aave V3 (${chain.name})`);
console.log("══════════════════════════════════════════════════════════════════");
console.log("  Asset  | Available Liquidity        | Flash Fee (0.05%)");
console.log("  ───────|───────────────────────────|──────────────────");

for (const asset of assets) {
  try {
    // Flash loan liquidity ≈ aToken balance in the Pool (total supplied)
    const balance = await client.readContract({
      address: asset.address,
      abi: ERC20_BALANCE_ABI,
      functionName: "balanceOf",
      args: [poolAddress],
    });

    const amount = parseFloat(formatUnits(balance, asset.decimals));
    const fee = amount * 0.0005; // 0.05% fee

    const fmtAmount = amount >= 1e6
      ? `${(amount / 1e6).toFixed(2)}M`
      : amount >= 1e3
        ? `${(amount / 1e3).toFixed(2)}K`
        : amount.toFixed(4);

    const fmtFee = fee >= 1e3
      ? `${(fee / 1e3).toFixed(2)}K`
      : fee.toFixed(4);

    const sym = asset.symbol.padEnd(6);
    const liq = `${fmtAmount} ${asset.symbol}`.padEnd(25);

    console.log(`  ${sym} | ${liq} | ${fmtFee} ${asset.symbol}`);
  } catch {
    console.log(`  ${asset.symbol.padEnd(6)} | Error fetching               |`);
  }
}

console.log("══════════════════════════════════════════════════════════════════");
console.log("  Note: Actual available liquidity may be lower due to borrows.");
console.log("  Flash loans can borrow up to the total supplied amount.");

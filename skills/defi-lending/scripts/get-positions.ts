/**
 * DeFi Lending — Get User Positions (Aave V3)
 *
 * Queries Aave V3 Pool contract to get user account data:
 * total collateral, total debt, available borrows, LTV, health factor.
 * Uses free public RPC — no API key required.
 *
 * Usage:
 *   npx tsx get-positions.ts <address> [--chain ethereum]
 */

import { createPublicClient, http, formatUnits, type Address } from "viem";
import { mainnet, base, arbitrum, polygon, optimism, avalanche } from "viem/chains";

const CHAIN_MAP = { ethereum: mainnet, base, arbitrum, polygon, optimism, avalanche } as const;
const RPC_URLS: Record<string, string> = {
  ethereum: "https://cloudflare-eth.com",
  base: "https://mainnet.base.org",
  arbitrum: "https://arb1.arbitrum.io/rpc",
  polygon: "https://polygon-rpc.com",
  optimism: "https://mainnet.optimism.io",
  avalanche: "https://api.avax.network/ext/bc/C/rpc",
};

// Aave V3 Pool addresses (retrieved via PoolAddressesProvider)
const AAVE_POOL: Record<string, Address> = {
  ethereum: "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
  arbitrum: "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
  polygon: "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
  base: "0xA238Dd80C259a72e81d7e4664a9801593F98d1c5",
  optimism: "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
  avalanche: "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
};

const POOL_ABI = [
  {
    name: "getUserAccountData",
    type: "function",
    stateMutability: "view",
    inputs: [{ name: "user", type: "address" }],
    outputs: [
      { name: "totalCollateralBase", type: "uint256" },
      { name: "totalDebtBase", type: "uint256" },
      { name: "availableBorrowsBase", type: "uint256" },
      { name: "currentLiquidationThreshold", type: "uint256" },
      { name: "ltv", type: "uint256" },
      { name: "healthFactor", type: "uint256" },
    ],
  },
] as const;

const address = process.argv[2] as Address | undefined;
const chainFlag = process.argv.indexOf("--chain");
const chainName = chainFlag !== -1 ? (process.argv[chainFlag + 1] as keyof typeof CHAIN_MAP) : "ethereum";

if (!address) {
  console.error("Usage: npx tsx get-positions.ts <address> [--chain ethereum]");
  process.exit(1);
}

const chain = CHAIN_MAP[chainName];
const poolAddress = AAVE_POOL[chainName];

if (!chain || !poolAddress) {
  console.error(`Chain "${chainName}" not supported`);
  process.exit(1);
}

const client = createPublicClient({
  chain,
  transport: http(RPC_URLS[chainName]),
});

try {
  const result = await client.readContract({
    address: poolAddress,
    abi: POOL_ABI,
    functionName: "getUserAccountData",
    args: [address],
  });

  const [totalCollateral, totalDebt, availableBorrows, liqThreshold, ltv, healthFactor] = result;

  // Aave returns values in base currency units (USD with 8 decimals)
  const collateralUsd = parseFloat(formatUnits(totalCollateral, 8));
  const debtUsd = parseFloat(formatUnits(totalDebt, 8));
  const availableUsd = parseFloat(formatUnits(availableBorrows, 8));
  const hf = parseFloat(formatUnits(healthFactor, 18));

  const hfDisplay = hf > 1000 ? "∞ (no debt)" : hf.toFixed(4);
  const hfIcon = hf > 2 ? "🟢" : hf > 1.2 ? "🟡" : "🔴";

  console.log("══════════════════════════════════════════════════");
  console.log("  🏛️  Aave V3 Position");
  console.log("══════════════════════════════════════════════════");
  console.log(`  Address:          ${address}`);
  console.log(`  Chain:            ${chain.name}`);
  console.log("──────────────────────────────────────────────────");
  console.log(`  Collateral:       $${collateralUsd.toLocaleString(undefined, { maximumFractionDigits: 2 })}`);
  console.log(`  Debt:             $${debtUsd.toLocaleString(undefined, { maximumFractionDigits: 2 })}`);
  console.log(`  Available Borrow: $${availableUsd.toLocaleString(undefined, { maximumFractionDigits: 2 })}`);
  console.log(`  LTV:              ${(Number(ltv) / 100).toFixed(2)}%`);
  console.log(`  Liq. Threshold:   ${(Number(liqThreshold) / 100).toFixed(2)}%`);
  console.log(`  Health Factor:    ${hfIcon} ${hfDisplay}`);

  if (hf < 1.2 && hf > 0) {
    console.log("");
    console.log("  ⚠️  WARNING: Health factor is LOW — liquidation risk!");
    console.log("  ⚠️  Consider repaying debt or supplying more collateral.");
  }

  console.log("══════════════════════════════════════════════════");
} catch (error) {
  console.error("Failed to read position:", (error as Error).message);
  process.exit(1);
}

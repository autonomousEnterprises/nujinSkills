export {};
/**
 * DeFi Lending — Get Current Rates
 *
 * Fetches current supply and borrow APY rates from Aave V3.
 * Uses DeFiLlama yields API for rate data (free, no key).
 *
 * Usage:
 *   npx tsx get-rates.ts                        → All Aave V3 pools
 *   npx tsx get-rates.ts --chain ethereum       → Ethereum only
 *   npx tsx get-rates.ts --protocol aave-v3     → Aave V3 (default)
 *   npx tsx get-rates.ts --protocol compound-v3 → Compound V3
 */

function getArg(flag: string): string | undefined {
  const idx = process.argv.indexOf(flag);
  return idx !== -1 ? process.argv[idx + 1] : undefined;
}

const chainFilter = getArg("--chain")?.toLowerCase();
const protocol = getArg("--protocol") || "aave-v3";

interface YieldPool {
  pool: string;
  chain: string;
  project: string;
  symbol: string;
  tvlUsd: number;
  apy: number;
  apyBase: number;
  apyReward: number;
  apyBaseBorrow?: number;
  apyRewardBorrow?: number;
  totalSupplyUsd?: number;
  totalBorrowUsd?: number;
}

const response = await fetch("https://yields.llama.fi/pools");
if (!response.ok) {
  console.error("DeFiLlama API error:", response.status);
  process.exit(1);
}

const { data } = (await response.json()) as { data: YieldPool[] };

const pools = data
  .filter((p) => p.project === protocol)
  .filter((p) => !chainFilter || p.chain.toLowerCase() === chainFilter)
  .filter((p) => p.tvlUsd > 100000) // Min $100K TVL
  .sort((a, b) => b.tvlUsd - a.tvlUsd);

const fmtVal = (v: number | undefined) => {
  if (!v) return "—";
  if (v >= 1e9) return `$${(v / 1e9).toFixed(2)}B`;
  if (v >= 1e6) return `$${(v / 1e6).toFixed(2)}M`;
  return `$${(v / 1e3).toFixed(0)}K`;
};

const fmtApy = (v: number | undefined) => {
  if (v === undefined || v === null) return "  —    ";
  return `${v.toFixed(2)}%`.padStart(7);
};

const label = protocol.toUpperCase();
const chainLabel = chainFilter ? ` (${chainFilter})` : "";

console.log("══════════════════════════════════════════════════════════════════════════════════════");
console.log(`  🏛️  ${label} Lending Rates${chainLabel}`);
console.log("══════════════════════════════════════════════════════════════════════════════════════");
console.log("  Asset           | Chain      | Supply APY | Borrow APY | TVL");
console.log("  ────────────────|────────────|────────────|────────────|──────────────");

for (const pool of pools.slice(0, 25)) {
  const symbol = pool.symbol.slice(0, 15).padEnd(15);
  const chain = pool.chain.slice(0, 10).padEnd(10);
  const supplyApy = fmtApy(pool.apyBase).padEnd(10);
  const borrowApy = fmtApy(pool.apyBaseBorrow).padEnd(10);
  const tvl = fmtVal(pool.tvlUsd);

  console.log(`  ${symbol} | ${chain} | ${supplyApy} | ${borrowApy} | ${tvl}`);
}

console.log("══════════════════════════════════════════════════════════════════════════════════════");
console.log("  Source: DeFiLlama Yields API (free, no API key)");

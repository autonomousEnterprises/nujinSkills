export {};
/**
 * DeFi Market — Get Yield Pools
 *
 * Fetches top yield farming opportunities from DeFiLlama.
 * Filterable by chain and minimum TVL.
 * Source: DeFiLlama Yields API (free, no API key).
 *
 * Usage:
 *   npx tsx get-yields.ts                           → Top 20 pools by APY
 *   npx tsx get-yields.ts --chain ethereum           → Ethereum pools only
 *   npx tsx get-yields.ts --chain arbitrum --min-tvl 1000000 → Arbitrum, >$1M TVL
 */

const chainFlag = process.argv.indexOf("--chain");
const chainFilter = chainFlag !== -1 ? process.argv[chainFlag + 1]?.toLowerCase() : undefined;
const minTvlFlag = process.argv.indexOf("--min-tvl");
const minTvl = minTvlFlag !== -1 ? parseFloat(process.argv[minTvlFlag + 1]) : 100000;
const limitFlag = process.argv.indexOf("--limit");
const limit = limitFlag !== -1 ? parseInt(process.argv[limitFlag + 1]) : 20;

interface YieldPool {
  pool: string;
  chain: string;
  project: string;
  symbol: string;
  tvlUsd: number;
  apy: number;
  apyBase?: number;
  apyReward?: number;
  stablecoin: boolean;
  ilRisk: string;
}

const response = await fetch("https://yields.llama.fi/pools");
if (!response.ok) {
  console.error("DeFiLlama Yields API error:", response.status);
  process.exit(1);
}

const { data } = (await response.json()) as { data: YieldPool[] };

const fmtTvl = (tvl: number) => {
  if (tvl >= 1e9) return `$${(tvl / 1e9).toFixed(2)}B`;
  if (tvl >= 1e6) return `$${(tvl / 1e6).toFixed(2)}M`;
  if (tvl >= 1e3) return `$${(tvl / 1e3).toFixed(0)}K`;
  return `$${tvl.toFixed(0)}`;
};

// Filter and sort
let pools = data
  .filter((p) => p.tvlUsd >= minTvl && p.apy > 0 && p.apy < 10000) // Filter unrealistic APYs
  .filter((p) => !chainFilter || p.chain.toLowerCase() === chainFilter);

pools.sort((a, b) => b.apy - a.apy);
pools = pools.slice(0, limit);

const chainLabel = chainFilter ? chainFilter.charAt(0).toUpperCase() + chainFilter.slice(1) : "All Chains";

console.log("═══════════════════════════════════════════════════════════════════════════════════");
console.log(`  🌾 Top Yield Pools — ${chainLabel} (min TVL: ${fmtTvl(minTvl)})`);
console.log("═══════════════════════════════════════════════════════════════════════════════════");
console.log("  #  | Protocol         | Pool             | Chain      | APY      | TVL");
console.log("  ───|──────────────────|──────────────────|────────────|──────────|──────────");

pools.forEach((p, i) => {
  const rank = String(i + 1).padStart(3);
  const project = p.project.slice(0, 16).padEnd(16);
  const symbol = p.symbol.slice(0, 16).padEnd(16);
  const chain = p.chain.slice(0, 10).padEnd(10);
  const apy = `${p.apy.toFixed(2)}%`.padStart(8);
  const tvl = fmtTvl(p.tvlUsd);

  console.log(`  ${rank} | ${project} | ${symbol} | ${chain} | ${apy} | ${tvl}`);
});

console.log("═══════════════════════════════════════════════════════════════════════════════════");
console.log("  Source: DeFiLlama Yields API (free, no API key)");

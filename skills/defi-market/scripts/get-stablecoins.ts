export {};
/**
 * DeFi Market — Stablecoin Analytics
 *
 * Fetches stablecoin market data from DeFiLlama.
 * Source: DeFiLlama Stablecoins API (free, no API key).
 *
 * Usage:
 *   npx tsx get-stablecoins.ts              → All stablecoins by market cap
 *   npx tsx get-stablecoins.ts --chains     → Stablecoin market cap by chain
 */

const showChains = process.argv.includes("--chains");

const fmtCap = (c: number) => {
  if (c >= 1e12) return `$${(c / 1e12).toFixed(2)}T`;
  if (c >= 1e9) return `$${(c / 1e9).toFixed(2)}B`;
  if (c >= 1e6) return `$${(c / 1e6).toFixed(2)}M`;
  return `$${c.toLocaleString()}`;
};

if (showChains) {
  interface ChainStable {
    [chain: string]: { peggedUSD: number };
  }

  const response = await fetch("https://stablecoins.llama.fi/stablecoinchains");
  const chains = (await response.json()) as Array<{ name: string; totalCirculatingUSD: { peggedUSD: number } }>;

  const sorted = chains
    .filter((c) => c.totalCirculatingUSD?.peggedUSD > 0)
    .sort((a, b) => b.totalCirculatingUSD.peggedUSD - a.totalCirculatingUSD.peggedUSD)
    .slice(0, 20);

  console.log("══════════════════════════════════════════════════");
  console.log("  🏦 Stablecoin Market Cap by Chain — Top 20");
  console.log("══════════════════════════════════════════════════");
  console.log("  #  | Chain           | Stablecoin Market Cap");
  console.log("  ───|─────────────────|──────────────────────");

  sorted.forEach((c, i) => {
    const rank = String(i + 1).padStart(3);
    const name = c.name.padEnd(15);
    console.log(`  ${rank} | ${name} | ${fmtCap(c.totalCirculatingUSD.peggedUSD)}`);
  });

  console.log("══════════════════════════════════════════════════");
} else {
  interface Stablecoin {
    id: string;
    name: string;
    symbol: string;
    gecko_id: string;
    pegType: string;
    pegMechanism: string;
    circulating: { peggedUSD: number };
    chains: string[];
  }

  interface StableResponse {
    peggedAssets: Stablecoin[];
  }

  const response = await fetch("https://stablecoins.llama.fi/stablecoins?includePrices=true");
  const data = (await response.json()) as StableResponse;

  const sorted = data.peggedAssets
    .filter((s) => s.circulating?.peggedUSD > 0)
    .sort((a, b) => b.circulating.peggedUSD - a.circulating.peggedUSD)
    .slice(0, 20);

  console.log("══════════════════════════════════════════════════════════════════════════════");
  console.log("  🪙 Stablecoins — Top 20 by Market Cap");
  console.log("══════════════════════════════════════════════════════════════════════════════");
  console.log("  #  | Name            | Symbol | Market Cap    | Peg Type   | Chains");
  console.log("  ───|─────────────────|────────|───────────────|────────────|────────");

  sorted.forEach((s, i) => {
    const rank = String(i + 1).padStart(3);
    const name = s.name.slice(0, 15).padEnd(15);
    const symbol = s.symbol.padEnd(6);
    const cap = fmtCap(s.circulating.peggedUSD).padEnd(13);
    const peg = (s.pegType || "—").slice(0, 10).padEnd(10);
    const chains = (s.chains?.length ?? 0).toString();

    console.log(`  ${rank} | ${name} | ${symbol} | ${cap} | ${peg} | ${chains}`);
  });

  console.log("══════════════════════════════════════════════════════════════════════════════");
}

console.log("  Source: DeFiLlama Stablecoins API (free, no API key)");

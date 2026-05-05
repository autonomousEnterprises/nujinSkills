export {};
/**
 * DeFi Market — Get DEX Volumes
 *
 * Fetches DEX trading volumes from DeFiLlama.
 * Source: DeFiLlama (free, no API key).
 *
 * Usage:
 *   npx tsx get-dex-volumes.ts                    → Top DEXs by volume
 *   npx tsx get-dex-volumes.ts --chain ethereum   → Ethereum DEXs only
 */

const chainFlag = process.argv.indexOf("--chain");
const chainFilter = chainFlag !== -1 ? process.argv[chainFlag + 1] : undefined;

interface DexProtocol {
  name: string;
  total24h?: number;
  total7d?: number;
  total30d?: number;
  totalAllTime?: number;
  change_1d?: number;
  chains?: string[];
}

interface DexOverview {
  protocols: DexProtocol[];
  total24h?: number;
  total7d?: number;
}

const url = chainFilter
  ? `https://api.llama.fi/overview/dexs/${chainFilter}`
  : "https://api.llama.fi/overview/dexs";

const response = await fetch(url);
if (!response.ok) {
  console.error("DeFiLlama DEX API error:", response.status);
  process.exit(1);
}

const data = (await response.json()) as DexOverview;

const fmtVol = (v: number | undefined) => {
  if (!v) return "—";
  if (v >= 1e12) return `$${(v / 1e12).toFixed(2)}T`;
  if (v >= 1e9) return `$${(v / 1e9).toFixed(2)}B`;
  if (v >= 1e6) return `$${(v / 1e6).toFixed(2)}M`;
  if (v >= 1e3) return `$${(v / 1e3).toFixed(0)}K`;
  return `$${v.toFixed(0)}`;
};

const sorted = data.protocols
  .filter((p) => (p.total24h ?? 0) > 0)
  .sort((a, b) => (b.total24h ?? 0) - (a.total24h ?? 0))
  .slice(0, 20);

const chainLabel = chainFilter || "All Chains";

console.log("═══════════════════════════════════════════════════════════════════════");
console.log(`  🔄 DEX Volumes — ${chainLabel}`);
if (data.total24h) {
  console.log(`  Total 24h Volume: ${fmtVol(data.total24h)}`);
}
console.log("═══════════════════════════════════════════════════════════════════════");
console.log("  #  | DEX              | 24h Volume    | 7d Volume     | 24h Change");
console.log("  ───|──────────────────|───────────────|───────────────|───────────");

sorted.forEach((dex, i) => {
  const rank = String(i + 1).padStart(3);
  const name = dex.name.slice(0, 16).padEnd(16);
  const vol24 = fmtVol(dex.total24h).padEnd(13);
  const vol7d = fmtVol(dex.total7d).padEnd(13);
  const change = dex.change_1d != null ? `${dex.change_1d >= 0 ? "+" : ""}${dex.change_1d.toFixed(1)}%` : "—";

  console.log(`  ${rank} | ${name} | ${vol24} | ${vol7d} | ${change}`);
});

console.log("═══════════════════════════════════════════════════════════════════════");
console.log("  Source: DeFiLlama (free, no API key)");

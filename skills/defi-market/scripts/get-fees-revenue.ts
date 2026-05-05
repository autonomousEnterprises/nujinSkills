export {};
/**
 * DeFi Market — Get Fees & Revenue
 *
 * Fetches protocol fee and revenue data from DeFiLlama.
 * Source: DeFiLlama (free, no API key).
 *
 * Usage:
 *   npx tsx get-fees-revenue.ts → Top protocols by 24h fees
 */

interface FeeProtocol {
  name: string;
  total24h?: number;
  total7d?: number;
  total30d?: number;
  totalAllTime?: number;
  revenue24h?: number;
  change_1d?: number;
  category?: string;
}

interface FeesOverview {
  protocols: FeeProtocol[];
  total24h?: number;
}

const response = await fetch("https://api.llama.fi/overview/fees");
if (!response.ok) {
  console.error("DeFiLlama Fees API error:", response.status);
  process.exit(1);
}

const data = (await response.json()) as FeesOverview;

const fmtVal = (v: number | undefined) => {
  if (!v) return "—";
  if (v >= 1e9) return `$${(v / 1e9).toFixed(2)}B`;
  if (v >= 1e6) return `$${(v / 1e6).toFixed(2)}M`;
  if (v >= 1e3) return `$${(v / 1e3).toFixed(0)}K`;
  return `$${v.toFixed(0)}`;
};

const sorted = data.protocols
  .filter((p) => (p.total24h ?? 0) > 0)
  .sort((a, b) => (b.total24h ?? 0) - (a.total24h ?? 0))
  .slice(0, 20);

console.log("══════════════════════════════════════════════════════════════════════════════");
console.log("  💸 Protocol Fees & Revenue — Top 20");
if (data.total24h) {
  console.log(`  Total 24h Fees: ${fmtVal(data.total24h)}`);
}
console.log("══════════════════════════════════════════════════════════════════════════════");
console.log("  #  | Protocol         | 24h Fees      | 30d Fees      | Category");
console.log("  ───|──────────────────|───────────────|───────────────|──────────────");

sorted.forEach((p, i) => {
  const rank = String(i + 1).padStart(3);
  const name = p.name.slice(0, 16).padEnd(16);
  const fees24 = fmtVal(p.total24h).padEnd(13);
  const fees30 = fmtVal(p.total30d).padEnd(13);
  const cat = (p.category || "—").slice(0, 12);

  console.log(`  ${rank} | ${name} | ${fees24} | ${fees30} | ${cat}`);
});

console.log("══════════════════════════════════════════════════════════════════════════════");
console.log("  Source: DeFiLlama (free, no API key)");

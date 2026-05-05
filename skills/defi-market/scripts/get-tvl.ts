export {};
/**
 * DeFi Market — Get TVL
 *
 * Fetches Total Value Locked for DeFi protocols and chains.
 * Source: DeFiLlama (free, no API key).
 *
 * Usage:
 *   npx tsx get-tvl.ts                     → Top 20 protocols by TVL
 *   npx tsx get-tvl.ts --protocol aave     → Specific protocol TVL
 *   npx tsx get-tvl.ts --chains            → TVL by chain
 */

const protocolFlag = process.argv.indexOf("--protocol");
const protocolName = protocolFlag !== -1 ? process.argv[protocolFlag + 1] : undefined;
const showChains = process.argv.includes("--chains");

const fmtTvl = (tvl: number) => {
  if (tvl >= 1e12) return `$${(tvl / 1e12).toFixed(2)}T`;
  if (tvl >= 1e9) return `$${(tvl / 1e9).toFixed(2)}B`;
  if (tvl >= 1e6) return `$${(tvl / 1e6).toFixed(2)}M`;
  if (tvl >= 1e3) return `$${(tvl / 1e3).toFixed(2)}K`;
  return `$${tvl.toFixed(2)}`;
};

if (protocolName) {
  // Specific protocol
  const response = await fetch(`https://api.llama.fi/tvl/${protocolName}`);
  if (!response.ok) {
    console.error(`Protocol "${protocolName}" not found`);
    process.exit(1);
  }
  const tvl = (await response.json()) as number;

  console.log("══════════════════════════════════════════════════");
  console.log(`  🏦 ${protocolName} — TVL`);
  console.log("══════════════════════════════════════════════════");
  console.log(`  TVL: ${fmtTvl(tvl)}`);
  console.log("══════════════════════════════════════════════════");
} else if (showChains) {
  // TVL by chain
  interface ChainTvl {
    gecko_id: string;
    tvl: number;
    tokenSymbol: string;
    name: string;
  }

  const response = await fetch("https://api.llama.fi/v2/chains");
  const chains = (await response.json()) as ChainTvl[];

  const sorted = chains.sort((a, b) => b.tvl - a.tvl).slice(0, 25);

  console.log("══════════════════════════════════════════════════════════════");
  console.log("  ⛓️  DeFi TVL by Chain — Top 25");
  console.log("══════════════════════════════════════════════════════════════");
  console.log("  #  | Chain           | TVL");
  console.log("  ───|─────────────────|──────────────");

  sorted.forEach((chain, i) => {
    const rank = String(i + 1).padStart(3);
    const name = chain.name.padEnd(15);
    console.log(`  ${rank} | ${name} | ${fmtTvl(chain.tvl)}`);
  });

  console.log("══════════════════════════════════════════════════════════════");
} else {
  // Top protocols by TVL
  interface Protocol {
    name: string;
    tvl: number;
    chain: string;
    category: string;
    change_1d?: number;
    change_7d?: number;
  }

  const response = await fetch("https://api.llama.fi/protocols");
  const protocols = (await response.json()) as Protocol[];

  const sorted = protocols
    .filter((p) => p.tvl > 0)
    .sort((a, b) => b.tvl - a.tvl)
    .slice(0, 20);

  console.log("════════════════════════════════════════════════════════════════════════════");
  console.log("  🏦 DeFi TVL — Top 20 Protocols");
  console.log("════════════════════════════════════════════════════════════════════════════");
  console.log("  #  | Protocol         | TVL           | Chain          | Category");
  console.log("  ───|──────────────────|───────────────|────────────────|──────────────");

  sorted.forEach((p, i) => {
    const rank = String(i + 1).padStart(3);
    const name = p.name.slice(0, 16).padEnd(16);
    const tvl = fmtTvl(p.tvl).padEnd(13);
    const chain = (p.chain || "Multi").slice(0, 14).padEnd(14);
    const cat = (p.category || "—").slice(0, 12);

    console.log(`  ${rank} | ${name} | ${tvl} | ${chain} | ${cat}`);
  });

  console.log("════════════════════════════════════════════════════════════════════════════");
  console.log("  Source: DeFiLlama (free, no API key)");
}

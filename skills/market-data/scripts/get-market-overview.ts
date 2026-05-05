export {};
/**
 * Market Data — Market Overview (Top Coins)
 *
 * Fetches top cryptocurrencies by market cap from CoinGecko.
 * No API key required.
 *
 * Usage:
 *   npx tsx get-market-overview.ts              → Top 20 by market cap
 *   npx tsx get-market-overview.ts --limit 50   → Top 50
 */

const limitFlag = process.argv.indexOf("--limit");
const limit = limitFlag !== -1 ? parseInt(process.argv[limitFlag + 1]) : 20;

interface CoinMarket {
  id: string;
  symbol: string;
  name: string;
  current_price: number;
  market_cap: number;
  market_cap_rank: number;
  total_volume: number;
  price_change_percentage_24h: number;
}

const url = `https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=${limit}&page=1&sparkline=false`;

const response = await fetch(url);

if (!response.ok) {
  console.error(`CoinGecko API error: ${response.status}`);
  process.exit(1);
}

const coins = (await response.json()) as CoinMarket[];

const fmtPrice = (p: number) => {
  if (p >= 1000) return `$${p.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
  if (p >= 1) return `$${p.toFixed(2)}`;
  return `$${p.toFixed(6)}`;
};

const fmtCap = (c: number) => {
  if (c >= 1e12) return `$${(c / 1e12).toFixed(2)}T`;
  if (c >= 1e9) return `$${(c / 1e9).toFixed(2)}B`;
  if (c >= 1e6) return `$${(c / 1e6).toFixed(2)}M`;
  return `$${c.toLocaleString()}`;
};

console.log("══════════════════════════════════════════════════════════════════════════════");
console.log(`  🌍 Market Overview — Top ${coins.length} by Market Cap`);
console.log("══════════════════════════════════════════════════════════════════════════════");
console.log("  #  | Symbol  | Price          | 24h Change  | Market Cap    | Volume 24h");
console.log("  ───|─────────|────────────────|─────────────|───────────────|──────────────");

for (const coin of coins) {
  const rank = String(coin.market_cap_rank).padStart(3);
  const sym = coin.symbol.toUpperCase().padEnd(7);
  const price = fmtPrice(coin.current_price).padEnd(14);
  const change = coin.price_change_percentage_24h;
  const changeStr = `${change >= 0 ? "🟢+" : "🔴"}${change?.toFixed(2) ?? "N/A"}%`.padEnd(11);
  const cap = fmtCap(coin.market_cap).padEnd(13);
  const vol = fmtCap(coin.total_volume);

  console.log(`  ${rank} | ${sym} | ${price} | ${changeStr} | ${cap} | ${vol}`);
}

console.log("══════════════════════════════════════════════════════════════════════════════");
console.log("  Source: CoinGecko (free tier, no API key)");

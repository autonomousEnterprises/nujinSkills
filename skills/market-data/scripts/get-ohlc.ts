export {};
/**
 * Market Data — Get OHLC Candlestick Data
 *
 * Fetches OHLC (Open, High, Low, Close) candlestick data from Binance.
 * No API key required.
 *
 * Usage:
 *   npx tsx get-ohlc.ts BTCUSDT --interval 1h --limit 24
 *   npx tsx get-ohlc.ts ETHUSDT --interval 1d --limit 30
 *
 * Intervals: 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M
 */

const symbol = process.argv[2]?.toUpperCase();
const intervalFlag = process.argv.indexOf("--interval");
const interval = intervalFlag !== -1 ? process.argv[intervalFlag + 1] : "1h";
const limitFlag = process.argv.indexOf("--limit");
const limit = limitFlag !== -1 ? parseInt(process.argv[limitFlag + 1]) : 24;

if (!symbol) {
  console.error("Usage: npx tsx get-ohlc.ts <SYMBOL> [--interval 1h] [--limit 24]");
  console.error("Intervals: 1m, 5m, 15m, 1h, 4h, 1d, 1w, 1M");
  process.exit(1);
}

const url = `https://api.binance.com/api/v3/klines?symbol=${symbol}&interval=${interval}&limit=${limit}`;
const response = await fetch(url);

if (!response.ok) {
  console.error(`Binance API error: ${response.status}`);
  process.exit(1);
}

type KlineArray = [
  number, string, string, string, string, string,
  number, string, number, string, string, string
];

const klines = (await response.json()) as KlineArray[];

console.log("══════════════════════════════════════════════════════════════════════");
console.log(`  📈 ${symbol} — ${interval} candles (last ${klines.length})`);
console.log("══════════════════════════════════════════════════════════════════════");
console.log("  Time                | Open       | High       | Low        | Close      | Volume");
console.log("  ────────────────────|────────────|────────────|────────────|────────────|──────────");

for (const k of klines) {
  const time = new Date(k[0]).toISOString().replace("T", " ").slice(0, 16);
  const open = parseFloat(k[1]).toFixed(2).padStart(10);
  const high = parseFloat(k[2]).toFixed(2).padStart(10);
  const low = parseFloat(k[3]).toFixed(2).padStart(10);
  const close = parseFloat(k[4]).toFixed(2).padStart(10);
  const vol = parseFloat(k[5]).toFixed(2).padStart(10);

  console.log(`  ${time} | ${open} | ${high} | ${low} | ${close} | ${vol}`);
}

console.log("══════════════════════════════════════════════════════════════════════");

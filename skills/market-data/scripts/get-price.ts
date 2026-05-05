export {};
/**
 * Market Data — Get Current Price
 *
 * Fetches the current price for a crypto trading pair.
 * Primary: Binance API. Fallback: CoinGecko API.
 * No API key required.
 *
 * Usage:
 *   npx tsx get-price.ts BTC               → BTC/USDT from Binance
 *   npx tsx get-price.ts ETH               → ETH/USDT from Binance
 *   npx tsx get-price.ts BTCETH            → BTC/ETH from Binance
 *   npx tsx get-price.ts bitcoin --gecko   → Bitcoin from CoinGecko
 */

const symbol = process.argv[2]?.toUpperCase();
const useGecko = process.argv.includes("--gecko");

if (!symbol) {
  console.error("Usage: npx tsx get-price.ts <SYMBOL> [--gecko]");
  console.error("Examples: BTC, ETH, SOL, BTCETH, AVAXUSDT");
  process.exit(1);
}

interface BinancePrice {
  symbol: string;
  price: string;
}

interface BinanceTicker {
  symbol: string;
  priceChange: string;
  priceChangePercent: string;
  lastPrice: string;
  highPrice: string;
  lowPrice: string;
  volume: string;
  quoteVolume: string;
}

interface CoinGeckoPrice {
  [id: string]: { usd: number; usd_24h_change?: number; usd_24h_vol?: number; usd_market_cap?: number };
}

if (useGecko) {
  // CoinGecko path — use slug (e.g., "bitcoin", "ethereum")
  const id = symbol.toLowerCase();
  const url = `https://api.coingecko.com/api/v3/simple/price?ids=${id}&vs_currencies=usd&include_24hr_change=true&include_24hr_vol=true&include_market_cap=true`;

  const response = await fetch(url);
  if (!response.ok) throw new Error(`CoinGecko error: ${response.status}`);
  const data = (await response.json()) as CoinGeckoPrice;

  const coin = data[id];
  if (!coin) {
    console.error(`Token "${id}" not found on CoinGecko. Use the slug (e.g., "bitcoin", "ethereum").`);
    process.exit(1);
  }

  console.log("══════════════════════════════════════════════════");
  console.log(`  📊 ${id} (CoinGecko)`);
  console.log("══════════════════════════════════════════════════");
  console.log(`  Price:       $${coin.usd.toLocaleString()}`);
  console.log(`  24h Change:  ${coin.usd_24h_change?.toFixed(2)}%`);
  console.log(`  24h Volume:  $${coin.usd_24h_vol?.toLocaleString()}`);
  console.log(`  Market Cap:  $${coin.usd_market_cap?.toLocaleString()}`);
  console.log("══════════════════════════════════════════════════");
} else {
  // Binance path — append USDT if needed
  const pair = symbol.includes("USDT") || symbol.includes("BTC") || symbol.includes("ETH") || symbol.includes("BNB")
    ? symbol
    : `${symbol}USDT`;

  // Fetch 24h ticker for more data
  const url = `https://api.binance.com/api/v3/ticker/24hr?symbol=${pair}`;
  const response = await fetch(url);

  if (!response.ok) {
    // Try with USDT suffix
    const fallbackUrl = `https://api.binance.com/api/v3/ticker/24hr?symbol=${symbol}USDT`;
    const fallbackResponse = await fetch(fallbackUrl);
    if (!fallbackResponse.ok) {
      console.error(`Symbol "${pair}" not found on Binance.`);
      process.exit(1);
    }
    const data = (await fallbackResponse.json()) as BinanceTicker;
    printBinanceTicker(data);
  } else {
    const data = (await response.json()) as BinanceTicker;
    printBinanceTicker(data);
  }
}

function printBinanceTicker(data: BinanceTicker) {
  const price = parseFloat(data.lastPrice);
  const changePercent = parseFloat(data.priceChangePercent);
  const high = parseFloat(data.highPrice);
  const low = parseFloat(data.lowPrice);
  const volume = parseFloat(data.quoteVolume);

  const arrow = changePercent >= 0 ? "🟢" : "🔴";

  console.log("══════════════════════════════════════════════════");
  console.log(`  📊 ${data.symbol} (Binance)`);
  console.log("══════════════════════════════════════════════════");
  console.log(`  Price:       $${price.toLocaleString()}`);
  console.log(`  24h Change:  ${arrow} ${changePercent >= 0 ? "+" : ""}${changePercent.toFixed(2)}%`);
  console.log(`  24h High:    $${high.toLocaleString()}`);
  console.log(`  24h Low:     $${low.toLocaleString()}`);
  console.log(`  24h Volume:  $${volume.toLocaleString()}`);
  console.log("══════════════════════════════════════════════════");
}

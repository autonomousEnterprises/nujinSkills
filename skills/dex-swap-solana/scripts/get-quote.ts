export {};
/**
 * Solana DEX Swap — Get Quote (Jupiter)
 *
 * Gets the best swap quote across all Solana DEXs via Jupiter Aggregator.
 * No API key required (keyless tier, rate-limited).
 *
 * Usage:
 *   npx tsx get-quote.ts --from SOL --to USDC --amount 1
 *   npx tsx get-quote.ts --from USDC --to SOL --amount 100
 *   npx tsx get-quote.ts --from <mint> --to <mint> --amount 1 --slippage 100
 */

// ─── Token Mint Shortcuts ────────────────────────────────────────────────────

const MINTS: Record<string, { address: string; decimals: number; symbol: string }> = {
  SOL: { address: "So11111111111111111111111111111111111111112", decimals: 9, symbol: "SOL" },
  USDC: { address: "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", decimals: 6, symbol: "USDC" },
  USDT: { address: "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB", decimals: 6, symbol: "USDT" },
  JUP: { address: "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN", decimals: 6, symbol: "JUP" },
  BONK: { address: "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263", decimals: 5, symbol: "BONK" },
  RAY: { address: "4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R", decimals: 6, symbol: "RAY" },
};

function getArg(flag: string): string | undefined {
  const idx = process.argv.indexOf(flag);
  return idx !== -1 ? process.argv[idx + 1] : undefined;
}

const fromArg = getArg("--from");
const toArg = getArg("--to");
const amountArg = getArg("--amount");
const slippageBps = parseInt(getArg("--slippage") || "50"); // Default 0.5%

if (!fromArg || !toArg || !amountArg) {
  console.error("Usage: npx tsx get-quote.ts --from <token> --to <token> --amount <amount> [--slippage 50]");
  console.error("Tokens: SOL, USDC, USDT, JUP, BONK, RAY, or a mint address");
  process.exit(1);
}

function resolveToken(input: string) {
  const shortcut = MINTS[input.toUpperCase()];
  if (shortcut) return shortcut;
  return { address: input, decimals: 9, symbol: input.slice(0, 6) + "..." };
}

const tokenIn = resolveToken(fromArg);
const tokenOut = resolveToken(toArg);
const amount = Math.round(parseFloat(amountArg) * 10 ** tokenIn.decimals);

// ─── Jupiter Quote API ──────────────────────────────────────────────────────

interface JupiterQuote {
  inputMint: string;
  outputMint: string;
  inAmount: string;
  outAmount: string;
  otherAmountThreshold: string;
  swapMode: string;
  slippageBps: number;
  priceImpactPct: string;
  routePlan: Array<{
    swapInfo: {
      ammKey: string;
      label: string;
      inputMint: string;
      outputMint: string;
      inAmount: string;
      outAmount: string;
      feeAmount: string;
      feeMint: string;
    };
    percent: number;
  }>;
}

const params = new URLSearchParams({
  inputMint: tokenIn.address,
  outputMint: tokenOut.address,
  amount: amount.toString(),
  slippageBps: slippageBps.toString(),
});

const url = `https://api.jup.ag/quote?${params}`;
const response = await fetch(url);

if (!response.ok) {
  const text = await response.text();
  console.error(`Jupiter API error: ${response.status}`, text);
  process.exit(1);
}

const quote = (await response.json()) as JupiterQuote;

const outAmount = parseFloat(quote.outAmount) / 10 ** tokenOut.decimals;
const inAmountHuman = parseFloat(quote.inAmount) / 10 ** tokenIn.decimals;
const rate = outAmount / inAmountHuman;

console.log("══════════════════════════════════════════════════");
console.log("  🔄 Jupiter Swap Quote (Solana)");
console.log("══════════════════════════════════════════════════");
console.log(`  From:          ${inAmountHuman} ${tokenIn.symbol}`);
console.log(`  To:            ${outAmount.toFixed(6)} ${tokenOut.symbol}`);
console.log(`  Rate:          1 ${tokenIn.symbol} = ${rate.toFixed(6)} ${tokenOut.symbol}`);
console.log(`  Slippage:      ${slippageBps / 100}%`);
console.log(`  Price Impact:  ${quote.priceImpactPct}%`);
console.log("──────────────────────────────────────────────────");
console.log("  Route:");

for (const step of quote.routePlan) {
  console.log(`    ${step.percent}% → ${step.swapInfo.label}`);
}

console.log("══════════════════════════════════════════════════");

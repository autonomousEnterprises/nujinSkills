/**
 * Chain Configuration Registry
 *
 * Canonical chain metadata: native tokens, block explorers,
 * common token addresses (WETH, USDC, USDT) per chain.
 */

export interface TokenAddress {
  symbol: string;
  address: string;
  decimals: number;
}

export interface ChainConfig {
  chainId: number;
  name: string;
  shortName: string;
  nativeToken: { symbol: string; decimals: number };
  explorer: string;
  tokens: Record<string, TokenAddress>;
}

export const CHAINS: Record<string, ChainConfig> = {
  ethereum: {
    chainId: 1,
    name: "Ethereum Mainnet",
    shortName: "ETH",
    nativeToken: { symbol: "ETH", decimals: 18 },
    explorer: "https://etherscan.io",
    tokens: {
      WETH: { symbol: "WETH", address: "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2", decimals: 18 },
      USDC: { symbol: "USDC", address: "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", decimals: 6 },
      USDT: { symbol: "USDT", address: "0xdAC17F958D2ee523a2206206994597C13D831ec7", decimals: 6 },
      DAI: { symbol: "DAI", address: "0x6B175474E89094C44Da98b954EedeAC495271d0F", decimals: 18 },
      WBTC: { symbol: "WBTC", address: "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599", decimals: 8 },
    },
  },
  base: {
    chainId: 8453,
    name: "Base",
    shortName: "BASE",
    nativeToken: { symbol: "ETH", decimals: 18 },
    explorer: "https://basescan.org",
    tokens: {
      WETH: { symbol: "WETH", address: "0x4200000000000000000000000000000000000006", decimals: 18 },
      USDC: { symbol: "USDC", address: "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913", decimals: 6 },
      USDbC: { symbol: "USDbC", address: "0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA", decimals: 6 },
    },
  },
  arbitrum: {
    chainId: 42161,
    name: "Arbitrum One",
    shortName: "ARB",
    nativeToken: { symbol: "ETH", decimals: 18 },
    explorer: "https://arbiscan.io",
    tokens: {
      WETH: { symbol: "WETH", address: "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1", decimals: 18 },
      USDC: { symbol: "USDC", address: "0xaf88d065e77c8cC2239327C5EDb3A432268e5831", decimals: 6 },
      USDT: { symbol: "USDT", address: "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9", decimals: 6 },
      ARB: { symbol: "ARB", address: "0x912CE59144191C1204E64559FE8253a0e49E6548", decimals: 18 },
    },
  },
  polygon: {
    chainId: 137,
    name: "Polygon PoS",
    shortName: "MATIC",
    nativeToken: { symbol: "POL", decimals: 18 },
    explorer: "https://polygonscan.com",
    tokens: {
      WMATIC: { symbol: "WMATIC", address: "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270", decimals: 18 },
      WETH: { symbol: "WETH", address: "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619", decimals: 18 },
      USDC: { symbol: "USDC", address: "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359", decimals: 6 },
      USDT: { symbol: "USDT", address: "0xc2132D05D31c914a87C6611C10748AEb04B58e8F", decimals: 6 },
    },
  },
  bsc: {
    chainId: 56,
    name: "BNB Smart Chain",
    shortName: "BSC",
    nativeToken: { symbol: "BNB", decimals: 18 },
    explorer: "https://bscscan.com",
    tokens: {
      WBNB: { symbol: "WBNB", address: "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c", decimals: 18 },
      USDT: { symbol: "USDT", address: "0x55d398326f99059fF775485246999027B3197955", decimals: 18 },
      USDC: { symbol: "USDC", address: "0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d", decimals: 18 },
      BUSD: { symbol: "BUSD", address: "0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56", decimals: 18 },
    },
  },
  optimism: {
    chainId: 10,
    name: "Optimism",
    shortName: "OP",
    nativeToken: { symbol: "ETH", decimals: 18 },
    explorer: "https://optimistic.etherscan.io",
    tokens: {
      WETH: { symbol: "WETH", address: "0x4200000000000000000000000000000000000006", decimals: 18 },
      USDC: { symbol: "USDC", address: "0x0b2C639c533813f4Aa9D7837CAf62653d097Ff85", decimals: 6 },
      OP: { symbol: "OP", address: "0x4200000000000000000000000000000000000042", decimals: 18 },
    },
  },
  avalanche: {
    chainId: 43114,
    name: "Avalanche C-Chain",
    shortName: "AVAX",
    nativeToken: { symbol: "AVAX", decimals: 18 },
    explorer: "https://snowtrace.io",
    tokens: {
      WAVAX: { symbol: "WAVAX", address: "0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7", decimals: 18 },
      USDC: { symbol: "USDC", address: "0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E", decimals: 6 },
      USDT: { symbol: "USDT", address: "0x9702230A8Ea53601f5cD2dc00fDBc13d4dF4A8c7", decimals: 6 },
    },
  },
};

// ─── Solana Common Tokens ────────────────────────────────────────────────────

export const SOLANA_TOKENS: Record<string, { mint: string; decimals: number; symbol: string }> = {
  SOL: { mint: "So11111111111111111111111111111111111111112", decimals: 9, symbol: "SOL" },
  USDC: { mint: "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", decimals: 6, symbol: "USDC" },
  USDT: { mint: "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB", decimals: 6, symbol: "USDT" },
  BONK: { mint: "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263", decimals: 5, symbol: "BONK" },
  JUP: { mint: "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN", decimals: 6, symbol: "JUP" },
  RAY: { mint: "4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R", decimals: 6, symbol: "RAY" },
};

// ─── Helpers ─────────────────────────────────────────────────────────────────

/**
 * Get chain config by name or chain ID.
 */
export function getChain(nameOrId: string | number): ChainConfig {
  if (typeof nameOrId === "number") {
    const entry = Object.values(CHAINS).find((c) => c.chainId === nameOrId);
    if (!entry) throw new Error(`Unknown chain ID: ${nameOrId}`);
    return entry;
  }
  const chain = CHAINS[nameOrId.toLowerCase()];
  if (!chain) throw new Error(`Unknown chain: ${nameOrId}`);
  return chain;
}

/**
 * Get a specific token address on a given chain.
 */
export function getTokenAddress(chain: string, symbol: string): string {
  const config = CHAINS[chain.toLowerCase()];
  if (!config) throw new Error(`Unknown chain: ${chain}`);
  const token = config.tokens[symbol.toUpperCase()];
  if (!token) throw new Error(`Token ${symbol} not found on ${chain}`);
  return token.address;
}

/**
 * Format a native token amount from wei/lamports to human-readable.
 */
export function formatNativeAmount(amount: bigint, decimals: number): string {
  const divisor = BigInt(10 ** decimals);
  const whole = amount / divisor;
  const remainder = amount % divisor;
  const fractionStr = remainder.toString().padStart(decimals, "0").slice(0, 6);
  return `${whole}.${fractionStr}`;
}

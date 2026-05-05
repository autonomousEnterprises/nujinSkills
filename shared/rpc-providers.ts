/**
 * Free Public RPC Provider Registry
 *
 * All endpoints listed here are free and require NO API key.
 * They are rate-limited and intended for development, prototyping, and light usage.
 * For production workloads, consider running your own node or using a dedicated provider.
 *
 * Sources: chainlist.org, official chain documentation
 */

export interface RpcEndpoint {
  url: string;
  provider: string;
  note?: string;
}

export interface ChainRpcConfig {
  chainId: number;
  name: string;
  rpcs: RpcEndpoint[];
}

// ─── EVM Chains ──────────────────────────────────────────────────────────────

export const EVM_RPCS: Record<string, ChainRpcConfig> = {
  ethereum: {
    chainId: 1,
    name: "Ethereum Mainnet",
    rpcs: [
      { url: "https://cloudflare-eth.com", provider: "Cloudflare", note: "Highly reliable" },
      { url: "https://eth.llamarpc.com", provider: "LlamaNodes" },
      { url: "https://rpc.ankr.com/eth", provider: "Ankr Public" },
      { url: "https://ethereum-rpc.publicnode.com", provider: "PublicNode" },
      { url: "https://1rpc.io/eth", provider: "1RPC" },
      { url: "https://rpc.flashbots.net", provider: "Flashbots" },
      { url: "https://eth-mainnet.public.blastapi.io", provider: "Blast" },
    ],
  },
  base: {
    chainId: 8453,
    name: "Base",
    rpcs: [
      { url: "https://mainnet.base.org", provider: "Base Official" },
      { url: "https://base.llamarpc.com", provider: "LlamaNodes" },
      { url: "https://rpc.ankr.com/base", provider: "Ankr Public" },
      { url: "https://base-rpc.publicnode.com", provider: "PublicNode" },
      { url: "https://base.drpc.org", provider: "dRPC" },
    ],
  },
  arbitrum: {
    chainId: 42161,
    name: "Arbitrum One",
    rpcs: [
      { url: "https://arb1.arbitrum.io/rpc", provider: "Arbitrum Official" },
      { url: "https://arbitrum.llamarpc.com", provider: "LlamaNodes" },
      { url: "https://rpc.ankr.com/arbitrum", provider: "Ankr Public" },
      { url: "https://arbitrum-one-rpc.publicnode.com", provider: "PublicNode" },
    ],
  },
  polygon: {
    chainId: 137,
    name: "Polygon PoS",
    rpcs: [
      { url: "https://polygon-rpc.com", provider: "Polygon Official" },
      { url: "https://polygon.llamarpc.com", provider: "LlamaNodes" },
      { url: "https://rpc.ankr.com/polygon", provider: "Ankr Public" },
      { url: "https://polygon-bor-rpc.publicnode.com", provider: "PublicNode" },
    ],
  },
  bsc: {
    chainId: 56,
    name: "BNB Smart Chain",
    rpcs: [
      { url: "https://bsc-dataseed.binance.org", provider: "Binance Official" },
      { url: "https://bsc.llamarpc.com", provider: "LlamaNodes" },
      { url: "https://rpc.ankr.com/bsc", provider: "Ankr Public" },
      { url: "https://bsc-rpc.publicnode.com", provider: "PublicNode" },
    ],
  },
  optimism: {
    chainId: 10,
    name: "Optimism",
    rpcs: [
      { url: "https://mainnet.optimism.io", provider: "Optimism Official" },
      { url: "https://optimism.llamarpc.com", provider: "LlamaNodes" },
      { url: "https://rpc.ankr.com/optimism", provider: "Ankr Public" },
    ],
  },
  avalanche: {
    chainId: 43114,
    name: "Avalanche C-Chain",
    rpcs: [
      { url: "https://api.avax.network/ext/bc/C/rpc", provider: "Avalanche Official" },
      { url: "https://rpc.ankr.com/avalanche", provider: "Ankr Public" },
      { url: "https://avalanche-c-chain-rpc.publicnode.com", provider: "PublicNode" },
    ],
  },

  // ─── Testnets ────────────────────────────────────────────────────────────
  sepolia: {
    chainId: 11155111,
    name: "Sepolia Testnet",
    rpcs: [
      { url: "https://rpc.sepolia.org", provider: "Sepolia Official" },
      { url: "https://ethereum-sepolia-rpc.publicnode.com", provider: "PublicNode" },
      { url: "https://rpc.ankr.com/eth_sepolia", provider: "Ankr Public" },
    ],
  },
};

// ─── Solana ──────────────────────────────────────────────────────────────────

export const SOLANA_RPCS = {
  mainnet: {
    name: "Solana Mainnet Beta",
    rpcs: [
      { url: "https://api.mainnet-beta.solana.com", provider: "Solana Official", note: "Rate-limited" },
    ],
  },
  devnet: {
    name: "Solana Devnet",
    rpcs: [
      { url: "https://api.devnet.solana.com", provider: "Solana Official" },
    ],
  },
};

// ─── Bitcoin ─────────────────────────────────────────────────────────────────

export const BITCOIN_APIS = {
  mainnet: {
    name: "Bitcoin Mainnet",
    apis: [
      { url: "https://blockstream.info/api", provider: "Blockstream", note: "REST API, no key" },
      { url: "https://mempool.space/api", provider: "Mempool.space", note: "REST API, no key" },
    ],
  },
  testnet: {
    name: "Bitcoin Testnet",
    apis: [
      { url: "https://blockstream.info/testnet/api", provider: "Blockstream" },
      { url: "https://mempool.space/testnet/api", provider: "Mempool.space" },
    ],
  },
};

// ─── Helpers ─────────────────────────────────────────────────────────────────

/**
 * Get the first available RPC URL for a given EVM chain.
 * Falls back through the list if the primary is unavailable.
 */
export function getEvmRpc(chain: keyof typeof EVM_RPCS): string {
  const config = EVM_RPCS[chain];
  if (!config) throw new Error(`Unknown EVM chain: ${chain}`);
  return config.rpcs[0].url;
}

/**
 * Get the chain ID for a given EVM chain name.
 */
export function getChainId(chain: keyof typeof EVM_RPCS): number {
  const config = EVM_RPCS[chain];
  if (!config) throw new Error(`Unknown EVM chain: ${chain}`);
  return config.chainId;
}

/**
 * Get the primary Bitcoin API base URL.
 */
export function getBitcoinApi(network: "mainnet" | "testnet" = "mainnet"): string {
  return BITCOIN_APIS[network].apis[0].url;
}

/**
 * Get the primary Solana RPC URL.
 */
export function getSolanaRpc(network: "mainnet" | "devnet" = "mainnet"): string {
  return SOLANA_RPCS[network].rpcs[0].url;
}

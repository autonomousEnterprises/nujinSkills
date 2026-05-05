export {};
/**
 * EVM DEX Swap — Execute Swap (Uniswap V3)
 *
 * Executes a token swap on Uniswap V3.
 *
 * Usage:
 *   export PRIVATE_KEY=0x...
 *   npx tsx execute-swap.ts <tokenIn> <tokenOut> <amountIn> <fee> [--chain ethereum|base|...]
 *
 * Note: fee is usually 3000 (0.3%) or 500 (0.05%).
 */

import { createWalletClient, createPublicClient, http, fallback, parseUnits, type Address, type Hex } from "viem";
import { privateKeyToAccount } from "viem/accounts";
import { mainnet, base, arbitrum, polygon, bsc, optimism, avalanche } from "viem/chains";
import { EVM_RPCS } from "../../../shared/rpc-providers";

const CHAIN_MAP = { ethereum: mainnet, base, arbitrum, polygon, bsc, optimism, avalanche } as const;

// Uniswap V3 SwapRouter02 (same on most chains)
const SWAP_ROUTER_ADDRESS = "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45";

async function main() {
  const tokenIn = process.argv[2] as Address | undefined;
  const tokenOut = process.argv[3] as Address | undefined;
  const amountIn = process.argv[4];
  const fee = parseInt(process.argv[5] || "3000");
  const chainFlag = process.argv.indexOf("--chain");
  const chainName = chainFlag !== -1 ? (process.argv[chainFlag + 1] as keyof typeof CHAIN_MAP) : "ethereum";

  const privateKey = process.env.PRIVATE_KEY as Hex | undefined;

  if (!tokenIn || !tokenOut || !amountIn || !privateKey) {
    console.error("Usage: export PRIVATE_KEY=0x... && npx tsx execute-swap.ts <tokenIn> <tokenOut> <amountIn> <fee> [--chain <chain>]");
    process.exit(1);
  }

  const chain = CHAIN_MAP[chainName];
  if (!chain) {
    console.error(`Unknown chain: ${chainName}`);
    process.exit(1);
  }

  const account = privateKeyToAccount(privateKey);
  const rpcConfig = EVM_RPCS[chainName];
  const transports = rpcConfig.rpcs.map((rpc) => http(rpc.url));

  const publicClient = createPublicClient({ chain, transport: fallback(transports) });
  const walletClient = createWalletClient({ account, chain, transport: fallback(transports) });

  const ERC20_ABI = [
    { name: "approve", type: "function", stateMutability: "nonpayable", inputs: [{ name: "spender", type: "address" }, { name: "amount", type: "uint256" }], outputs: [{ name: "", type: "bool" }] },
    { name: "decimals", type: "function", stateMutability: "view", inputs: [], outputs: [{ name: "", type: "uint8" }] },
    { name: "symbol", type: "function", stateMutability: "view", inputs: [], outputs: [{ name: "", type: "string" }] },
  ] as const;

  const ROUTER_ABI = [
    {
      name: "exactInputSingle",
      type: "function",
      stateMutability: "payable",
      inputs: [
        {
          name: "params",
          type: "tuple",
          components: [
            { name: "tokenIn", type: "address" },
            { name: "tokenOut", type: "address" },
            { name: "fee", type: "uint24" },
            { name: "recipient", type: "address" },
            { name: "amountIn", type: "uint256" },
            { name: "amountOutMinimum", type: "uint256" },
            { name: "sqrtPriceLimitX96", type: "uint160" },
          ],
        },
      ],
      outputs: [{ name: "amountOut", type: "uint256" }],
    },
  ] as const;

  try {
    const [decimalsIn, symbolIn] = await Promise.all([
      publicClient.readContract({ address: tokenIn, abi: ERC20_ABI, functionName: "decimals" }),
      publicClient.readContract({ address: tokenIn, abi: ERC20_ABI, functionName: "symbol" }),
    ]);

    const amountInUnits = parseUnits(amountIn, decimalsIn);

    console.log("══════════════════════════════════════════════════");
    console.log(`  🦄 Uniswap V3 Swap on ${chain.name}`);
    console.log("══════════════════════════════════════════════════");
    console.log(`  Swap:   ${amountIn} ${symbolIn} -> ${tokenOut}`);
    console.log(`  Account: ${account.address}`);

    // 1. Approve Router
    console.log("  ⏳ Approving SwapRouter...");
    const approveHash = await walletClient.writeContract({
      address: tokenIn,
      abi: ERC20_ABI,
      functionName: "approve",
      args: [SWAP_ROUTER_ADDRESS, amountInUnits],
    });
    console.log(`  ✅ Approved! Hash: ${approveHash}`);

    // 2. Execute Swap
    console.log("  ⏳ Executing Swap...");
    const swapHash = await walletClient.writeContract({
      address: SWAP_ROUTER_ADDRESS,
      abi: ROUTER_ABI,
      functionName: "exactInputSingle",
      args: [
        {
          tokenIn,
          tokenOut,
          fee,
          recipient: account.address,
          amountIn: amountInUnits,
          amountOutMinimum: 0n, // slippage not handled for simplicity in this demo
          sqrtPriceLimitX96: 0n,
        },
      ],
    });

    console.log("  ✅ Swap Transaction Sent!");
    console.log(`  Hash:     ${swapHash}`);
    console.log(`  Explorer: ${chain.blockExplorers?.default.url}/tx/${swapHash}`);
  } catch (error: any) {
    console.error("  ❌ Swap Failed:");
    console.error(`  ${error.message}`);
  }
  console.log("══════════════════════════════════════════════════");
}

main();

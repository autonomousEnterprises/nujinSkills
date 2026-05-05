export {};
/**
 * DeFi Lending — Aave V3 Withdraw
 *
 * Withdraws an asset from Aave V3.
 *
 * Usage:
 *   export PRIVATE_KEY=0x...
 *   npx tsx withdraw.ts <asset_address> <amount> [--chain ethereum|base|...]
 */

import { createWalletClient, createPublicClient, http, fallback, parseUnits, type Address, type Hex } from "viem";
import { privateKeyToAccount } from "viem/accounts";
import { mainnet, base, arbitrum, polygon, optimism } from "viem/chains";
import { EVM_RPCS } from "../../../shared/rpc-providers";

const CHAIN_MAP = { ethereum: mainnet, base, arbitrum, polygon, optimism } as const;

// Aave V3 Pool Proxy
const AAVE_POOL_ADDRESS = "0x87870B2ec3Ac9223124815121006E5497aa94E7d";

async function main() {
  const asset = process.argv[2] as Address | undefined;
  const amount = process.argv[3];
  const chainFlag = process.argv.indexOf("--chain");
  const chainName = chainFlag !== -1 ? (process.argv[chainFlag + 1] as keyof typeof CHAIN_MAP) : "ethereum";

  const privateKey = process.env.PRIVATE_KEY as Hex | undefined;

  if (!asset || !amount || !privateKey) {
    console.error("Usage: export PRIVATE_KEY=0x... && npx tsx withdraw.ts <asset> <amount> [--chain <chain>]");
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
    { name: "decimals", type: "function", stateMutability: "view", inputs: [], outputs: [{ name: "", type: "uint8" }] },
    { name: "symbol", type: "function", stateMutability: "view", inputs: [], outputs: [{ name: "", type: "string" }] },
  ] as const;

  const POOL_ABI = [
    {
      name: "withdraw",
      type: "function",
      stateMutability: "nonpayable",
      inputs: [
        { name: "asset", type: "address" },
        { name: "amount", type: "uint256" },
        { name: "to", type: "address" },
      ],
      outputs: [{ name: "", type: "uint256" }],
    },
  ] as const;

  try {
    const [decimals, symbol] = await Promise.all([
      publicClient.readContract({ address: asset, abi: ERC20_ABI, functionName: "decimals" }),
      publicClient.readContract({ address: asset, abi: ERC20_ABI, functionName: "symbol" }),
    ]);

    // Use Max Uint256 for "withdraw all" if amount is "max"
    const amountInUnits = amount.toLowerCase() === "max" 
      ? 115792089237316195423570985008687907853269984665640564039457584007913129639935n 
      : parseUnits(amount, decimals);

    console.log("══════════════════════════════════════════════════");
    console.log(`  👻 Aave V3 Withdraw on ${chain.name}`);
    console.log("══════════════════════════════════════════════════");
    console.log(`  Asset:   ${symbol} (${asset})`);
    console.log(`  Amount:  ${amount}`);

    console.log("  ⏳ Executing Withdrawal...");
    const withdrawHash = await walletClient.writeContract({
      address: AAVE_POOL_ADDRESS,
      abi: POOL_ABI,
      functionName: "withdraw",
      args: [asset, amountInUnits, account.address],
    });

    console.log("  ✅ Withdrawal Transaction Sent!");
    console.log(`  Hash:     ${withdrawHash}`);
    console.log(`  Explorer: ${chain.blockExplorers?.default.url}/tx/${withdrawHash}`);
  } catch (error: any) {
    console.error("  ❌ Withdrawal Failed:");
    console.error(`  ${error.message}`);
  }
  console.log("══════════════════════════════════════════════════");
}

main();

export {};
/**
 * DeFi Lending — Aave V3 Repay
 *
 * Repays a borrowed asset on Aave V3.
 *
 * Usage:
 *   export PRIVATE_KEY=0x...
 *   npx tsx repay.ts <asset_address> <amount> [--chain ethereum|base|...]
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
    console.error("Usage: export PRIVATE_KEY=0x... && npx tsx repay.ts <asset> <amount> [--chain <chain>]");
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

  const POOL_ABI = [
    {
      name: "repay",
      type: "function",
      stateMutability: "nonpayable",
      inputs: [
        { name: "asset", type: "address" },
        { name: "amount", type: "uint256" },
        { name: "interestRateMode", type: "uint256" },
        { name: "onBehalfOf", type: "address" },
      ],
      outputs: [{ name: "", type: "uint256" }],
    },
  ] as const;

  try {
    const [decimals, symbol] = await Promise.all([
      publicClient.readContract({ address: asset, abi: ERC20_ABI, functionName: "decimals" }),
      publicClient.readContract({ address: asset, abi: ERC20_ABI, functionName: "symbol" }),
    ]);

    const amountInUnits = parseUnits(amount, decimals);

    console.log("══════════════════════════════════════════════════");
    console.log(`  👻 Aave V3 Repay on ${chain.name}`);
    console.log("══════════════════════════════════════════════════");
    console.log(`  Asset:   ${symbol} (${asset})`);
    console.log(`  Amount:  ${amount}`);

    // 1. Approve Pool
    console.log("  ⏳ Approving Aave Pool...");
    const approveHash = await walletClient.writeContract({
      address: asset,
      abi: ERC20_ABI,
      functionName: "approve",
      args: [AAVE_POOL_ADDRESS, amountInUnits],
    });
    console.log(`  ✅ Approved! Hash: ${approveHash}`);

    // 2. Repay
    console.log("  ⏳ Executing Repay...");
    const repayHash = await walletClient.writeContract({
      address: AAVE_POOL_ADDRESS,
      abi: POOL_ABI,
      functionName: "repay",
      args: [asset, amountInUnits, 2n, account.address], // 2 = Variable rate
    });

    console.log("  ✅ Repay Transaction Sent!");
    console.log(`  Hash:     ${repayHash}`);
    console.log(`  Explorer: ${chain.blockExplorers?.default.url}/tx/${repayHash}`);
  } catch (error: any) {
    console.error("  ❌ Repay Failed:");
    console.error(`  ${error.message}`);
  }
  console.log("══════════════════════════════════════════════════");
}

main();

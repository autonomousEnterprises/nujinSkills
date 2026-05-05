export {};
/**
 * DeFi Lending — Aave V3 Health Factor
 *
 * Checks the health factor of a user on Aave V3.
 *
 * Usage:
 *   npx tsx health-factor.ts <address> [--chain ethereum|base|...]
 */

import { createPublicClient, http, fallback, formatUnits, type Address } from "viem";
import { mainnet, base, arbitrum, polygon, optimism } from "viem/chains";
import { EVM_RPCS } from "../../../shared/rpc-providers";

const CHAIN_MAP = { ethereum: mainnet, base, arbitrum, polygon, optimism } as const;

// Aave V3 Pool Proxy
const AAVE_POOL_ADDRESS = "0x87870B2ec3Ac9223124815121006E5497aa94E7d";

async function main() {
  const address = process.argv[2] as Address | undefined;
  const chainFlag = process.argv.indexOf("--chain");
  const chainName = chainFlag !== -1 ? (process.argv[chainFlag + 1] as keyof typeof CHAIN_MAP) : "ethereum";

  if (!address) {
    console.error("Usage: npx tsx health-factor.ts <address> [--chain <chain>]");
    process.exit(1);
  }

  const chain = CHAIN_MAP[chainName];
  if (!chain) {
    console.error(`Unknown chain: ${chainName}`);
    process.exit(1);
  }

  const rpcConfig = EVM_RPCS[chainName];
  const transports = rpcConfig.rpcs.map((rpc) => http(rpc.url));
  const client = createPublicClient({ chain, transport: fallback(transports) });

  const POOL_ABI = [
    {
      name: "getUserAccountData",
      type: "function",
      stateMutability: "view",
      inputs: [{ name: "user", type: "address" }],
      outputs: [
        { name: "totalCollateralBase", type: "uint256" },
        { name: "totalDebtBase", type: "uint256" },
        { name: "availableBorrowsBase", type: "uint256" },
        { name: "currentLiquidationThreshold", type: "uint256" },
        { name: "ltv", type: "uint256" },
        { name: "healthFactor", type: "uint256" },
      ],
    },
  ] as const;

  try {
    const data = await client.readContract({
      address: AAVE_POOL_ADDRESS,
      abi: POOL_ABI,
      functionName: "getUserAccountData",
      args: [address],
    });

    const [collateral, debt, available, threshold, ltv, healthFactor] = data;

    const hf = Number(formatUnits(healthFactor, 18));
    let status = "🟢 SAFE";
    if (hf < 1.0) status = "🔴 LIQUIDATABLE";
    else if (hf < 1.5) status = "🟡 WARNING";

    console.log("══════════════════════════════════════════════════");
    console.log(`  👻 Aave V3 Health Status (${chain.name})`);
    console.log("══════════════════════════════════════════════════");
    console.log(`  Address:       ${address}`);
    console.log(`  Health Factor: ${hf.toFixed(4)} [${status}]`);
    console.log(`  Collateral:    $${(Number(collateral) / 1e8).toFixed(2)}`);
    console.log(`  Total Debt:    $${(Number(debt) / 1e8).toFixed(2)}`);
    console.log(`  Liquidation:   at HF < 1.0`);
    console.log("══════════════════════════════════════════════════");

  } catch (error: any) {
    console.error("  ❌ Failed to fetch health factor:");
    console.error(`  ${error.message}`);
  }
}

main();

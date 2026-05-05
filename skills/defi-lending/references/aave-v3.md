# Aave V3 Integration Reference

## Architecture

Aave V3 uses a **proxy pattern** — always resolve the Pool address through the `PoolAddressesProvider`:

```
PoolAddressesProvider → getPool() → Pool (proxy)
```

## Core Functions (IPool Interface)

### Supply (Deposit Collateral)
```solidity
function supply(
  address asset,      // ERC-20 token address to supply
  uint256 amount,     // Amount in token's native units
  address onBehalfOf, // Recipient of aTokens (usually msg.sender)
  uint16 referralCode // Set to 0
) external;
```

**Prerequisites**: Approve the Pool to spend your tokens first.

### Borrow
```solidity
function borrow(
  address asset,           // Token to borrow
  uint256 amount,          // Amount to borrow
  uint256 interestRateMode, // 1 = Stable, 2 = Variable
  uint16 referralCode,     // Set to 0
  address onBehalfOf       // Borrower (usually msg.sender)
) external;
```

**Prerequisites**: Must have sufficient collateral supplied. Check health factor.

### Repay
```solidity
function repay(
  address asset,           // Token to repay
  uint256 amount,          // Amount (use type(uint256).max to repay all)
  uint256 interestRateMode, // Must match borrow mode
  address onBehalfOf       // Borrower address
) external returns (uint256);
```

### Withdraw
```solidity
function withdraw(
  address asset,  // Token to withdraw
  uint256 amount, // Amount (use type(uint256).max for all)
  address to      // Recipient
) external returns (uint256);
```

### Get User Account Data
```solidity
function getUserAccountData(address user) external view returns (
  uint256 totalCollateralBase,       // Total collateral in base currency (USD, 8 decimals)
  uint256 totalDebtBase,             // Total debt in base currency
  uint256 availableBorrowsBase,      // How much more can be borrowed
  uint256 currentLiquidationThreshold, // Liquidation threshold (basis points)
  uint256 ltv,                       // Loan-to-value ratio (basis points)
  uint256 healthFactor               // Health factor (18 decimals, < 1 = liquidatable)
);
```

## Deployed Pool Addresses

| Chain | Pool Address |
|-------|-------------|
| Ethereum | `0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2` |
| Arbitrum | `0x794a61358D6845594F94dc1DB02A252b5b4814aD` |
| Polygon | `0x794a61358D6845594F94dc1DB02A252b5b4814aD` |
| Base | `0xA238Dd80C259a72e81d7e4664a9801593F98d1c5` |
| Optimism | `0x794a61358D6845594F94dc1DB02A252b5b4814aD` |
| Avalanche | `0x794a61358D6845594F94dc1DB02A252b5b4814aD` |

## Supported Assets (Ethereum Mainnet)

| Asset | aToken | Variable Debt Token |
|-------|--------|-------------------|
| WETH | aWETH | variableDebtWETH |
| USDC | aUSDC | variableDebtUSDC |
| USDT | aUSDT | variableDebtUSDT |
| DAI | aDAI | variableDebtDAI |
| WBTC | aWBTC | variableDebtWBTC |

## Health Factor Explained

- **> 2.0** 🟢 Safe — comfortable margin
- **1.2 — 2.0** 🟡 Caution — monitor closely
- **1.0 — 1.2** 🔴 Danger — liquidation imminent
- **< 1.0** ☠️ Liquidatable — anyone can liquidate your position

## Fee Structure

- **Flash Loan Fee**: 0.05% (Aave V3)
- **Supply/Borrow**: No protocol fees (interest is the cost)
- **Gas**: Standard EVM gas costs apply

## Resources

- [Aave V3 Docs](https://docs.aave.com/developers/)
- [Deployed Contracts](https://docs.aave.com/developers/deployed-contracts/deployed-contracts)
- [GitHub: aave-v3-core](https://github.com/aave/aave-v3-core)

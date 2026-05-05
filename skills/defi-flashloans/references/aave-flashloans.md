# Aave V3 Flash Loan Reference

## Execution Flow

```
┌─────────────────┐    flashLoanSimple()    ┌──────────────┐
│  Your Contract   │ ─────────────────────→  │  Aave Pool   │
│                  │                          │              │
│                  │  ← sends borrowed tokens │              │
│                  │                          │              │
│  executeOperation()  ← Aave calls back     │              │
│  ┌─────────────────────────────────┐       │              │
│  │  1. Custom logic (arb, swap)    │       │              │
│  │  2. Approve Pool for repayment  │       │              │
│  │  3. Return true                 │       │              │
│  └─────────────────────────────────┘       │              │
│                  │                          │              │
│                  │  Pool pulls repayment →  │              │
│                  │  (amount + 0.05% fee)    │              │
└─────────────────┘                          └──────────────┘
```

## Interface: IFlashLoanSimpleReceiver

```solidity
function executeOperation(
    address asset,      // The borrowed token
    uint256 amount,     // The amount borrowed
    uint256 premium,    // The fee (0.05%)
    address initiator,  // Who initiated the flash loan
    bytes calldata params // Custom encoded parameters
) external returns (bool);
```

## flashLoanSimple Parameters

```solidity
Pool.flashLoanSimple(
    address receiverAddress,  // Contract implementing IFlashLoanSimpleReceiver
    address asset,            // Token to borrow
    uint256 amount,           // Amount to borrow
    bytes calldata params,    // Passed to executeOperation
    uint16 referralCode       // Set to 0
);
```

## Multi-Asset Flash Loans

For borrowing multiple assets in a single transaction, use `flashLoan` instead:

```solidity
Pool.flashLoan(
    address receiverAddress,
    address[] calldata assets,   // Array of tokens
    uint256[] calldata amounts,  // Array of amounts
    uint256[] calldata interestRateModes, // 0 = no debt, 1 = stable, 2 = variable
    address onBehalfOf,
    bytes calldata params,
    uint16 referralCode
);
```

## Fee Calculation

```
fee = amount × 0.0005 (0.05%)
total_repayment = amount + fee
```

| Borrowed Amount | Fee | Total Repayment |
|----------------|-----|----------------|
| 100,000 USDC | 50 USDC | 100,050 USDC |
| 1,000,000 USDC | 500 USDC | 1,000,500 USDC |
| 10 WETH | 0.005 WETH | 10.005 WETH |

## Common Pitfalls

1. **Insufficient balance for repayment**: If `executeOperation` doesn't generate enough to cover `amount + premium`, the entire transaction reverts
2. **Missing approval**: You MUST call `IERC20(asset).approve(address(POOL), amountOwed)` before returning
3. **Reentrancy**: Flash loans are atomic — the callback must complete in the same tx
4. **Gas limits**: Complex operations inside `executeOperation` may hit block gas limits
5. **Front-running**: Arbitrage opportunities may be front-run by MEV bots — use Flashbots or private mempool

## Testing Approach

1. **Local fork**: Use Hardhat or Foundry to fork mainnet locally
2. **Tenderly simulation**: Simulate transactions without deploying
3. **Sepolia testnet**: Aave V3 is deployed on Sepolia for testing
4. **Start small**: Begin with small amounts on mainnet before scaling

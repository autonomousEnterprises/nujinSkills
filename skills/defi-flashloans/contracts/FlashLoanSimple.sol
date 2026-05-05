// SPDX-License-Identifier: MIT
pragma solidity ^0.8.10;

import {FlashLoanSimpleReceiverBase} from "@aave/core-v3/contracts/flashloan/base/FlashLoanSimpleReceiverBase.sol";
import {IPoolAddressesProvider} from "@aave/core-v3/contracts/interfaces/IPoolAddressesProvider.sol";
import {IERC20} from "@aave/core-v3/contracts/dependencies/openzeppelin/contracts/IERC20.sol";

/**
 * @title FlashLoanSimple
 * @notice Single-asset Aave V3 flash loan receiver template.
 *
 * Usage:
 *   1. Deploy this contract with the PoolAddressesProvider address
 *   2. Call requestFlashLoan(asset, amount) to initiate
 *   3. Custom logic goes in executeOperation()
 *   4. Contract auto-repays the loan + 0.05% fee
 *
 * PoolAddressesProvider addresses:
 *   Ethereum: 0x2f39d218133AFaB8F2B819B1066c7E434Ad94E9e
 *   Arbitrum: 0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb
 *   Polygon:  0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb
 *   Base:     0xe20fCBdBfFC4Dd138cE8b2E6FBb6CB49777ad64D
 */
contract FlashLoanSimple is FlashLoanSimpleReceiverBase {
    address public owner;

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner");
        _;
    }

    constructor(address _addressProvider)
        FlashLoanSimpleReceiverBase(IPoolAddressesProvider(_addressProvider))
    {
        owner = msg.sender;
    }

    /**
     * @notice Initiates a flash loan.
     * @param asset The address of the asset to flash borrow.
     * @param amount The amount to borrow (in asset's native decimals).
     */
    function requestFlashLoan(address asset, uint256 amount) external onlyOwner {
        bytes memory params = ""; // Optional: encode custom params here
        uint16 referralCode = 0;

        POOL.flashLoanSimple(
            address(this), // receiverAddress
            asset,         // asset to borrow
            amount,        // amount to borrow
            params,        // custom params passed to executeOperation
            referralCode
        );
    }

    /**
     * @notice Aave calls this function after sending the flash-borrowed amount.
     * @dev Implement your custom logic here (arbitrage, collateral swap, etc.).
     *
     * @param asset The address of the flash-borrowed asset.
     * @param amount The amount borrowed.
     * @param premium The fee to pay (0.05% of amount).
     * @param initiator The address that initiated the flash loan.
     * @param params Custom parameters encoded in requestFlashLoan.
     * @return True if the operation was successful.
     */
    function executeOperation(
        address asset,
        uint256 amount,
        uint256 premium,
        address initiator,
        bytes calldata params
    ) external override returns (bool) {
        // Verify the call is from the Aave Pool
        require(msg.sender == address(POOL), "Caller must be Pool");
        require(initiator == address(this), "Initiator must be this contract");

        // ═══════════════════════════════════════════════════
        // YOUR CUSTOM LOGIC HERE
        //
        // At this point, this contract holds `amount` of `asset`.
        // You can:
        //   - Swap on DEXs for arbitrage
        //   - Supply/withdraw on lending protocols
        //   - Liquidate underwater positions
        //   - Swap collateral types
        //
        // You MUST end with enough balance to repay amount + premium.
        // ═══════════════════════════════════════════════════

        // Approve the Pool to pull back the owed amount
        uint256 amountOwed = amount + premium;
        IERC20(asset).approve(address(POOL), amountOwed);

        return true;
    }

    /**
     * @notice Withdraw any ERC-20 tokens stuck in this contract.
     * @param token The token address to withdraw.
     */
    function withdrawToken(address token) external onlyOwner {
        uint256 balance = IERC20(token).balanceOf(address(this));
        require(balance > 0, "No balance");
        IERC20(token).transfer(owner, balance);
    }

    /**
     * @notice Withdraw any ETH stuck in this contract.
     */
    function withdrawETH() external onlyOwner {
        uint256 balance = address(this).balance;
        require(balance > 0, "No balance");
        payable(owner).transfer(balance);
    }

    receive() external payable {}
}

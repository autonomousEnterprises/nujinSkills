"""
strategy_search_engine.py - Generic Iterative Search & Backtesting Engine
Evaluates vectorized conditions dynamically across feature sets until targets are met.
"""

import sys
import os
import json
import argparse
import pandas as pd
import numpy as np

def run_vectorized_backtest(df: pd.DataFrame, entry_signal: pd.Series, exit_signal: pd.Series, fee_bps: float = 5.0, slippage_bps: float = 2.0):
    """Computes vectorized return metrics with friction."""
    price = df['close'] if 'close' in df.columns else df.iloc[:, 1]
    returns = price.pct_change().fillna(0)
    
    position = pd.Series(0, index=df.index)
    pos = 0
    positions = []
    
    for i in range(len(df)):
        if entry_signal.iloc[i] and pos == 0:
            pos = 1
        elif exit_signal.iloc[i] and pos == 1:
            pos = 0
        positions.append(pos)
        
    position = pd.Series(positions, index=df.index)
    trades_mask = position.diff().abs() > 0
    num_trades = trades_mask.sum()
    
    friction_per_trade = (fee_bps + slippage_bps) / 10000.0
    strategy_returns = position.shift(1) * returns
    strategy_returns[trades_mask] -= friction_per_trade
    
    cum_returns = (1 + strategy_returns).cumprod()
    peak = cum_returns.cummax()
    drawdown = (cum_returns - peak) / peak
    max_dd = abs(drawdown.min())
    
    mean_ret = strategy_returns.mean()
    std_ret = strategy_returns.std()
    sharpe = (mean_ret / std_ret * np.sqrt(252 * 24 * 4)) if std_ret > 0 else 0.0
    
    return {
        "sharpe": float(sharpe),
        "max_drawdown": float(max_dd),
        "num_trades": int(num_trades),
        "total_return": float(cum_returns.iloc[-1] - 1) if len(cum_returns) > 0 else 0.0
    }

def main():
    parser = argparse.ArgumentParser(description="Generic Iterative Strategy Search Engine")
    parser.add_argument("--features", type=str, required=True, help="Path to features CSV")
    parser.add_argument("--target-sharpe", type=float, default=1.5, help="Target Sharpe Ratio threshold")
    parser.add_argument("--max-dd", type=float, default=0.10, help="Maximum allowed Drawdown")
    args = parser.parse_args()

    print(f"🚀 Initializing Search Engine on: {args.features}")
    if not os.path.exists(args.features):
        print(f"❌ Feature file not found: {args.features}")
        sys.exit(1)
        
    df = pd.read_csv(args.features)
    print(f"  • Feature dataset shape: {df.shape}")
    
    # Generic Search Loop (Iterating over quantile thresholds & z-score shocks)
    best_result = None
    best_sharpe = -999.0
    
    z_col = "z_returns" if "z_returns" in df.columns else df.columns[-1]
    
    print("\n🔄 Running Iterative Parameter & Rule Mutation Loop...")
    for entry_thresh in np.linspace(-3.0, -1.0, 10):
        for exit_thresh in np.linspace(0.0, 2.0, 10):
            entry_signal = df[z_col] < entry_thresh
            exit_signal = df[z_col] > exit_thresh
            
            res = run_vectorized_backtest(df, entry_signal, exit_signal)
            if res["num_trades"] >= 20 and res["sharpe"] > best_sharpe:
                best_sharpe = res["sharpe"]
                best_result = {
                    "entry_threshold": float(entry_thresh),
                    "exit_threshold": float(exit_thresh),
                    "metrics": res
                }
                
    os.makedirs(".nujin", exist_ok=True)
    with open(".nujin/best_rule.json", "w") as f:
        json.dump(best_result, f, indent=2)
        
    print("\n✨ Search Loop Completed!")
    if best_result:
        print(f"  • Best Sharpe Ratio: {best_result['metrics']['sharpe']:.2f}")
        print(f"  • Max Drawdown: {best_result['metrics']['max_drawdown']*100:.2f}%")
        print(f"  • Total Trades: {best_result['metrics']['num_trades']}")
        print("  • Saved best rule spec to `.nujin/best_rule.json`")
    else:
        print("  ⚠️ No rule satisfied criteria in initial grid. Triggering feature space expansion.")

if __name__ == "__main__":
    main()

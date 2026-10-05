"""
data_miner.py - Generic Empirical Anomaly & Feature Mining Tool
Analyzes input time series without hardcoded indicator assumptions.
Calculates statistical moments, variance ratios, stationarity, and extracts normalized features.
"""

import sys
import argparse
import pandas as pd
import numpy as np

def calculate_variance_ratio(series: pd.Series, lag: int = 2) -> float:
    """Calculates Lo-MacKinlay Variance Ratio."""
    returns = np.log(series / series.shift(1)).dropna()
    n = len(returns)
    mu = returns.mean()
    
    var_1 = np.sum((returns - mu)**2) / (n - 1)
    
    returns_k = np.log(series / series.shift(lag)).dropna()
    var_k = np.sum((returns_k - lag * mu)**2) / (n - lag)
    
    vr = var_k / (lag * var_1)
    return float(vr)

def main():
    parser = argparse.ArgumentParser(description="Generic Empirical Data Miner")
    parser.add_argument("--input", type=str, required=True, help="Input CSV file path")
    parser.add_argument("--output", type=str, default="data/features.csv", help="Output features CSV file path")
    args = parser.parse_args()

    print(f"🔍 Loading series from: {args.input}")
    try:
        df = pd.read_csv(args.input)
    except Exception as e:
        print(f"❌ Failed to load input file: {e}")
        sys.exit(1)

    close_col = [c for c in df.columns if c.lower() in ['close', 'price', 'val', 'value']]
    if not close_col:
        close_col = [df.columns[1]] if len(df.columns) > 1 else [df.columns[0]]
    price_col = close_col[0]

    series = df[price_col].astype(float)
    vr_2 = calculate_variance_ratio(series, lag=2)
    vr_5 = calculate_variance_ratio(series, lag=5)
    
    print("\n📊 Empirical Series Statistical Profile:")
    print(f"  • Total Bars / Observations: {len(series)}")
    print(f"  • Lo-MacKinlay Variance Ratio (lag=2): {vr_2:.4f}")
    print(f"  • Lo-MacKinlay Variance Ratio (lag=5): {vr_5:.4f}")
    
    if vr_2 < 0.95:
        print("  • Market Property: Mean-reverting tendencies detected.")
    elif vr_2 > 1.05:
        print("  • Market Property: Persistence / Trending tendencies detected.")
    else:
        print("  • Market Property: Near Random Walk behavior.")

    # Generic Feature Engineering (Scale-Invariant & Normalized)
    df["returns"] = series.pct_change()
    df["z_returns"] = (df["returns"] - df["returns"].rolling(20).mean()) / (df["returns"].rolling(20).std() + 1e-8)
    df["volatility_20"] = df["returns"].rolling(20).std()
    df["volatility_ratio"] = df["volatility_20"] / (df["returns"].rolling(100).std() + 1e-8)

    df.to_csv(args.output, index=False)
    print(f"\n✅ Generated generic normalized features -> {args.output}")

if __name__ == "__main__":
    main()

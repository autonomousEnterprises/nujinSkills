#!/usr/bin/env python3
import argparse
import sys
import numpy as np
import polars as pl

def process_features(input_path: str, output_path: str, window: int = 20):
    print(f"[FeatureMiner] Reading OHLCV data from {input_path}...")
    df = pl.read_csv(input_path)
    
    # Standardize column names to lowercase
    rename_dict = {col: col.lower() for col in df.columns}
    df = df.rename(rename_dict)
    
    required_cols = ["open", "high", "low", "close", "volume"]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column in CSV: {col}")

    # 1. Bar Geometry & Physics
    df = df.with_columns([
        ((pl.col("high") - pl.col("low")).clip(1e-6, None)).alias("total_range"),
    ]).with_columns([
        ((pl.col("close") - pl.col("open")).abs() / pl.col("total_range")).alias("body_ratio"),
        ((pl.col("high") - pl.max_horizontal("close", "open")) / pl.col("total_range")).alias("upper_wick"),
        ((pl.min_horizontal("close", "open") - pl.col("low")) / pl.col("total_range")).alias("lower_wick"),
        ((pl.col("close") - pl.col("low")) / pl.col("total_range")).alias("buying_pressure"),
        ((pl.col("high") - pl.col("close")) / pl.col("total_range")).alias("selling_pressure"),
        (pl.col("total_range") / (pl.col("volume") + 1e-6)).alias("v_spread"),
    ])
    
    # 2. Effort vs Result (VSA - Volume Z-score)
    vol_mean = pl.col("volume").rolling_mean(window)
    vol_std = pl.col("volume").rolling_std(window).clip(1e-6, None)
    df = df.with_columns([
        ((pl.col("volume") - vol_mean) / vol_std).alias("volume_zscore"),
    ])
    
    # 3. Parkinson Volatility (Intra-candle dispersion)
    pv_factor = 1.0 / (4.0 * np.log(2.0))
    df = df.with_columns([
        (pl.col("high") / pl.col("low").clip(1e-6, None)).log().pow(2).mul(pv_factor).sqrt().rolling_mean(window).alias("parkinson_vol")
    ])
    
    # 4. Rolling Hurst Exponent Proxy (H < 0.45 chop, H > 0.55 trend)
    df = df.with_columns([
        (pl.col("close") / pl.col("close").shift(1).clip(1e-6, None)).log().alias("_ret1"),
        (pl.col("close") / pl.col("close").shift(5).clip(1e-6, None)).log().alias("_ret5"),
    ]).with_columns([
        (pl.col("_ret5").rolling_var(50) / (pl.col("_ret1").rolling_var(50).clip(1e-6, None) * 5.0)).clip(0.1, 0.9).alias("hurst_proxy")
    ]).drop(["_ret1", "_ret5"])
    
    # 5. Anchored VWAP Z-Score Proxy
    df = df.with_columns([
        (pl.col("close") * pl.col("volume")).rolling_sum(100).alias("_pv_sum"),
        pl.col("volume").rolling_sum(100).alias("_v_sum"),
    ]).with_columns([
        (pl.col("_pv_sum") / pl.col("_v_sum").clip(1e-6, None)).alias("avwap_100")
    ]).with_columns([
        ((pl.col("close") - pl.col("avwap_100")) / pl.col("close").rolling_std(100).clip(1e-6, None)).alias("avwap_zscore")
    ]).drop(["_pv_sum", "_v_sum"])

    # 6. Bollinger Bands & Moving Averages for rule evaluation
    df = df.with_columns([
        pl.col("close").rolling_mean(20).alias("sma_20"),
        pl.col("close").rolling_std(20).alias("std_20"),
    ]).with_columns([
        (pl.col("sma_20") + 2.0 * pl.col("std_20")).alias("upper_band"),
        (pl.col("sma_20") - 2.0 * pl.col("std_20")).alias("lower_band"),
    ])

    df.write_csv(output_path)
    print(f"[FeatureMiner] Success! Features written to {output_path} ({len(df)} rows, {len(df.columns)} columns)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Feature Extraction CLI Tool")
    parser.add_argument("--input", required=True, help="Input CSV file path with OHLCV data")
    parser.add_argument("--output", required=True, help="Output CSV file path for extracted features")
    parser.add_argument("--window", type=int, default=20, help="Rolling window size (default: 20)")
    args = parser.parse_args()
    
    process_features(args.input, args.output, args.window)

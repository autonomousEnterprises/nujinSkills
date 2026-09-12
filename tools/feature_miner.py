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

    # 7. Prop Firm Scalping Features (Trader MNQ ATR Bands & Shooting Star Rejection)
    # True Range = max(high - low, abs(high - close_prev), abs(low - close_prev))
    prev_close = pl.col("close").shift(1).fill_null(pl.col("open"))
    tr1 = (pl.col("high") - pl.col("low")).abs()
    tr2 = (pl.col("high") - prev_close).abs()
    tr3 = (pl.col("low") - prev_close).abs()
    
    df = df.with_columns([
        pl.max_horizontal(tr1, tr2, tr3).clip(1e-6, None).alias("true_range")
    ]).with_columns([
        pl.col("true_range").rolling_mean(14).fill_null(pl.col("true_range")).alias("atr_14")
    ]).with_columns([
        (pl.col("close").shift(1) - 3.1 * pl.col("atr_14").shift(1)).alias("atr_lower_band_3_1"),
        (pl.col("close").shift(1) + 3.1 * pl.col("atr_14").shift(1)).alias("atr_upper_band_3_1"),
        # Shooting star pattern: Upper wick >= 2 * body, lower wick <= 0.1 * upper wick, upper wick >= 0.40
        ((pl.col("upper_wick") >= 2.0 * pl.col("body_ratio")) & 
         (pl.col("lower_wick") <= 0.12 * pl.col("upper_wick")) & 
         (pl.col("upper_wick") >= 0.38)).cast(pl.Int32).alias("shooting_star"),
        # Rolling 24h / multi-bar regime: negative drift (bearish daily environment)
        (pl.col("close") < pl.col("close").shift(96).fill_null(pl.col("close"))).cast(pl.Int32).alias("regime_bearish_daily")
    ])

    # 8. Order Flow & Microstructure Toxicity Proxies (CVD, Delta, VPIN Proxy)
    df = df.with_columns([
        (((pl.col("close") - pl.col("open")) / pl.col("total_range")) * pl.col("volume")).alias("delta_proxy")
    ]).with_columns([
        pl.col("delta_proxy").rolling_sum(window).alias("cvd_proxy"),
        (pl.col("delta_proxy").abs().rolling_sum(window) / (pl.col("volume").rolling_sum(window).clip(1e-6, None))).alias("vpin_proxy")
    ])

    # 9. Smart Money Concepts (SMC) & Liquidity Sweeps (FVGs, High/Low Sweeps)
    df = df.with_columns([
        # Fair Value Gaps (Bullish & Bearish Imbalances)
        ((pl.col("low") > pl.col("high").shift(2)) & (pl.col("close") > pl.col("open"))).cast(pl.Int32).alias("fvg_bullish"),
        ((pl.col("high") < pl.col("low").shift(2)) & (pl.col("close") < pl.col("open"))).cast(pl.Int32).alias("fvg_bearish"),
        # Liquidity Sweep Rejections (fading liquidity runs beyond 20-bar rolling extremes)
        ((pl.col("high") > pl.col("high").shift(1).rolling_max(window).fill_null(pl.col("high"))) & 
         (pl.col("upper_wick") >= 0.38) & 
         (pl.col("volume_zscore") > 1.0)).cast(pl.Int32).alias("sweep_high_rejection"),
        ((pl.col("low") < pl.col("low").shift(1).rolling_min(window).fill_null(pl.col("low"))) & 
         (pl.col("lower_wick") >= 0.38) & 
         (pl.col("volume_zscore") > 1.0)).cast(pl.Int32).alias("sweep_low_rejection")
    ])

    # 10. Session Windows / Killzones (if timestamp present)
    if "timestamp" in df.columns:
        # Convert timestamp to UTC hour if numeric unix epoch
        try:
            ts_dtype = df.schema["timestamp"]
            if ts_dtype in [pl.Int64, pl.Float64, pl.Int32]:
                # Assuming unix timestamp in seconds
                df = df.with_columns([
                    ((pl.col("timestamp") % 86400) // 3600).alias("utc_hour")
                ])
                df = df.with_columns([
                    ((pl.col("utc_hour") >= 0) & (pl.col("utc_hour") < 6)).cast(pl.Int32).alias("session_asian"),
                    ((pl.col("utc_hour") >= 7) & (pl.col("utc_hour") < 9)).cast(pl.Int32).alias("killzone_london"),
                    ((pl.col("utc_hour") >= 12) & (pl.col("utc_hour") < 15)).cast(pl.Int32).alias("killzone_ny")
                ])
        except Exception as e:
            print(f"[FeatureMiner] Note on timestamp session extraction: {e}")

    df.write_csv(output_path)
    print(f"[FeatureMiner] Success! Features written to {output_path} ({len(df)} rows, {len(df.columns)} columns)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Feature Extraction CLI Tool")
    parser.add_argument("--input", required=True, help="Input CSV file path with OHLCV data")
    parser.add_argument("--output", required=True, help="Output CSV file path for extracted features")
    parser.add_argument("--window", type=int, default=20, help="Rolling window size (default: 20)")
    args = parser.parse_args()
    
    process_features(args.input, args.output, args.window)

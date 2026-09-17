#!/usr/bin/env python3
"""
Anomaly Scanner: Empirical Quantitative Market Anomaly & Statistical Discovery Engine
Part of NujinSkills Alpha Mining System

Calculates:
1. Variance Ratio & Multi-Horizon Hurst Analysis (Trend vs Random Walk vs Mean-Reversion)
2. Temporal & Session Volatility/Drift Matrix (Hourly anomalies, t-stats, p-values)
3. Conditional Forward Return Distributions across 10 canonical market state conditions:
   - Mean forward return, standard error, t-statistic, p-value, win rate, sample size
4. Alpha Half-Life Decay Curves (Optimal holding horizon before alpha decays to noise)
5. Generates Structured Empirical Briefing (.nujin/empirical_briefing.json) for LLM ingestion
"""

import os
import sys
import json
import argparse
import logging
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("AnomalyScanner")


def load_candles(data_path: str) -> pd.DataFrame:
    """Loads OHLCV candle data and standardizes columns."""
    if not os.path.exists(data_path):
        for fallback in ["data/candles_15m.csv", "data/btc_candles_5m.csv", "data/xauusd_candles_1m.csv"]:
            if os.path.exists(fallback):
                data_path = fallback
                break
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"No candle dataset found at {data_path}")

    df = pd.read_csv(data_path)
    df.columns = [c.lower() for c in df.columns]

    time_col = "timestamp" if "timestamp" in df.columns else ("time" if "time" in df.columns else None)
    if time_col:
        df["time"] = df[time_col].astype(int)
    else:
        df["time"] = np.arange(len(df)) * 900

    for col in ["open", "high", "low", "close", "volume"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(100.0)
        else:
            df[col] = 100.0

    # Retain and convert any additional feature columns
    for col in df.columns:
        if col not in ["time", "timestamp"]:
            try:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            except Exception:
                pass

    return df.sort_values(by="time").reset_index(drop=True)


def compute_variance_ratios_and_hurst(df: pd.DataFrame, lags: List[int] = [2, 4, 8, 16]) -> Dict[str, Any]:
    """
    Computes Lo-MacKinlay Variance Ratio test and empirical Hurst exponent estimate.
    VR(q) = Var(r_q) / (q * Var(r_1))
    Hurst H = 0.5 * (1 + ln(VR(q)) / ln(q))
    """
    close = df["close"].values
    ret1 = np.diff(np.log(close))
    var1 = np.var(ret1, ddof=1)

    if var1 < 1e-12:
        return {"hurst": 0.5, "regime": "RANDOM_WALK", "variance_ratios": {}}

    vr_results = {}
    hurst_estimates = []

    for q in lags:
        ret_q = np.log(close[q:] / close[:-q])
        var_q = np.var(ret_q, ddof=1)
        vr = float(var_q / (q * var1))
        vr_results[f"lag_{q}"] = round(vr, 3)

        if vr > 0:
            h_q = 0.5 * (1.0 + np.log(vr) / np.log(q))
            hurst_estimates.append(np.clip(h_q, 0.1, 0.9))

    avg_hurst = round(float(np.mean(hurst_estimates)) if hurst_estimates else 0.50, 3)
    
    if avg_hurst > 0.55:
        regime = "PERSISTENT_TREND"
        regime_desc = f"Asset exhibits trending momentum (Hurst={avg_hurst:.2f} > 0.55). Trend-following & breakout strategies hold structural statistical advantage."
    elif avg_hurst < 0.45:
        regime = "MEAN_REVERTING"
        regime_desc = f"Asset exhibits mean-reverting chop (Hurst={avg_hurst:.2f} < 0.45). Range fading, liquidity sweep rejection, and envelope reversion hold structural advantage."
    else:
        regime = "RANDOM_WALK"
        regime_desc = f"Asset is near Brownian noise (Hurst={avg_hurst:.2f} in [0.45, 0.55]). High-frequency triggers must rely on microstructural traps rather than directional momentum."

    return {
        "hurst_exponent": avg_hurst,
        "regime": regime,
        "description": regime_desc,
        "variance_ratios": vr_results
    }


def compute_session_hourly_matrix(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Groups returns and range by UTC hour (0-23) to detect session volatility spikes and directional drift.
    """
    if "time" not in df.columns or len(df) < 100:
        return []

    # Derive UTC hour
    ts = df["time"].values
    # If timestamps are in milliseconds
    if ts[0] > 1e11:
        ts = ts // 1000
    hours = (ts % 86400) // 3600
    df["utc_hour"] = hours

    # Compute bar return & range
    df["bar_return"] = (df["close"] - df["open"]) / df["open"]
    df["bar_range"] = (df["high"] - df["low"]) / df["open"]
    baseline_range = df["bar_range"].mean()

    hourly_stats = []
    for h in range(24):
        h_subset = df[df["utc_hour"] == h]
        if len(h_subset) < 10:
            continue

        ret_series = h_subset["bar_return"].values
        mean_ret = float(np.mean(ret_series))
        avg_range = float(h_subset["bar_range"].mean())
        vol_multiplier = round(float(avg_range / (baseline_range + 1e-8)), 2)

        # 1-sample t-test testing H0: mean return == 0
        t_stat, p_val = stats.ttest_1samp(ret_series, 0.0)
        t_stat = float(t_stat) if not np.isnan(t_stat) else 0.0
        p_val = float(p_val) if not np.isnan(p_val) else 1.0

        # Tag sessions
        session_tag = "OFF_HOURS"
        if 0 <= h < 6:
            session_tag = "ASIAN_SESSION"
        elif 7 <= h <= 9:
            session_tag = "LONDON_OPEN"
        elif 10 <= h <= 12:
            session_tag = "LONDON_MIDDAY"
        elif 13 <= h <= 16:
            session_tag = "NEW_YORK_OPEN_OVERLAP"
        elif 17 <= h <= 20:
            session_tag = "NEW_YORK_AFTERNOON"

        is_stat_significant = bool(p_val < 0.05 and abs(t_stat) >= 2.0)

        hourly_stats.append({
            "utc_hour": h,
            "session": session_tag,
            "sample_count": len(h_subset),
            "volatility_multiplier": vol_multiplier,
            "mean_return_pct": round(mean_ret * 100, 3),
            "t_statistic": round(t_stat, 2),
            "p_value": round(p_val, 4),
            "statistically_significant_drift": is_stat_significant
        })

    return hourly_stats


def extract_mathematical_primitives(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes scale-invariant, dimensionless mathematical and auction primitives on raw OHLCV.
    No indicators (no Donchian, no Bollinger, no ATR, no RSI) are hardcoded.
    All metrics are normalized, scale-invariant, and strictly backward-looking (causal).
    """
    d = df.copy()
    c = d["close"]
    h = d["high"]
    l = d["low"]
    o = d["open"]
    v = d["volume"]

    total_range = (h - l).replace(0, 1e-6)

    # 1. Dimensionless Auction Geometry [0.0 to 1.0]
    d["close_location"] = (c - l) / total_range
    d["upper_wick_ratio"] = (h - np.maximum(c, o)) / total_range
    d["lower_wick_ratio"] = (np.minimum(c, o) - l) / total_range
    d["body_ratio"] = (c - o).abs() / total_range

    # 2. Scale-Invariant Log Returns & Volatility Shocks
    d["log_ret"] = np.log(c / c.shift(1).replace(0, 1e-6)).fillna(0.0)
    ret_mean = d["log_ret"].rolling(50).mean()
    ret_std = d["log_ret"].rolling(50).std().replace(0, 1e-6)
    d["ret_zscore"] = (d["log_ret"] - ret_mean) / ret_std

    # 3. Normalized Price Range (Percentage of price)
    d["norm_range"] = total_range / o.replace(0, 1e-6)
    range_median = d["norm_range"].rolling(50).median().replace(0, 1e-6)
    d["relative_range"] = d["norm_range"] / range_median

    # 4. Relative Volume Multiplier (Causal backward-looking rolling median)
    vol_median = v.rolling(50).median().replace(0, 1e-6)
    d["relative_vol"] = v / vol_median

    # 5. Consecutive Directional Runs (Markov State Counter)
    is_up = (c > c.shift(1)).astype(int)
    is_down = (c < c.shift(1)).astype(int)
    
    # Cumulative run length
    d["run_up_3"] = (is_up == 1) & (is_up.shift(1) == 1) & (is_up.shift(2) == 1)
    d["run_down_3"] = (is_down == 1) & (is_down.shift(1) == 1) & (is_down.shift(2) == 1)

    return d


def scan_conditional_anomalies(df: pd.DataFrame, horizons: List[int] = [1, 2, 3, 5, 8, 13, 21]) -> List[Dict[str, Any]]:
    """
    Tests scale-invariant mathematical primitives AND dynamically scans any user feature columns.
    Uses strictly causal backward-looking rolling statistics (zero lookahead bias).
    Evaluates forward return distributions across horizons for both LONG and SHORT directions.
    """
    d = extract_mathematical_primitives(df)
    c = d["close"]

    # 1. Pure Mathematical & Auction Primitives (Scale-Invariant)
    conditions = {
        "RUN_CONSECUTIVE_DOWN_3": d["run_down_3"],
        "RUN_CONSECUTIVE_UP_3": d["run_up_3"],
        "RETURN_SHOCK_DOWNSIDE": d["ret_zscore"] < -2.0,
        "RETURN_SHOCK_UPSIDE": d["ret_zscore"] > 2.0,
        "UPPER_WICK_REJECTION": (d["upper_wick_ratio"] > 0.45) & (d["relative_range"] > 1.2),
        "LOWER_WICK_REJECTION": (d["lower_wick_ratio"] > 0.45) & (d["relative_range"] > 1.2),
        "VOLATILITY_COMPRESSION_50": d["norm_range"] < d["norm_range"].rolling(50).quantile(0.15),
        "VOLUME_EFFORT_ABSORPTION": (d["relative_vol"] > 2.0) & (d["body_ratio"] < 0.30),
        "VOLUME_EFFORT_EXPANSION": (d["relative_vol"] > 2.0) & (d["body_ratio"] > 0.65)
    }

    # 2. Dynamic Open-Domain Feature Columns (User-Supplied in CSV)
    # Strictly backward-looking rolling quantiles (prevents dataset lookahead bias)
    standard_cols = {
        "time", "timestamp", "open", "high", "low", "close", "volume", 
        "utc_hour", "bar_return", "bar_range", "total_range", "log_ret", 
        "ret_zscore", "norm_range", "relative_range", "relative_vol",
        "close_location", "upper_wick_ratio", "lower_wick_ratio", "body_ratio",
        "run_up_3", "run_down_3"
    }
    user_cols = [
        col for col in d.columns 
        if col not in standard_cols and pd.api.types.is_numeric_dtype(d[col])
    ]

    for col in user_cols:
        s = d[col].dropna()
        if len(s) < 100 or s.nunique() < 5:
            continue
        try:
            # Causal backward-looking rolling 50-bar quantiles
            roll_q90 = d[col].rolling(50).quantile(0.90)
            roll_q10 = d[col].rolling(50).quantile(0.10)
            conditions[f"USER_FEATURE_{col.upper()}_SPIKE"] = d[col] >= roll_q90
            conditions[f"USER_FEATURE_{col.upper()}_DIP"] = d[col] <= roll_q10
        except Exception:
            continue

    # Precalculate forward returns for all horizons
    fwd_returns = {}
    for hz in horizons:
        fwd_returns[hz] = (c.shift(-hz) - c) / c

    results = []

    for name, mask in conditions.items():
        indices = np.where(mask)[0]
        # Exclude indices too close to the end
        valid_indices = [idx for idx in indices if idx < len(d) - max(horizons)]
        sample_count = len(valid_indices)

        if sample_count < 15:
            continue

        horizon_data = {}
        peak_abs_t_stat = 0.0
        optimal_horizon = horizons[0]
        optimal_direction = "LONG"
        optimal_trade_return = 0.0

        for hz in horizons:
            rets = fwd_returns[hz].iloc[valid_indices].dropna().values
            if len(rets) < 10:
                continue

            mean_r = float(np.mean(rets))
            std_r = float(np.std(rets, ddof=1))
            t_stat, p_val = stats.ttest_1samp(rets, 0.0)
            t_stat = float(t_stat) if not np.isnan(t_stat) else 0.0
            p_val = float(p_val) if not np.isnan(p_val) else 1.0

            long_win_rate = float(np.sum(rets > 0) / len(rets)) * 100
            short_win_rate = float(np.sum(rets < 0) / len(rets)) * 100

            trade_dir = "LONG" if mean_r >= 0 else "SHORT"
            trade_ret = mean_r if trade_dir == "LONG" else -mean_r
            trade_win = long_win_rate if trade_dir == "LONG" else short_win_rate

            horizon_data[f"h_{hz}"] = {
                "bars": hz,
                "asset_return_pct": round(mean_r * 100, 3),
                "trade_return_pct": round(trade_ret * 100, 3),
                "t_statistic": round(t_stat, 2),
                "p_value": round(p_val, 4),
                "long_win_rate": round(long_win_rate, 1),
                "short_win_rate": round(short_win_rate, 1),
                "optimal_dir": trade_dir
            }

            if abs(t_stat) > peak_abs_t_stat:
                peak_abs_t_stat = abs(t_stat)
                optimal_horizon = hz
                optimal_direction = trade_dir
                optimal_trade_return = trade_ret

        best_hz_info = horizon_data.get(f"h_{optimal_horizon}", {})
        best_p_val = best_hz_info.get("p_value", 1.0)
        best_t_stat = best_hz_info.get("t_statistic", 0.0)
        best_win = best_hz_info.get("long_win_rate" if optimal_direction == "LONG" else "short_win_rate", 50.0)

        # First-principles causal economic hypothesis
        hypothesis_rationale = synthesize_structural_rationale(name, optimal_direction, optimal_horizon, best_t_stat)

        results.append({
            "anomaly_id": name,
            "sample_count": sample_count,
            "favored_direction": optimal_direction,
            "alpha_half_life_bars": optimal_horizon,
            "peak_t_statistic": round(best_t_stat, 2),
            "p_value": best_p_val,
            "expected_return_pct": round(optimal_trade_return * 100, 3),
            "win_rate_pct": round(best_win, 1),
            "is_statistically_significant": bool(best_p_val < 0.05 and peak_abs_t_stat >= 2.0),
            "economic_rationale": hypothesis_rationale,
            "horizons_profile": horizon_data
        })

    results.sort(key=lambda x: abs(x["peak_t_statistic"]), reverse=True)
    return results


def synthesize_structural_rationale(condition_name: str, direction: str, horizon: int, t_stat: float = 0.0) -> str:
    """Generates the causal, first-principles economic explanation for the empirical anomaly."""
    if "RUN_CONSECUTIVE_DOWN" in condition_name:
        behavior = "exhaustion mean-reversion" if direction == "LONG" else "cascade continuation"
        return f"Sequential 3-bar downside selling pressure exhibits statistical {behavior} towards {direction} over {horizon} bars (t={t_stat:+.2f})."
    elif "RUN_CONSECUTIVE_UP" in condition_name:
        behavior = "exhaustion pullback" if direction == "SHORT" else "trend persistence"
        return f"Sequential 3-bar upside buying pressure exhibits statistical {behavior} towards {direction} over {horizon} bars (t={t_stat:+.2f})."
    elif "RETURN_SHOCK_DOWNSIDE" in condition_name:
        behavior = "liquidity squeeze bounce" if direction == "LONG" else "liquidation cascade"
        return f"Statistically extreme downside displacement (> 2 sigma) exhibits {behavior} towards {direction} over {horizon} bars (t={t_stat:+.2f})."
    elif "RETURN_SHOCK_UPSIDE" in condition_name:
        behavior = "mean-reversion fade" if direction == "SHORT" else "breakout continuation"
        return f"Statistically extreme upside displacement (> 2 sigma) exhibits {behavior} towards {direction} over {horizon} bars (t={t_stat:+.2f})."
    elif "UPPER_WICK_REJECTION" in condition_name:
        return f"Auction rejection at highs: elongated upper shadow with range expansion indicates institutional limit absorption ({direction} fade, half-life {horizon} bars)."
    elif "LOWER_WICK_REJECTION" in condition_name:
        return f"Auction rejection at lows: elongated lower shadow with range expansion indicates institutional limit absorption ({direction} bounce, half-life {horizon} bars)."
    elif "VOLATILITY_COMPRESSION" in condition_name:
        return f"Dimensional energy accumulation: price range in bottom 15% precedes directional volatility expansion."
    elif "VOLUME_EFFORT_ABSORPTION" in condition_name:
        return f"Auction liquidity absorption: volume turnover exceeding 2x median with tight body spread demonstrates passive limit presence ({direction})."
    elif "VOLUME_EFFORT_EXPANSION" in condition_name:
        return f"Effort with directional result: volume turnover exceeding 2x median with wide body spread indicates genuine institutional displacement ({direction})."
    elif "USER_FEATURE" in condition_name:
        feat = condition_name.replace("USER_FEATURE_", "")
        return f"User-supplied feature {feat} exhibits statistically significant conditional forward asymmetry towards {direction} over {horizon} bars (t={t_stat:+.2f})."
    return f"Empirical statistical deviation from random walk over {horizon}-bar holding horizon ({direction})."


def generate_empirical_briefing(
    data_path: str,
    output_path: str = ".nujin/empirical_briefing.json"
) -> Dict[str, Any]:
    """
    Executes all statistical scans and writes the Structured Empirical Briefing to disk.
    """
    df = load_candles(data_path)
    asset_name = os.path.basename(data_path).replace(".csv", "")

    hurst_data = compute_variance_ratios_and_hurst(df)
    session_data = compute_session_hourly_matrix(df)
    anomalies = scan_conditional_anomalies(df)

    briefing = {
        "asset": asset_name,
        "dataset_path": data_path,
        "total_bars": len(df),
        "macro_regime_characteristics": hurst_data,
        "session_hourly_matrix": session_data,
        "empirical_anomalies_detected": anomalies,
        "statistically_significant_count": sum(1 for a in anomalies if a["is_statistically_significant"]),
        "generated_at": pd.Timestamp.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(briefing, f, indent=2)

    return briefing


def print_ascii_briefing(briefing: Dict[str, Any]):
    """Pretty prints the empirical briefing for terminal display."""
    asset = briefing.get("asset", "Unknown")
    bars = briefing.get("total_bars", 0)
    hurst_info = briefing.get("macro_regime_characteristics", {})
    anomalies = briefing.get("empirical_anomalies_detected", [])

    print("\n" + "=" * 88)
    print(f" 🔬 NUJINSKILLS EMPIRICAL ANOMALY SCANNER — HARD STATISTICAL DISCOVERY BRIEFING")
    print("=" * 88)
    print(f"  Asset Dataset: {asset} ({bars} Total Historical Bars)")
    print(f"  Macro Regime:  {hurst_info.get('regime')} (Empirical Hurst H = {hurst_info.get('hurst_exponent')})")
    print(f"  ↳ {hurst_info.get('description')}")
    print("-" * 88)

    print("\n[1] TOP EMPIRICAL ANOMALIES (Conditional Forward Returns & Alpha Half-Life):")
    header = f"{'Anomaly / Condition':<32} {'Dir':<6} {'N':<6} {'Half-Life':<10} {'Peak t-Stat':<12} {'p-value':<9} {'Win%':<7} {'Status'}"
    print("-" * len(header))
    print(header)
    print("-" * len(header))

    for a in anomalies:
        status = "🟢 STAT SIG" if a.get("is_statistically_significant") else "⚪ MARGINAL"
        hl_str = f"{a.get('alpha_half_life_bars')} bars"
        t_str = f"{a.get('peak_t_statistic'):+5.2f}"
        p_str = f"{a.get('p_value'):.4f}"
        win_str = f"{a.get('win_rate_pct'):.1f}%"
        print(f"{a['anomaly_id']:<32} {a['favored_direction']:<6} {a['sample_count']:<6} {hl_str:<10} {t_str:<12} {p_str:<9} {win_str:<7} {status}")
    print("-" * len(header))

    print("\n[2] FIRST-PRINCIPLES ECONOMIC RATIONALE (Top Significant Anomalies):")
    sig_anomalies = [a for a in anomalies if a.get("is_statistically_significant")]
    if not sig_anomalies:
        sig_anomalies = anomalies[:3]

    for a in sig_anomalies[:4]:
        dir_icon = "🟢" if a['favored_direction'] == "LONG" else "🔴"
        print(f"  {dir_icon} [{a['anomaly_id']}] -> Optimal Action: {a['favored_direction']} (Exit after {a['alpha_half_life_bars']} bars)")
        print(f"     ↳ Stats: t={a['peak_t_statistic']:+.2f}, p={a['p_value']:.4f}, Exp Return: {a['expected_return_pct']:+.2f}%, Win: {a['win_rate_pct']:.1f}%")
        print(f"     ↳ Rationale: {a['economic_rationale']}\n")

    print("=" * 88 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NujinSkills Empirical Anomaly Scanner")
    parser.add_argument("--data", type=str, default="data/candles_15m.csv", help="Path to OHLCV candle CSV")
    parser.add_argument("--output", type=str, default=".nujin/empirical_briefing.json", help="Path to output JSON briefing")
    parser.add_argument("--json", action="store_true", help="Output raw JSON to stdout")

    args = parser.parse_args()

    briefing = generate_empirical_briefing(data_path=args.data, output_path=args.output)

    if args.json:
        print(json.dumps(briefing, indent=2))
    else:
        print_ascii_briefing(briefing)

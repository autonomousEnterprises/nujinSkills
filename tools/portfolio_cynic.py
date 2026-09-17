#!/usr/bin/env python3
"""
Portfolio Cynic: Correlation Matrix & Regime Orthogonality Engine
Part of NujinSkills Quantitative System

Computes:
1. Pairwise Pearson & Spearman return correlation matrix (rho_ij) across candidate & active strategies.
2. Market Regime Slicing (Bull, Bear, Range/Chop) with per-regime Sharpe, Win Rate, and PnL.
3. Blended Portfolio Metrics (Ensemble Sharpe, Combined MaxDD, Diversification Benefit Ratio).
4. Orthogonality Gate: Flag/reject strategies with correlation > threshold (default 0.50) against active portfolio.
"""

import os
import sys
import json
import argparse
import logging
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from server.backtest_engine import load_strategy_instance, _ensure_freqtrade_shim

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("PortfolioCynic")


def load_candle_data(data_path: str = "data/candles_15m.csv") -> pd.DataFrame:
    """Loads and standardizes historical candle data."""
    if not os.path.exists(data_path):
        # Fallback search
        for fallback in ["data/btc_candles_5m.csv", "data/xauusd_candles_1m.csv"]:
            if os.path.exists(fallback):
                data_path = fallback
                break
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"No candle dataset found at {data_path}")

    df = pd.read_csv(data_path)
    time_col = "timestamp" if "timestamp" in df.columns else "time"
    if time_col not in df.columns:
        df["time"] = np.arange(len(df)) * 900
    else:
        df["time"] = df[time_col].astype(int)

    for col in ["open", "high", "low", "close", "volume"]:
        if col in df.columns:
            df[col] = df[col].astype(float)
        else:
            df[col] = 100.0

    return df.sort_values(by="time").reset_index(drop=True)


def classify_market_regimes(df: pd.DataFrame, window: int = 96) -> pd.Series:
    """
    Classifies each bar into one of three market regimes:
    - 'BULL': Price above 200 EMA with positive 20-bar slope
    - 'BEAR': Price below 200 EMA with negative 20-bar slope
    - 'RANGE': Oscillating around baseline, ADX < 20 or low slope
    """
    close = df["close"]
    ema200 = close.ewm(span=min(200, len(df)), adjust=False).mean()
    slope = (ema200 - ema200.shift(20)) / ema200.shift(20)

    regimes = pd.Series("RANGE", index=df.index)
    bull_mask = (close > ema200) & (slope > 0.002)
    bear_mask = (close < ema200) & (slope < -0.002)

    regimes[bull_mask] = "BULL"
    regimes[bear_mask] = "BEAR"
    return regimes


def simulate_strategy_bar_returns(strategy_name: str, df: pd.DataFrame) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
    """
    Executes a strategy's populate_indicators and entry/exit logic,
    returning a continuous bar-by-bar return array matching the length of df.
    """
    clean_name = strategy_name.replace(".py", "")
    strat = load_strategy_instance(clean_name)
    if not strat:
        logger.warning(f"Could not instantiate strategy class for {clean_name}")
        return np.zeros(len(df)), []

    df_strat = df.copy()
    metadata = {"pair": "BTC/USDT"}

    try:
        df_strat = strat.populate_indicators(df_strat, metadata)
        df_strat = strat.populate_entry_trend(df_strat, metadata)
        if hasattr(strat, "populate_exit_trend"):
            df_strat = strat.populate_exit_trend(df_strat, metadata)
        else:
            df_strat["exit_long"] = 0
            df_strat["exit_short"] = 0
    except Exception as e:
        logger.warning(f"Error evaluating strategy {clean_name}: {e}")
        return np.zeros(len(df)), []

    enter_long = df_strat.get("enter_long", pd.Series(0, index=df_strat.index)).fillna(0).astype(int)
    enter_short = df_strat.get("enter_short", pd.Series(0, index=df_strat.index)).fillna(0).astype(int)
    exit_long = df_strat.get("exit_long", pd.Series(0, index=df_strat.index)).fillna(0).astype(int)
    exit_short = df_strat.get("exit_short", pd.Series(0, index=df_strat.index)).fillna(0).astype(int)

    # Friction: 5 bps taker fee + 2 bps slippage per side (7 bps = 0.0007)
    friction = 0.0007
    bar_returns = np.zeros(len(df_strat))
    trades = []

    in_pos = 0  # 1 for long, -1 for short, 0 flat
    entry_bar = 0
    entry_price = 0.0
    max_hold_bars = getattr(strat, "max_hold_bars", 20)

    for i in range(1, len(df_strat)):
        c_price = df_strat.loc[i, "close"]
        prev_price = df_strat.loc[i - 1, "close"]
        time_curr = int(df_strat.loc[i, "time"])

        if in_pos == 1:
            raw_bar_ret = (c_price - prev_price) / prev_price
            bars_held = i - entry_bar
            should_exit = (exit_long.iloc[i] == 1) or (bars_held >= max_hold_bars) or (c_price <= entry_price * 0.985) or (c_price >= entry_price * 1.03)
            if should_exit:
                bar_returns[i] = raw_bar_ret - friction
                pnl = (c_price - entry_price) / entry_price - (friction * 2)
                trades.append({
                    "entry_bar": entry_bar, "exit_bar": i,
                    "direction": "LONG", "pnl": pnl,
                    "entry_time": int(df_strat.loc[entry_bar, "time"]),
                    "exit_time": time_curr
                })
                in_pos = 0
            else:
                bar_returns[i] = raw_bar_ret
        elif in_pos == -1:
            raw_bar_ret = -(c_price - prev_price) / prev_price
            bars_held = i - entry_bar
            should_exit = (exit_short.iloc[i] == 1) or (bars_held >= max_hold_bars) or (c_price >= entry_price * 1.015) or (c_price <= entry_price * 0.97)
            if should_exit:
                bar_returns[i] = raw_bar_ret - friction
                pnl = (entry_price - c_price) / entry_price - (friction * 2)
                trades.append({
                    "entry_bar": entry_bar, "exit_bar": i,
                    "direction": "SHORT", "pnl": pnl,
                    "entry_time": int(df_strat.loc[entry_bar, "time"]),
                    "exit_time": time_curr
                })
                in_pos = 0
            else:
                bar_returns[i] = raw_bar_ret
        else:
            if enter_long.iloc[i] == 1:
                in_pos = 1
                entry_bar = i
                entry_price = c_price
                bar_returns[i] = -friction
            elif enter_short.iloc[i] == 1:
                in_pos = -1
                entry_bar = i
                entry_price = c_price
                bar_returns[i] = -friction

    return bar_returns, trades


def calculate_metrics(returns: np.ndarray) -> Dict[str, float]:
    """Computes Sharpe, Total Return %, and Max Drawdown from bar returns."""
    active_r = returns[returns != 0]
    if len(active_r) < 5:
        return {"sharpe": 0.0, "total_return_pct": 0.0, "max_drawdown_pct": 0.0}

    ann_factor = np.sqrt(35040)
    std = float(np.std(returns))
    sharpe = float((np.mean(returns) / std) * ann_factor) if std > 1e-8 else 0.0

    cum = np.cumsum(returns)
    total_ret = float(cum[-1] * 100) if len(cum) > 0 else 0.0
    running_max = np.maximum.accumulate(cum)
    drawdowns = running_max - cum
    max_dd = float(np.max(drawdowns) * 100) if len(drawdowns) > 0 else 0.0

    return {
        "sharpe": round(sharpe, 2),
        "total_return_pct": round(total_ret, 2),
        "max_drawdown_pct": round(max_dd, 2)
    }


def evaluate_portfolio(
    strategy_names: Optional[List[str]] = None,
    data_path: str = "data/candles_15m.csv",
    correlation_threshold: float = 0.50
) -> Dict[str, Any]:
    """
    Main portfolio evaluation engine:
    1. Loads candidates/active strategies.
    2. Runs continuous bar return simulations.
    3. Builds Pearson & Spearman correlation matrices.
    4. Evaluates Bull, Bear, Range regime breakdown.
    5. Calculates blended portfolio metrics and diversification ratio.
    """
    df = load_candle_data(data_path)
    regimes = classify_market_regimes(df)

    if not strategy_names:
        strat_dir = "strategies"
        if os.path.exists(strat_dir):
            strategy_names = [f.replace(".py", "") for f in os.listdir(strat_dir) if f.endswith(".py") and not f.startswith("__")]
        else:
            strategy_names = []

    if not strategy_names:
        return {"error": "No strategies provided or found in strategies/"}

    strategy_returns: Dict[str, np.ndarray] = {}
    strategy_trades: Dict[str, List[Dict[str, Any]]] = {}
    individual_metrics: Dict[str, Any] = {}
    regime_breakdown: Dict[str, Any] = {}

    for s_name in strategy_names:
        ret, trades = simulate_strategy_bar_returns(s_name, df)
        strategy_returns[s_name] = ret
        strategy_trades[s_name] = trades
        individual_metrics[s_name] = calculate_metrics(ret)

        reg_metrics = {}
        for r_name in ["BULL", "BEAR", "RANGE"]:
            mask = (regimes == r_name).values
            r_ret = ret[mask]
            reg_metrics[r_name] = {
                "trades": sum(1 for t in trades if df.loc[t["entry_bar"], "time"] in df.loc[mask, "time"].values),
                "pnl_pct": round(float(np.sum(r_ret) * 100), 2),
                "sharpe": round(float((np.mean(r_ret) / (np.std(r_ret) + 1e-8)) * np.sqrt(35040)), 2) if np.std(r_ret) > 1e-8 else 0.0
            }
        regime_breakdown[s_name] = reg_metrics

    ret_df = pd.DataFrame(strategy_returns)
    valid_cols = [c for c in ret_df.columns if ret_df[c].std() > 1e-8]
    if len(valid_cols) > 1:
        corr_matrix = ret_df[valid_cols].corr(method="pearson").round(3).to_dict()
        spearman_matrix = ret_df[valid_cols].corr(method="spearman").round(3).to_dict()
    else:
        corr_matrix = {c: {c: 1.0} for c in valid_cols}
        spearman_matrix = {c: {c: 1.0} for c in valid_cols}

    redundancy_flags = []
    for i, c1 in enumerate(valid_cols):
        for j, c2 in enumerate(valid_cols):
            if i < j:
                rho = corr_matrix.get(c1, {}).get(c2, 0.0)
                if rho > correlation_threshold:
                    redundancy_flags.append({
                        "pair": f"{c1} <-> {c2}",
                        "correlation": rho,
                        "status": "REDUNDANT",
                        "recommendation": f"High collinearity (rho={rho:.2f} > {correlation_threshold}). Running both doubles leverage during drawdowns without diversification benefits."
                    })
                elif rho < 0.15:
                    redundancy_flags.append({
                        "pair": f"{c1} <-> {c2}",
                        "correlation": rho,
                        "status": "COMPLEMENTARY",
                        "recommendation": f"Excellent regime orthogonality (rho={rho:.2f}). Highly complementary return stream."
                    })

    if valid_cols:
        blended_returns = ret_df[valid_cols].mean(axis=1).values
        blended_metrics = calculate_metrics(blended_returns)

        indiv_vols = [ret_df[c].std() for c in valid_cols]
        blended_vol = float(np.std(blended_returns))
        div_ratio = round(float(np.mean(indiv_vols) / (blended_vol + 1e-8)), 2)
    else:
        blended_metrics = {"sharpe": 0.0, "total_return_pct": 0.0, "max_drawdown_pct": 0.0}
        div_ratio = 1.0

    return {
        "strategies": valid_cols,
        "correlation_matrix": corr_matrix,
        "spearman_matrix": spearman_matrix,
        "individual_metrics": individual_metrics,
        "regime_breakdown": regime_breakdown,
        "portfolio_ensemble": {
            "blended_sharpe": blended_metrics["sharpe"],
            "blended_total_return_pct": blended_metrics["total_return_pct"],
            "blended_max_drawdown_pct": blended_metrics["max_drawdown_pct"],
            "diversification_ratio": div_ratio,
            "correlation_threshold": correlation_threshold
        },
        "pairwise_analysis": redundancy_flags
    }


def print_ascii_report(report: Dict[str, Any]):
    """Pretty prints an ASCII table summary of the portfolio correlation & regime breakdown."""
    strats = report.get("strategies", [])
    corr = report.get("correlation_matrix", {})
    ens = report.get("portfolio_ensemble", {})
    reg = report.get("regime_breakdown", {})

    print("\n" + "=" * 80)
    print(" 📊 NUJINSKILLS PORTFOLIO CYNIC — CORRELATION & REGIME ORTHOGONALITY")
    print("=" * 80)

    # 1. Correlation Matrix Table
    print("\n[1] PAIRWISE RETURN CORRELATION MATRIX (Pearson rho):")
    header = f"{'Strategy':<30}" + "".join([f"{s[:10]:>12}" for s in strats])
    print("-" * len(header))
    print(header)
    print("-" * len(header))
    for s1 in strats:
        row = f"{s1:<30}"
        for s2 in strats:
            val = corr.get(s1, {}).get(s2, 0.0)
            color_mark = f"{val:+.2f}"
            row += f"{color_mark:>12}"
        print(row)
    print("-" * len(header))

    # 2. Regime Breakdown
    print("\n[2] REGIME SLICING ATTRIBUTION (PnL % / Sharpe):")
    print(f"{'Strategy':<30} | {'BULL REGIME':<18} | {'BEAR REGIME':<18} | {'RANGE/CHOP':<18}")
    print("-" * 92)
    for s in strats:
        r_info = reg.get(s, {})
        b_pnl = r_info.get("BULL", {}).get("pnl_pct", 0)
        b_sr = r_info.get("BULL", {}).get("sharpe", 0)
        be_pnl = r_info.get("BEAR", {}).get("pnl_pct", 0)
        be_sr = r_info.get("BEAR", {}).get("sharpe", 0)
        rg_pnl = r_info.get("RANGE", {}).get("pnl_pct", 0)
        rg_sr = r_info.get("RANGE", {}).get("sharpe", 0)
        print(f"{s:<30} | {b_pnl:>+6.1f}% (SR {b_sr:4.1f}) | {be_pnl:>+6.1f}% (SR {be_sr:4.1f}) | {rg_pnl:>+6.1f}% (SR {rg_sr:4.1f})")
    print("-" * 92)

    # 3. Blended Portfolio Metrics
    print("\n[3] ENSEMBLE BLENDED PORTFOLIO STATS:")
    print(f"  • Blended Annualized Sharpe : {ens.get('blended_sharpe', 0.0):.2f}")
    print(f"  • Blended Max Drawdown      : {ens.get('blended_max_drawdown_pct', 0.0):.2f}%")
    print(f"  • Blended Net Return        : {ens.get('blended_total_return_pct', 0.0):.2f}%")
    print(f"  • Diversification Ratio     : {ens.get('diversification_ratio', 1.0):.2f}x (Volatility Reduction)")

    # 4. Pairwise Complementarity Status
    print("\n[4] COMPLEMENTARITY AUDIT FLAGS:")
    pairs = report.get("pairwise_analysis", [])
    if not pairs:
        print("  None detected.")
    else:
        for p in pairs:
            badge = "🟢 [COMPLEMENTARY]" if p["status"] == "COMPLEMENTARY" else "🔴 [REDUNDANT / REJECT]"
            print(f"  {badge:<24} {p['pair']:<35} (rho={p['correlation']:+.2f})")
            print(f"    ↳ {p['recommendation']}")

    print("=" * 80 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Portfolio Correlation Matrix & Regime Orthogonality Cynic")
    parser.add_argument("--strategies", type=str, default="", help="Comma-separated strategy names (default: all in strategies/)")
    parser.add_argument("--data", type=str, default="data/candles_15m.csv", help="Candle CSV dataset")
    parser.add_argument("--threshold", type=float, default=0.50, help="Correlation rejection threshold (default: 0.50)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON instead of ASCII report")

    args = parser.parse_args()
    s_list = [s.strip() for s in args.strategies.split(",") if s.strip()] if args.strategies else None

    result = evaluate_portfolio(strategy_names=s_list, data_path=args.data, correlation_threshold=args.threshold)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print_ascii_report(result)

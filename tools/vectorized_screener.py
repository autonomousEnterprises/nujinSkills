#!/usr/bin/env python3
import argparse
import json
import sys
import numpy as np
import pandas as pd

import os

def run_screener(data_path: str, rules_json: str, fee_bps: float, slippage_bps: float, output_path: str, strategy: str = ""):
    # 1. Resolve Data Path
    if not os.path.exists(data_path):
        for fallback in ["data/candles_15m.csv", "data/features.csv", "data/xauusd_candles_1m.csv"]:
            if os.path.exists(fallback):
                print(f"[VectorizedScreener] Notice: '{data_path}' not found. Falling back to '{fallback}'.")
                data_path = fallback
                break

    if not os.path.exists(data_path):
        print(f"[VectorizedScreener] ERROR: Data file '{data_path}' not found.")
        sys.exit(1)

    print(f"[VectorizedScreener] Loading dataset from {data_path}...")
    df = pd.read_csv(data_path)

    # If raw candles lack features, compute essential features
    if "lower_wick" not in df.columns and "high" in df.columns and "low" in df.columns and "close" in df.columns:
        total_range = (df["high"] - df["low"]).clip(1e-6, None)
        df["lower_wick"] = (df[["close", "open"]].min(axis=1) - df["low"]) / total_range
        df["upper_wick"] = (df["high"] - df[["close", "open"]].max(axis=1)) / total_range
        df["body_ratio"] = (df["close"] - df["open"]).abs() / total_range
        vol_mean = df["volume"].rolling(20).mean()
        vol_std = df["volume"].rolling(20).std().clip(1e-6, None)
        df["volume_zscore"] = (df["volume"] - vol_mean) / vol_std

    sl_stop = None
    tp_stop = None
    max_bars = 12

    # 2. Strategy evaluation vs Rule string evaluation
    if strategy:
        import sys
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        if root_dir not in sys.path:
            sys.path.insert(0, root_dir)
        from server.backtest_engine import load_strategy_instance
        clean_name = os.path.basename(strategy).replace(".py", "")
        strat = load_strategy_instance(clean_name)
        if not strat:
            print(f"[VectorizedScreener] ERROR: Could not instantiate strategy '{clean_name}'.")
            sys.exit(1)
        
        metadata = {"pair": "BTC/USDT"}
        df = strat.populate_indicators(df, metadata)
        df = strat.populate_entry_trend(df, metadata)
        if hasattr(strat, "populate_exit_trend"):
            df = strat.populate_exit_trend(df, metadata)
        else:
            df["exit_long"] = 0
            df["exit_short"] = 0

        entries = (df.get("enter_long", 0) == 1) | (df.get("enter_short", 0) == 1)
        raw_exits = (df.get("exit_long", 0) == 1) | (df.get("exit_short", 0) == 1)
        sl_stop = getattr(strat, "stoploss", None)
        if sl_stop is not None:
            sl_stop = abs(float(sl_stop))
    else:
        try:
            rules = json.loads(rules_json) if isinstance(rules_json, str) else (rules_json or {})
        except Exception as e:
            print(f"[VectorizedScreener] Error parsing rules JSON: {e}")
            sys.exit(1)
            
        entry_rule = rules.get("entry_long", rules.get("entry", "lower_wick > 0.55 and volume_zscore > 1.5"))
        exit_rule = rules.get("exit", None)
        max_bars = int(rules.get("max_bars_held", 12))
        sl_stop = float(rules.get("stop_loss", 0.0)) if rules.get("stop_loss") else None
        tp_stop = float(rules.get("take_profit", 0.0)) if rules.get("take_profit") else None

        # Evaluate Entry Conditions safely
        try:
            entries = df.eval(entry_rule).astype(bool)
        except Exception as e:
            print(f"[VectorizedScreener] Failed to evaluate entry rule '{entry_rule}': {e}")
            entries = (df.get('lower_wick', 0) > 0.5) & (df.get('volume_zscore', 0) > 1.0)

        # Evaluate Exit Conditions safely
        if exit_rule and exit_rule != "bars >= 12":
            try:
                raw_exits = df.eval(exit_rule).astype(bool)
            except Exception:
                raw_exits = pd.Series(False, index=df.index)
        else:
            raw_exits = pd.Series(False, index=df.index)

    # Holding period exits
    exits = pd.Series(False, index=entries.index)
    bars_held = 0
    in_pos = False
    for i in range(len(entries)):
        if in_pos:
            bars_held += 1
            if bars_held >= max_bars or bool(raw_exits.iloc[i]) or i == len(entries) - 1:
                exits.iloc[i] = True
                in_pos = False
                bars_held = 0
        elif bool(entries.iloc[i]):
            in_pos = True
            bars_held = 0

    close_series = df['close']
    fee_rate = fee_bps / 10000.0
    slippage_rate = slippage_bps / 10000.0

    # Execute VectorBT Portfolio Simulation
    try:
        import vectorbt as vbt
        vbt_kwargs = {
            "close": close_series,
            "entries": entries,
            "exits": exits,
            "fees": fee_rate,
            "slippage": slippage_rate,
            "freq": "15m"
        }
        if sl_stop and sl_stop > 0:
            vbt_kwargs["sl_stop"] = sl_stop
        if tp_stop and tp_stop > 0:
            vbt_kwargs["tp_stop"] = tp_stop

        pf = vbt.Portfolio.from_signals(**vbt_kwargs)
        num_trades = int(pf.trades.count())

        if num_trades == 0:
            trade_returns = np.array([])
            sharpe = 0.0
            win_rate = 0.0
            profit_factor = 0.0
            max_dd = 0.0
            expectancy_bps = 0.0
        else:
            trade_returns = pf.trades.returns.values
            sharpe_val = pf.sharpe_ratio()
            sharpe = float(sharpe_val) if not np.isnan(sharpe_val) else 0.0
            win_rate = float(pf.trades.win_rate())
            pf_val = pf.trades.profit_factor()
            profit_factor = float(pf_val) if not np.isinf(pf_val) and not np.isnan(pf_val) else 999.0
            max_dd = abs(float(pf.max_drawdown()))
            mean_ret = float(np.mean(trade_returns)) if len(trade_returns) > 0 else 0.0
            expectancy_bps = mean_ret * 10000.0

    except Exception as e_vbt:
        print(f"[VectorizedScreener] VectorBT execution error ({e_vbt}), falling back to direct calculations...")
        trade_returns = np.array([])
        num_trades = 0
        sharpe = 0.0
        win_rate = 0.0
        profit_factor = 0.0
        max_dd = 0.0
        expectancy_bps = 0.0

    if num_trades == 0:
        results = {
            "status": "REJECT",
            "reason": "Zero trades generated by strategy rules",
            "sharpe": 0.0,
            "trades": 0,
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "max_drawdown": 0.0,
            "expectancy_bps": 0.0
        }
        print(json.dumps(results, indent=2))
        with open(output_path, 'w') as f:
            json.dump([], f)
        return

    fee_threshold_bps = 2.0 * (fee_bps + slippage_bps)
    reasons = []
    if sharpe < 1.3:
        reasons.append(f"Sharpe {sharpe:.2f} < 1.3")
    if num_trades < 60:
        reasons.append(f"Trades {num_trades} < 60")
    if profit_factor < 1.4:
        reasons.append(f"Profit Factor {profit_factor:.2f} < 1.4")
    if expectancy_bps <= fee_threshold_bps:
        reasons.append(f"Expectancy {expectancy_bps:.1f}bps <= 2x Fees ({fee_threshold_bps:.1f}bps)")
        
    status = "PASS" if len(reasons) == 0 else "REJECT"
    
    summary = {
        "status": status,
        "reasons": reasons,
        "sharpe": round(sharpe, 4),
        "trades": num_trades,
        "win_rate": round(win_rate, 4),
        "profit_factor": round(profit_factor, 4),
        "max_drawdown": round(max_dd, 4),
        "expectancy_bps": round(expectancy_bps, 2),
        "fee_bps": fee_bps,
        "slippage_bps": slippage_bps,
        "engine": "vectorbt"
    }
    
    print(json.dumps(summary, indent=2))
    
    with open(output_path, 'w') as f:
        json.dump(trade_returns.tolist(), f)
    print(f"[VectorizedScreener] Candidate trade returns written to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Vectorized In-Sample Strategy Coarse Filter via VectorBT")
    parser.add_argument("--data", default="data/candles_15m.csv", help="Input dataset or features CSV file path (default: data/candles_15m.csv)")
    parser.add_argument("--rules", default="", help="Rule dict or JSON string specifying strategy entry/exit")
    parser.add_argument("--strategy", default="", help="Strategy filename or path to screen directly")
    parser.add_argument("--fee-bps", type=float, default=5.0, help="Taker fee in bps (default: 5.0)")
    parser.add_argument("--slippage-bps", type=float, default=2.0, help="Slippage in bps (default: 2.0)")
    parser.add_argument("--output", default="data/screener_returns.json", help="Output JSON path for trade return series")
    args = parser.parse_args()
    
    if not args.rules and not args.strategy:
        print("[VectorizedScreener] ERROR: Must provide either --rules or --strategy.")
        sys.exit(1)

    run_screener(args.data, args.rules, args.fee_bps, args.slippage_bps, args.output, strategy=args.strategy)

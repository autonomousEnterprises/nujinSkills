import os
import sys
import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional

logger = logging.getLogger("ChartPrimitives")

COLOR_PALETTE = [
    "#38bdf8", # Sky Blue (Fast EMA)
    "#f59e0b", # Amber (Mid EMA / Level)
    "#a855f7", # Purple (Slow EMA)
    "#ec4899", # Pink
    "#10b981", # Emerald (Support / Lower Band)
    "#f43f5e", # Rose (Resistance / Upper Band)
    "#06b6d4", # Cyan
    "#84cc16", # Lime
]

def _classify_line(col_name: str, idx: int) -> Dict[str, Any]:
    c_lower = col_name.lower()
    title = col_name.replace("_", " ").title()
    line_width = 1.5
    line_style = 0 # 0: Solid, 1: Dotted, 2: Dashed

    if "ema" in c_lower or "sma" in c_lower:
        title = col_name.upper()
        if "fast" in c_lower or any(f"_{s}" in c_lower for s in [7, 9, 10, 13]):
            color = "#38bdf8"
        elif "mid" in c_lower or any(f"_{s}" in c_lower for s in [20, 21, 30, 34]):
            color = "#f59e0b"
        elif "slow" in c_lower or any(f"_{s}" in c_lower for s in [50, 89, 100]):
            color = "#a855f7"
        else:
            color = "#ec4899"
    elif "upper" in c_lower or "high" in c_lower or "res" in c_lower:
        color = "#f43f5e"
        line_style = 2 # Dashed
        line_width = 1.0
    elif "lower" in c_lower or "low" in c_lower or "sup" in c_lower:
        color = "#10b981"
        line_style = 2 # Dashed
        line_width = 1.0
    elif "mid" in c_lower or "middle" in c_lower or "poc" in c_lower:
        color = "#94a3b8"
        line_style = 1 # Dotted
        line_width = 1.0
    else:
        color = COLOR_PALETTE[idx % len(COLOR_PALETTE)]

    return {
        "id": col_name,
        "title": title,
        "color": color,
        "lineWidth": line_width,
        "lineStyle": line_style
    }

def extract_strategy_primitives(strategy_name: str, candles: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not candles:
        return {"lines": [], "boxes": [], "levels": [], "hud_items": []}

    try:
        from server.backtest_engine import load_strategy_instance
        strat = load_strategy_instance(strategy_name)
    except Exception as e:
        logger.warning(f"[ChartPrimitives] Could not load strategy {strategy_name}: {e}")
        strat = None

    df = pd.DataFrame(candles)
    if "time" not in df.columns and "timestamp" in df.columns:
        df["time"] = df["timestamp"]

    # If strategy has populate_indicators, execute it in Python
    if strat and hasattr(strat, "populate_indicators"):
        try:
            df = strat.populate_indicators(df, {})
        except Exception as e:
            logger.error(f"[ChartPrimitives] populate_indicators error for {strategy_name}: {e}")

    # Check for custom get_chart_primitives method
    if strat and hasattr(strat, "get_chart_primitives"):
        try:
            res = strat.get_chart_primitives(df)
            if isinstance(res, dict):
                return res
        except Exception as e:
            logger.warning(f"[ChartPrimitives] Custom get_chart_primitives failed: {e}")

    # Auto-extract primitives dynamically
    standard_cols = {"open", "high", "low", "close", "volume", "time", "timestamp", "enter_long", "enter_short", "exit_long", "exit_short"}
    
    lines_cfg = []
    series_data = {}
    boxes = []
    levels = []
    hud_items = []

    # 1. Line Series Auto-Discovery (EMAs, Bands, Channels, S&R)
    indicator_cols = [c for c in df.columns if c not in standard_cols and pd.api.types.is_numeric_dtype(df[c])]
    
    # Prioritize price overlays (ignore non-price columns like volume zscore, boolean flags)
    close_median = df["close"].median() if "close" in df.columns else 1.0
    valid_line_cols = []

    for col in indicator_cols:
        series = df[col].dropna()
        if len(series) == 0:
            continue
        # Check if values are close to price range (price overlay)
        med_val = series.median()
        if med_val > close_median * 0.1 and med_val < close_median * 10.0:
            valid_line_cols.append(col)

    # If strategy has chart_indicators manifest, use that
    custom_manifest = getattr(strat, "chart_indicators", None) if strat else None
    if custom_manifest and isinstance(custom_manifest, list):
        for cfg in custom_manifest:
            cid = cfg.get("id")
            if cid in df.columns:
                pts = [{"time": int(t), "value": round(float(v), 4)} for t, v in zip(df["time"], df[cid]) if pd.notnull(v)]
                lines_cfg.append(cfg)
                series_data[cid] = pts
    else:
        # Auto-configure up to 6 key price overlays
        for idx, col in enumerate(valid_line_cols[:6]):
            cfg = _classify_line(col, idx)
            pts = [{"time": int(t), "value": round(float(v), 4)} for t, v in zip(df["time"], df[col]) if pd.notnull(v)]
            lines_cfg.append(cfg)
            series_data[col] = pts

    # 2. 2D Zone Boxes Auto-Discovery (FVG, Order Blocks, Asian Range)
    # Fair Value Gaps
    if "fvg_bullish" in df.columns or ("low" in df.columns and "high" in df.columns):
        fvg_bull_mask = df.get("fvg_bullish", pd.Series(0, index=df.index))
        fvg_bear_mask = df.get("fvg_bearish", pd.Series(0, index=df.index))

        # Scan recent 200 bars for distinct FVGs
        scan_len = min(250, len(df))
        sub_df = df.iloc[-scan_len:].reset_index(drop=True)
        for i in range(2, len(sub_df)):
            t_curr = int(sub_df.loc[i, "time"])
            t_prev2 = int(sub_df.loc[i-2, "time"])
            
            # Bullish FVG: Low of candle i > High of candle i-2
            if (fvg_bull_mask.iloc[-scan_len + i] if len(fvg_bull_mask) >= scan_len else False) or (sub_df.loc[i, "low"] > sub_df.loc[i-2, "high"] and sub_df.loc[i-1, "close"] > sub_df.loc[i-1, "open"]):
                p_high = float(sub_df.loc[i, "low"])
                p_low = float(sub_df.loc[i-2, "high"])
                if p_high > p_low:
                    # Extend box up to 15 bars forward or end of data
                    end_idx = min(len(sub_df) - 1, i + 12)
                    t_end = int(sub_df.loc[end_idx, "time"])
                    boxes.append({
                        "id": f"fvg_bull_{t_curr}",
                        "label": "Bullish FVG",
                        "time_start": t_prev2,
                        "time_end": t_end,
                        "price_high": p_high,
                        "price_low": p_low,
                        "color": "rgba(38, 166, 154, 0.20)",
                        "borderColor": "#26a69a",
                        "borderStyle": "dashed",
                        "type": "FVG_BULL"
                    })

            # Bearish FVG: High of candle i < Low of candle i-2
            if (fvg_bear_mask.iloc[-scan_len + i] if len(fvg_bear_mask) >= scan_len else False) or (sub_df.loc[i, "high"] < sub_df.loc[i-2, "low"] and sub_df.loc[i-1, "close"] < sub_df.loc[i-1, "open"]):
                p_high = float(sub_df.loc[i-2, "low"])
                p_low = float(sub_df.loc[i, "high"])
                if p_high > p_low:
                    end_idx = min(len(sub_df) - 1, i + 12)
                    t_end = int(sub_df.loc[end_idx, "time"])
                    boxes.append({
                        "id": f"fvg_bear_{t_curr}",
                        "label": "Bearish FVG",
                        "time_start": t_prev2,
                        "time_end": t_end,
                        "price_high": p_high,
                        "price_low": p_low,
                        "color": "rgba(239, 83, 80, 0.20)",
                        "borderColor": "#ef5350",
                        "borderStyle": "dashed",
                        "type": "FVG_BEAR"
                    })

    # Limit to latest 8 most relevant boxes to prevent visual clutter
    boxes = boxes[-8:]

    # 3. Horizontal Price Levels (Daily Open, ATR Pivots, Key Highs/Lows)
    if "open" in df.columns and len(df) > 0:
        latest_close = float(df["close"].iloc[-1])
        # Daily open approximation (first candle of UTC day or rolling 96 bars on 15m)
        lookback = min(96, len(df))
        d_open = float(df["open"].iloc[-lookback])
        levels.append({
            "id": "day_open",
            "price": d_open,
            "title": f"Session Open: ${d_open:.2f}",
            "color": "#38bdf8",
            "lineStyle": "dotted",
            "axisLabel": True
        })

    # 4. HUD Telemetry Items for Latest Bar
    last_idx = len(df) - 1
    if last_idx >= 0:
        for cfg in lines_cfg:
            cid = cfg["id"]
            val = df[cid].iloc[last_idx] if cid in df.columns else None
            hud_items.append({
                "id": cid,
                "label": cfg["title"],
                "color": cfg["color"],
                "value": f"${val:.2f}" if pd.notnull(val) else "–"
            })
        
        # Also include non-overlay indicators like RSI or Volume Z-Score in HUD
        for sub_col in ["rsi_14", "rsi_7", "rsi_21", "volume_zscore", "adx_14", "hurst_proxy"]:
            if sub_col in df.columns:
                val = df[sub_col].iloc[last_idx]
                if pd.notnull(val):
                    hud_items.append({
                        "id": sub_col,
                        "label": sub_col.upper(),
                        "color": "#38bdf8" if "rsi" in sub_col else "#a855f7",
                        "value": f"{val:.2f}"
                    })

    return {
        "lines": lines_cfg,
        "series": series_data,
        "boxes": boxes,
        "levels": levels,
        "hud_items": hud_items
    }

#!/usr/bin/env python3
import argparse
import json
import os
import sys

import re
from typing import Dict, Any

TOOL_NAME = "[StrategyEmitter]"

def generate_freqtrade_code(thesis: str, class_name: str, rules: Dict[str, Any]) -> str:
    archetype = rules.get("archetype", "custom")
    timeframe = rules.get("timeframe", "15m")
    bias = rules.get("bias", "DUAL").upper()
    can_short = bias in ["DUAL", "SHORT"]
    
    stoploss_pct = float(rules.get("stoploss_pct", 0.02))
    takeprofit_pct = float(rules.get("takeprofit_pct", 0.04))
    max_bars_held = int(rules.get("max_bars_held", 12))
    
    entry_long = rules.get("entry_long", "close > ema_50 and ema_9 > ema_21")
    entry_short = rules.get("entry_short", "close < ema_50 and ema_9 < ema_21")
    exit_rule = rules.get("exit", None)

    rule_text = f"{entry_long} {entry_short} {str(exit_rule)}"

    # Dynamic ROI calculation
    half_bars = max(1, max_bars_held // 2)
    roi_table = {
        "0": round(takeprofit_pct, 4),
        str(half_bars): round(takeprofit_pct * 0.5, 4),
        str(max_bars_held): 0.0
    }

    use_trailing = archetype in ["trend_following", "momentum_breakout"]
    trailing_block = f"""    trailing_stop = {use_trailing}
    trailing_stop_positive = {round(takeprofit_pct * 0.25, 4)}
    trailing_stop_positive_offset = {round(takeprofit_pct * 0.40, 4)}""" if use_trailing else "    trailing_stop = False"

    # Indicators builder
    indicators = []
    
    # Range & Geometry
    if any(k in rule_text for k in ["wick", "body_ratio", "total_range", "buying_pressure", "selling_pressure"]):
        indicators.append("""        # Bar Geometry
        dataframe['total_range'] = (dataframe['high'] - dataframe['low']).replace(0, 1e-6)
        dataframe['body_ratio'] = (dataframe['close'] - dataframe['open']).abs() / dataframe['total_range']
        dataframe['upper_wick'] = (dataframe['high'] - np.maximum(dataframe['close'], dataframe['open'])) / dataframe['total_range']
        dataframe['lower_wick'] = (np.minimum(dataframe['close'], dataframe['open']) - dataframe['low']) / dataframe['total_range']""")

    # Volume Z-score
    if "volume_zscore" in rule_text:
        indicators.append("""        # Volume Z-Score
        vol_mean = dataframe['volume'].rolling(20).mean()
        vol_std = dataframe['volume'].rolling(20).std().replace(0, 1e-6)
        dataframe['volume_zscore'] = (dataframe['volume'] - vol_mean) / vol_std""")

    # Dynamic Multi-Scale EMAs
    ema_spans = sorted(list(set(int(x) for x in re.findall(r"ema_(\d+)", rule_text))))
    if ema_spans:
        ema_lines = [f"        dataframe['ema_{span}'] = dataframe['close'].ewm(span={span}).mean()" for span in ema_spans]
        indicators.append("        # Exponential Moving Averages\n" + "\n".join(ema_lines))

    # Dynamic Multi-Scale RSIs
    rsi_spans = sorted(list(set(int(x) for x in re.findall(r"rsi_(\d+)", rule_text))))
    if not rsi_spans and "rsi" in rule_text:
        rsi_spans = [14]
    if rsi_spans:
        rsi_blocks = [f"""        # RSI ({span})
        delta_{span} = dataframe['close'].diff()
        gain_{span} = delta_{span}.clip(lower=0)
        loss_{span} = -delta_{span}.clip(upper=0)
        avg_gain_{span} = gain_{span}.ewm(span={span}).mean()
        avg_loss_{span} = loss_{span}.ewm(span={span}).mean().replace(0, 1e-6)
        rs_{span} = avg_gain_{span} / avg_loss_{span}
        dataframe['rsi_{span}'] = 100.0 - (100.0 / (1.0 + rs_{span}))""" for span in rsi_spans]
        indicators.append("\n\n".join(rsi_blocks))

    # MACD
    if any(k in rule_text for k in ["macd_12_26", "macd_signal", "macd_hist"]):
        indicators.append("""        # MACD (12, 26, 9)
        ema_12 = dataframe['close'].ewm(span=12).mean()
        ema_26 = dataframe['close'].ewm(span=26).mean()
        dataframe['macd_12_26'] = ema_12 - ema_26
        dataframe['macd_signal'] = dataframe['macd_12_26'].ewm(span=9).mean()
        dataframe['macd_hist'] = dataframe['macd_12_26'] - dataframe['macd_signal']""")

    # ATR
    atr_spans = sorted(list(set(int(x) for x in re.findall(r"atr_(\d+)", rule_text))))
    if not atr_spans and any(k in rule_text for k in ["adx", "plus_di", "minus_di"]):
        atr_spans = [14]
    if atr_spans:
        atr_blocks = [f"""        # Average True Range ({span})
        prev_close = dataframe['close'].shift(1).fillna(dataframe['open'])
        tr = np.maximum(dataframe['high'] - dataframe['low'],
                        np.maximum((dataframe['high'] - prev_close).abs(), (dataframe['low'] - prev_close).abs()))
        dataframe['atr_{span}'] = tr.rolling({span}).mean().fillna(tr)""" for span in atr_spans]
        indicators.append("\n\n".join(atr_blocks))

    # ADX
    adx_spans = sorted(list(set(int(x) for x in re.findall(r"adx_(\d+)", rule_text))))
    if not adx_spans and any(k in rule_text for k in ["adx", "plus_di", "minus_di"]):
        adx_spans = [14]
    if adx_spans:
        adx_blocks = [f"""        # Directional Movement & ADX ({span})
        up_move = dataframe['high'].diff()
        down_move = -dataframe['low'].diff()
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
        atr_ref = dataframe.get('atr_{span}', dataframe.get('atr_14', dataframe['high'] - dataframe['low']))
        plus_di = 100.0 * pd.Series(plus_dm, index=dataframe.index).ewm(span={span}).mean() / atr_ref.replace(0, 1e-6)
        minus_di = 100.0 * pd.Series(minus_dm, index=dataframe.index).ewm(span={span}).mean() / atr_ref.replace(0, 1e-6)
        dataframe['plus_di'] = plus_di
        dataframe['minus_di'] = minus_di
        dx = 100.0 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, 1e-6)
        dataframe['adx_{span}'] = dx.ewm(span={span}).mean()""" for span in adx_spans]
        indicators.append("\n\n".join(adx_blocks))

    # Dynamic Donchian Channels
    donch_spans = sorted(list(set(int(x) for x in re.findall(r"donchian_(?:upper|lower|mid)_(\d+)", rule_text))))
    if donch_spans:
        donch_blocks = [f"""        # Donchian Channels ({span})
        dataframe['donchian_upper_{span}'] = dataframe['high'].rolling({span}).max()
        dataframe['donchian_lower_{span}'] = dataframe['low'].rolling({span}).min()
        dataframe['donchian_mid_{span}'] = (dataframe['donchian_upper_{span}'] + dataframe['donchian_lower_{span}']) / 2.0""" for span in donch_spans]
        indicators.append("\n\n".join(donch_blocks))

    # Bollinger Bands
    if any(k in rule_text for k in ["upper_band", "lower_band", "sma_20"]):
        indicators.append("""        # Bollinger Bands (20, 2.0)
        dataframe['sma_20'] = dataframe['close'].rolling(20).mean()
        std_20 = dataframe['close'].rolling(20).std()
        dataframe['upper_band'] = dataframe['sma_20'] + 2.0 * std_20
        dataframe['lower_band'] = dataframe['sma_20'] - 2.0 * std_20""")

    # Candlestick Patterns
    if any(k in rule_text for k in ["engulfing_bullish", "engulfing_bearish", "inside_bar", "pinbar_bullish", "pinbar_bearish"]):
        indicators.append("""        # Candlestick Formations
        prev_c = dataframe['close'].shift(1)
        prev_o = dataframe['open'].shift(1)
        prev_h = dataframe['high'].shift(1)
        prev_l = dataframe['low'].shift(1)
        dataframe['engulfing_bullish'] = ((dataframe['close'] > dataframe['open']) & (prev_c < prev_o) & (dataframe['close'] >= prev_o) & (dataframe['open'] <= prev_c)).astype(int)
        dataframe['engulfing_bearish'] = ((dataframe['close'] < dataframe['open']) & (prev_c > prev_o) & (dataframe['close'] <= prev_o) & (dataframe['open'] >= prev_c)).astype(int)
        dataframe['inside_bar'] = ((dataframe['high'] <= prev_h) & (dataframe['low'] >= prev_l)).astype(int)""")

    # SMC & Liquidity Sweeps
    if any(k in rule_text for k in ["sweep_low_rejection", "sweep_high_rejection", "fvg_bullish", "fvg_bearish"]):
        indicators.append("""        # SMC Liquidity Sweeps
        roll_high = dataframe['high'].shift(1).rolling(20).max()
        roll_low = dataframe['low'].shift(1).rolling(20).min()
        dataframe['sweep_high_rejection'] = ((dataframe['high'] > roll_high) & (dataframe['upper_wick'] >= 0.38)).astype(int)
        dataframe['sweep_low_rejection'] = ((dataframe['low'] < roll_low) & (dataframe['lower_wick'] >= 0.38)).astype(int)""")

    # Hurst Proxy
    if "hurst_proxy" in rule_text:
        indicators.append("""        # Rolling Hurst Proxy
        ret1 = np.log(dataframe['close'] / dataframe['close'].shift(1))
        ret5 = np.log(dataframe['close'] / dataframe['close'].shift(5))
        dataframe['hurst_proxy'] = (ret5.rolling(50).var() / (ret1.rolling(50).var().replace(0, 1e-6) * 5.0)).clip(0.1, 0.9)""")

    if not indicators:
        indicators.append("        # Baseline price\n        dataframe['close_ref'] = dataframe['close']")

    indicators_code = "\n\n".join(indicators)

    entry_long_clean = entry_long.replace("'", '"')
    entry_short_clean = entry_short.replace("'", '"')

    exit_long_code = ""
    exit_short_code = ""
    if exit_rule and "bars >=" not in exit_rule:
        exit_clean = exit_rule.replace("'", '"')
        exit_long_code = f"""        try:
            dataframe.loc[dataframe.eval('{exit_clean}'), 'exit_long'] = 1
        except Exception:
            pass"""
        exit_short_code = f"""        try:
            dataframe.loc[dataframe.eval('{exit_clean}'), 'exit_short'] = 1
        except Exception:
            pass"""
    else:
        exit_long_code = "        # Exits managed primarily via minimal_roi & stoploss\n        dataframe['exit_long'] = 0"
        exit_short_code = "        dataframe['exit_short'] = 0"

    # Dynamic Hyperparameter Spaces (Freqtrade Hyperopt & Cynic Plateau Audit)
    hyperparams = []
    if "ema" in rule_text:
        hyperparams.append("    # EMA Lookback Spaces")
        if "ema_7" in rule_text:
            hyperparams.append("    buy_ema_ultra_fast = IntParameter(5, 12, default=7, space='buy')")
        if "ema_9" in rule_text:
            hyperparams.append("    buy_ema_fast = IntParameter(5, 20, default=9, space='buy')")
        if "ema_13" in rule_text:
            hyperparams.append("    buy_ema_fast_13 = IntParameter(10, 20, default=13, space='buy')")
        if "ema_21" in rule_text:
            hyperparams.append("    buy_ema_mid = IntParameter(15, 35, default=21, space='buy')")
        if "ema_34" in rule_text:
            hyperparams.append("    buy_ema_mid_34 = IntParameter(25, 45, default=34, space='buy')")
        if "ema_50" in rule_text:
            hyperparams.append("    buy_ema_slow = IntParameter(40, 70, default=50, space='buy')")
        if "ema_200" in rule_text:
            hyperparams.append("    buy_ema_macro = IntParameter(150, 250, default=200, space='buy')")
    if "rsi" in rule_text:
        hyperparams.append("    # RSI Hyperparameter Space")
        hyperparams.append("    buy_rsi_threshold = IntParameter(20, 55, default=30, space='buy')")
        hyperparams.append("    sell_rsi_threshold = IntParameter(55, 85, default=70, space='sell')")
    if "adx" in rule_text:
        hyperparams.append("    # ADX Trend Filter Space")
        hyperparams.append("    buy_adx_min = IntParameter(15, 35, default=20, space='buy')")
    if "donchian" in rule_text:
        hyperparams.append("    # Donchian Breakout Horizon")
        hyperparams.append("    buy_donchian_period = IntParameter(10, 55, default=20, space='buy')")
    if "wick" in rule_text:
        hyperparams.append("    # Wick Rejection Selectivity")
        hyperparams.append("    buy_wick_min = DecimalParameter(0.25, 0.60, default=0.40, decimals=2, space='buy')")
    if "volume_zscore" in rule_text:
        hyperparams.append("    # Volume Effort vs Result")
        hyperparams.append("    buy_volume_zscore = DecimalParameter(0.5, 2.5, default=1.0, decimals=1, space='buy')")

    hyperparam_code = "\n".join(hyperparams) if hyperparams else "    # No explicit indicator hyperparameters"

    code = f'''# --- Freqtrade Strategy Generated by NujinAI ---
# Thesis: {thesis}
# Archetype: {archetype}
# Target Constraints: Net Sharpe >= 1.80, MaxDD <= 4.5%, DSR >= 0.95

import numpy as np
import pandas as pd
from pandas import DataFrame

try:
    from freqtrade.strategy import IStrategy, DecimalParameter, IntParameter
except ImportError:
    class IStrategy:
        pass
    class DecimalParameter:
        def __init__(self, *args, **kwargs): self.value = kwargs.get('default', 0.0)
    class IntParameter:
        def __init__(self, *args, **kwargs): self.value = kwargs.get('default', 0)

class {class_name}(IStrategy):
    """
    {thesis}
    Archetype: {archetype.upper()}
    Autonomous quantitative strategy generated by NujinSkills engine.
    """
    INTERFACE_VERSION = 3
    timeframe = '{timeframe}'
    can_short = {can_short}

    minimal_roi = {json.dumps(roi_table, indent=8)}

    stoploss = -{stoploss_pct}
{trailing_block}

{hyperparam_code}

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
{indicators_code}
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        try:
            dataframe.loc[dataframe.eval('{entry_long_clean}'), 'enter_long'] = 1
        except Exception as e:
            pass

        if self.can_short:
            try:
                dataframe.loc[dataframe.eval('{entry_short_clean}'), 'enter_short'] = 1
            except Exception as e:
                pass
        else:
            dataframe['enter_short'] = 0

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
{exit_long_code}
{exit_short_code}
        return dataframe
'''
    return code

def generate_jesse_code(thesis: str, class_name: str, rules: Dict[str, Any]) -> str:
    return f'''# --- Jesse Strategy Generated by NujinAI ---
# Thesis: {thesis}

from jesse.strategies import Strategy
import jesse.indicators as ta

class {class_name}(Strategy):
    """
    {thesis}
    """
    def should_long(self) -> bool:
        return False

    def should_short(self) -> bool:
        return False

    def should_cancel_entry(self) -> bool:
        return True

    def go_long(self):
        qty = 1.0
        self.buy = qty, self.price
        self.stop_loss = qty, self.price * 0.98
        self.take_profit = qty, self.price * 1.04
'''

def emit_strategy(thesis: str, rules_path_or_json: str, framework: str, out_path: str):
    print(f"{TOOL_NAME} Emitting {framework} strategy code for thesis: '{thesis}'...")
    
    clean_thesis = "".join([c for c in thesis.title() if c.isalnum()])
    class_name = f"{clean_thesis}Strategy" if clean_thesis else "NujinSkillsStrategy"

    rules = {}
    if rules_path_or_json:
        if os.path.exists(rules_path_or_json):
            with open(rules_path_or_json, "r", encoding="utf-8") as f:
                rules = json.load(f)
        else:
            try:
                rules = json.loads(rules_path_or_json)
            except Exception:
                rules = {}

    if framework.lower() == "jesse":
        code = generate_jesse_code(thesis, class_name, rules)
    else:
        code = generate_freqtrade_code(thesis, class_name, rules)

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w") as f:
        f.write(code.strip() + "\n")

    print(f"{TOOL_NAME} Strategy script successfully generated: {out_path}")

    try:
        import urllib.request
        req = urllib.request.Request("http://localhost:8000/api/strategies/sync", data=b"{}", headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=2) as resp:
            print(f"{TOOL_NAME} Telemetry server notified — real-time Cockpit telemetry updated instantly.")
    except Exception:
        try:
            sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
            from server.state_manager import strategy_registry
            strategy_registry.sync_with_filesystem()
            print(f"{TOOL_NAME} Local strategy registry synced on disk.")
        except Exception:
            pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Multi-Archetype Strategy Code Emitter CLI")
    parser.add_argument("--thesis", required=True, help="Economic thesis description")
    parser.add_argument("--rules", default="{}", help="Rules JSON string or path")
    parser.add_argument("--framework", choices=["freqtrade", "jesse"], default="freqtrade", help="Target strategy framework")
    parser.add_argument("--out", default="", help="Output python strategy file path (defaults to strategies/<StrategyName>.py)")
    args = parser.parse_args()

    clean_thesis = "".join([c for c in args.thesis.title() if c.isalnum()])
    class_name = f"{clean_thesis}Strategy" if clean_thesis else "NujinSkillsStrategy"
    out_path = args.out if args.out else f"strategies/{class_name}.py"
    if out_path.startswith("user_data/strategies/"):
        out_path = out_path.replace("user_data/strategies/", "strategies/")

    emit_strategy(args.thesis, args.rules, args.framework, out_path)


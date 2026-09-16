#!/usr/bin/env python3
import argparse
import datetime
import json
import os
import py_compile
import subprocess
import sys
import time
from typing import Dict, Any, List

TOOL_NAME = "[NujinMiner]"
NUJIN_DIR = ".nujin" if os.path.exists(".nujin") or not os.path.exists(".autoresearch") else ".autoresearch"
AUTORESEARCH_DIR = NUJIN_DIR

def get_python_exec() -> str:
    venv_py = os.path.abspath(".venv/bin/python")
    if os.path.exists(venv_py):
        return venv_py
    venv_py3 = os.path.abspath(".venv/bin/python3")
    if os.path.exists(venv_py3):
        return venv_py3
    return sys.executable

def ensure_gitignore():
    gitignore_path = ".gitignore"
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r", encoding="utf-8") as f:
            content = f.read()
        entries_to_add = []
        if ".nujin/" not in content and ".nujin" not in content:
            entries_to_add.append(".nujin/")
        if ".autoresearch/" not in content and ".autoresearch" not in content:
            entries_to_add.append(".autoresearch/")
        if entries_to_add:
            with open(gitignore_path, "a", encoding="utf-8") as f:
                f.write("\n# Nujin research state\n" + "\n".join(entries_to_add) + "\n")

def dispatch_telemetry(payload: Dict[str, Any]):
    dispatcher_script = os.path.join("tools", "ui_dispatcher.py")
    if os.path.exists(dispatcher_script):
        try:
            subprocess.run(
                [get_python_exec(), dispatcher_script, "--event", "UPSERT_WIDGET", "--payload", json.dumps(payload)],
                capture_output=True,
                text=True,
                timeout=5
            )
        except Exception:
            pass

ARCHETYPE_TEMPLATES = {
    "mean_reversion": {
        "archetype": "mean_reversion",
        "entry_long": "lower_wick > 0.40 and volume_zscore > 1.0",
        "entry_short": "upper_wick > 0.40 and volume_zscore > 1.0",
        "exit": "bars >= 8",
        "max_bars_held": 8,
        "stoploss_pct": 0.018,
        "takeprofit_pct": 0.035,
        "bias": "DUAL"
    },
    "trend_following": {
        "archetype": "trend_following",
        "entry_long": "close > ema_50 and ema_9 > ema_21 and adx_14 > 20 and rsi_14 > 50",
        "entry_short": "close < ema_50 and ema_9 < ema_21 and adx_14 > 20 and rsi_14 < 50",
        "exit": "close < ema_21",
        "max_bars_held": 24,
        "stoploss_pct": 0.020,
        "takeprofit_pct": 0.055,
        "bias": "DUAL"
    },
    "momentum_breakout": {
        "archetype": "momentum_breakout",
        "entry_long": "close >= donchian_upper_20 and volume_zscore > 1.2 and adx_14 > 22",
        "entry_short": "close <= donchian_lower_20 and volume_zscore > 1.2 and adx_14 > 22",
        "exit": "close < donchian_mid_20",
        "max_bars_held": 18,
        "stoploss_pct": 0.015,
        "takeprofit_pct": 0.045,
        "bias": "DUAL"
    },
    "price_action": {
        "archetype": "price_action",
        "entry_long": "engulfing_bullish == 1 and close > ema_50 and volume_zscore > 0.8",
        "entry_short": "engulfing_bearish == 1 and close < ema_50 and volume_zscore > 0.8",
        "exit": "bars >= 10",
        "max_bars_held": 10,
        "stoploss_pct": 0.015,
        "takeprofit_pct": 0.035,
        "bias": "DUAL"
    },
    "smc_liquidity": {
        "archetype": "smc_liquidity",
        "entry_long": "sweep_low_rejection == 1 and volume_zscore > 1.0",
        "entry_short": "sweep_high_rejection == 1 and volume_zscore > 1.0",
        "exit": "bars >= 8",
        "max_bars_held": 8,
        "stoploss_pct": 0.018,
        "takeprofit_pct": 0.035,
        "bias": "DUAL"
    }
}

def action_init(target: str, scope: str, context: str, archetype: str = "mean_reversion", initial_rules_input: str = ""):
    print(f"{TOOL_NAME} Initializing Nujin research environment in {AUTORESEARCH_DIR}/...")
    os.makedirs(AUTORESEARCH_DIR, exist_ok=True)
    ensure_gitignore()

    # Determine initial rules
    initial_rules = None
    if initial_rules_input:
        if os.path.exists(initial_rules_input):
            with open(initial_rules_input, "r", encoding="utf-8") as f:
                initial_rules = json.load(f)
        else:
            try:
                initial_rules = json.loads(initial_rules_input)
            except Exception:
                initial_rules = None

    if not initial_rules:
        initial_rules = ARCHETYPE_TEMPLATES.get(archetype, ARCHETYPE_TEMPLATES["mean_reversion"])

    arch_name = initial_rules.get("archetype", archetype)

    state = {
        "target": target or f"{arch_name.replace('_', ' ').title()} Discovery",
        "scope": scope or "BTC/USDT 15m / XAUUSD 1m",
        "context": context or "Net Sharpe >= 1.8, MaxDD <= 4.5%, DSR >= 0.95",
        "archetype": arch_name,
        "run_number": 0,
        "best_score": 0,
        "best_validation_score": 0,
        "max_score": 6,
        "criteria_count": 6,
        "confidence_margin": 1,
        "plateau_counter": 0,
        "active_mutation_operator": "baseline",
        "validation_slices": [
            {"name": "slice_1_trending", "start_pct": 0.0, "end_pct": 0.35},
            {"name": "slice_2_vol_cascade", "start_pct": 0.35, "end_pct": 0.70},
            {"name": "slice_3_ranging_chop", "start_pct": 0.70, "end_pct": 1.00}
        ],
        "sampled_slices": ["slice_1_trending", "slice_2_vol_cascade", "slice_3_ranging_chop"],
        "slice_failures": {}
    }

    state_path = os.path.join(AUTORESEARCH_DIR, "state.json")
    rules_path = os.path.join(AUTORESEARCH_DIR, "rules.json")
    best_rules_path = os.path.join(AUTORESEARCH_DIR, "best_rules.json")
    results_path = os.path.join(AUTORESEARCH_DIR, "results.jsonl")

    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

    with open(rules_path, "w", encoding="utf-8") as f:
        json.dump(initial_rules, f, indent=2)

    with open(best_rules_path, "w", encoding="utf-8") as f:
        json.dump(initial_rules, f, indent=2)

    if not os.path.exists(results_path):
        with open(results_path, "w", encoding="utf-8") as f:
            pass

    print(f"{TOOL_NAME} State initialized successfully.")
    print(f"{TOOL_NAME} Target: {state['target']} (Archetype: {arch_name})")
    print(f"{TOOL_NAME} Validation Slices: {len(state['validation_slices'])} regime partitions")
    print(f"{TOOL_NAME} Files created: {state_path}, {rules_path}, {best_rules_path}, {results_path}")

def mutate_rules(rules: Dict[str, Any], operator: str, failures: List[str]) -> Dict[str, Any]:
    mutated = dict(rules)
    arch = mutated.get("archetype", "mean_reversion")

    if operator == "add_constraint":
        if arch == "trend_following":
            if "adx_14" not in mutated.get("entry_long", ""):
                mutated["entry_long"] = f"{mutated['entry_long']} and adx_14 > 22"
                mutated["entry_short"] = f"{mutated['entry_short']} and adx_14 > 22"
            elif "volume_zscore" not in mutated.get("entry_long", ""):
                mutated["entry_long"] = f"{mutated['entry_long']} and volume_zscore > 0.5"
                mutated["entry_short"] = f"{mutated['entry_short']} and volume_zscore > 0.5"
        elif arch == "momentum_breakout":
            if "parkinson_vol" not in mutated.get("entry_long", ""):
                mutated["entry_long"] = f"{mutated['entry_long']} and parkinson_vol > 0.01"
                mutated["entry_short"] = f"{mutated['entry_short']} and parkinson_vol > 0.01"
        elif arch == "price_action":
            if "close > ema_50" not in mutated.get("entry_long", ""):
                mutated["entry_long"] = f"{mutated['entry_long']} and close > ema_50"
                mutated["entry_short"] = f"{mutated['entry_short']} and close < ema_50"
        else: # mean_reversion or smc_liquidity
            if "hurst_proxy" not in mutated.get("entry_long", ""):
                mutated["entry_long"] = f"{mutated['entry_long']} and hurst_proxy < 0.48"
                mutated["entry_short"] = f"{mutated['entry_short']} and hurst_proxy < 0.48"
            elif "parkinson_vol" not in mutated.get("entry_long", ""):
                mutated["entry_long"] = f"{mutated['entry_long']} and parkinson_vol < 0.02"
                mutated["entry_short"] = f"{mutated['entry_short']} and parkinson_vol < 0.02"

    elif operator == "add_negative_example":
        if arch == "trend_following":
            if "rsi_14 < 75" not in mutated.get("entry_long", ""):
                mutated["entry_long"] = f"{mutated['entry_long']} and rsi_14 < 75"
                mutated["entry_short"] = f"{mutated['entry_short']} and rsi_14 > 25"
        elif arch == "momentum_breakout":
            if "body_ratio" not in mutated.get("entry_long", ""):
                mutated["entry_long"] = f"{mutated['entry_long']} and body_ratio > 0.45"
                mutated["entry_short"] = f"{mutated['entry_short']} and body_ratio > 0.45"
        else:
            if "body_ratio" not in mutated.get("entry_long", ""):
                mutated["entry_long"] = f"{mutated['entry_long']} and body_ratio < 0.65"
                mutated["entry_short"] = f"{mutated['entry_short']} and body_ratio < 0.65"

    elif operator == "restructure_exit":
        curr_bars = int(mutated.get("max_bars_held", 12))
        if arch == "trend_following":
            new_bars = 36 if curr_bars == 24 else (16 if curr_bars == 36 else 24)
            mutated["max_bars_held"] = new_bars
            mutated["takeprofit_pct"] = round(mutated.get("takeprofit_pct", 0.055) * 1.15, 4)
        else:
            new_bars = 12 if curr_bars == 8 else (6 if curr_bars == 12 else 8)
            mutated["max_bars_held"] = new_bars
            if "bars >=" in mutated.get("exit", ""):
                mutated["exit"] = f"bars >= {new_bars}"
            mutated["takeprofit_pct"] = round(mutated.get("takeprofit_pct", 0.035) * 1.15, 4)

    elif operator == "tighten_thresholds":
        if "adx_14 > 20" in mutated.get("entry_long", ""):
            mutated["entry_long"] = mutated["entry_long"].replace("adx_14 > 20", "adx_14 > 25")
            mutated["entry_short"] = mutated["entry_short"].replace("adx_14 > 20", "adx_14 > 25")
        if "volume_zscore > 1.0" in mutated.get("entry_long", ""):
            mutated["entry_long"] = mutated["entry_long"].replace("volume_zscore > 1.0", "volume_zscore > 1.3")
            mutated["entry_short"] = mutated["entry_short"].replace("volume_zscore > 1.0", "volume_zscore > 1.3")
        if "lower_wick > 0.40" in mutated.get("entry_long", ""):
            mutated["entry_long"] = mutated["entry_long"].replace("lower_wick > 0.40", "lower_wick > 0.45")
            mutated["entry_short"] = mutated["entry_short"].replace("upper_wick > 0.40", "upper_wick > 0.45")
        mutated["stoploss_pct"] = round(mutated.get("stoploss_pct", 0.018) * 0.90, 4)

    elif operator == "remove_bloat":
        base_template = ARCHETYPE_TEMPLATES.get(arch, ARCHETYPE_TEMPLATES["mean_reversion"])
        mutated["entry_long"] = base_template["entry_long"]
        mutated["entry_short"] = base_template["entry_short"]
        mutated["max_bars_held"] = base_template["max_bars_held"]
        mutated["exit"] = base_template["exit"]

    elif operator == "directional_bias_flip":
        curr_bias = mutated.get("bias", "DUAL")
        new_bias = "LONG" if curr_bias == "DUAL" else ("SHORT" if curr_bias == "LONG" else "DUAL")
        mutated["bias"] = new_bias

    elif operator == "plateau_break":
        # Radical pivot to an orthogonal archetype
        next_arch = "trend_following" if arch == "mean_reversion" else ("momentum_breakout" if arch == "trend_following" else "mean_reversion")
        mutated = dict(ARCHETYPE_TEMPLATES[next_arch])
        print(f"{TOOL_NAME} Plateau Break: Switching hypothesis archetype from '{arch}' to '{next_arch}'")
    return mutated

def execute_screener_eval(rules: Dict[str, Any], features_path: str) -> Dict[str, Any]:
    output_returns = os.path.join(AUTORESEARCH_DIR, "eval_returns.json")
    cmd = [
        get_python_exec(),
        "tools/vectorized_screener.py",
        "--data", features_path,
        "--rules", json.dumps(rules),
        "--fee-bps", "5.0",
        "--slippage-bps", "2.0",
        "--output", output_returns
    ]
    
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        return {
            "status": "REJECT",
            "sharpe": 0.0,
            "trades": 0,
            "win_rate": 0.0,
            "max_drawdown": 1.0,
            "profit_factor": 0.0,
            "expectancy_bps": 0.0,
            "dsr": 0.0,
            "param_stability": "FAIL"
        }

    try:
        lines = [line.strip() for line in proc.stdout.split("\n") if line.strip().startswith("{") or "status" in line]
        # find JSON block in stdout
        start_idx = proc.stdout.find("{")
        end_idx = proc.stdout.rfind("}")
        if start_idx != -1 and end_idx != -1:
            screener_res = json.loads(proc.stdout[start_idx:end_idx+1])
        else:
            screener_res = {}
    except Exception:
        screener_res = {}

    # Run Cynic DSR Audit
    cmd_cynic = [
        get_python_exec(),
        "tools/validation_cynic.py",
        "--returns", output_returns,
        "--trials", "60"
    ]
    cynic_proc = subprocess.run(cmd_cynic, capture_output=True, text=True)
    cynic_res = {}
    if cynic_proc.returncode == 0:
        try:
            start_idx = cynic_proc.stdout.find("{")
            end_idx = cynic_proc.stdout.rfind("}")
            if start_idx != -1 and end_idx != -1:
                cynic_res = json.loads(cynic_proc.stdout[start_idx:end_idx+1])
        except Exception:
            cynic_res = {}

    dsr_val = cynic_res.get("gate_1_dsr", {}).get("dsr", 0.0)
    param_status = cynic_res.get("gate_2_parameter_stability", {}).get("status", "FAIL")

    return {
        "status": screener_res.get("status", "REJECT"),
        "sharpe": screener_res.get("sharpe", 0.0),
        "trades": screener_res.get("trades", 0),
        "win_rate": screener_res.get("win_rate", 0.0),
        "max_drawdown": screener_res.get("max_drawdown", 0.0),
        "profit_factor": screener_res.get("profit_factor", 0.0),
        "expectancy_bps": screener_res.get("expectancy_bps", 0.0),
        "dsr": dsr_val,
        "param_stability": param_status
    }

def action_step(features_path: str = "data/features.csv", rules_override: str = None):
    state_path = os.path.join(AUTORESEARCH_DIR, "state.json")
    rules_path = os.path.join(AUTORESEARCH_DIR, "rules.json")
    best_rules_path = os.path.join(AUTORESEARCH_DIR, "best_rules.json")
    results_path = os.path.join(AUTORESEARCH_DIR, "results.jsonl")

    if not os.path.exists(state_path) or not os.path.exists(rules_path):
        print(f"{TOOL_NAME} No initialized state found. Running 'init' first...")
        action_init(target="", scope="", context="")

    with open(state_path, "r", encoding="utf-8") as f:
        state = json.load(f)
    
    if rules_override:
        if os.path.exists(rules_override):
            with open(rules_override, "r", encoding="utf-8") as f:
                current_rules = json.load(f)
        else:
            try:
                current_rules = json.loads(rules_override)
            except Exception:
                with open(rules_path, "r", encoding="utf-8") as f:
                    current_rules = json.load(f)
        # Write active candidate
        with open(rules_path, "w", encoding="utf-8") as f:
            json.dump(current_rules, f, indent=2)
    else:
        with open(rules_path, "r", encoding="utf-8") as f:
            current_rules = json.load(f)

    with open(best_rules_path, "r", encoding="utf-8") as f:
        best_rules = json.load(f)

    run_num = state.get("run_number", 0) + 1
    print(f"\n{TOOL_NAME} ========================================================")
    print(f"{TOOL_NAME} STARTING AUTORESEARCH CYCLE #{run_num} (Archetype: {state.get('archetype', 'mean_reversion')})")
    print(f"{TOOL_NAME} ========================================================")

    # Ensure features file exists
    if not os.path.exists(features_path):
        candles_path = "data/candles_15m.csv"
        if os.path.exists(candles_path):
            print(f"{TOOL_NAME} Generating {features_path} from {candles_path}...")
            subprocess.run([get_python_exec(), "tools/feature_miner.py", "--input", candles_path, "--output", features_path], check=True)
        else:
            print(f"{TOOL_NAME} ERROR: Neither {features_path} nor {candles_path} exist.")
            sys.exit(1)

    # 1. Execute Evaluation
    metrics = execute_screener_eval(current_rules, features_path)

    # 2. Strict Binary Criteria Evaluation
    criteria = {
        "sharpe_gte_1_8": 1 if metrics["sharpe"] >= 1.80 else 0,
        "drawdown_lte_4_5": 1 if metrics["max_drawdown"] <= 0.045 else 0,
        "sample_trades_gte_60": 1 if (metrics["trades"] >= 60 and metrics["win_rate"] >= 0.50) else 0,
        "fee_drag_protected": 1 if metrics["expectancy_bps"] >= 14.0 else 0,
        "dsr_gte_0_95": 1 if metrics["dsr"] >= 0.95 else 0,
        "param_plateau": 1 if metrics["param_stability"] == "PASS" else 0
    }

    score = sum(criteria.values())
    validation_score = score  # Evaluated on full multi-regime features
    max_score = state.get("max_score", 6)
    failures = [crit for crit, val in criteria.items() if val == 0]

    best_v_score = state.get("best_validation_score", -1)
    confidence_margin = state.get("confidence_margin", 1)
    plateau_counter = state.get("plateau_counter", 0)

    # 3. Keep / Discard Decision
    is_keep = (validation_score > best_v_score) and ((validation_score - best_v_score) >= confidence_margin or best_v_score <= 0)

    if is_keep:
        status = "KEEP"
        state["best_score"] = score
        state["best_validation_score"] = validation_score
        state["plateau_counter"] = 0
        best_rules = dict(current_rules)
        with open(best_rules_path, "w", encoding="utf-8") as f:
            json.dump(best_rules, f, indent=2)
        print(f"{TOOL_NAME} Result: [KEEP] New Best Validation Score: {validation_score}/{max_score}!")
    else:
        status = "DISCARD"
        state["plateau_counter"] = plateau_counter + 1
        current_rules = dict(best_rules) # revert to best
        print(f"{TOOL_NAME} Result: [DISCARD] Validation Score {validation_score}/{max_score} did not beat best {best_v_score}/{max_score}.")

    # 4. Mutation Operator Selection for Next Run
    operators = [
        "add_constraint",
        "add_negative_example",
        "restructure_exit",
        "tighten_thresholds",
        "remove_bloat",
        "directional_bias_flip"
    ]
    
    if state["plateau_counter"] >= 5:
        chosen_op = "plateau_break"
        print(f"{TOOL_NAME} Plateau breaker triggered (5 consecutive failures). Synthesizing radical orthogonal rules...")
    else:
        chosen_op = operators[(run_num - 1) % len(operators)]

    next_rules = mutate_rules(best_rules, chosen_op, failures)
    with open(rules_path, "w", encoding="utf-8") as f:
        json.dump(next_rules, f, indent=2)

    # 5. Log Entry to results.jsonl
    result_entry = {
        "run": run_num,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "score": score,
        "validation_score": validation_score,
        "max": max_score,
        "metrics": metrics,
        "criteria": criteria,
        "status": status,
        "mutation_operator": chosen_op,
        "failures": failures,
        "rules": current_rules
    }

    with open(results_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(result_entry) + "\n")

    state["run_number"] = run_num
    state["active_mutation_operator"] = chosen_op
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

    # 6. Dispatch Real-Time Telemetry to Frontend Dashboard
    dispatch_telemetry({
        "id": "autoresearch_loop_telemetry",
        "component": "MetricCard",
        "title": "Autoresearch Alpha Swarm",
        "phase": f"CYCLE #{run_num}",
        "props": {
            "value": f"{status} (Score {validation_score}/{max_score})",
            "target": f"Best {state['best_validation_score']}/{max_score}",
            "status": "PASS" if is_keep else "WARN",
            "subtitle": f"Op: {chosen_op} | Sharpe: {metrics['sharpe']} | DSR: {metrics['dsr']}"
        }
    })

    print(f"{TOOL_NAME} Cycle #{run_num} Completed:")
    print(f"  Status:             {status}")
    print(f"  Score:              {validation_score}/{max_score}")
    print(f"  Sharpe / Win Rate:  {metrics['sharpe']} / {metrics['win_rate']*100:.1f}%")
    print(f"  DSR / MaxDD:        {metrics['dsr']} / {metrics['max_drawdown']*100:.2f}%")
    print(f"  Next Mutation:      {chosen_op}")
    print(f"{TOOL_NAME} Logged to {results_path}")

def action_run(cycles: int, features_path: str = "data/features.csv"):
    print(f"{TOOL_NAME} Initiating continuous autonomous research loop ({cycles} cycles)...")
    for i in range(cycles):
        action_step(features_path)
        time.sleep(0.5)
    print(f"\n{TOOL_NAME} Finished batch of {cycles} cycles.")
    action_status()

def action_status():
    state_path = os.path.join(AUTORESEARCH_DIR, "state.json")
    results_path = os.path.join(AUTORESEARCH_DIR, "results.jsonl")
    best_rules_path = os.path.join(AUTORESEARCH_DIR, "best_rules.json")

    if not os.path.exists(state_path):
        print(f"{TOOL_NAME} No active autoresearch environment found in {AUTORESEARCH_DIR}/.")
        return

    with open(state_path, "r", encoding="utf-8") as f:
        state = json.load(f)

    runs = []
    if os.path.exists(results_path):
        with open(results_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        runs.append(json.loads(line.strip()))
                    except Exception:
                        pass

    best_rules = {}
    if os.path.exists(best_rules_path):
        with open(best_rules_path, "r", encoding="utf-8") as f:
            best_rules = json.load(f)

    print("\n" + "=" * 65)
    print(f"{TOOL_NAME} AUTORESEARCH STATUS & TELEMETRY SUMMARY")
    print("=" * 65)
    print(f"  Target:                  {state.get('target')}")
    print(f"  Total Runs Executed:     {state.get('run_number', 0)}")
    print(f"  Best Validation Score:   {state.get('best_validation_score', 0)} / {state.get('max_score', 6)}")
    print(f"  Plateau Counter:         {state.get('plateau_counter', 0)} / 5")
    print(f"  Active Mutation Operator:{state.get('active_mutation_operator')}")
    print("-" * 65)
    print("  CURRENT BEST RULES:")
    print(f"    LONG:       {best_rules.get('entry_long')}")
    print(f"    SHORT:      {best_rules.get('entry_short')}")
    print(f"    Holding:    {best_rules.get('max_bars_held')} bars")
    print(f"    SL / TP:    {best_rules.get('stoploss_pct')} / {best_rules.get('takeprofit_pct')}")
    print("-" * 65)
    if runs:
        print("  RECENT CYCLE HISTORY (Last 5):")
        for r in runs[-5:]:
            stat = r.get("status")
            sc = r.get("validation_score")
            mx = r.get("max")
            op = r.get("mutation_operator")
            sh = r.get("metrics", {}).get("sharpe", 0.0)
            dsr = r.get("metrics", {}).get("dsr", 0.0)
            print(f"    Run #{r.get('run'):<3} [{stat:<7}] Score: {sc}/{mx} | Sharpe: {sh:<5} | DSR: {dsr:<5} | Op: {op}")
    print("=" * 65 + "\n")

def action_improve_tool(tool_name: str):
    print(f"{TOOL_NAME} Running Meta-Autoresearch self-improvement audit on tool: {tool_name}...")
    tools_dir = "tools"
    target_path = os.path.join(tools_dir, tool_name) if not tool_name.startswith("tools/") else tool_name
    
    if not os.path.exists(target_path):
        print(f"{TOOL_NAME} ERROR: Tool file not found at {target_path}")
        sys.exit(1)

    findings = []
    
    # Check 1: Python syntax compilation
    try:
        py_compile.compile(target_path, doraise=True)
        findings.append("Syntax compilation: PASS")
    except Exception as e:
        findings.append(f"Syntax compilation: FAIL ({e})")

    # Check 2: Shebang and Tool Prefix standard
    with open(target_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    has_shebang = len(lines) > 0 and lines[0].startswith("#!/usr/bin/env python3")
    has_tool_name = any("TOOL_NAME =" in l or "TOOL_NAME=" in l for l in lines)
    has_flat_argparse = any("choices=" in l for l in lines)

    findings.append(f"Shebang '#!/usr/bin/env python3': {'PASS' if has_shebang else 'WARN'}")
    findings.append(f"Standard TOOL_NAME constant: {'PASS' if has_tool_name else 'WARN'}")
    findings.append(f"Flat action argparse pattern: {'PASS' if has_flat_argparse else 'WARN'}")

    # Check 3: Benchmarking execution overhead
    t0 = time.time()
    try:
        proc = subprocess.run([get_python_exec(), target_path, "--help"], capture_output=True, text=True, timeout=5)
        duration_ms = (time.time() - t0) * 1000
        findings.append(f"CLI Help Invocation latency: {duration_ms:.1f}ms (PASS)")
    except Exception as e:
        findings.append(f"CLI Help Invocation: FAIL ({e})")

    print("\n" + "=" * 60)
    print(f"{TOOL_NAME} META-AUDIT REPORT: {target_path}")
    print("=" * 60)
    for f_item in findings:
        print(f"  • {f_item}")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Autonomous Quant Research Engine & Tool Evolver")
    parser.add_argument("action", choices=["init", "step", "run", "status", "improve-tool"], help="Autoresearch action")
    parser.add_argument("--target", default="", help="Optimization target description")
    parser.add_argument("--scope", default="", help="Target scope (symbol/timeframe)")
    parser.add_argument("--context", default="", help="Target constraints/context")
    parser.add_argument("--archetype", default="mean_reversion", choices=["mean_reversion", "trend_following", "momentum_breakout", "price_action", "smc_liquidity", "custom"], help="Strategy archetype template")
    parser.add_argument("--initial-rules", default="", help="JSON string or file path containing initial candidate rules")
    parser.add_argument("--rules-file", default="", help="Candidate rules JSON file or string to evaluate in this step")
    parser.add_argument("--features", default="data/features.csv", help="Feature data CSV path")
    parser.add_argument("--cycles", type=int, default=5, help="Number of continuous cycles for 'run'")
    parser.add_argument("--tool", default="feature_miner.py", help="Tool filename for 'improve-tool'")
    args = parser.parse_args()

    if args.action == "init":
        action_init(args.target, args.scope, args.context, archetype=args.archetype, initial_rules_input=args.initial_rules)
    elif args.action == "step":
        action_step(args.features, rules_override=args.rules_file)
    elif args.action == "run":
        action_run(args.cycles, args.features)
    elif args.action == "status":
        action_status()
    elif args.action == "improve-tool":
        action_improve_tool(args.tool)

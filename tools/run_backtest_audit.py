#!/usr/bin/env python3
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from server.backtest_engine import run_real_backtest

def audit(strategy: str, save_state: bool, output_path: str):
    print(f"[BacktestAudit] Running quantitative audit for strategy: {strategy}")
    print(f"[BacktestAudit] save_state={save_state} | output={output_path}")

    try:
        results = run_real_backtest(strategy, save_as_active=save_state)
    except Exception as e:
        print(f"[BacktestAudit] ERROR — backtest failed: {e}")
        sys.exit(1)

    summary = results.get("summary", {})
    gates   = results.get("falsification_gates", {})
    regimes = results.get("regime_breakdown", {})
    trades  = results.get("trades_detail", [])

    print("\n" + "=" * 70)
    print(f"[BacktestAudit] STRATEGY AUDIT REPORT: {results.get('strategy')}")
    print("=" * 70)
    print(f"  Target Profile:        {results.get('thesis_props', {}).get('target_profile')}")
    print(f"  Net Sharpe Ratio:      {summary.get('sharpe')} (>= 1.8 required)")
    print(f"  Win Rate:              {summary.get('win_rate', 0) * 100:.1f}%")
    print(f"  Profit Factor:         {summary.get('profit_factor')}")
    print(f"  Max Drawdown (IS):     {summary.get('max_drawdown', 0) * 100:.2f}% (<= 4.5%)")
    print(f"  Monte Carlo MDD99:     {summary.get('mdd_99', 0) * 100:.2f}% (max 4.5%)")
    print(f"  Deflated Sharpe (DSR): {summary.get('dsr')} (>= 0.95) -> {gates.get('gate_1_dsr', {}).get('status')}")
    print(f"  Expectancy:            {summary.get('expectancy_bps')} bps")
    print(f"  Total Trades:          {len(trades)}")
    print("-" * 70)
    print("  5-GATE CYNIC AUDIT MATRIX:")
    print(f"    [Gate 1] DSR:                 {gates.get('gate_1_dsr', {}).get('status')} (Score: {summary.get('dsr')})")
    print(f"    [Gate 2] Param Stability:     {gates.get('gate_2_parameter_stability', {}).get('status')} ({gates.get('gate_2_parameter_stability', {}).get('plateau_status')})")
    print(f"    [Gate 3] Monte Carlo MDD99:   {gates.get('gate_3_monte_carlo', {}).get('status')} ({summary.get('mdd_99', 0) * 100:.2f}%)")
    print(f"    [Gate 4] OOS Walk-Forward:    {gates.get('gate_4_oos_walkforward', {}).get('status')} (Retention: {gates.get('gate_4_oos_walkforward', {}).get('retention_pct')}%)")
    print(f"    [Gate 5] Regime Survival:     {gates.get('gate_5_regime_survival', {}).get('status')} (Score: {gates.get('gate_5_regime_survival', {}).get('score')}/100)")
    print("-" * 70)
    print("  MARKET REGIME SURVIVAL:")
    for reg, data in regimes.items():
        label = reg.replace("_", " ").title()
        print(f"    {label:<16}: {data.get('trade_count')} trades | WR: {data.get('win_rate', 0) * 100:.1f}% | PF: {data.get('profit_factor')} | PnL: {data.get('net_pnl_pct', 0):+.2f}%")
    print("=" * 70 + "\n")

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"[BacktestAudit] Audit report saved to {output_path}")
    if save_state:
        print(f"[BacktestAudit] Strategy state written to data/state.json via StateManager")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EdgeMiner AI Strategy Backtest & Cynic Audit")
    parser.add_argument("--strategy",    default="PropFirmVsaWickRejectionStrategy.py", help="Strategy filename in strategies/")
    parser.add_argument("--save-state",  action="store_true", default=False,            help="Deploy as active strategy (writes data/state.json)")
    parser.add_argument("--json-output", default="data/audit_report.json",              help="Output JSON report path")
    args = parser.parse_args()

    audit(args.strategy, args.save_state, args.json_output)

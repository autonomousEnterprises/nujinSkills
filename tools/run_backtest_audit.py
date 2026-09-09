#!/usr/bin/env python3
"""
tools/run_backtest_audit.py
AI-First CLI tool for quantitative strategy evaluation, 5-gate Cynic Audit,
equity curve generation, and multi-regime survival testing.
"""

import sys
import os
import json
import argparse
import logging

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from server.backtest_engine import run_real_backtest

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("RunBacktestAudit")

def main():
    parser = argparse.ArgumentParser(description="AI-First EdgeMiner Strategy Backtest & Cynic Audit Suite")
    parser.add_argument("--strategy", type=str, default="PropFirmVsaWickRejectionStrategy.py",
                        help="Name of strategy file in strategies/ (e.g. PropFirmVsaWickRejectionStrategy.py)")
    parser.add_argument("--save-state", action="store_true", default=False,
                        help="Save audited strategy state as active system deployment in data/state.json")
    parser.add_argument("--json-output", type=str, default="data/audit_report.json",
                        help="Path to output JSON audit report")

    args = parser.parse_args()

    logger.info(f"🚀 AI Quantitative Strategy Audit Initiated for: {args.strategy}")
    
    try:
        results = run_real_backtest(args.strategy, save_as_active=args.save_state)
    except Exception as e:
        logger.error(f"❌ Backtest audit failed with error: {e}")
        sys.exit(1)

    summary = results.get("summary", {})
    gates = results.get("falsification_gates", {})
    regimes = results.get("regime_breakdown", {})
    equity_curve = results.get("equity_curve", [])
    trades_detail = results.get("trades_detail", [])

    # Print Terminal Summary for AI agent inspectability
    print("\n" + "=" * 70)
    print(f"📊 EDGEMINER AI STRATEGY AUDIT REPORT: {results.get('strategy')}")
    print("=" * 70)
    print(f" Target Profile:        {results.get('thesis_props', {}).get('target_profile')}")
    print(f" Net Sharpe Ratio:      {summary.get('sharpe')} (Threshold: >= 1.8)")
    print(f" Win Rate:              {summary.get('win_rate', 0) * 100:.1f}%")
    print(f" Profit Factor:         {summary.get('profit_factor')}")
    print(f" Max Drawdown (IS):     {summary.get('max_drawdown', 0) * 100:.2f}% (Cap: <= 4.5%)")
    print(f" Monte Carlo MDD99:     {summary.get('mdd_99', 0) * 100:.2f}% (Max Allowed: 4.5%)")
    print(f" Deflated Sharpe (DSR): {summary.get('dsr')} (Gate: >= 0.95) -> STATUS: {gates.get('gate_1_dsr', {}).get('status')}")
    print(f" Expectancy:            {summary.get('expectancy_bps')} bps")
    print(f" Total Trades:          {len(trades_detail)}")
    print("-" * 70)
    print(" 🛡️ 5-GATE CYNIC AUDIT MATRIX:")
    print(f"   [Gate 1] DSR:                    {gates.get('gate_1_dsr', {}).get('status')} (Score: {summary.get('dsr')})")
    print(f"   [Gate 2] Parameter Stability:    {gates.get('gate_2_parameter_stability', {}).get('status')} ({gates.get('gate_2_parameter_stability', {}).get('plateau_status')})")
    print(f"   [Gate 3] Monte Carlo MDD99:      {gates.get('gate_3_monte_carlo', {}).get('status')} ({summary.get('mdd_99', 0) * 100:.2f}%)")
    print(f"   [Gate 4] OOS Walk-Forward:       {gates.get('gate_4_oos_walkforward', {}).get('status')} (Retention: {gates.get('gate_4_oos_walkforward', {}).get('retention_pct')}%)")
    print(f"   [Gate 5] Multi-Regime Survival:  {gates.get('gate_5_regime_survival', {}).get('status')} (Score: {gates.get('gate_5_regime_survival', {}).get('score')}/100)")
    print("-" * 70)
    print(" 📈 MARKET REGIME SURVIVAL BREAKDOWN:")
    for reg, data in regimes.items():
        name_fmt = reg.replace('_', ' ').title()
        print(f"   • {name_fmt:<16}: {data.get('trade_count')} trades | Win Rate: {data.get('win_rate') * 100:.1f}% | PF: {data.get('profit_factor')} | Net PnL: {data.get('net_pnl_pct'):+.2f}%")
    print("=" * 70 + "\n")

    # Write report JSON to output path
    out_dir = os.path.dirname(args.json_output)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    with open(args.json_output, "w") as f:
        json.dump(results, f, indent=2)

    logger.info(f"✅ Audit report saved to {args.json_output}")
    if args.save_state:
        logger.info(f"✅ Saved audited strategy state to data/state.json")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import argparse
import json
import os
import sys
import urllib.request

TOOL_NAME = "[StrategyManager]"

# Add project root to sys.path for direct module access if server is offline
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

def _fetch_json(url: str, method: str = "GET", data: dict = None, timeout: int = 5):
    try:
        req_data = json.dumps(data).encode("utf-8") if data is not None else None
        headers = {"Content-Type": "application/json"} if req_data is not None else {}
        req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None

def list_strategies(endpoint: str):
    res = _fetch_json(f"{endpoint}/api/strategies/manage")
    if res and "strategies" in res:
        strats = res["strategies"]
    else:
        # Offline fallback
        from server.state_manager import strategy_registry
        strats = strategy_registry.get_all(sync=True)

    print(f"{TOOL_NAME} STRATEGY REGISTRY ({len(strats)} Total Strategies):")
    print("-" * 88)
    header = f"{'Rank':<5} {'Strategy Name':<32} {'Status':<15} {'Tier':<14} {'Sharpe':<8} {'DSR':<8} {'Win%':<8} {'MaxDD'}"
    print(header)
    print("-" * 88)
    for s in strats:
        bt = s.get("latest_backtest", {})
        rank_str = f"#{s.get('rank', '-')}"
        name = s.get("name", "")[:30]
        status = s.get("status", "")
        tier = s.get("tier", "").split(" ")[0]
        sharpe = f"{bt.get('sharpe', 0.0):.2f}"
        dsr = f"{bt.get('dsr', 0.0):.2f}"
        win = f"{bt.get('win_rate', 0.0) * 100:.1f}%"
        dd = f"{bt.get('max_drawdown', 0.0) * 100:.2f}%"
        print(f"{rank_str:<5} {name:<32} {status:<15} {tier:<14} {sharpe:<8} {dsr:<8} {win:<8} {dd}")
    print("-" * 88)

def update_status(strategy: str, new_status: str, endpoint: str, exclusive: bool = False):
    print(f"{TOOL_NAME} Updating status for '{strategy}' -> {new_status} (exclusive={exclusive})...")
    res = _fetch_json(
        f"{endpoint}/api/strategies/manage/status",
        method="POST",
        data={"strategy": strategy, "status": new_status, "exclusive": exclusive}
    )
    if res and res.get("status") == "SUCCESS":
        print(f"{TOOL_NAME} SUCCESS: Updated {strategy} to {new_status}")
        updated = res.get("strategy", {})
        print(json.dumps(updated, indent=2))
    else:
        # Offline fallback
        from server.state_manager import strategy_registry
        try:
            updated = strategy_registry.update_status(strategy, new_status, exclusive=exclusive)
            print(f"{TOOL_NAME} SUCCESS (Local): Updated {strategy} to {new_status}")
            print(json.dumps(updated, indent=2))
        except Exception as e:
            print(f"{TOOL_NAME} ERROR: Failed to update status: {e}")
            sys.exit(1)

def show_portfolio(endpoint: str):
    res = _fetch_json(f"{endpoint}/api/strategies/manage/portfolio")
    if res and "portfolio_summary" in res:
        port = res["portfolio_summary"]
    else:
        from server.state_manager import strategy_registry
        port = strategy_registry.get_portfolio_summary()

    print("\n" + "=" * 76)
    print(f"{TOOL_NAME} AGGREGATED PORTFOLIO PERFORMANCE (ALL ACTIVE STRATEGIES)")
    print("=" * 76)
    print(f"  Active Strategies Count:  {port.get('active_count', 0)}")
    print(f"  Running In Parallel:      {', '.join(port.get('active_strategies', [])) or 'None'}")
    print(f"  Symbols Diversification:  {', '.join(port.get('symbols', [])) or 'None'}")
    print(f"  ----------------------------------------------------------------------")
    print(f"  Blended Win Rate:         {port.get('blended_win_rate', 0.0):.1f}%")
    print(f"  Blended Expected Sharpe:  {port.get('blended_sharpe', 0.0):.2f}")
    print(f"  Combined Profit Factor:   {port.get('combined_profit_factor', 0.0):.2f}")
    print(f"  Total Portfolio Trades:   {port.get('total_trades', 0)}")
    print(f"  Total Realized Net PnL:   ${port.get('total_realized_pnl', 0.0):.2f}")
    print(f"  Top Active Alpha:         {port.get('best_performer') or 'N/A'}")
    print("=" * 76 + "\n")

def show_drift_distribution(endpoint: str):
    res = _fetch_json(f"{endpoint}/api/strategies/manage/portfolio")
    if res and "distribution_analytics" in res:
        dist = res["distribution_analytics"]
    else:
        from server.state_manager import strategy_registry
        dist = strategy_registry.get_distribution_analytics()

    print("\n" + "=" * 76)
    print(f"{TOOL_NAME} STRATEGY PROFITABILITY DRIFT & PERFORMANCE DISTRIBUTION")
    print("=" * 76)
    print("  [ALPHA DRIFT TRAJECTORY]")
    improving = dist.get("improving", [])
    decaying = dist.get("decaying", [])
    stable = dist.get("stable", [])

    if improving:
        print("  🟢 GAINING EDGE / MORE PROFITABLE:")
        for s in improving:
            print(f"     • {s.get('name')}: ΔSharpe +{s.get('delta_sharpe')} | ΔWinRate +{s.get('delta_win_rate')}% ({s.get('snapshots_count')} snapshots)")
    else:
        print("  🟢 GAINING EDGE: None currently showing upward alpha expansion")

    if decaying:
        print("  🔴 DECAYING EDGE / LESS PROFITABLE:")
        for s in decaying:
            print(f"     • {s.get('name')}: ΔSharpe {s.get('delta_sharpe')} | ΔWinRate {s.get('delta_win_rate')}% ({s.get('snapshots_count')} snapshots)")
    else:
        print("  🔴 DECAYING EDGE: None currently flagged with significant edge decay")

    print(f"  ⚪ STABLE / CONSISTENT: {len(stable)} strategies within normal variance bounds")

    print("\n  [SHARPE RATIO DISTRIBUTION]")
    for b, c in dist.get("sharpe_distribution", {}).items():
        bar = "█" * (c * 4)
        print(f"     {b:<12} : {c:>2} {bar}")

    print("\n  [TIER DISTRIBUTION]")
    for t, c in dist.get("tier_distribution", {}).items():
        bar = "█" * (c * 4)
        print(f"     {t:<12} : {c:>2} {bar}")

    print("\n  [ASSET DIVERSIFICATION]")
    for a, c in dist.get("asset_distribution", {}).items():
        bar = "█" * (c * 4)
        print(f"     {a:<12} : {c:>2} {bar}")
    print("=" * 76 + "\n")

def run_backtest(strategy: str, endpoint: str):
    print(f"{TOOL_NAME} Running quantitative backtest for '{strategy}'...")
    res = _fetch_json(
        f"{endpoint}/api/strategies/manage/run-backtest",
        method="POST",
        data={"strategy": strategy},
        timeout=60
    )
    if res and res.get("status") == "SUCCESS":
        print(f"{TOOL_NAME} Backtest completed successfully for {strategy}")
        summary = res.get("result", {}).get("summary", {})
        print(json.dumps(summary, indent=2))
    else:
        # Offline fallback
        from server.backtest_engine import run_real_backtest
        from server.state_manager import strategy_registry
        try:
            result = run_real_backtest(strategy, save_as_active=False)
            strategy_registry.record_backtest(strategy, result, is_cron=False)
            print(f"{TOOL_NAME} Backtest completed (Local) for {strategy}")
            print(json.dumps(result.get("summary", {}), indent=2))
        except Exception as e:
            print(f"{TOOL_NAME} ERROR: Backtest failed: {e}")
            sys.exit(1)

def run_cron(endpoint: str):
    print(f"{TOOL_NAME} Triggering evaluations across all CRON_BACKTEST strategies...")
    res = _fetch_json(
        f"{endpoint}/api/strategies/manage/cron-trigger",
        method="POST",
        data={},
        timeout=120
    )
    if res and res.get("status") == "SUCCESS":
        evaled = res.get("evaluated", [])
        print(f"{TOOL_NAME} Evaluated {len(evaled)} strategies: {', '.join(evaled)}")
    else:
        # Offline fallback
        from server.backtest_engine import run_real_backtest
        from server.state_manager import strategy_registry
        strats = strategy_registry.get_all(sync=False)
        targets = [s for s in strats if s.get("status") == "CRON_BACKTEST"]
        print(f"{TOOL_NAME} Found {len(targets)} strategies set to CRON_BACKTEST")
        for s in targets:
            try:
                print(f"{TOOL_NAME} Evaluating {s['name']}...")
                res_bt = run_real_backtest(s["file"], save_as_active=False)
                strategy_registry.record_backtest(s["name"], res_bt, is_cron=True)
                print(f"{TOOL_NAME} -> {s['name']} recorded into drift history.")
            except Exception as e:
                print(f"{TOOL_NAME} -> Failed for {s['name']}: {e}")
        print(f"{TOOL_NAME} Cron evaluation complete.")

def rank_strategies(endpoint: str):
    print(f"{TOOL_NAME} Recalculating multi-factor quantitative rankings...")
    from server.state_manager import strategy_registry
    strats = strategy_registry.get_all(sync=True)
    ranked = strategy_registry.calculate_rankings(strats)
    print(f"{TOOL_NAME} Leaderboard updated across {len(ranked)} strategies:")
    for s in ranked:
        print(f"  Rank #{s.get('rank')}: {s.get('name')} | Score: {s.get('ranking_score')} | Tier: {s.get('tier')}")

def register_strategy(strategy: str, thesis: str, profile: str, symbol: str, timeframe: str, endpoint: str):
    print(f"{TOOL_NAME} Registering strategy '{strategy}'...")
    from server.state_manager import strategy_registry
    record = strategy_registry.register_strategy({
        "file": strategy if strategy.endswith(".py") else f"{strategy}.py",
        "name": strategy.replace(".py", ""),
        "thesis": thesis,
        "target_profile": profile,
        "symbol": symbol,
        "timeframe": timeframe,
        "status": "CRON_BACKTEST"
    })
    print(f"{TOOL_NAME} Strategy registered successfully:")
    print(json.dumps(record, indent=2))

def summary(endpoint: str):
    from server.state_manager import strategy_registry, state_manager
    strats = strategy_registry.get_all(sync=True)
    state = state_manager.get()
    active_name = state.get("active_strategy", "None")

    active_count = sum(1 for s in strats if s.get("status") == "ACTIVE_LIVE")
    cron_count = sum(1 for s in strats if s.get("status") == "CRON_BACKTEST")
    deact_count = sum(1 for s in strats if s.get("status") == "DEACTIVATED")

    print("\n" + "=" * 76)
    print(f"{TOOL_NAME} QUANT EDGE STRATEGY LEADERBOARD & LIFECYCLE SUMMARY")
    print("=" * 76)
    print(f"  System Active Bot Strategy:  {active_name}")
    print(f"  Total Managed Strategies:    {len(strats)}")
    print(f"  [ACTIVE_LIVE]:               {active_count}")
    print(f"  [CRON_BACKTEST]:             {cron_count}")
    print(f"  [DEACTIVATED]:               {deact_count}")
    print("-" * 76)
    for s in strats:
        bt = s.get("latest_backtest", {})
        drift_cnt = len(s.get("cron_config", {}).get("drift_history", []))
        print(f"  • Rank #{s.get('rank')} [{s.get('tier')}]: {s.get('name')}")
        print(f"    Status: {s.get('status')} | Target: {s.get('target_profile')} | Asset: {s.get('symbol')} {s.get('timeframe')}")
        print(f"    Sharpe: {bt.get('sharpe', 0.0)} | DSR: {bt.get('dsr', 0.0)} | Win%: {bt.get('win_rate', 0.0)*100:.1f}% | MDD: {bt.get('max_drawdown', 0.0)*100:.2f}% | Drift Snapshots: {drift_cnt}")
    print("=" * 76 + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EdgeMiner AI Strategy Management CLI")
    parser.add_argument(
        "action",
        choices=["list", "status", "backtest", "cron", "rank", "register", "summary", "portfolio", "drift"],
        help="list | status | backtest | cron | rank | register | summary | portfolio | drift"
    )
    parser.add_argument("pos_strategy", nargs="?", default=None, help="Optional positional strategy name")
    parser.add_argument("pos_status", nargs="?", default=None, help="Optional positional status")
    parser.add_argument("--strategy",  default="GoatFundedTraderXauusdScalper.py", help="Strategy filename or name")
    parser.add_argument("--status",    default="CRON_BACKTEST", choices=["ACTIVE_LIVE", "CRON_BACKTEST", "DEACTIVATED"], help="Target status")
    parser.add_argument("--exclusive", action="store_true", help="Demote other active strategies if activating this one")
    parser.add_argument("--thesis",    default="Out-of-the-Box Edge Hypothesis",   help="Core thesis description")
    parser.add_argument("--profile",   default="Prop Firm Challenge",              help="Target risk profile")
    parser.add_argument("--symbol",    default="BTC/USDT",                         help="Trading pair symbol")
    parser.add_argument("--timeframe", default="15m",                              help="Candle timeframe")
    parser.add_argument("--endpoint",  default="http://localhost:8000",            help="Backend API endpoint")
    args = parser.parse_args()

    effective_strategy = args.pos_strategy or args.strategy
    effective_status = args.pos_status or args.status

    if   args.action == "list":      list_strategies(args.endpoint)
    elif args.action == "status":    update_status(effective_strategy, effective_status, args.endpoint, args.exclusive)
    elif args.action == "backtest":  run_backtest(effective_strategy, args.endpoint)
    elif args.action == "cron":      run_cron(args.endpoint)
    elif args.action == "rank":      rank_strategies(args.endpoint)
    elif args.action == "register":  register_strategy(effective_strategy, args.thesis, args.profile, args.symbol, args.timeframe, args.endpoint)
    elif args.action == "summary":   summary(args.endpoint)
    elif args.action == "portfolio": show_portfolio(args.endpoint)
    elif args.action == "drift":     show_drift_distribution(args.endpoint)


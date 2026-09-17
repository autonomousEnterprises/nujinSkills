#!/usr/bin/env python3
import argparse
import json
import os
import sys
import urllib.request
from typing import Optional, Dict, Any, List

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

def list_plugins_cli(endpoint: str):
    res = _fetch_json(f"{endpoint}/api/plugins")
    if res and "plugins" in res:
        plugins = res["plugins"]
    else:
        from server.plugin_loader import plugin_manager
        plugins = plugin_manager.get_all_plugins()

    print(f"\n{TOOL_NAME} INSTALLED PLUGINS & EXTENSIONS ({len(plugins)} Total Active):")
    print("-" * 88)
    if not plugins:
        print("  No plugins installed. (Drop plugins into plugins/ folder to activate)")
    else:
        for p in plugins:
            pro_badge = "💎 [PRO]" if p.get("is_pro") else "📦 [COMMUNITY]"
            print(f"  {pro_badge} {p.get('name')} (v{p.get('version')}) — ID: {p.get('id')}")
            print(f"     Description: {p.get('description')}")
            print(f"     Author:      {p.get('author')}")
            print(f"     Strategies:  {p.get('strategy_count')} active ready-to-use alpha(s)")
            print(f"     Location:    {p.get('path')}")
            if p.get("features"):
                print(f"     Features:    {', '.join(p.get('features'))}")
            print("  " + "-" * 84)
    print()

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
        if s.get("is_pro"):
            name = f"💎 {name}"[:30]
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

def show_correlation(endpoint: str, threshold: float = 0.50, as_json: bool = False):
    res = _fetch_json(f"{endpoint}/api/portfolio/correlation?threshold={threshold}")
    if res and "correlation_matrix" in res:
        data = res
    else:
        from tools.portfolio_cynic import evaluate_portfolio
        data = evaluate_portfolio(correlation_threshold=threshold)

    if as_json:
        print(json.dumps(data, indent=2))
        return

    from tools.portfolio_cynic import print_ascii_report
    print_ascii_report(data)

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

def rank_strategies(endpoint: str, as_json: bool = False):
    """
    Recalculates and displays multi-pillar quantitative rankings.
    Contacts the live server to broadcast STRATEGIES_UPDATED over WebSocket if running.
    """
    res = _fetch_json(f"{endpoint}/api/strategies/manage/rank", method="POST", data={})
    if res and "strategies" in res:
        strats = res["strategies"]
        server_synced = True
    else:
        from server.state_manager import strategy_registry
        strats = strategy_registry.recalculate_and_save()
        server_synced = False

    if as_json:
        print(json.dumps(strats, indent=2))
        return

    sync_badge = "🟢 Live WebSocket Synced" if server_synced else "⚪ Local File Synced"
    print("\n" + "=" * 108)
    print(f"{TOOL_NAME} INSTITUTIONAL QUANTITATIVE LEADERBOARD & TIERS ({sync_badge})")
    print("=" * 108)
    header = f"{'Rank':<5} {'Tier':<24} {'Score':<6} {'E/Rob/Rsk/Drf':<16} {'Strategy Name':<28} {'Sharpe':<8} {'DSR':<8} {'Win%':<8} {'MaxDD':<8} {'PF':<6} {'Gates'}"
    print(header)
    print("-" * 108)

    tier_counts = {"S-Tier": 0, "A-Tier": 0, "B-Tier": 0, "C-Tier": 0}
    for s in strats:
        bt = s.get("latest_backtest", {})
        rb = s.get("ranking_breakdown", {})
        rank_str = f"#{s.get('rank', '-')}"
        tier = s.get("tier", "C-Tier")
        for t in tier_counts:
            if t in tier:
                tier_counts[t] += 1
        score = f"{s.get('ranking_score', 0.0):.1f}"
        e_sub = int(round(rb.get("edge_score", 0)))
        rob_sub = int(round(rb.get("robustness_score", 0)))
        rsk_sub = int(round(rb.get("risk_score", 0)))
        drf_sub = int(round(rb.get("drift_score", 0)))
        sub_str = f"{e_sub:>2}/{rob_sub:>2}/{rsk_sub:>2}/{drf_sub:>2}"
        name = s.get("name", "")
        if s.get("is_pro"):
            name = f"💎 {name}"
        name = name[:28]
        sharpe = f"{bt.get('sharpe', 0.0):.2f}"
        dsr = f"{bt.get('dsr', 0.0):.2f}"
        win = f"{bt.get('win_rate', 0.0) * 100:.1f}%" if bt.get('win_rate', 0.0) <= 1.0 else f"{bt.get('win_rate', 0.0):.1f}%"
        dd = f"{bt.get('max_drawdown', 0.0) * 100:.2f}%" if bt.get('max_drawdown', 0.0) <= 1.0 else f"{bt.get('max_drawdown', 0.0):.2f}%"
        pf = f"{bt.get('profit_factor', 0.0):.2f}"
        gates = f"{rb.get('gates_passed', 0)}/5"
        print(f"{rank_str:<5} {tier:<24} {score:<6} {sub_str:<16} {name:<28} {sharpe:<8} {dsr:<8} {win:<8} {dd:<8} {pf:<6} {gates}")

    print("-" * 108)
    print(f"  TIER DISTRIBUTION: S-Tier: {tier_counts['S-Tier']} | A-Tier: {tier_counts['A-Tier']} | B-Tier: {tier_counts['B-Tier']} | C-Tier: {tier_counts['C-Tier']}")
    print("=" * 108 + "\n")


def show_insights(strategy_name: Optional[str], endpoint: str, as_json: bool = False):
    """
    Displays an in-depth quantitative breakdown of a strategy's ranking, tier rationale,
    sub-scores (Edge, Robustness, Risk, Drift), and 5-gate cynic audit compliance.
    """
    from server.state_manager import strategy_registry
    strats = strategy_registry.get_all(sync=False)
    if not strats:
        print(f"{TOOL_NAME} No strategies found in registry.")
        return

    target = None
    if strategy_name:
        clean_target = strategy_name.replace(".py", "").lower()
        for s in strats:
            if s.get("name", "").lower() == clean_target or s.get("file", "").lower() == f"{clean_target}.py":
                target = s
                break
        if not target:
            print(f"{TOOL_NAME} Strategy '{strategy_name}' not found. Available strategies:")
            for s in strats:
                print(f"  • {s.get('name')}")
            return
    else:
        # Default to top-ranked strategy
        target = strats[0]

    bt = target.get("latest_backtest", {})
    rb = target.get("ranking_breakdown", {})
    gates = target.get("falsification_gates", {})

    if as_json:
        print(json.dumps({
            "name": target.get("name"),
            "rank": target.get("rank"),
            "tier": target.get("tier"),
            "ranking_score": target.get("ranking_score"),
            "ranking_breakdown": rb,
            "latest_backtest": bt,
            "falsification_gates": gates
        }, indent=2))
        return

    raw_wr = bt.get("win_rate", 0.0)
    wr_pct = raw_wr * 100.0 if raw_wr <= 1.0 else raw_wr
    raw_dd = bt.get("max_drawdown", 0.0)
    dd_pct = raw_dd * 100.0 if raw_dd <= 1.0 else raw_dd

    print("\n" + "=" * 84)
    print(f"{TOOL_NAME} STRATEGY QUANTITATIVE INSIGHTS & TIER RATIONALE")
    print("=" * 84)
    print(f"  Strategy Name:    {target.get('display_name', target.get('name'))} ({target.get('file')})")
    print(f"  Rank & Tier:      Rank #{target.get('rank')} — {target.get('tier')}")
    print(f"  Status / Profile: {target.get('status')} | {target.get('target_profile')}")
    print(f"  Asset Scope:      {target.get('symbol')} ({target.get('timeframe')})")
    period = target.get("time_period", {}).get("period_label") or bt.get("period_label", "N/A")
    print(f"  Time Period:      {period}")
    print(f"  Thesis:           {target.get('thesis')}")
    print("  " + "-" * 80)
    print(f"  COMPOSITE SCORE:  {target.get('ranking_score', 0.0):.1f} / 100.0")
    print(f"    • Edge Strength (35%):          {rb.get('edge_score', 0.0):>5.1f} / 100  (Sharpe {bt.get('sharpe', 0.0):.2f}, PF {bt.get('profit_factor', 0.0):.2f})")
    print(f"    • Statistical Robustness (30%): {rb.get('robustness_score', 0.0):>5.1f} / 100  (DSR {bt.get('dsr', 0.0):.2f}, Trades {bt.get('trades', 0)})")
    print(f"    • Downside Risk & MDD (25%):    {rb.get('risk_score', 0.0):>5.1f} / 100  (Max DD {dd_pct:.2f}%, Win Rate {wr_pct:.1f}%)")
    print(f"    • Drift Stability (10%):        {rb.get('drift_score', 0.0):>5.1f} / 100  (Snapshots: {len(target.get('cron_config', {}).get('drift_history', []))})")
    print("  " + "-" * 80)
    print(f"  CYNIC AUDIT GATES ({rb.get('gates_passed', 0)}/5 PASSED):")
    g1_pass = "✅ PASS" if bt.get("sharpe", 0.0) >= 1.8 else "❌ FAIL"
    g2_pass = "✅ PASS" if (dd_pct / 100.0) <= 0.045 else "❌ FAIL"
    g3_pass = "✅ PASS" if (bt.get("trades", 0) >= 30 and wr_pct >= 50.0) else "❌ FAIL"
    g4_pass = "✅ PASS" if bt.get("profit_factor", 0.0) >= 1.3 else "❌ FAIL"
    g5_pass = "✅ PASS" if bt.get("dsr", 0.0) >= 0.95 else "❌ FAIL"
    print(f"    [Gate 1] Net Annualized Sharpe >= 1.80 : {g1_pass} ({bt.get('sharpe', 0.0):.2f})")
    print(f"    [Gate 2] Max Drawdown <= 4.50%         : {g2_pass} ({dd_pct:.2f}%)")
    print(f"    [Gate 3] Trades >= 30 & Win Rate >= 50%: {g3_pass} ({bt.get('trades', 0)} trades, {wr_pct:.1f}%)")
    print(f"    [Gate 4] Profit Factor >= 1.30         : {g4_pass} ({bt.get('profit_factor', 0.0):.2f})")
    print(f"    [Gate 5] Deflated Sharpe DSR >= 0.95   : {g5_pass} ({bt.get('dsr', 0.0):.2f})")
    print("  " + "-" * 80)
    print(f"  TIER RATIONALE:   {rb.get('tier_reason', 'N/A')}")
    print("=" * 84 + "\n")

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

    # Notify running server for real-time Cockpit updates
    sync_res = _fetch_json(f"{endpoint}/api/strategies/sync", method="POST", data={})
    if sync_res:
        print(f"{TOOL_NAME} Real-time Cockpit telemetry updated via {endpoint}.")

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

def show_signals(strategy: Optional[str], endpoint: str):
    from server.state_manager import signal_store
    sigs = signal_store.get_all(strategy)
    actives = signal_store.get_active_signals()
    stats = signal_store.get_stats(strategy)

    title_suffix = f" FOR '{strategy}'" if strategy else " ACROSS ALL STRATEGIES"
    print("\n" + "=" * 76)
    print(f"{TOOL_NAME} STRATEGY LIVE SIGNALS & POSITIONS{title_suffix}")
    print("=" * 76)
    print(f"  Total Signals:   {len(sigs)}")
    print(f"  Active In Pos:   {len(actives)}")
    print(f"  Live Win Rate:   {stats.get('win_rate', 0.0)*100:.1f}% ({stats.get('wins', 0)}W / {stats.get('losses', 0)}L)")
    print(f"  Profit Factor:   {stats.get('profit_factor', 0.0)}")
    print(f"  Total Live PnL:  {stats.get('total_pnl_pct', 0.0):+.2f}%")
    print("-" * 76)

    if actives:
        print("  [CURRENT OPEN POSITIONS]:")
        for a in actives:
            print(f"   🟢 #{a.get('id')} [{a.get('strategy')}] {a.get('action')} {a.get('pair')} @ ${a.get('price'):,.2f}")
            print(f"      SL: ${a.get('stop_loss', 0):,.2f} | TP: ${a.get('take_profit', 0):,.2f} | Annotation: {a.get('annotation')}")
        print("-" * 76)
    else:
        print("  [CURRENT OPEN POSITIONS]: None (Scanning market regimes)\n" + "-" * 76)

    print("  [RECENT SIGNALS HISTORY (Latest 10)]:")
    for s in sigs[:10]:
        status_icon = "🟢" if s.get("status") == "ACTIVE_IN_POSITION" else ("✅" if s.get("pnl_pct", 0) > 0 else "❌")
        pnl_str = f"{s.get('pnl_pct', 0):+.2f}%" if s.get("status") != "ACTIVE_IN_POSITION" else "IN PROGRESS"
        print(f"   {status_icon} #{s.get('id')} [{s.get('strategy')}] {s.get('action')} {s.get('pair')} @ ${s.get('price'):,.2f} -> {s.get('exit_reason', 'OPEN')} ({pnl_str})")
    print("=" * 76 + "\n")

def sync_strategies(endpoint: str):
    """Explicitly re-scans strategies/ folder, indexes new files, removes deleted ones, and updates rankings."""
    print(f"{TOOL_NAME} Synchronizing strategy registry with filesystem (strategies/)...")
    res = _fetch_json(f"{endpoint}/api/strategies/sync", method="POST", data={})
    if res and res.get("status") == "SUCCESS":
        total = res.get("total", len(res.get("strategies", [])))
        print(f"{TOOL_NAME} SUCCESS: Synced with running server ({total} strategies indexed).")
    else:
        from server.state_manager import strategy_registry
        strats = strategy_registry.sync_with_filesystem()
        print(f"{TOOL_NAME} SUCCESS: Synced locally with filesystem ({len(strats)} strategies indexed).")
    list_strategies(endpoint)

def remove_strategy_cli(strategy: str, endpoint: str):
    """Removes strategy file from strategies/ and prunes it from the registry."""
    if not strategy:
        print(f"{TOOL_NAME} ERROR: Please specify strategy name to remove (e.g. python tools/strategy_manager.py remove MyStrategy)")
        sys.exit(1)
    print(f"{TOOL_NAME} Removing strategy '{strategy}'...")
    res = _fetch_json(f"{endpoint}/api/strategies/manage/remove", method="POST", data={"strategy": strategy})
    if res and res.get("status") == "SUCCESS":
        print(f"{TOOL_NAME} SUCCESS: Removed '{strategy}' via server. Registry updated.")
    else:
        from server.state_manager import strategy_registry
        removed = strategy_registry.remove_strategy(strategy)
        if removed:
            print(f"{TOOL_NAME} SUCCESS: Removed '{strategy}' from disk and updated registry.")
        else:
            print(f"{TOOL_NAME} WARNING: Strategy file for '{strategy}' not found on disk, pruned from registry.")
    list_strategies(endpoint)

def add_strategy_cli(filepath: str, endpoint: str):
    """Copies a new strategy Python file into strategies/ and synchronizes."""
    if not filepath or not os.path.exists(filepath):
        print(f"{TOOL_NAME} ERROR: Source file '{filepath}' does not exist.")
        sys.exit(1)
    import shutil
    fname = os.path.basename(filepath)
    if not fname.endswith(".py"):
        print(f"{TOOL_NAME} ERROR: Strategy file must be a .py file.")
        sys.exit(1)
    target_path = os.path.join(ROOT_DIR, "strategies", fname)
    if os.path.abspath(filepath) != os.path.abspath(target_path):
        shutil.copy2(filepath, target_path)
        print(f"{TOOL_NAME} Copied {fname} -> strategies/{fname}")
    sync_strategies(endpoint)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EdgeMiner AI Strategy Management CLI")
    parser.add_argument(
        "action",
        choices=["list", "plugins", "status", "backtest", "cron", "rank", "insights", "register", "summary", "portfolio", "correlation", "drift", "signals", "sync", "remove", "add"],
        help="list | plugins | status | backtest | cron | rank | insights | register | summary | portfolio | correlation | drift | signals | sync | remove | add"
    )
    parser.add_argument("pos_strategy", nargs="?", default=None, help="Optional positional strategy name or file path")
    parser.add_argument("pos_status", nargs="?", default=None, help="Optional positional status")
    parser.add_argument("--strategy",  default="", help="Strategy filename or name (filter for signals, target for status/remove)")
    parser.add_argument("--file",      default="", help="Source strategy file for add action")
    parser.add_argument("--status",    default="CRON_BACKTEST", choices=["ACTIVE_LIVE", "CRON_BACKTEST", "DEACTIVATED"], help="Target status")
    parser.add_argument("--exclusive", action="store_true", help="Demote other active strategies if activating this one")
    parser.add_argument("--thesis",    default="Out-of-the-Box Edge Hypothesis",   help="Core thesis description")
    parser.add_argument("--profile",   default="Prop Firm Challenge",              help="Target risk profile")
    parser.add_argument("--symbol",    default="BTC/USDT",                         help="Trading pair symbol")
    parser.add_argument("--timeframe", default="15m",                              help="Candle timeframe")
    parser.add_argument("--threshold", type=float, default=0.50,                   help="Correlation threshold for orthogonality rejection")
    parser.add_argument("--endpoint",  default="http://localhost:8000",            help="Backend API endpoint")
    parser.add_argument("--json",      dest="as_json", action="store_true",        help="Output in JSON format for automated agent ingestion")
    args = parser.parse_args()

    effective_strategy = args.pos_strategy or args.strategy
    effective_status = args.pos_status or args.status
    effective_file = args.file or args.pos_strategy

    if   args.action == "list":        list_strategies(args.endpoint)
    elif args.action == "plugins":     list_plugins_cli(args.endpoint)
    elif args.action == "status":      update_status(effective_strategy, effective_status, args.endpoint, args.exclusive)
    elif args.action == "backtest":    run_backtest(effective_strategy, args.endpoint)
    elif args.action == "cron":        run_cron(args.endpoint)
    elif args.action == "rank":        rank_strategies(args.endpoint, as_json=args.as_json)
    elif args.action == "insights":    show_insights(effective_strategy, args.endpoint, as_json=args.as_json)
    elif args.action == "register":    register_strategy(effective_strategy, args.thesis, args.profile, args.symbol, args.timeframe, args.endpoint)
    elif args.action == "summary":     summary(args.endpoint)
    elif args.action == "portfolio":   show_portfolio(args.endpoint)
    elif args.action == "correlation": show_correlation(args.endpoint, threshold=args.threshold, as_json=args.as_json)
    elif args.action == "drift":       show_drift_distribution(args.endpoint)
    elif args.action == "signals":     show_signals(effective_strategy, args.endpoint)
    elif args.action == "sync":        sync_strategies(args.endpoint)
    elif args.action == "remove":      remove_strategy_cli(effective_strategy, args.endpoint)
    elif args.action == "add":         add_strategy_cli(effective_file, args.endpoint)


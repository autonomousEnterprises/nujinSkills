#!/usr/bin/env python3
import argparse
import json
import urllib.request
import sys

def get_state(key: str, endpoint: str):
    url = f"{endpoint}/api/state"
    try:
        with urllib.request.urlopen(url, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if key:
                # Dotted key path: e.g. "backtest_summary.sharpe"
                for part in key.split("."):
                    if isinstance(data, dict) and part in data:
                        data = data[part]
                    else:
                        print(f"[StateControl] Key not found: {key}")
                        sys.exit(1)
            print(json.dumps(data, indent=2) if isinstance(data, (dict, list)) else data)
    except Exception as e:
        print(f"[StateControl] Error fetching state: {e}")

def patch_state(patch_json: str, endpoint: str):
    url = f"{endpoint}/api/state"
    try:
        updates = json.loads(patch_json)
    except json.JSONDecodeError as e:
        print(f"[StateControl] Invalid JSON: {e}")
        sys.exit(1)
    data = json.dumps(updates).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST", headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            print(f"[StateControl] State patched successfully.")
            print(json.dumps(result.get("state", result), indent=2))
    except Exception as e:
        print(f"[StateControl] Error patching state: {e}")

def deploy_strategy(strategy: str, mode: str, endpoint: str):
    url = f"{endpoint}/api/bot/deploy"
    data = json.dumps({"strategy": strategy, "mode": mode}).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            print(f"[StateControl] Strategy deployed: {strategy}")
            print(json.dumps(result.get("state", result), indent=2))
    except Exception as e:
        print(f"[StateControl] Error deploying strategy: {e}")

def stop_strategy(endpoint: str):
    url = f"{endpoint}/api/bot/stop"
    req = urllib.request.Request(url, data=b"{}", headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            print(f"[StateControl] Strategy stopped.")
            print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"[StateControl] Error stopping strategy: {e}")

def get_signals(endpoint: str):
    url = f"{endpoint}/api/signals"
    try:
        with urllib.request.urlopen(url, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f"[StateControl] Signals ({len(data.get('signals', []))} total):")
            print(json.dumps(data, indent=2))
    except Exception as e:
        print(f"[StateControl] Error fetching signals: {e}")

def get_signal_stats(endpoint: str):
    url = f"{endpoint}/api/signals/stats"
    try:
        with urllib.request.urlopen(url, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f"[StateControl] Live Signal Performance Stats:")
            print(json.dumps(data, indent=2))
    except Exception as e:
        print(f"[StateControl] Error fetching signal stats: {e}")

def add_signal(signal_json: str, endpoint: str):
    url = f"{endpoint}/api/broadcast"
    try:
        payload = json.loads(signal_json)
    except json.JSONDecodeError as e:
        print(f"[StateControl] Invalid JSON: {e}")
        sys.exit(1)
    envelope = {"event_type": "SIGNAL_TRIGGERED", "payload": payload}
    data = json.dumps(envelope).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            print(f"[StateControl] Signal broadcast result: HTTP {resp.status}")
    except Exception as e:
        print(f"[StateControl] Error broadcasting signal: {e}")

def get_schema(endpoint: str):
    # Schema is derived from DEFAULT_STATE — request state and display its keys
    url = f"{endpoint}/api/state"
    try:
        with urllib.request.urlopen(url, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            schema = {k: type(v).__name__ for k, v in data.items()}
            print(f"[StateControl] State schema (key: type):")
            print(json.dumps(schema, indent=2))
    except Exception as e:
        print(f"[StateControl] Error fetching schema: {e}")

def get_managed_strategies(endpoint: str):
    url = f"{endpoint}/api/strategies/manage"
    try:
        with urllib.request.urlopen(url, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            strats = data.get("strategies", [])
            print(f"[StateControl] Managed Strategies ({len(strats)} total):")
            for s in strats:
                bt = s.get("latest_backtest", {})
                print(f"  #{s.get('rank')}: {s.get('name')} | Status: {s.get('status')} | Sharpe: {bt.get('sharpe', 0.0)} | DSR: {bt.get('dsr', 0.0)} | Tier: {s.get('tier')}")
    except Exception:
        # Offline fallback
        import os, sys
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
        from server.state_manager import strategy_registry
        strats = strategy_registry.get_all(sync=True)
        print(f"[StateControl] Managed Strategies (Local, {len(strats)} total):")
        for s in strats:
            bt = s.get("latest_backtest", {})
            print(f"  #{s.get('rank')}: {s.get('name')} | Status: {s.get('status')} | Sharpe: {bt.get('sharpe', 0.0)} | DSR: {bt.get('dsr', 0.0)} | Tier: {s.get('tier')}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EdgeMiner State Control CLI — shared state for server, frontend, and AI agent.")
    parser.add_argument(
        "action",
        choices=["get", "patch", "deploy", "stop", "signals", "signal-stats", "signal-add", "schema", "strategies"],
        help=(
            "get: read state or a dotted key | "
            "patch: merge-patch state with JSON | "
            "deploy: run backtest and activate strategy | "
            "stop: deactivate active strategy | "
            "signals: list all signals | "
            "signal-stats: live win rate, PF, Sharpe, PnL | "
            "signal-add: broadcast a new signal | "
            "schema: show state schema | "
            "strategies: list all managed strategies with status and rank"
        )
    )
    parser.add_argument("--key",      default="",                       help="Dotted key path for 'get', e.g. backtest_summary.sharpe")
    parser.add_argument("--patch",    default="{}",                     help="JSON object to merge-patch into state")
    parser.add_argument("--strategy", default="PropFirmVsaWickRejection.py", help="Strategy filename to deploy")
    parser.add_argument("--mode",     default="dry-run", choices=["dry-run", "live"], help="Bot execution mode (default: dry-run)")
    parser.add_argument("--signal",   default="{}",                     help="Signal JSON object for signal-add")
    parser.add_argument("--endpoint", default="http://localhost:8000",  help="Backend API endpoint (default: http://localhost:8000)")
    args = parser.parse_args()

    if   args.action == "get":          get_state(args.key, args.endpoint)
    elif args.action == "patch":        patch_state(args.patch, args.endpoint)
    elif args.action == "deploy":       deploy_strategy(args.strategy, args.mode, args.endpoint)
    elif args.action == "stop":         stop_strategy(args.endpoint)
    elif args.action == "signals":      get_signals(args.endpoint)
    elif args.action == "signal-stats": get_signal_stats(args.endpoint)
    elif args.action == "signal-add":   add_signal(args.signal, args.endpoint)
    elif args.action == "schema":       get_schema(args.endpoint)
    elif args.action == "strategies":   get_managed_strategies(args.endpoint)

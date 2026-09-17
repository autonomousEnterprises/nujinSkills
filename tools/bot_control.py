#!/usr/bin/env python3
import argparse
import json
import sys
import urllib.request

opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

def deploy_bot(strategy: str, mode: str, endpoint: str):
    url = f"{endpoint}/api/bot/deploy"
    data = json.dumps({"strategy": strategy, "mode": mode}).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    
    try:
        with opener.open(req) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            print(f"[BotControl] Strategy Deployment Request Result:")
            print(json.dumps(res, indent=2))
    except Exception as e:
        print(f"[BotControl] Error communicating with server: {e}")

def stop_bot(endpoint: str, strategy: str = ""):
    url = f"{endpoint}/api/bot/stop"
    payload = {"strategy": strategy} if strategy else {}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    
    try:
        with opener.open(req) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            print(f"[BotControl] Bot Termination Result:")
            print(json.dumps(res, indent=2))
    except Exception as e:
        print(f"[BotControl] Error communicating with server: {e}")

def check_status(endpoint: str):
    url = f"{endpoint}/api/bot/status"
    try:
        with opener.open(url) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            print(f"[BotControl] Active Bot Status:")
            print(json.dumps(res, indent=2))
    except Exception as e:
        print(f"[BotControl] Server offline or unreachable: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Trading Bot Supervisor Control CLI")
    parser.add_argument("action", choices=["deploy", "stop", "status"], help="Action to execute")
    parser.add_argument("--strategy", default="", help="Strategy name to deploy or stop (leave empty to stop all)")
    parser.add_argument("--mode", choices=["dry-run", "live", "paper"], default="dry-run", help="Execution mode (dry-run/paper or live)")
    parser.add_argument("--endpoint", default="http://localhost:8000", help="Backend API endpoint")
    args = parser.parse_args()

    mode = "dry-run" if args.mode == "paper" else args.mode

    if args.action == "deploy":
        if not args.strategy:
            from server.state_manager import strategy_registry
            deploy_strat = strategy_registry.get_active_strategy_name()
        else:
            import os
            deploy_strat = os.path.basename(args.strategy).replace(".py", "")
        deploy_bot(deploy_strat, mode, args.endpoint)
    elif args.action == "stop":
        import os
        strat = os.path.basename(args.strategy).replace(".py", "") if args.strategy else ""
        stop_bot(args.endpoint, strat)
    elif args.action == "status":
        check_status(args.endpoint)

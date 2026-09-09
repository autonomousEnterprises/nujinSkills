#!/usr/bin/env python3
import argparse
import json
import sys
import urllib.request

def deploy_bot(strategy: str, mode: str, endpoint: str):
    url = f"{endpoint}/api/bot/deploy"
    data = json.dumps({"strategy": strategy, "mode": mode}).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    
    try:
        with urllib.request.urlopen(req) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            print(f"[BotControl] Strategy Deployment Request Result:")
            print(json.dumps(res, indent=2))
    except Exception as e:
        print(f"[BotControl] Error communicating with server: {e}")

def stop_bot(endpoint: str):
    url = f"{endpoint}/api/bot/stop"
    req = urllib.request.Request(url, data=b"{}", headers={"Content-Type": "application/json"})
    
    try:
        with urllib.request.urlopen(req) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            print(f"[BotControl] Bot Termination Result:")
            print(json.dumps(res, indent=2))
    except Exception as e:
        print(f"[BotControl] Error communicating with server: {e}")

def check_status(endpoint: str):
    url = f"{endpoint}/api/bot/status"
    try:
        with urllib.request.urlopen(url) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            print(f"[BotControl] Active Bot Status:")
            print(json.dumps(res, indent=2))
    except Exception as e:
        print(f"[BotControl] Server offline or unreachable: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Trading Bot Supervisor Control CLI")
    parser.add_argument("action", choices=["deploy", "stop", "status"], help="Action to execute")
    parser.add_argument("--strategy", default="TrapFade_v1", help="Strategy name to deploy")
    parser.add_argument("--mode", choices=["dry-run", "live"], default="dry-run", help="Execution mode")
    parser.add_argument("--endpoint", default="http://localhost:8000", help="Backend API endpoint")
    args = parser.parse_args()

    if args.action == "deploy":
        deploy_bot(args.strategy, args.mode, args.endpoint)
    elif args.action == "stop":
        stop_bot(args.endpoint)
    elif args.action == "status":
        check_status(args.endpoint)

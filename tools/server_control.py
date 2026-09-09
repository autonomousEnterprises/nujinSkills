#!/usr/bin/env python3
import argparse
import os
import sys
import subprocess
import time
import urllib.request
import json

PID_FILE = ".server.pid"

def get_pid() -> int:
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, "r") as f:
                return int(f.read().strip())
        except Exception:
            return 0
    return 0

def check_status(port: int = 8000):
    url = f"http://localhost:{port}/api/health"
    try:
        with urllib.request.urlopen(url, timeout=2) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f"[ServerControl] ONLINE (Port {port})")
            print(json.dumps(data, indent=2))
            return True
    except Exception:
        print(f"[ServerControl] OFFLINE (Port {port})")
        return False

def start_server(host: str, port: int, daemon: bool):
    if check_status(port):
        print(f"[ServerControl] Server is already running on port {port}.")
        return

    cmd = [
        sys.executable, "-m", "uvicorn", "server.main:app",
        "--host", host,
        "--port", str(port),
        "--reload"
    ]
    
    print(f"[ServerControl] Launching Telemetry Server & Telegram Gateway on {host}:{port}...")
    
    if daemon:
        # Launch detached process
        proc = subprocess.Popen(
            cmd,
            stdout=open("server.log", "a"),
            stderr=subprocess.STDOUT,
            preexec_fn=os.setsid
        )
        with open(PID_FILE, "w") as f:
            f.write(str(proc.pid))
        print(f"[ServerControl] Server started in background with PID {proc.pid}. Logs: server.log")
        time.sleep(2)
        check_status(port)
    else:
        # Foreground process
        try:
            subprocess.run(cmd)
        except KeyboardInterrupt:
            print("\n[ServerControl] Server stopped by user.")

def stop_server():
    pid = get_pid()
    if pid > 0:
        try:
            os.kill(pid, 9)
            os.remove(PID_FILE)
            print(f"[ServerControl] Killed process with PID {pid}")
        except Exception as e:
            print(f"[ServerControl] Failed to kill PID {pid}: {e}")
            if os.path.exists(PID_FILE):
                os.remove(PID_FILE)
    else:
        print("[ServerControl] No active PID file found.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Telemetry Server Control CLI")
    parser.add_argument("action", choices=["start", "stop", "status"], help="Action to execute")
    parser.add_argument("--host", default="0.0.0.0", help="Host IP (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port (default: 8000)")
    parser.add_argument("--daemon", action="store_true", help="Run in background daemon mode")
    args = parser.parse_args()

    if args.action == "start":
        start_server(args.host, args.port, args.daemon)
    elif args.action == "stop":
        stop_server()
    elif args.action == "status":
        check_status(args.port)

#!/usr/bin/env python3
import argparse
import os
import sys
import subprocess
import time
import urllib.request
from pathlib import Path

# Ensure modern Node.js is in PATH if nvm is available
def setup_node_path():
    nvm_node_dir = Path.home() / ".nvm" / "versions" / "node"
    if nvm_node_dir.exists():
        # Find latest node version
        versions = sorted([d for d in nvm_node_dir.iterdir() if d.is_dir()], key=lambda x: x.name, reverse=True)
        if versions:
            latest_node_bin = str(versions[0] / "bin")
            if latest_node_bin not in os.environ.get("PATH", ""):
                os.environ["PATH"] = f"{latest_node_bin}:{os.environ.get('PATH', '')}"

setup_node_path()

PID_FILE = ".frontend.pid"

def check_status(port: int = 3000):
    url = f"http://localhost:{port}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            print(f"[FrontendControl] ONLINE (Port {port}, Status {resp.status})")
            return True
    except Exception:
        print(f"[FrontendControl] OFFLINE (Port {port})")
        return False

def build_frontend():
    frontend_dir = os.path.abspath("frontend")
    print(f"[FrontendControl] Using Node version: {subprocess.getoutput('node --version')}")
    print(f"[FrontendControl] Installing npm dependencies & building UI in {frontend_dir}...")
    
    if not os.path.exists(os.path.join(frontend_dir, "node_modules")):
        subprocess.run(["npm", "install"], cwd=frontend_dir, check=True, env=os.environ)
        
    subprocess.run(["npm", "run", "build"], cwd=frontend_dir, check=True, env=os.environ)
    print("[FrontendControl] Frontend build completed successfully!")

def start_frontend(port: int, daemon: bool):
    frontend_dir = os.path.abspath("frontend")
    
    if check_status(port):
        print(f"[FrontendControl] Frontend is already running on port {port}.")
        return

    if not os.path.exists(os.path.join(frontend_dir, "node_modules")):
        print("[FrontendControl] Installing dependencies first...")
        subprocess.run(["npm", "install"], cwd=frontend_dir, check=True, env=os.environ)

    cmd = ["npx", "vite", "preview", "--port", str(port), "--host"]
    print(f"[FrontendControl] Using Node version: {subprocess.getoutput('node --version')}")
    print(f"[FrontendControl] Starting Vite Preview Server on port {port}...")
    
    if daemon:
        log_f = open("frontend_server.log", "a")
        proc = subprocess.Popen(
            cmd,
            cwd=frontend_dir,
            stdout=log_f,
            stderr=log_f,
            env=os.environ,
            preexec_fn=os.setsid
        )
        with open(PID_FILE, "w") as f:
            f.write(str(proc.pid))
        print(f"[FrontendControl] Frontend started in background with PID {proc.pid}. Logs: frontend_server.log")
        time.sleep(3)
        check_status(port)
    else:
        try:
            subprocess.run(cmd, cwd=frontend_dir, env=os.environ)
        except KeyboardInterrupt:
            print("\n[FrontendControl] Frontend stopped by user.")

def stop_frontend():
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, "r") as f:
                pid = int(f.read().strip())
            os.kill(pid, 9)
            os.remove(PID_FILE)
            print(f"[FrontendControl] Killed process with PID {pid}")
        except Exception as e:
            print(f"[FrontendControl] Failed to stop frontend process: {e}")
            if os.path.exists(PID_FILE):
                os.remove(PID_FILE)
    else:
        print("[FrontendControl] No active PID file found.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Frontend UI Control CLI")
    parser.add_argument("action", choices=["build", "start", "stop", "status"], help="Action to execute")
    parser.add_argument("--port", type=int, default=3000, help="Port (default: 3000)")
    parser.add_argument("--daemon", action="store_true", help="Run in background daemon mode")
    args = parser.parse_args()

    if args.action == "build":
        build_frontend()
    elif args.action == "start":
        start_frontend(args.port, args.daemon)
    elif args.action == "stop":
        stop_frontend()
    elif args.action == "status":
        check_status(args.port)

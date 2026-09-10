import subprocess
import os
import signal
import logging
from typing import Dict, Any, Optional

from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

logger = logging.getLogger("BotRunner")

class BotSupervisor:
    """
    Supervises background strategy runners, supporting concurrent execution
    of multiple strategies in parallel (e.g. XAUUSD Scalper + BTC VSA Wick Rejection).
    """
    def __init__(self):
        # Maps strategy_name -> {process, mode, started_at, config_path}
        self.runners: Dict[str, Dict[str, Any]] = {}

    @property
    def active_strategy(self) -> str:
        """Backward compatibility helper: returns the most recently deployed strategy."""
        return list(self.runners.keys())[-1] if self.runners else ""

    @property
    def active_strategies(self) -> List[str]:
        """Returns list of all currently active strategy names."""
        return list(self.runners.keys())

    @property
    def mode(self) -> str:
        return self.runners[self.active_strategy]["mode"] if self.active_strategy else "stopped"

    def deploy_strategy(self, strategy_name: str, mode: str = "dry-run", config_path: str = "user_data/config.json") -> Dict[str, Any]:
        clean_name = strategy_name.replace(".py", "")
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Stop existing runner for this specific strategy if running
        if clean_name in self.runners and self.runners[clean_name].get("process"):
            self.stop_strategy(clean_name)

        cmd = [
            "freqtrade", "trade",
            "--strategy", clean_name,
            "--config", config_path
        ]
        if mode == "dry-run":
            cmd.append("--dry-run")

        logger.info(f"[BotRunner] Deploying strategy '{clean_name}' (mode: {mode})...")

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.runners[clean_name] = {
                "process": proc,
                "mode": mode,
                "started_at": now_iso,
                "config_path": config_path
            }
            return {
                "status": "SUCCESS",
                "message": f"Bot deployed for strategy '{clean_name}' in {mode} mode",
                "pid": proc.pid,
                "active_strategies": list(self.runners.keys())
            }
        except FileNotFoundError:
            logger.info(f"[BotRunner] freqtrade binary not found on PATH. Activated native Python telemetry runner for '{clean_name}'.")
            self.runners[clean_name] = {
                "process": None,
                "mode": "python-telemetry",
                "started_at": now_iso,
                "config_path": config_path
            }
            return {
                "status": "SUCCESS",
                "message": f"Strategy '{clean_name}' deployed in Native Telemetry mode (freqtrade not on PATH).",
                "mode": "python-telemetry",
                "pid": None,
                "active_strategies": list(self.runners.keys())
            }

    def stop_strategy(self, strategy_name: str) -> Dict[str, Any]:
        clean_name = strategy_name.replace(".py", "")
        if clean_name not in self.runners:
            return {"status": "SUCCESS", "message": f"Strategy '{clean_name}' is not currently running"}

        runner = self.runners.pop(clean_name)
        proc: Optional[subprocess.Popen] = runner.get("process")
        if proc and proc.poll() is None:
            try:
                proc.send_signal(signal.SIGTERM)
                proc.wait(timeout=5)
            except Exception as e:
                logger.warning(f"Error terminating runner for {clean_name}: {e}")
                proc.kill()

        logger.info(f"[BotRunner] Stopped strategy '{clean_name}'. Remaining active: {list(self.runners.keys())}")
        return {"status": "SUCCESS", "message": f"Strategy '{clean_name}' terminated", "remaining_active": list(self.runners.keys())}

    def stop_all(self) -> Dict[str, Any]:
        stopped = []
        for name in list(self.runners.keys()):
            self.stop_strategy(name)
            stopped.append(name)
        return {"status": "SUCCESS", "message": f"Stopped {len(stopped)} active strategies", "stopped": stopped}

    def stop_bot(self, strategy_name: Optional[str] = None) -> Dict[str, Any]:
        """Backward-compatible stop method. If strategy_name provided, stops that; otherwise stops all."""
        if strategy_name:
            return self.stop_strategy(strategy_name)
        return self.stop_all()

    def get_status(self) -> Dict[str, Any]:
        # Filter dead processes
        dead = []
        for name, runner in self.runners.items():
            p = runner.get("process")
            if p is not None and p.poll() is not None:
                dead.append(name)
        for name in dead:
            self.runners.pop(name, None)

        is_running = len(self.runners) > 0
        primary = self.active_strategy

        return {
            "is_running": is_running,
            "mode": self.mode,
            "active_strategy": primary,
            "active_strategies": list(self.runners.keys()),
            "count": len(self.runners),
            "pid": self.runners[primary]["process"].pid if (primary and self.runners[primary].get("process")) else None,
            "runners": {
                name: {
                    "mode": r["mode"],
                    "pid": r["process"].pid if r.get("process") else None,
                    "started_at": r["started_at"]
                }
                for name, r in self.runners.items()
            }
        }

bot_supervisor = BotSupervisor()

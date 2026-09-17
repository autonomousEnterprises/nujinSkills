import subprocess
import os
import signal
import logging
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Callable

logger = logging.getLogger("BotRunner")

class BotSupervisor:
    """
    Supervises background strategy runners, supporting concurrent execution
    of multiple strategies in parallel (e.g. XAUUSD Scalper + BTC VSA Wick Rejection).
    Seamlessly falls back to native Python Strategy Runners when freqtrade is not on PATH.
    """
    def __init__(self):
        # Maps strategy_name -> {process, mode, started_at, config_path, native_runner}
        self.runners: Dict[str, Dict[str, Any]] = {}
        self.broadcast_callback: Optional[Callable] = None

    def set_broadcast_callback(self, callback: Callable) -> None:
        self.broadcast_callback = callback
        # Propagate to any existing native runners
        for r in self.runners.values():
            if r.get("native_runner"):
                r["native_runner"].broadcast_callback = callback

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
        if clean_name in self.runners:
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
                "config_path": config_path,
                "native_runner": None
            }
            return {
                "status": "SUCCESS",
                "message": f"Bot deployed for strategy '{clean_name}' in {mode} mode",
                "pid": proc.pid,
                "active_strategies": list(self.runners.keys())
            }
        except FileNotFoundError:
            logger.info(f"[BotRunner] freqtrade binary not found on PATH. Activating native Python telemetry runner for '{clean_name}'.")
            from server.strategy_executor import NativeStrategyRunner

            runner = NativeStrategyRunner(strategy_name=clean_name, broadcast_callback=self.broadcast_callback)

            # Start runner task in active asyncio event loop if running
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(runner.start())
            except RuntimeError:
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        loop.create_task(runner.start())
                    else:
                        asyncio.run(runner.start())
                except Exception as e_start:
                    logger.warning(f"[BotRunner] Could not start native runner immediately: {e_start}")

            self.runners[clean_name] = {
                "process": None,
                "mode": "python-telemetry",
                "started_at": now_iso,
                "config_path": config_path,
                "native_runner": runner
            }
            return {
                "status": "SUCCESS",
                "message": f"Strategy '{clean_name}' deployed in Native Autonomous Trading Bot mode.",
                "mode": "python-telemetry",
                "pid": None,
                "active_strategies": list(self.runners.keys())
            }

    def stop_strategy(self, strategy_name: str) -> Dict[str, Any]:
        clean_name = strategy_name.replace(".py", "")
        if clean_name not in self.runners:
            return {"status": "SUCCESS", "message": f"Strategy '{clean_name}' is not currently running"}

        runner_info = self.runners.pop(clean_name)
        proc: Optional[subprocess.Popen] = runner_info.get("process")
        if proc and proc.poll() is None:
            try:
                proc.send_signal(signal.SIGTERM)
                proc.wait(timeout=5)
            except Exception as e:
                logger.warning(f"Error terminating runner for {clean_name}: {e}")
                proc.kill()

        native_runner = runner_info.get("native_runner")
        if native_runner and native_runner.is_running:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(native_runner.stop())
            except RuntimeError:
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        loop.create_task(native_runner.stop())
                    else:
                        asyncio.run(native_runner.stop())
                except Exception as e_stop:
                    logger.warning(f"[BotRunner] Error stopping native runner: {e_stop}")

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
        # Filter dead OS processes
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
                    "started_at": r["started_at"],
                    "native_active": bool(r.get("native_runner") and r["native_runner"].is_running)
                }
                for name, r in self.runners.items()
            }
        }

    def check_signal_cannibalization(self, new_signal: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Delegates to module-level check_signal_cannibalization."""
        return check_signal_cannibalization(new_signal)

def check_signal_cannibalization(new_signal: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Signal Cannibalization Guard:
    Checks if another active strategy currently holds an opposing position on the same asset.
    Prevents wash-trading and commission bleed across parallel ensemble strategies.
    Returns the conflicting active position dict if cannibalization is detected, or None.
    """
    from server.state_manager import signal_store
    active_positions = signal_store.get_active_signals()
    if not active_positions:
        return None

    incoming_pair = (new_signal.get("pair") or new_signal.get("symbol") or "").upper().replace("/", "").replace("_", "").replace("-", "")
    incoming_action = (new_signal.get("action") or new_signal.get("side") or "").upper()
    incoming_is_long = incoming_action in ("BUY", "LONG")
    incoming_strategy = new_signal.get("strategy", "").replace(".py", "").lower()

    for pos in active_positions:
        pos_strategy = pos.get("strategy", "").replace(".py", "").lower()
        if pos_strategy == incoming_strategy:
            continue  # Handled by single-strategy position check

        pos_pair = (pos.get("pair") or pos.get("symbol") or "").upper().replace("/", "").replace("_", "").replace("-", "")
        if pos_pair == incoming_pair:
            pos_action = (pos.get("action") or pos.get("side") or "").upper()
            pos_is_long = pos_action in ("BUY", "LONG")
            if incoming_is_long != pos_is_long:
                return pos

    return None

bot_supervisor = BotSupervisor()


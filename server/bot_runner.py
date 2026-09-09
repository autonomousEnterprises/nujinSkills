import subprocess
import os
import signal
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("BotRunner")

class BotSupervisor:
    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.active_strategy: str = ""
        self.mode: str = "stopped"

    def deploy_strategy(self, strategy_name: str, mode: str = "dry-run", config_path: str = "user_data/config.json") -> Dict[str, Any]:
        if self.process and self.process.poll() is None:
            self.stop_bot()
            
        cmd = [
            "freqtrade", "trade",
            "--strategy", strategy_name,
            "--config", config_path
        ]
        if mode == "dry-run":
            cmd.append("--dry-run")
            
        logger.info(f"Deploying bot with command: {' '.join(cmd)}")
        
        try:
            # Launch in background process
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.active_strategy = strategy_name
            self.mode = mode
            return {"status": "SUCCESS", "message": f"Bot deployed for strategy '{strategy_name}' in {mode} mode", "pid": self.process.pid}
        except FileNotFoundError:
            raise RuntimeError(
                f"[BotRunner] freqtrade binary not found on PATH. "
                f"Install freqtrade first: pip install freqtrade. "
                f"Strategy '{strategy_name}' was NOT deployed."
            )

    def stop_bot(self) -> Dict[str, Any]:
        if self.process and self.process.poll() is None:
            self.process.send_signal(signal.SIGTERM)
            self.process.wait(timeout=5)
            self.process = None
            self.mode = "stopped"
            return {"status": "SUCCESS", "message": f"Strategy '{self.active_strategy}' terminated"}
        else:
            self.mode = "stopped"
            return {"status": "SUCCESS", "message": "No active bot process running"}

    def get_status(self) -> Dict[str, Any]:
        is_running = self.process is not None and self.process.poll() is None
        return {
            "is_running": is_running,
            "mode": self.mode,
            "active_strategy": self.active_strategy,
            "pid": self.process.pid if is_running else None
        }

bot_supervisor = BotSupervisor()

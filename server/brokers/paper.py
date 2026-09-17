"""
server/brokers/paper.py
─────────────────────────────────────────────────────────────
Default In-Memory & Local Database Simulated Execution Broker.
Requires zero external API credentials or third-party packages.
"""

from __future__ import annotations

import logging
import time
from typing import Dict, Any, List, Optional

from server.brokers.base import BaseExecutionBroker
from server.state_manager import signal_store

logger = logging.getLogger("PaperExecutionBroker")


class PaperExecutionBroker(BaseExecutionBroker):
    """
    Standard Paper Trading execution adapter.
    Logs trades locally into SignalStore with simulated fills.
    """

    def __init__(self):
        super().__init__(broker_id="paper", name="Nujin Simulated Paper Execution")
        self.initial_balance = 100000.0
        self.balance = self.initial_balance
        self.is_connected = True

    def connect(self, config: Optional[Dict[str, Any]] = None) -> bool:
        self.is_connected = True
        logger.info("[PaperBroker] Connected to local simulated trading engine.")
        return True

    def disconnect(self) -> None:
        self.is_connected = False

    def get_account_info(self) -> Dict[str, Any]:
        stats = signal_store.get_stats()
        realized_pnl = float(stats.get("total_pnl_pct", 0.0)) / 100.0 * self.initial_balance
        equity = self.balance + realized_pnl
        return {
            "broker_id": self.broker_id,
            "broker_name": self.name,
            "balance": round(self.balance, 2),
            "equity": round(equity, 2),
            "free_margin": round(equity, 2),
            "currency": "USD",
            "is_demo": True,
            "connected": self.is_connected,
        }

    def execute_order(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        fill_price = float(signal.get("price", 0.0))
        signal_id = str(signal.get("id") or int(time.time() * 1000))
        lots = float(signal.get("lots") or signal.get("lot_size") or 1.0)
        logger.info(
            f"[PaperBroker] 📝 Simulating fill for {signal.get('strategy')} "
            f"{signal.get('action')} {signal.get('symbol')} ({lots:.2f} lots) @ {fill_price}"
        )
        return {
            "status": "FILLED",
            "order_id": f"paper_{signal_id}",
            "filled_price": fill_price,
            "filled_lots": lots,
            "error": None,
        }

    def close_position(self, position_id: str, reason: str = "MANUAL", current_price: Optional[float] = None) -> Dict[str, Any]:
        logger.info(f"[PaperBroker] 🏁 Position {position_id} closed locally: reason={reason}")
        return {
            "status": "CLOSED",
            "position_id": position_id,
            "exit_price": current_price or 0.0,
            "realized_pnl": 0.0,
            "error": None,
        }

    def get_open_positions(self) -> List[Dict[str, Any]]:
        return signal_store.get_active_signals()

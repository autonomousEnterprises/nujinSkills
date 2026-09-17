"""
server/brokers/base.py
─────────────────────────────────────────────────────────────
Abstract Base Class for Execution Broker & Exchange Adapters.

Enables Nujin to deploy automated execution across any broker, prop firm,
or exchange (e.g. TradeLocker, Binance, Bybit, Interactive Brokers, OANDA)
without modifying strategy logic.
"""

from __future__ import annotations

import abc
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("ExecutionBroker")


class BaseExecutionBroker(abc.ABC):
    """
    Standard interface for all execution adapters.
    """

    def __init__(self, broker_id: str, name: str):
        self.broker_id = broker_id
        self.name = name
        self.is_connected = False

    @property
    def supports_multi_account(self) -> bool:
        """Indicates whether this broker adapter supports concurrent multi-account execution."""
        return False

    def validate_credentials(self, config: Dict[str, Any]) -> tuple[bool, str]:
        """
        Validates a set of credentials without modifying the primary adapter session.
        Returns (is_valid: bool, message_or_error: str).
        """
        return True, "Validation passed"

    @abc.abstractmethod
    def connect(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Initializes connection / session with the broker using credentials.
        Returns True if authenticated successfully.
        """
        pass

    @abc.abstractmethod
    def disconnect(self) -> None:
        """Gracefully terminates active broker session or WebSocket stream."""
        pass

    @abc.abstractmethod
    def get_account_info(self) -> Dict[str, Any]:
        """
        Returns account balance & margin status:
        {
            "balance": float,
            "equity": float,
            "free_margin": float,
            "currency": str,
            "is_demo": bool
        }
        """
        pass

    @abc.abstractmethod
    def execute_order(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes an order on the exchange/broker from a Nujin signal.
        signal schema:
          - action: "BUY" | "SELL" | "LONG" | "SHORT"
          - symbol: str (e.g. "BTC/USDT", "XAUUSD")
          - price: float
          - stop_loss: Optional[float]
          - take_profit: Optional[float]
          - strategy: str

        Returns order confirmation dict:
        {
            "status": "FILLED" | "REJECTED",
            "order_id": str,
            "filled_price": float,
            "filled_lots": float,
            "error": Optional[str]
        }
        """
        pass

    @abc.abstractmethod
    def close_position(self, position_id: str, reason: str = "MANUAL", current_price: Optional[float] = None) -> Dict[str, Any]:
        """
        Closes an open position on the broker.
        Returns confirmation dict:
        {
            "status": "CLOSED" | "FAILED",
            "position_id": str,
            "exit_price": float,
            "realized_pnl": float,
            "error": Optional[str]
        }
        """
        pass

    @abc.abstractmethod
    def get_open_positions(self) -> List[Dict[str, Any]]:
        """Returns list of currently open positions from the broker."""
        pass

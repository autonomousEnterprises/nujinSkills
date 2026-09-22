"""
server/brokers/registry.py
─────────────────────────────────────────────────────────────
BrokerRegistry: Dynamic factory and manager for all execution brokers.
Auto-discovers proprietary and third-party broker adapters across plugins.
"""

from __future__ import annotations

import importlib.util
import logging
import os
import sys
from typing import Dict, Any, List, Optional, Type

from server.brokers.base import BaseExecutionBroker
from server.brokers.paper import PaperExecutionBroker

logger = logging.getLogger("BrokerRegistry")

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class BrokerRegistry:
    """Registry and resolver for execution brokers."""
    _broker_classes: Dict[str, Type[BaseExecutionBroker]] = {
        "paper": PaperExecutionBroker
    }
    _instances: Dict[str, BaseExecutionBroker] = {}
    _plugins_scanned: bool = False

    @classmethod
    def register(cls, broker_id: str, broker_cls: Type[BaseExecutionBroker]) -> None:
        clean_id = broker_id.lower().strip()
        cls._broker_classes[clean_id] = broker_cls
        logger.info(f"[BrokerRegistry] Registered broker adapter: '{clean_id}' -> {broker_cls.__name__}")

    @classmethod
    def scan_plugin_brokers(cls) -> None:
        """
        Discovers broker adapters in plugins/*/brokers/*.py
        """
        if cls._plugins_scanned:
            return

        plugins_dir = os.path.join(_ROOT, "plugins")
        if not os.path.exists(plugins_dir):
            cls._plugins_scanned = True
            return

        for pentry in os.listdir(plugins_dir):
            pdir = os.path.join(plugins_dir, pentry)
            if not os.path.isdir(pdir):
                continue
            bdir = os.path.join(pdir, "brokers")
            if not os.path.exists(bdir) or not os.path.isdir(bdir):
                continue

            for fname in os.listdir(bdir):
                if fname.endswith(".py") and not fname.startswith("__"):
                    fpath = os.path.join(bdir, fname)
                    mod_name = f"nujin_plugin_broker_{pentry}_{fname.replace('.py', '')}"
                    try:
                        spec = importlib.util.spec_from_file_location(mod_name, fpath)
                        if spec and spec.loader:
                            mod = importlib.util.module_from_spec(spec)
                            sys.modules[mod_name] = mod
                            spec.loader.exec_module(mod)
                            logger.info(f"[BrokerRegistry] Loaded plugin broker module: {fname} from {pentry}")
                    except Exception as e:
                        logger.warning(f"[BrokerRegistry] Failed loading plugin broker {fname}: {e}")

        cls._plugins_scanned = True

    @classmethod
    def list_available_brokers(cls) -> List[Dict[str, Any]]:
        cls.scan_plugin_brokers()
        result = []
        for b_id, b_cls in cls._broker_classes.items():
            inst = cls.get_broker(b_id)
            info = inst.get_account_info() if inst else {}
            result.append({
                "broker_id": b_id,
                "name": getattr(inst, "name", b_cls.__name__),
                "is_active": (b_id == cls.get_active_broker_id()),
                "is_pro": b_id != "paper",
                "account_info": info
            })
        return result

    @classmethod
    def get_active_broker_id(cls) -> str:
        env_id = os.environ.get("NUJIN_BROKER", "").lower().strip()
        if env_id:
            return env_id

        # Auto-detect active connected accounts from accounts_store
        try:
            from server.accounts_store import accounts_store
            active_accounts = accounts_store.get_all_active_accounts(decrypt=False)
            if active_accounts:
                for acc in active_accounts:
                    b_id = (acc.get("broker_id") or "").lower().strip()
                    if b_id and b_id != "paper":
                        return b_id
        except Exception as e_acc:
            logger.debug(f"[BrokerRegistry] Account store check note: {e_acc}")

        return "paper"

    @classmethod
    def get_broker(cls, broker_id: Optional[str] = None) -> BaseExecutionBroker:
        cls.scan_plugin_brokers()
        target_id = (broker_id or cls.get_active_broker_id()).lower().strip()

        if target_id not in cls._broker_classes:
            logger.warning(
                f"[BrokerRegistry] Broker '{target_id}' not found. "
                f"Available brokers: {list(cls._broker_classes.keys())}. Falling back to 'paper'."
            )
            target_id = "paper"

        if target_id not in cls._instances:
            broker_cls = cls._broker_classes[target_id]
            inst = broker_cls()
            inst.connect()
            cls._instances[target_id] = inst

        return cls._instances[target_id]


broker_registry = BrokerRegistry

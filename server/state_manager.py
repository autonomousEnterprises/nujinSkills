"""
server/state_manager.py
─────────────────────────────────────────────────────────────
Single Source of Truth for EdgeMiner runtime state.

Consumers:
  • server/main.py          (FastAPI server)
  • server/backtest_engine.py
  • tools/state_control.py  (AI agent CLI)
  • tools/run_backtest_audit.py

All reads/writes go through StateManager and SignalStore.
File locking prevents corruption from concurrent writes.

NO mock/fallback/synthetic data is ever returned.
Empty collections are valid and intentional when no real data exists yet.
"""

from __future__ import annotations

import fcntl
import json
import logging
import math
import os
import time
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("StateManager")

# ─────────────────────────────────────────────────────────────
# Paths (relative to project root, resolved at import time)
# ─────────────────────────────────────────────────────────────
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
STATE_FILE = os.path.join(_ROOT, "data", "state.json")
SIGNALS_FILE = os.path.join(_ROOT, "data", "signals.json")

# ─────────────────────────────────────────────────────────────
# Canonical schema / default state
# ─────────────────────────────────────────────────────────────
DEFAULT_STATE: Dict[str, Any] = {
    "active_strategy": "PropFirmVsaWickRejectionStrategy",
    "target_profile": "Prop Firm Challenge",
    "status": "ACTIVE_DEPLOYED",
    "backtest_summary": {
        "sharpe": 0.0,
        "win_rate": 0.0,
        "max_drawdown": 0.0,
        "mdd_99": 0.0,
        "dsr": 0.0,
        "trades": 0,
        "profit_factor": 0.0,
        "expectancy_bps": 0.0,
    },
    "equity_curve": [],
    "return_distribution": [],
    "regime_breakdown": {},
    "falsification_gates": {},
    "trade_markers": [],
    "trades_detail": [],
    "thesis_props": {},
    "signals_count": 0,
    "last_updated": "",
}


# ─────────────────────────────────────────────────────────────
# Low-level file helpers (with POSIX exclusive locks)
# ─────────────────────────────────────────────────────────────

def _ensure_dir(path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)


def _read_json_locked(path: str, default: Any) -> Any:
    """Read a JSON file under a shared lock. Returns `default` on missing/corrupt."""
    _ensure_dir(path)
    if not os.path.exists(path):
        return deepcopy(default)
    try:
        with open(path, "r") as f:
            fcntl.flock(f, fcntl.LOCK_SH)
            try:
                return json.load(f)
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)
    except Exception as e:
        logger.warning(f"[StateManager] Could not read {path}: {e}")
        return deepcopy(default)


def _write_json_locked(path: str, data: Any) -> None:
    """Write JSON to a file under an exclusive lock (atomic tmp-then-rename)."""
    _ensure_dir(path)
    tmp_path = path + ".tmp"
    try:
        with open(tmp_path, "w") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                json.dump(data, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)
        os.replace(tmp_path, path)   # atomic on POSIX
    except Exception as e:
        logger.error(f"[StateManager] Write failed for {path}: {e}")
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def _deep_merge(base: dict, updates: dict) -> dict:
    """Recursively merge `updates` into `base` (non-destructive copy)."""
    result = deepcopy(base)
    for k, v in updates.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = deepcopy(v)
    return result


# ─────────────────────────────────────────────────────────────
# StateManager
# ─────────────────────────────────────────────────────────────

class StateManager:
    """
    Manages data/state.json.

    Usage (server):
        from server.state_manager import state_manager
        state = state_manager.get()
        state_manager.patch({"status": "STOPPED"})

    Usage (CLI tool):
        from server.state_manager import StateManager
        sm = StateManager()
        print(sm.get())
    """

    def __init__(self, path: str = STATE_FILE):
        self._path = path

    # ── Read ──────────────────────────────────────────────────
    def get(self) -> Dict[str, Any]:
        """Return full current state, merged with DEFAULT_STATE for missing keys."""
        raw = _read_json_locked(self._path, {})
        return _deep_merge(DEFAULT_STATE, raw)

    def get_key(self, dotted_key: str) -> Any:
        """
        Read a single value by dotted key path, e.g. 'backtest_summary.sharpe'.
        Returns None if path not found.
        """
        state = self.get()
        parts = dotted_key.split(".")
        node: Any = state
        for p in parts:
            if isinstance(node, dict) and p in node:
                node = node[p]
            else:
                return None
        return node

    # ── Write ─────────────────────────────────────────────────
    def patch(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep-merge `updates` into current state, stamp last_updated, write, return new state.
        Thread/process-safe via file lock.
        """
        current = self.get()
        updates["last_updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        merged = _deep_merge(current, updates)
        _write_json_locked(self._path, merged)
        logger.info(f"[StateManager] patch applied — keys: {list(updates.keys())}")
        return merged

    def set_full(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Replace state entirely (validates against schema by merging with DEFAULT)."""
        state["last_updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        merged = _deep_merge(DEFAULT_STATE, state)
        _write_json_locked(self._path, merged)
        logger.info(f"[StateManager] full state written for strategy: {state.get('active_strategy')}")
        return merged

    def reset(self) -> Dict[str, Any]:
        """Reset state to DEFAULT_STATE."""
        state = deepcopy(DEFAULT_STATE)
        state["last_updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        _write_json_locked(self._path, state)
        logger.info("[StateManager] state reset to DEFAULT")
        return state


# ─────────────────────────────────────────────────────────────
# SignalStore
# ─────────────────────────────────────────────────────────────

class SignalStore:
    """
    Manages data/signals.json.

    Usage:
        from server.state_manager import signal_store
        signal_store.add({"action": "BUY", "price": 63404, ...})
        all_sigs = signal_store.get_all()
        stats     = signal_store.get_stats()

    Returns empty list [] when no real signals have been recorded yet.
    Never returns mock or fallback data.
    """

    def __init__(self, path: str = SIGNALS_FILE):
        self._path = path

    def get_all(self) -> List[Dict[str, Any]]:
        """Return all real signals from disk. Returns [] if no signals yet — never fake data."""
        return _read_json_locked(self._path, [])

    def get_active(self) -> Optional[Dict[str, Any]]:
        """Return the current ACTIVE_IN_POSITION signal, or None if no real signals exist."""
        signals = self.get_all()
        return next((s for s in signals if s.get("status") == "ACTIVE_IN_POSITION"), None)

    def add(self, signal: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Prepend a new real signal, auto-assign id, write, return all signals."""
        signals = self.get_all()
        new_id = (signals[0]["id"] + 1) if signals else 1
        entry = {
            "id": new_id,
            "time": signal.get("time", int(time.time())),
            "pair": signal.get("pair", "BTC/USDT"),
            "action": signal.get("action", "BUY"),
            "price": float(signal.get("price", 0.0)),
            "stop_loss": float(signal.get("stop_loss", signal.get("price", 0.0) * 0.975)),
            "take_profit": float(signal.get("take_profit", signal.get("price", 0.0) * 1.04)),
            "status": signal.get("status", "ACTIVE_IN_POSITION"),
            "exit_price": signal.get("exit_price"),
            "exit_reason": signal.get("exit_reason"),
            "pnl_pct": float(signal.get("pnl_pct", 0.0)),
            "annotation": signal.get("annotation", "AI Live Signal"),
            "reasoning_md": signal.get("reasoning_md", ""),
            "strategy": signal.get("strategy", "PropFirmVsaWickRejectionStrategy"),
        }
        updated = [entry] + real_signals
        _write_json_locked(self._path, updated)
        # Also bump signals_count in state.json
        state_manager.patch({"signals_count": len(updated)})
        logger.info(f"[SignalStore] Signal #{new_id} added: {entry['action']} @ {entry['price']}")
        return updated

    def get_stats(self) -> Dict[str, Any]:
        """
        Compute live performance stats from closed signals.
        Returns win_rate, profit_factor, sharpe_live, total_pnl_pct, etc.
        """
        signals = self.get_all()
        closed = [
            s for s in signals
            if s.get("exit_reason") and s.get("pnl_pct") is not None
        ]
        open_trades = [s for s in signals if s.get("status") == "ACTIVE_IN_POSITION"]

        total = len(closed)
        wins = [s for s in closed if s.get("pnl_pct", 0) > 0]
        losses = [s for s in closed if s.get("pnl_pct", 0) <= 0]

        win_rate = len(wins) / total if total > 0 else 0.0
        gross_profit = sum(s.get("pnl_pct", 0) for s in wins)
        gross_loss = abs(sum(s.get("pnl_pct", 0) for s in losses))
        profit_factor = (
            round(gross_profit / gross_loss, 2) if gross_loss > 0
            else (99.0 if gross_profit > 0 else 0.0)
        )
        total_pnl = round(sum(s.get("pnl_pct", 0) for s in closed), 2)

        # Annualized Sharpe from trade returns
        returns = [s.get("pnl_pct", 0) for s in closed]
        if len(returns) > 1:
            mean_r = sum(returns) / len(returns)
            std_r = math.sqrt(
                sum((r - mean_r) ** 2 for r in returns) / len(returns)
            ) or 1e-8
            sharpe_live = round((mean_r / std_r) * math.sqrt(252), 2)
        else:
            sharpe_live = 0.0

        # Max consecutive losses
        max_consec = cur = 0
        for s in closed:
            if s.get("pnl_pct", 0) <= 0:
                cur += 1
                max_consec = max(max_consec, cur)
            else:
                cur = 0

        return {
            "total_trades": total,
            "open_trades": len(open_trades),
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": round(win_rate, 4),
            "profit_factor": profit_factor,
            "sharpe_live": sharpe_live,
            "total_pnl_pct": total_pnl,
            "avg_win_pct": round(gross_profit / len(wins), 2) if wins else 0.0,
            "avg_loss_pct": round(gross_loss / len(losses), 2) if losses else 0.0,
            "gross_profit_pct": round(gross_profit, 2),
            "gross_loss_pct": round(gross_loss, 2),
            "max_consecutive_losses": max_consec,
        }


# ─────────────────────────────────────────────────────────────
# Module-level singletons — import these everywhere
# ─────────────────────────────────────────────────────────────
state_manager = StateManager()
signal_store = SignalStore()

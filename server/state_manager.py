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
import re
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
STRATEGIES_FILE = os.path.join(_ROOT, "data", "strategies.json")
STRATEGIES_DIR = os.path.join(_ROOT, "strategies")

try:
    from server.plugin_loader import plugin_manager
except ImportError:
    plugin_manager = None

# ─────────────────────────────────────────────────────────────
# Canonical schema / default state
# ─────────────────────────────────────────────────────────────
DEFAULT_STATE: Dict[str, Any] = {
    "active_strategy": "",
    "target_profile": "Autonomous Alpha Model",
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

def _now_local_iso() -> str:
    """Returns ISO 8601 string in the local machine's timezone."""
    return datetime.now().astimezone().isoformat()


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
    tmp_path = f"{path}.{os.getpid()}.{time.time_ns()}.tmp"
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
            try:
                os.remove(tmp_path)
            except Exception:
                pass
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
        updates["last_updated"] = _now_local_iso()
        merged = _deep_merge(current, updates)
        _write_json_locked(self._path, merged)
        logger.info(f"[StateManager] patch applied — keys: {list(updates.keys())}")
        return merged

    def set_full(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Replace state entirely (validates against schema by merging with DEFAULT)."""
        state["last_updated"] = _now_local_iso()
        merged = _deep_merge(DEFAULT_STATE, state)
        _write_json_locked(self._path, merged)
        logger.info(f"[StateManager] full state written for strategy: {state.get('active_strategy')}")
        return merged

    def reset(self) -> Dict[str, Any]:
        """Reset state to DEFAULT_STATE."""
        state = deepcopy(DEFAULT_STATE)
        state["last_updated"] = _now_local_iso()
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
        signal_store.add({"action": "BUY", "price": 63404, "strategy": "GoatFundedTraderXauusdScalper"})
        all_sigs = signal_store.get_all()
        stats     = signal_store.get_stats()

    Returns empty list [] when no real signals have been recorded yet.
    Never returns mock or fallback data.
    """

    def __init__(self, path: str = SIGNALS_FILE):
        self._path = path

    def get_all(self, strategy: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return all real signals from disk, optionally filtered by strategy name."""
        signals = _read_json_locked(self._path, [])
        if strategy and strategy != "ALL":
            clean = strategy.replace(".py", "").lower()
            return [s for s in signals if s.get("strategy", "").replace(".py", "").lower() == clean]
        return signals

    def get_active(self, strategy: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Return the current ACTIVE_IN_POSITION signal for a strategy or the first open position."""
        signals = self.get_all(strategy)
        return next((s for s in signals if s.get("status") == "ACTIVE_IN_POSITION"), None)

    def get_active_signals(self) -> List[Dict[str, Any]]:
        """Return all signals currently marked ACTIVE_IN_POSITION across all strategies."""
        signals = self.get_all()
        return [s for s in signals if s.get("status") == "ACTIVE_IN_POSITION"]

    def add(self, signal: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Prepend a new real signal, auto-assign id, write, return all signals."""
        signals = self.get_all()
        new_id = (signals[0]["id"] + 1) if signals else 1

        # Detect strategy and pair intelligently if missing
        strat = signal.get("strategy")
        if not strat:
            strat = strategy_registry.get_active_strategy_name()
        clean_strat = strat.replace(".py", "")

        pair = signal.get("pair")
        if not pair:
            lower = clean_strat.lower()
            if "xau" in lower or "gold" in lower or "goat" in lower:
                pair = "XAU/USD"
            elif "eth" in lower:
                pair = "ETH/USDT"
            elif "sol" in lower:
                pair = "SOL/USDT"
            else:
                pair = "BTC/USDT"

        price = float(signal.get("price") or signal.get("entry_price") or 0.0)
        action = (signal.get("action") or signal.get("side") or "BUY").upper()
        if action in ["LONG", "BUY"]:
            action = "BUY"
            default_sl = price * 0.985 if "XAU" in pair else price * 0.975
            default_tp = price * 1.025 if "XAU" in pair else price * 1.04
        else:
            action = "SELL"
            default_sl = price * 1.015 if "XAU" in pair else price * 1.025
            default_tp = price * 0.975 if "XAU" in pair else price * 0.96

        entry = {
            "id": new_id,
            "time": int(signal.get("time") or time.time()),
            "pair": pair,
            "action": action,
            "side": "LONG" if action == "BUY" else "SHORT",
            "price": price,
            "entry_price": price,
            "stop_loss": float(signal.get("stop_loss") or default_sl),
            "take_profit": float(signal.get("take_profit") or default_tp),
            "lots": float(signal.get("lots") or signal.get("lot_size") or 0.10),
            "lot_size": float(signal.get("lots") or signal.get("lot_size") or 0.10),
            "status": signal.get("status", "ACTIVE_IN_POSITION"),
            "exit_price": signal.get("exit_price"),
            "exit_reason": signal.get("exit_reason"),
            "pnl_pct": float(signal.get("pnl_pct", 0.0)),
            "annotation": signal.get("annotation", "AI Live Signal"),
            "reasoning_md": signal.get("reasoning_md", ""),
            "strategy": clean_strat,
        }
        updated = [entry] + signals
        _write_json_locked(self._path, updated)
        # Also bump signals_count in state.json
        state_manager.patch({"signals_count": len(updated)})
        logger.info(f"[SignalStore] Signal #{new_id} added: {entry['action']} {entry['pair']} ({clean_strat}) @ {entry['price']}")
        return updated

    def close_position(
        self,
        signal_id: Optional[int] = None,
        strategy: Optional[str] = None,
        exit_price: float = 0.0,
        exit_reason: str = "MANUAL_CLOSE",
        pnl_pct: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """Close an active position by ID or latest open position for a strategy."""
        signals = self.get_all()
        target = None
        for s in signals:
            if s.get("status") == "ACTIVE_IN_POSITION":
                if signal_id is not None and s.get("id") == signal_id:
                    target = s
                    break
                elif strategy is not None and s.get("strategy", "").replace(".py", "").lower() == strategy.replace(".py", "").lower():
                    target = s
                    break
                elif signal_id is None and strategy is None:
                    target = s
                    break

        if not target:
            return None

        target["status"] = "CLOSED"
        target["exit_price"] = exit_price
        target["exit_reason"] = exit_reason
        target["exit_time"] = int(time.time())
        if pnl_pct is not None:
            target["pnl_pct"] = round(pnl_pct, 2)
        elif exit_price > 0 and target.get("price", 0) > 0:
            entry_p = target["price"]
            is_long = target.get("action") == "BUY" or target.get("side") == "LONG"
            raw_pnl = ((exit_price - entry_p) / entry_p * 100) if is_long else ((entry_p - exit_price) / entry_p * 100)
            target["pnl_pct"] = round(raw_pnl, 2)

        _write_json_locked(self._path, signals)
        logger.info(f"[SignalStore] Position #{target['id']} closed for {target['strategy']}: exit {exit_price}, pnl {target['pnl_pct']}%")
        return target

    def update_signal(self, signal_id: int, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        signals = self.get_all()
        for s in signals:
            if s.get("id") == signal_id:
                s.update(updates)
                _write_json_locked(self._path, signals)
                return s
        return None

    def clear(self, strategy: Optional[str] = None) -> List[Dict[str, Any]]:
        """Clears signals from disk. If strategy specified, only clears signals for that strategy."""
        if strategy and strategy != "ALL":
            clean = strategy.replace(".py", "").lower()
            all_sigs = self.get_all()
            remaining = [s for s in all_sigs if s.get("strategy", "").replace(".py", "").lower() != clean]
            _write_json_locked(self._path, remaining)
            state_manager.patch({"signals_count": len(remaining)})
            logger.info(f"[SignalStore] Signals cleared for strategy '{strategy}'. Remaining: {len(remaining)}")
            return remaining
        _write_json_locked(self._path, [])
        state_manager.patch({"signals_count": 0})
        logger.info("[SignalStore] All signals cleared.")
        return []

    def get_stats(self, strategy: Optional[str] = None) -> Dict[str, Any]:
        """
        Compute live performance stats from closed signals.
        Returns win_rate, profit_factor, sharpe_live, total_pnl_pct, etc.
        If strategy is None, also returns a per-strategy breakdown in 'by_strategy'.
        """
        signals = self.get_all(strategy)
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

        res = {
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

        # If overall stats requested, compute breakdown per strategy
        if not strategy or strategy == "ALL":
            all_raw = self.get_all()
            strats_seen = set(s.get("strategy", "Unknown") for s in all_raw if s.get("strategy"))
            by_strat = {}
            for strat_name in strats_seen:
                by_strat[strat_name] = self.get_stats(strat_name)
            res["by_strategy"] = by_strat

        return res


# ─────────────────────────────────────────────────────────────
# StrategyRegistry
# ─────────────────────────────────────────────────────────────
# StrategyRegistry
# ─────────────────────────────────────────────────────────────

class StrategyRegistry:
    """
    Manages data/strategies.json.
    Single Source of Truth for strategy records, lifecycle states, cron tracking,
    ranking scores, and backtest drift histories.

    Lifecycle statuses:
      • ACTIVE_LIVE    - Active trading/paper-trading bot execution
      • CRON_BACKTEST  - Monitored periodically via cron backtests to track drift
      • DEACTIVATED    - Inactive / archived strategy
    """

    def __init__(self, path: str = STRATEGIES_FILE, strategies_dir: str = STRATEGIES_DIR):
        self._path = path
        self._dir = strategies_dir

    def _read_raw(self) -> List[Dict[str, Any]]:
        return _read_json_locked(self._path, [])

    def _write_raw(self, data: List[Dict[str, Any]]) -> None:
        _write_json_locked(self._path, data)

    def get_active_strategy_name(self) -> str:
        """
        Dynamically resolves the active strategy.
        Checks current system state. If valid and existing on disk, returns it.
        Otherwise falls back to the #1 ranked strategy on disk.
        If no strategies exist on disk, returns ''.
        Never hardcodes any strategy name.
        """
        curr = state_manager.get().get("active_strategy", "")
        clean = curr.replace(".py", "").strip()
        if clean:
            # Check core or plugin paths
            if os.path.exists(os.path.join(self._dir, f"{clean}.py")):
                return clean
            if plugin_manager and plugin_manager.resolve_strategy_path(clean):
                return clean

        # Check ranked list in memory/disk
        raw = self._read_raw()
        for s in raw:
            s_name = s.get("name", "")
            s_file = s.get("file", "")
            if os.path.exists(os.path.join(self._dir, s_file)):
                top_name = s.get("name", s_file.replace(".py", ""))
                state_manager.patch({"active_strategy": top_name})
                return top_name
            if plugin_manager and plugin_manager.resolve_strategy_path(s_name):
                state_manager.patch({"active_strategy": s_name})
                return s_name

        # Fallback to #1 ranked strategy from core strategies directory
        py_files = sorted([f for f in os.listdir(self._dir) if f.endswith(".py")]) if os.path.exists(self._dir) else []
        if py_files:
            top_name = py_files[0].replace(".py", "")
            state_manager.patch({"active_strategy": top_name})
            return top_name

        # Fallback to plugin strategy if available
        if plugin_manager:
            plugin_strats = plugin_manager.get_plugin_strategy_files()
            if plugin_strats:
                top_name = plugin_strats[0]["strategy_name"]
                state_manager.patch({"active_strategy": top_name})
                return top_name

        return ""

    def remove_strategy(self, strategy_name: str) -> bool:
        """
        Safely removes a strategy from disk (if core) and synchronizes registry.
        If the strategy is in a plugin, it warns or safely unlinks.
        """
        clean = strategy_name.replace(".py", "").strip()
        py_path = os.path.join(self._dir, f"{clean}.py")
        pine_path = os.path.join(self._dir, f"{clean}.pine")
        removed = False
        if os.path.exists(py_path):
            try:
                os.remove(py_path)
                removed = True
            except Exception as e:
                logger.error(f"[StrategyRegistry] Error removing {py_path}: {e}")
        if os.path.exists(pine_path):
            try:
                os.remove(pine_path)
                removed = True
            except Exception as e:
                logger.error(f"[StrategyRegistry] Error removing {pine_path}: {e}")

        if not removed and plugin_manager:
            p_path = plugin_manager.resolve_strategy_path(clean)
            if p_path and os.path.exists(p_path):
                try:
                    os.remove(p_path)
                    removed = True
                except Exception as e:
                    logger.error(f"[StrategyRegistry] Error removing plugin strategy {p_path}: {e}")

        # Resync filesystem and rankings
        self.sync_with_filesystem()

        # If deleted strategy was the active strategy, auto-switch to top remaining
        curr_active = state_manager.get().get("active_strategy", "").replace(".py", "")
        if curr_active == clean:
            new_active = self.get_active_strategy_name()
            state_manager.patch({"active_strategy": new_active})

        return removed

    def _infer_metadata(self, filename: str, filepath_override: Optional[str] = None) -> Dict[str, Any]:
        """
        Dynamically extracts all strategy metadata from any Python file.
        Parses header comments, docstrings, and class variables.
        Zero hardcoded catalogs or static dictionary lookups.
        """
        clean = filename.replace(".py", "")
        filepath = filepath_override or os.path.join(self._dir, filename)

        thesis = ""
        symbol = ""
        timeframe = ""
        target_profile = ""
        display_name = ""

        # Parse from file content if it exists
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read(8192)
                    for line in content.splitlines():
                        line_s = line.strip()
                        if line_s.startswith("# Strategy:"):
                            raw_strat = line_s.replace("# Strategy:", "").strip()
                            match = re.search(r'\((.*?)\)', raw_strat)
                            if match:
                                display_name = match.group(1).strip()
                            elif raw_strat:
                                display_name = raw_strat
                        elif line_s.startswith("# Display Name:") or line_s.startswith("# Name:"):
                            display_name = line_s.split(":", 1)[1].strip()
                        elif line_s.startswith("# Thesis:"):
                            thesis = line_s.replace("# Thesis:", "").strip()
                        elif line_s.startswith("# Target Profile:") or line_s.startswith("# Target Prop Firm:"):
                            target_profile = line_s.split(":", 1)[1].strip()
                        elif line_s.startswith("# Asset:") or line_s.startswith("# Symbol:"):
                            sym = line_s.split(":", 1)[1].strip()
                            if "XAU" in sym.upper() or "GOLD" in sym.upper():
                                symbol = "XAU/USD"
                            elif "SP" in sym.upper() or "ES" in sym.upper():
                                symbol = "S&P 500 (ES)"
                            elif "MNQ" in sym.upper() or "NQ" in sym.upper():
                                symbol = "MNQ (Futures)"
                            elif "BTC" in sym.upper():
                                symbol = "BTC/USDT"
                            elif "ETH" in sym.upper():
                                symbol = "ETH/USDT"
                            elif "SOL" in sym.upper():
                                symbol = "SOL/USDT"
                            else:
                                symbol = sym
                        elif "timeframe =" in line_s or "timeframe=" in line_s:
                            tf = line_s.split("=")[-1].strip().strip("'\"")
                            if tf:
                                timeframe = tf
                        elif "symbol =" in line_s or "symbol=" in line_s:
                            sym = line_s.split("=")[-1].strip().strip("'\"")
                            if sym:
                                symbol = sym

                    # Docstring inspection fallback for thesis & display_name
                    if not thesis or not display_name:
                        doc_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
                        if doc_match:
                            doc_text = doc_match.group(1).strip()
                            doc_lines = [d.strip() for d in doc_text.splitlines() if d.strip()]
                            if doc_lines:
                                if not display_name and not doc_lines[0].lower().startswith("quantitative"):
                                    display_name = doc_lines[0]
                                if not thesis:
                                    # Use docstring text excluding header
                                    rationale = " ".join(doc_lines[1:]) if len(doc_lines) > 1 else doc_lines[0]
                                    thesis = rationale[:200]
            except Exception as e:
                logger.debug(f"[StrategyRegistry] Metadata extract error for {filename}: {e}")

        # Humanize filename cleanly
        humanized_name = re.sub(r'([A-Z]+)', r' \1', clean).replace('_', ' ').strip()
        humanized_name = re.sub(r'\s+', ' ', humanized_name)

        if not display_name:
            display_name = humanized_name

        if not symbol:
            clean_up = clean.upper()
            if any(k in clean_up for k in ["SP500", "SPX", "ES", "FLUSH"]):
                symbol = "S&P 500 (ES)"
            elif any(k in clean_up for k in ["XAU", "GOLD"]):
                symbol = "XAU/USD"
            elif any(k in clean_up for k in ["MNQ", "NQ"]):
                symbol = "MNQ (Futures)"
            elif any(k in clean_up for k in ["ETH"]):
                symbol = "ETH/USDT"
            elif any(k in clean_up for k in ["SOL"]):
                symbol = "SOL/USDT"
            else:
                symbol = "BTC/USDT"

        if not timeframe:
            timeframe = "1m" if any(k in symbol.upper() for k in ["XAU", "SP", "ES", "S&P"]) else "15m"

        if not target_profile:
            target_profile = f"{display_name} (Alpha Engine)"

        if not thesis:
            thesis = f"Autonomous Alpha Model: {display_name}"

        return {
            "display_name": display_name,
            "target_profile": target_profile,
            "thesis": thesis,
            "symbol": symbol,
            "timeframe": timeframe,
        }

    def _calculate_score_and_breakdown(self, strat: Dict[str, Any]) -> Dict[str, Any]:
        """
        Multi-pillar quantitative scoring and tier classification model.
        Evaluates strategies across 4 orthogonal dimensions:
          1. Edge Strength (35%): Net Annualized Sharpe (net of friction), Profit Factor, Expectancy
          2. Statistical Robustness & Falsification (30%): Deflated Sharpe Ratio (DSR), Sample Count, Cynic Gates
          3. Capital Preservation & Downside Risk (25%): Max Drawdown curve, Win Rate consistency
          4. Drift Stability & Out-of-Sample Performance (10%): Snapshot trajectory over time
        """
        summary = strat.get("latest_backtest", {})
        gates = strat.get("falsification_gates", {})
        if not summary or summary.get("trades", 0) == 0:
            return {
                "ranking_score": 0.0,
                "tier": "C-Tier (Sub-Hurdle)",
                "ranking_breakdown": {
                    "edge_score": 0.0,
                    "robustness_score": 0.0,
                    "risk_score": 0.0,
                    "drift_score": 50.0,
                    "composite_score": 0.0,
                    "gates_passed": 0,
                    "gates_total": 5,
                    "tier_reason": "No backtest trades recorded"
                }
            }

        sharpe = max(0.0, float(summary.get("sharpe", 0.0)))
        dsr = max(0.0, float(summary.get("dsr") if summary.get("dsr") is not None else gates.get("gate_1_dsr", {}).get("dsr", 0.0)))
        raw_wr = float(summary.get("win_rate", 0.0))
        win_rate = raw_wr / 100.0 if raw_wr > 1.0 else raw_wr
        profit_factor = max(0.0, float(summary.get("profit_factor", 0.0)))
        max_dd = max(0.0, float(summary.get("max_drawdown", 0.0)))
        trades = max(0, int(summary.get("trades", 0)))
        exp_bps = float(summary.get("expectancy_bps", 0.0))

        # ── 1. Edge Strength Score (0 to 100) - Weight 35% ──
        # Net Sharpe (Hurdle: 1.80, Benchmark: 3.50)
        if sharpe <= 0:
            sh_pts = 0.0
        elif sharpe < 1.8:
            sh_pts = (sharpe / 1.8) * 25.0
        elif sharpe <= 3.5:
            sh_pts = 25.0 + ((sharpe - 1.8) / 1.7) * 25.0
        else:
            sh_pts = 50.0

        # Profit Factor (Hurdle: 1.30, Benchmark: 2.00)
        if profit_factor <= 1.0:
            pf_pts = 0.0
        elif profit_factor < 1.3:
            pf_pts = ((profit_factor - 1.0) / 0.3) * 12.0
        elif profit_factor <= 2.0:
            pf_pts = 12.0 + ((profit_factor - 1.3) / 0.7) * 18.0
        else:
            pf_pts = 30.0

        # Expectancy & Friction Coverage (max 20 pts)
        if exp_bps >= 14.0 or (profit_factor >= 1.6 and win_rate >= 0.50):
            exp_pts = 20.0
        elif exp_bps > 0:
            exp_pts = min(20.0, (exp_bps / 14.0) * 20.0)
        else:
            exp_pts = max(0.0, min(20.0, win_rate * profit_factor * 15.0))
        edge_score = round(min(100.0, sh_pts + pf_pts + exp_pts), 1)

        # ── 2. Statistical Robustness & Falsification (0 to 100) - Weight 30% ──
        # Deflated Sharpe Ratio (DSR) (max 50 pts)
        if dsr >= 0.95:
            dsr_pts = 50.0
        elif dsr >= 0.90:
            dsr_pts = 35.0
        elif dsr >= 0.80:
            dsr_pts = 20.0
        elif dsr >= 0.50:
            dsr_pts = 10.0
        else:
            dsr_pts = 5.0

        # Sample Size Significance (max 30 pts)
        if trades >= 60:
            n_pts = 30.0
        elif trades >= 30:
            n_pts = 20.0
        elif trades >= 15:
            n_pts = 10.0
        else:
            n_pts = 3.0

        # 5-Gate Cynic Audit Verification (max 20 pts)
        g1 = 1 if sharpe >= 1.8 else 0
        g2 = 1 if max_dd <= 0.030 else 0
        g3 = 1 if (trades >= 30 and win_rate >= 0.50) else 0
        g4 = 1 if profit_factor >= 1.3 else 0
        g5 = 1 if dsr >= 0.95 else 0
        gates_passed = g1 + g2 + g3 + g4 + g5
        gates_pts = (gates_passed / 5.0) * 20.0
        robustness_score = round(min(100.0, dsr_pts + n_pts + gates_pts), 1)

        # ── 3. Capital Preservation & Risk (0 to 100) - Weight 25% ──
        # Max Drawdown (Gate <= 3.0%, Scalper Elite <= 1.0%)
        if max_dd <= 0.01:
            dd_pts = 60.0
        elif max_dd <= 0.030:
            dd_pts = 60.0 - ((max_dd - 0.01) / 0.020) * 25.0
        elif max_dd <= 0.06:
            dd_pts = max(5.0, 35.0 - ((max_dd - 0.030) / 0.030) * 30.0)
        else:
            dd_pts = 0.0

        # Win Rate Consistency (max 40 pts)
        if win_rate >= 0.60:
            wr_pts = 40.0
        elif win_rate >= 0.50:
            wr_pts = 25.0 + ((win_rate - 0.50) / 0.10) * 15.0
        elif win_rate >= 0.40:
            wr_pts = 15.0
        else:
            wr_pts = max(0.0, win_rate * 25.0)
        risk_score = round(min(100.0, dd_pts + wr_pts), 1)

        # ── 4. Drift Stability & Trajectory (0 to 100) - Weight 10% ──
        hist = strat.get("cron_config", {}).get("drift_history", [])
        if len(hist) >= 2:
            d_sh = float(hist[-1].get("sharpe", 0.0)) - float(hist[0].get("sharpe", 0.0))
            if d_sh >= 0.05:
                drift_score = 100.0
            elif d_sh >= -0.10:
                drift_score = 85.0
            elif d_sh >= -0.25:
                drift_score = 60.0
            else:
                drift_score = 25.0
        else:
            drift_score = 75.0

        composite_score = round(
            0.35 * edge_score + 0.30 * robustness_score + 0.25 * risk_score + 0.10 * drift_score,
            1
        )

        # ── Institutional Tier Determination ──
        is_s = (
            composite_score >= 80.0 and
            sharpe >= 2.5 and
            dsr >= 0.95 and
            max_dd <= 0.030 and
            win_rate >= 0.50 and
            profit_factor >= 1.5 and
            trades >= 25
        )
        is_a = (
            composite_score >= 65.0 and
            sharpe >= 1.8 and
            dsr >= 0.90 and
            max_dd <= 0.04 and
            profit_factor >= 1.3 and
            trades >= 20
        )

        if is_s:
            tier = "S-Tier (Superior Edge)"
            tier_reason = f"Elite Production Alpha: {gates_passed}/5 Gates Passed, DSR {dsr:.2f} >= 0.95, Sharpe {sharpe:.2f}"
        elif is_a:
            tier = "A-Tier (Robust Edge)"
            tier_reason = f"Production Edge: {gates_passed}/5 Gates Passed, DSR {dsr:.2f}, Sharpe {sharpe:.2f}"
        elif composite_score >= 45.0:
            tier = "B-Tier (Incubation Alpha)"
            reasons = []
            if dsr < 0.90:
                reasons.append(f"DSR {dsr:.2f} < 0.90")
            if win_rate < 0.50:
                reasons.append(f"WinRate {win_rate*100:.1f}% < 50%")
            if trades < 30:
                reasons.append(f"Trades {trades} < 30")
            tier_reason = f"Incubation: {gates_passed}/5 Gates. Pending: {', '.join(reasons) or 'Further OOS Data'}"
        else:
            tier = "C-Tier (Sub-Hurdle)"
            reasons = []
            if sharpe < 1.2:
                reasons.append(f"Low Sharpe ({sharpe:.2f})")
            if max_dd > 0.030:
                reasons.append(f"High Drawdown ({max_dd*100:.1f}%)")
            if profit_factor < 1.1:
                reasons.append(f"Low PF ({profit_factor:.2f})")
            tier_reason = f"Sub-Hurdle: {gates_passed}/5 Gates. {', '.join(reasons) or 'Fails Core Gates'}"

        return {
            "ranking_score": composite_score,
            "tier": tier,
            "ranking_breakdown": {
                "edge_score": edge_score,
                "robustness_score": robustness_score,
                "risk_score": risk_score,
                "drift_score": drift_score,
                "composite_score": composite_score,
                "gates_passed": gates_passed,
                "gates_total": 5,
                "tier_reason": tier_reason,
            }
        }

    def calculate_rankings(self, strategies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        for strat in strategies:
            meta = self._calculate_score_and_breakdown(strat)
            strat["ranking_score"] = meta["ranking_score"]
            strat["tier"] = meta["tier"]
            strat["ranking_breakdown"] = meta["ranking_breakdown"]

        # Sort descending by ranking_score
        strategies.sort(key=lambda s: s.get("ranking_score", 0.0), reverse=True)
        for idx, strat in enumerate(strategies, start=1):
            strat["rank"] = idx
        return strategies

    def recalculate_and_save(self) -> List[Dict[str, Any]]:
        """Recalculates multi-factor quantitative rankings across all strategies and saves to disk."""
        strategies = self.get_all(sync=False)
        ranked = self.calculate_rankings(strategies)
        self._write_raw(ranked)
        return ranked

    def sync_with_filesystem(self) -> List[Dict[str, Any]]:
        """Syncs data/strategies.json with files in strategies/*.py, installed plugins, and active state."""
        existing = {s["file"]: s for s in self._read_raw() if "file" in s}
        active_strat = self.get_active_strategy_name()
        clean_active = active_strat.replace(".py", "")

        os.makedirs(self._dir, exist_ok=True)
        # Collect core strategy files
        strategy_candidates = []
        for f in sorted(os.listdir(self._dir)):
            if f.endswith(".py"):
                strategy_candidates.append({
                    "filename": f,
                    "filepath": os.path.join(self._dir, f),
                    "path_rel": f"strategies/{f}",
                    "is_pro": False,
                    "plugin_id": None,
                    "plugin_name": None,
                })

        # Collect plugin strategy files
        if plugin_manager:
            for pfile in plugin_manager.get_plugin_strategy_files():
                rel_p = os.path.relpath(pfile["path"], _ROOT)
                strategy_candidates.append({
                    "filename": pfile["filename"],
                    "filepath": pfile["path"],
                    "path_rel": rel_p,
                    "is_pro": pfile.get("is_pro", True),
                    "plugin_id": pfile.get("plugin_id"),
                    "plugin_name": pfile.get("plugin_name"),
                })

        now_iso = _now_local_iso()
        updated_list: List[Dict[str, Any]] = []

        for candidate in strategy_candidates:
            py_file = candidate["filename"]
            clean_name = py_file.replace(".py", "")
            meta = self._infer_metadata(py_file, filepath_override=candidate["filepath"])
            is_active_sys = (clean_name == clean_active)

            if py_file in existing:
                item = existing[py_file]
                item["path"] = candidate["path_rel"]
                item["is_pro"] = candidate["is_pro"]
                if candidate.get("plugin_name"):
                    item["plugin_name"] = candidate["plugin_name"]
                if candidate.get("plugin_id"):
                    item["plugin_id"] = candidate["plugin_id"]

                # If system active strategy matches, sync status
                if is_active_sys and item.get("status") != "ACTIVE_LIVE":
                    item["status"] = "ACTIVE_LIVE"
                # Update display_name, thesis if available from file
                if meta.get("thesis") and meta["thesis"] != "AI Discovered Strategy":
                    item["thesis"] = meta["thesis"]
                if meta.get("display_name"):
                    item["display_name"] = meta["display_name"]
                if meta.get("target_profile"):
                    item["target_profile"] = meta["target_profile"]
                if meta.get("symbol"):
                    item["symbol"] = meta["symbol"]
                if meta.get("timeframe"):
                    item["timeframe"] = meta["timeframe"]

                cron_cfg = item.setdefault("cron_config", {
                    "enabled": (item.get("status") == "CRON_BACKTEST"),
                    "interval": "24h",
                    "last_run": "",
                    "drift_history": [],
                })
                if not cron_cfg.get("drift_history") and item.get("latest_backtest", {}).get("sharpe", 0) > 0:
                    bt = item["latest_backtest"]
                    cron_cfg["drift_history"] = [{
                        "timestamp": bt.get("last_run") or now_iso,
                        "sharpe": bt.get("sharpe", 0.0),
                        "dsr": bt.get("dsr", 0.0),
                        "win_rate": bt.get("win_rate", 0.0),
                        "max_drawdown": bt.get("max_drawdown", 0.0),
                        "trades": bt.get("trades", 0),
                        "profit_factor": bt.get("profit_factor", 0.0),
                    }]

                # Ensure time_period is populated from backtest equity curve if missing
                if not item.get("time_period") or not item.get("latest_backtest", {}).get("period_label"):
                    eq = item.get("backtest_equity_curve", [])
                    if eq and len(eq) >= 2:
                        t0 = eq[0].get("time", 0)
                        t1 = eq[-1].get("time", 0)
                        if t0 and t1 and t0 > 1000000000:
                            dt0 = datetime.fromtimestamp(t0, tz=timezone.utc)
                            dt1 = datetime.fromtimestamp(t1, tz=timezone.utc)
                            days = round((t1 - t0) / 86400, 1)
                            lbl = f"{dt0.strftime('%Y-%m-%d')} → {dt1.strftime('%Y-%m-%d')} ({days:.1f}d)"
                            item["time_period"] = {
                                "start_time": t0,
                                "end_time": t1,
                                "start_date": dt0.strftime("%Y-%m-%d %H:%M UTC"),
                                "end_date": dt1.strftime("%Y-%m-%d %H:%M UTC"),
                                "duration_days": days,
                                "period_label": lbl,
                            }
                            if "latest_backtest" in item:
                                item["latest_backtest"]["period_label"] = lbl
                                item["latest_backtest"]["duration_days"] = days
                                item["latest_backtest"]["start_date"] = dt0.strftime("%Y-%m-%d")
                                item["latest_backtest"]["end_date"] = dt1.strftime("%Y-%m-%d")

                updated_list.append(item)
            else:
                # Initialize new strategy record
                default_status = "ACTIVE_LIVE" if is_active_sys else "CRON_BACKTEST"
                record = {
                    "id": py_file,
                    "name": clean_name,
                    "file": py_file,
                    "path": candidate["path_rel"],
                    "is_pro": candidate["is_pro"],
                    "plugin_id": candidate.get("plugin_id"),
                    "plugin_name": candidate.get("plugin_name"),
                    "display_name": meta["display_name"],
                    "target_profile": meta["target_profile"],
                    "thesis": meta["thesis"],
                    "symbol": meta["symbol"],
                    "timeframe": meta["timeframe"],
                    "status": default_status,
                    "rank": 99,
                    "ranking_score": 0.0,
                    "tier": "PRO-Tier" if candidate["is_pro"] else "C-Tier (Sub-Hurdle)",
                    "latest_backtest": {
                        "sharpe": 0.0,
                        "win_rate": 0.0,
                        "profit_factor": 0.0,
                        "max_drawdown": 0.0,
                        "mdd_99": 0.0,
                        "dsr": 0.0,
                        "trades": 0,
                        "expectancy_bps": 0.0,
                        "last_run": "",
                    },
                    "backtest_equity_curve": [],
                    "falsification_gates": {},
                    "cron_config": {
                        "enabled": (default_status == "CRON_BACKTEST"),
                        "interval": "24h",
                        "last_run": "",
                        "drift_history": [],
                    },
                    "created_at": now_iso,
                    "updated_at": now_iso,
                }

                # Seed initial metrics from active state if this is the active strategy
                if is_active_sys:
                    curr_state = state_manager.get()
                    record["latest_backtest"] = deepcopy(curr_state.get("backtest_summary", record["latest_backtest"]))
                    record["latest_backtest"]["last_run"] = curr_state.get("last_updated", now_iso)
                    # Sample equity curve to 60 points max
                    eq = curr_state.get("equity_curve", [])
                    step = max(1, len(eq) // 60)
                    record["backtest_equity_curve"] = eq[::step]
                    record["falsification_gates"] = deepcopy(curr_state.get("falsification_gates", {}))
                    record["cron_config"]["drift_history"] = [{
                        "timestamp": curr_state.get("last_updated", now_iso),
                        "sharpe": record["latest_backtest"].get("sharpe", 0.0),
                        "dsr": record["latest_backtest"].get("dsr", 0.0),
                        "win_rate": record["latest_backtest"].get("win_rate", 0.0),
                        "max_drawdown": record["latest_backtest"].get("max_drawdown", 0.0),
                        "trades": record["latest_backtest"].get("trades", 0),
                    }]
                updated_list.append(record)

        ranked = self.calculate_rankings(updated_list)
        self._write_raw(ranked)
        return ranked

    def get_all(self, sync: bool = True) -> List[Dict[str, Any]]:
        """Returns all strategies with rankings, enriched with live stats and signals."""
        if sync or not os.path.exists(self._path):
            strategies = self.sync_with_filesystem()
        else:
            strategies = self._read_raw()
            if not strategies:
                strategies = self.sync_with_filesystem()

        # Enrich with real live signals & equity curve
        for strat in strategies:
            strat["live_stats"] = self.get_live_stats_for_strategy(strat.get("name", ""))
            strat["live_equity_curve"] = self.get_live_equity_for_strategy(strat.get("name", ""))
            strat["signals_summary"] = self.get_signals_summary(strat.get("name", ""))
        return strategies

    def get(self, strategy_id: str) -> Optional[Dict[str, Any]]:
        clean_id = strategy_id if strategy_id.endswith(".py") else f"{strategy_id}.py"
        clean_name = strategy_id.replace(".py", "")
        all_strats = self.get_all(sync=False)
        for s in all_strats:
            if s.get("file") == clean_id or s.get("name") == clean_name:
                return s
        return None

    def update_status(self, strategy_name: str, new_status: str, exclusive: bool = False) -> Dict[str, Any]:
        """
        Updates strategy status: ACTIVE_LIVE, CRON_BACKTEST, DEACTIVATED.
        If ACTIVE_LIVE and exclusive=True, switches other active strategies to CRON_BACKTEST.
        If exclusive=False (default), allows MULTIPLE strategies to run concurrently in ACTIVE_LIVE.
        """
        if new_status not in ("ACTIVE_LIVE", "CRON_BACKTEST", "DEACTIVATED"):
            raise ValueError(f"Invalid status: {new_status}")

        strategies = self.get_all(sync=False)
        clean_name = strategy_name.replace(".py", "")
        target_file = f"{clean_name}.py"
        target_found = False

        now_iso = _now_local_iso()

        for s in strategies:
            if s.get("file") == target_file or s.get("name") == clean_name:
                s["status"] = new_status
                s["updated_at"] = now_iso
                if "cron_config" in s:
                    s["cron_config"]["enabled"] = (new_status == "CRON_BACKTEST")
                target_found = True
            elif exclusive and new_status == "ACTIVE_LIVE" and s.get("status") == "ACTIVE_LIVE":
                # Demote previous active only if exclusive mode requested
                s["status"] = "CRON_BACKTEST"
                s["updated_at"] = now_iso
                if "cron_config" in s:
                    s["cron_config"]["enabled"] = True

        if not target_found:
            # Sync and retry
            strategies = self.sync_with_filesystem()
            for s in strategies:
                if s.get("file") == target_file or s.get("name") == clean_name:
                    s["status"] = new_status
                    s["updated_at"] = now_iso
                    target_found = True

        # Synchronize active strategies list in state_manager and bot_supervisor
        active_list = [s["name"] for s in strategies if s.get("status") == "ACTIVE_LIVE"]
        primary_active = clean_name if new_status == "ACTIVE_LIVE" else (active_list[0] if active_list else "")
        state_manager.patch({
            "active_strategy": primary_active,
            "active_strategies": active_list
        })

        # Sync bot_runner supervisor
        try:
            from server.bot_runner import bot_supervisor
            if new_status == "ACTIVE_LIVE":
                bot_supervisor.deploy_strategy(clean_name, mode="python-telemetry")
            else:
                bot_supervisor.stop_strategy(clean_name)
        except Exception as e_bot:
            logger.warning(f"Could not sync bot_supervisor for {clean_name}: {e_bot}")

        ranked = self.calculate_rankings(strategies)
        self._write_raw(ranked)
        logger.info(f"[StrategyRegistry] Updated status for {clean_name} -> {new_status} (Active: {active_list})")
        return next((s for s in ranked if s.get("name") == clean_name), {})

    def record_backtest(self, strategy_name: str, bt_result: Dict[str, Any], is_cron: bool = False) -> Dict[str, Any]:
        """
        Updates latest backtest results, compact equity curve, cynic gates, and drift history.
        """
        strategies = self.get_all(sync=False)
        clean_name = strategy_name.replace(".py", "")
        target_file = f"{clean_name}.py"
        now_iso = _now_local_iso()

        summary = bt_result.get("summary", {})
        gates = bt_result.get("falsification_gates", {})
        eq = bt_result.get("equity_curve", [])

        # Sample equity curve to 80 points max for storage efficiency
        step = max(1, len(eq) // 80) if len(eq) > 80 else 1
        compact_eq = eq[::step] if eq else []

        # Resolve time period info
        tp = bt_result.get("time_period") or {}
        if not tp and compact_eq and len(compact_eq) >= 2:
            t0 = compact_eq[0].get("time", 0)
            t1 = compact_eq[-1].get("time", 0)
            if t0 and t1 and t0 > 1000000000:
                dt0 = datetime.fromtimestamp(t0, tz=timezone.utc)
                dt1 = datetime.fromtimestamp(t1, tz=timezone.utc)
                days = round((t1 - t0) / 86400, 1)
                tp = {
                    "start_time": t0,
                    "end_time": t1,
                    "start_date": dt0.strftime("%Y-%m-%d %H:%M UTC"),
                    "end_date": dt1.strftime("%Y-%m-%d %H:%M UTC"),
                    "duration_days": days,
                    "period_label": f"{dt0.strftime('%Y-%m-%d')} → {dt1.strftime('%Y-%m-%d')} ({days:.1f}d)",
                    "candles_count": summary.get("candles_count")
                }

        target_strat = None
        for s in strategies:
            if s.get("file") == target_file or s.get("name") == clean_name:
                s["latest_backtest"] = {
                    "sharpe": summary.get("sharpe", 0.0),
                    "win_rate": summary.get("win_rate", 0.0),
                    "profit_factor": summary.get("profit_factor", 0.0),
                    "max_drawdown": summary.get("max_drawdown", 0.0),
                    "mdd_99": summary.get("mdd_99", 0.0),
                    "dsr": summary.get("dsr", 0.0),
                    "trades": summary.get("trades", 0),
                    "expectancy_bps": summary.get("expectancy_bps", 0.0),
                    "last_run": now_iso,
                    "start_time": tp.get("start_time") or summary.get("start_time"),
                    "end_time": tp.get("end_time") or summary.get("end_time"),
                    "start_date": tp.get("start_date") or summary.get("start_date"),
                    "end_date": tp.get("end_date") or summary.get("end_date"),
                    "duration_days": tp.get("duration_days") or summary.get("duration_days"),
                    "period_label": tp.get("period_label") or summary.get("period_label"),
                    "candles_count": tp.get("candles_count") or summary.get("candles_count"),
                }
                s["time_period"] = tp
                s["backtest_equity_curve"] = compact_eq
                s["falsification_gates"] = gates
                s["trade_markers"] = bt_result.get("trade_markers", [])
                s["trades_detail"] = bt_result.get("trades_detail", [])
                s["updated_at"] = now_iso

                cron_cfg = s.setdefault("cron_config", {"enabled": False, "interval": "24h", "last_run": "", "drift_history": []})
                if is_cron:
                    cron_cfg["last_run"] = now_iso

                # Enforce daily drift history: 1 snapshot per calendar day
                history = cron_cfg.setdefault("drift_history", [])
                snapshot = {
                    "timestamp": now_iso,
                    "sharpe": summary.get("sharpe", 0.0),
                    "dsr": summary.get("dsr") if summary.get("dsr") is not None else gates.get("gate_1_dsr", {}).get("dsr", 0.0),
                    "win_rate": summary.get("win_rate", 0.0),
                    "max_drawdown": summary.get("max_drawdown", 0.0),
                    "trades": summary.get("trades", 0),
                    "profit_factor": summary.get("profit_factor", 0.0),
                    "period_label": tp.get("period_label") or summary.get("period_label", ""),
                }
                if is_cron:
                    today_str = (now_iso or "")[:10]
                    history = [h for h in history if (h.get("timestamp") or "")[:10] != today_str]
                else:
                    # Avoid exact duplicate timestamp writes
                    history = [h for h in history if (h.get("timestamp") or "") != now_iso]
                history.append(snapshot)
                cron_cfg["drift_history"] = history[-30:]
                target_strat = s
                break

        ranked = self.calculate_rankings(strategies)
        self._write_raw(ranked)
        logger.info(f"[StrategyRegistry] Recorded backtest for {clean_name} (is_cron={is_cron})")
        return target_strat or {}

    def get_portfolio_summary(self) -> Dict[str, Any]:
        """
        Computes aggregate portfolio-level performance across ALL currently active strategies (ACTIVE_LIVE).
        Provides real live bot execution telemetry alongside historical backtest benchmarks.
        """
        strategies = self.get_all(sync=False)
        active_strats = [s for s in strategies if s.get("status") == "ACTIVE_LIVE"]

        if not active_strats:
            return {
                "active_count": 0,
                "active_strategies": [],
                "blended_win_rate": 0.0,
                "blended_sharpe": 0.0,
                "total_trades": 0,
                "combined_profit_factor": 0.0,
                "total_realized_pnl": 0.0,
                "total_net_pnl": 0.0,
                "backtest_net_pnl": 0.0,
                "symbols": [],
                "best_performer": None,
                "live_trades": 0,
                "live_wins": 0,
                "live_losses": 0,
                "live_win_rate": 0.0,
                "live_realized_pnl": 0.0,
                "live_profit_factor": 0.0,
                "backtest_trades": 0,
                "backtest_win_rate": 0.0,
                "backtest_sharpe": 0.0,
                "backtest_profit_factor": 0.0,
            }

        strategy_names = [s.get("name", "") for s in active_strats]
        symbols = []
        for s in active_strats:
            sym = s.get("symbol", "")
            if sym and sym not in symbols:
                symbols.append(sym)

        # 1. Real Live execution stats across active strategies (matching Signal screen single source of truth)
        all_signals = signal_store.get_all()
        active_clean_names = [s.get("name", "").replace(".py", "").lower() for s in active_strats]
        active_closed_signals = [
            sig for sig in all_signals
            if sig.get("exit_reason") and sig.get("pnl_pct") is not None and
            any(name in sig.get("strategy", "").lower() for name in active_clean_names)
        ]

        live_trades_count = len(active_closed_signals)
        live_wins_count = len([s for s in active_closed_signals if s.get("pnl_pct", 0) > 0])
        live_losses_count = len([s for s in active_closed_signals if s.get("pnl_pct", 0) <= 0])
        live_wr_pct = round((live_wins_count / live_trades_count * 100.0), 1) if live_trades_count > 0 else 0.0
        live_total_pnl = round(sum(s.get("pnl_pct", 0.0) for s in active_closed_signals), 2)
        live_gross_profit = sum(s.get("pnl_pct", 0.0) for s in active_closed_signals if s.get("pnl_pct", 0) > 0)
        live_gross_loss = abs(sum(s.get("pnl_pct", 0.0) for s in active_closed_signals if s.get("pnl_pct", 0) <= 0))
        live_pf = round(live_gross_profit / live_gross_loss, 2) if live_gross_loss > 0 else (99.0 if live_gross_profit > 0 else 0.0)

        # 2. Historical backtest benchmarks
        bt_trades_sum = 0
        bt_wins_sum = 0
        bt_sharpe_weighted = 0.0
        bt_pfs = []
        bt_net_pnl_pct = 0.0
        for s in active_strats:
            bt = s.get("latest_backtest", {})
            t = bt.get("trades", 0)
            raw_wr = bt.get("win_rate", 0.0)
            norm_wr = raw_wr if raw_wr <= 1.0 else (raw_wr / 100.0)
            sh = bt.get("sharpe", 0.0)
            pf = bt.get("profit_factor", 0.0)

            # Cumulative net pnl from equity curve
            eq = s.get("backtest_equity_curve", [])
            if eq and len(eq) >= 2:
                s_pnl = float(eq[-1].get("equity_pct", 100.0)) - float(eq[0].get("equity_pct", 100.0))
            else:
                s_pnl = 0.0
            bt_net_pnl_pct += s_pnl

            bt_trades_sum += t
            bt_wins_sum += round(t * norm_wr)
            bt_sharpe_weighted += sh * max(1, t)
            if pf > 0:
                bt_pfs.append(pf)

        bt_blended_win_rate = round((bt_wins_sum / bt_trades_sum * 100.0), 1) if bt_trades_sum > 0 else 0.0
        bt_blended_sharpe = round((bt_sharpe_weighted / max(1, bt_trades_sum)), 2) if bt_trades_sum > 0 else (
            round(sum(s.get("latest_backtest", {}).get("sharpe", 0.0) for s in active_strats) / len(active_strats), 2) if active_strats else 0.0
        )
        bt_combined_pf = round(sum(bt_pfs) / len(bt_pfs), 2) if bt_pfs else 0.0

        best = max(active_strats, key=lambda s: s.get("ranking_score", 0.0), default=None)

        return {
            "active_count": len(active_strats),
            "active_strategies": strategy_names,
            "symbols": symbols,
            "best_performer": best.get("name") if best else None,

            # Real Live Metrics (1:1 with Signal Screen telemetry)
            "live_trades": live_trades_count,
            "live_wins": live_wins_count,
            "live_losses": live_losses_count,
            "live_win_rate": live_wr_pct,
            "live_realized_pnl": live_total_pnl,
            "live_profit_factor": live_pf,

            # Historical Backtest Benchmarks
            "backtest_trades": bt_trades_sum,
            "backtest_win_rate": bt_blended_win_rate,
            "backtest_sharpe": bt_blended_sharpe,
            "backtest_profit_factor": bt_combined_pf,
            "backtest_net_pnl": round(bt_net_pnl_pct, 2),

            # Unified root fields representing the portfolio benchmark across all activated strategies
            "blended_win_rate": bt_blended_win_rate,
            "blended_sharpe": bt_blended_sharpe,
            "total_trades": bt_trades_sum,
            "combined_profit_factor": bt_combined_pf,
            "total_realized_pnl": live_total_pnl,
            "total_net_pnl": live_total_pnl if live_trades_count > 0 else round(bt_net_pnl_pct, 2),
        }

    def get_distribution_analytics(self) -> Dict[str, Any]:
        """
        Computes drift distribution (improving vs decaying strategies) and
        performance distributions (Sharpe bins, Tier counts, Asset diversification).
        """
        strategies = self.get_all(sync=False)

        improving = []
        decaying = []
        stable = []

        sharpe_bins = {"< 1.0": 0, "1.0 - 1.5": 0, "1.5 - 2.5": 0, "> 2.5": 0}
        tier_counts = {"S-Tier": 0, "A-Tier": 0, "B-Tier": 0, "C-Tier": 0}
        asset_counts: Dict[str, int] = {}

        for s in strategies:
            tier_raw = s.get("tier", "C-Tier")
            for t in ["S-Tier", "A-Tier", "B-Tier", "C-Tier"]:
                if t in tier_raw:
                    tier_counts[t] += 1
                    break

            sym = s.get("symbol", "Other")
            asset_counts[sym] = asset_counts.get(sym, 0) + 1

            bt = s.get("latest_backtest", {})
            sh = bt.get("sharpe", 0.0)
            if sh < 1.0:
                sharpe_bins["< 1.0"] += 1
            elif sh <= 1.5:
                sharpe_bins["1.0 - 1.5"] += 1
            elif sh <= 2.5:
                sharpe_bins["1.5 - 2.5"] += 1
            else:
                sharpe_bins["> 2.5"] += 1

            drift_hist = s.get("cron_config", {}).get("drift_history", [])
            delta_sharpe = 0.0
            delta_win_rate = 0.0

            if len(drift_hist) >= 2:
                latest_p = drift_hist[-1]
                prev_p = drift_hist[-2]
                delta_sharpe = round(latest_p.get("sharpe", 0.0) - prev_p.get("sharpe", 0.0), 2)
                delta_win_rate = round(latest_p.get("win_rate", 0.0) - prev_p.get("win_rate", 0.0), 1)

            entry = {
                "name": s.get("name"),
                "display_name": s.get("display_name"),
                "status": s.get("status"),
                "sharpe": sh,
                "win_rate": bt.get("win_rate", 0.0),
                "delta_sharpe": delta_sharpe,
                "delta_win_rate": delta_win_rate,
                "snapshots_count": len(drift_hist)
            }

            if delta_sharpe > 0.05 or delta_win_rate > 1.0:
                entry["trajectory"] = "GAINING_EDGE"
                improving.append(entry)
            elif delta_sharpe < -0.05 or delta_win_rate < -1.0:
                entry["trajectory"] = "DECAYING_EDGE"
                decaying.append(entry)
            else:
                entry["trajectory"] = "STABLE"
                stable.append(entry)

        return {
            "improving": improving,
            "decaying": decaying,
            "stable": stable,
            "sharpe_distribution": sharpe_bins,
            "tier_distribution": tier_counts,
            "asset_distribution": asset_counts,
            "total_evaluated": len(strategies)
        }

    def get_live_stats_for_strategy(self, strategy_name: str) -> Dict[str, Any]:
        """Calculates live performance metrics for a specific strategy from signal_store."""
        clean_name = strategy_name.replace(".py", "").lower()
        signals = signal_store.get_all()
        # Filter signals matching strategy case-insensitively
        strat_signals = [
            s for s in signals
            if clean_name in s.get("strategy", "").lower() or s.get("strategy", "").replace(".py", "").lower() == clean_name
        ]
        closed = [s for s in strat_signals if s.get("exit_reason") and s.get("pnl_pct") is not None]
        wins = [s for s in closed if s.get("pnl_pct", 0) > 0]
        losses = [s for s in closed if s.get("pnl_pct", 0) <= 0]

        total = len(closed)
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
            std_r = math.sqrt(sum((r - mean_r) ** 2 for r in returns) / len(returns)) or 1e-8
            sharpe_live = round((mean_r / std_r) * math.sqrt(252), 2)
        else:
            sharpe_live = 0.0

        return {
            "total_trades": total,
            "open_trades": len([s for s in strat_signals if s.get("status") == "ACTIVE_IN_POSITION"]),
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": round(win_rate, 4),
            "gross_profit": round(gross_profit, 2),
            "gross_loss": round(gross_loss, 2),
            "profit_factor": profit_factor,
            "sharpe_live": sharpe_live,
            "total_pnl_pct": total_pnl,
        }

    def get_live_equity_for_strategy(self, strategy_name: str) -> List[Dict[str, Any]]:
        """Reconstructs live equity curve progression from closed trades for this strategy."""
        clean_name = strategy_name.replace(".py", "").lower()
        signals = signal_store.get_all()
        strat_signals = [
            s for s in signals
            if clean_name in s.get("strategy", "").lower() or s.get("strategy", "").replace(".py", "").lower() == clean_name
        ]
        closed = [s for s in strat_signals if s.get("exit_reason") and s.get("pnl_pct") is not None]
        if not closed:
            return []

        # Sort chronologically by time
        closed.sort(key=lambda s: s.get("time", 0))

        equity_curve: List[Dict[str, Any]] = []
        current_eq = 100.0
        peak = 100.0

        first_time = closed[0].get("time", int(time.time())) - 60
        equity_curve.append({"time": first_time, "equity_pct": 100.0, "drawdown_pct": 0.0})

        for s in closed:
            pnl = float(s.get("pnl_pct", 0.0))
            current_eq = round(current_eq * (1.0 + (pnl / 100.0)), 2)
            peak = max(peak, current_eq)
            dd = round(((peak - current_eq) / peak) * 100.0, 2)
            equity_curve.append({
                "time": s.get("time", int(time.time())),
                "equity_pct": current_eq,
                "drawdown_pct": dd,
            })
        return equity_curve

    def get_signals_summary(self, strategy_name: str) -> Dict[str, Any]:
        """Provides recent signals and trades summary for this strategy sorted newest first."""
        clean_name = strategy_name.replace(".py", "").lower()
        signals = signal_store.get_all()
        strat_signals = [
            s for s in signals
            if clean_name in s.get("strategy", "").lower() or s.get("strategy", "").replace(".py", "").lower() == clean_name
        ]
        # Sort newest first
        strat_signals.sort(key=lambda s: s.get("time", 0), reverse=True)
        return {
            "total_signals": len(strat_signals),
            "recent_signals": strat_signals[:25],
        }

    def register_strategy(self, strat_data: Dict[str, Any]) -> Dict[str, Any]:
        """Registers a new strategy programmatically from the AI agent."""
        strategies = self.get_all(sync=True)
        py_file = strat_data.get("file") or f"{strat_data.get('name')}.py"
        clean_name = py_file.replace(".py", "")

        now_iso = _now_local_iso()
        record = {
            "id": py_file,
            "name": clean_name,
            "file": py_file,
            "path": f"strategies/{py_file}",
            "display_name": strat_data.get("display_name", clean_name),
            "target_profile": strat_data.get("target_profile", "Custom Strategy"),
            "thesis": strat_data.get("thesis", "AI Discovered Strategy"),
            "symbol": strat_data.get("symbol", "BTC/USDT"),
            "timeframe": strat_data.get("timeframe", "15m"),
            "status": strat_data.get("status", "CRON_BACKTEST"),
            "rank": 99,
            "ranking_score": 0.0,
            "tier": "C-Tier (Sub-Hurdle)",
            "latest_backtest": strat_data.get("latest_backtest", {
                "sharpe": 0.0, "win_rate": 0.0, "profit_factor": 0.0,
                "max_drawdown": 0.0, "mdd_99": 0.0, "dsr": 0.0,
                "trades": 0, "expectancy_bps": 0.0, "last_run": now_iso
            }),
            "backtest_equity_curve": strat_data.get("backtest_equity_curve", []),
            "falsification_gates": strat_data.get("falsification_gates", {}),
            "cron_config": {
                "enabled": (strat_data.get("status", "CRON_BACKTEST") == "CRON_BACKTEST"),
                "interval": strat_data.get("interval", "1h"),
                "last_run": now_iso,
                "drift_history": [],
            },
            "created_at": now_iso,
            "updated_at": now_iso,
        }
        # Replace or append
        strategies = [s for s in strategies if s.get("file") != py_file] + [record]
        ranked = self.calculate_rankings(strategies)
        self._write_raw(ranked)
        logger.info(f"[StrategyRegistry] Registered new strategy: {py_file}")
        return record


# ─────────────────────────────────────────────────────────────
# Module-level singletons — import these everywhere
# ─────────────────────────────────────────────────────────────
state_manager = StateManager()
signal_store = SignalStore()
strategy_registry = StrategyRegistry()

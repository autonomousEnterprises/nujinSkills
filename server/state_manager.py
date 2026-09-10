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
STRATEGIES_FILE = os.path.join(_ROOT, "data", "strategies.json")
STRATEGIES_DIR = os.path.join(_ROOT, "strategies")

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
        updated = [entry] + signals
        _write_json_locked(self._path, updated)
        # Also bump signals_count in state.json
        state_manager.patch({"signals_count": len(updated)})
        logger.info(f"[SignalStore] Signal #{new_id} added: {entry['action']} @ {entry['price']}")
        return updated

    def clear(self) -> List[Dict[str, Any]]:
        """Clears all signals from disk and resets signals_count to 0."""
        _write_json_locked(self._path, [])
        state_manager.patch({"signals_count": 0})
        logger.info("[SignalStore] All signals cleared.")
        return []

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

    def _infer_metadata(self, filename: str) -> Dict[str, Any]:
        clean = filename.replace(".py", "")
        is_xau = ("XAU" in clean.upper()) or ("GOAT" in clean.upper())
        is_trap = "TRAP" in clean.upper()

        if is_xau:
            return {
                "display_name": "Goat Funded Trader XAUUSD Scalper",
                "target_profile": "Goat Funded Trader Prop Scalper (2m-15m)",
                "thesis": "Dynamic Range Expansion Momentum Train on 1m-15m London/NY sessions",
                "symbol": "XAU/USD",
                "timeframe": "1m",
            }
        elif is_trap:
            return {
                "display_name": "Trap Fade Liquidity Sweep",
                "target_profile": "Liquidity Sweep Fade (LONG & SHORT)",
                "thesis": "Dual-Directional Asian Session Liquidity Sweep Fade beyond session extremes",
                "symbol": "BTC/USDT",
                "timeframe": "15m",
            }
        else:
            return {
                "display_name": "Prop Firm VSA Wick Rejection",
                "target_profile": "Prop Firm Challenge (LONG & SHORT)",
                "thesis": "VSA Wick Rejection with Volume Z-Score > 1.0 counterparty limit absorption",
                "symbol": "BTC/USDT",
                "timeframe": "15m",
            }

    def _calculate_score(self, summary: Dict[str, Any], gates: Dict[str, Any]) -> float:
        if not summary or summary.get("trades", 0) == 0:
            return 0.0
        sharpe = max(0.0, float(summary.get("sharpe", 0.0)))
        dsr = max(0.0, float(summary.get("dsr", 0.0)))
        win_rate = max(0.0, float(summary.get("win_rate", 0.0)))
        profit_factor = min(max(0.0, float(summary.get("profit_factor", 0.0))), 5.0)
        max_dd = max(0.0, float(summary.get("max_drawdown", 0.0)))

        # Weighted score: Sharpe (35%), DSR (25%), Win Rate (20%), PF (15%), Drawdown penalty (10%)
        sharpe_pts = sharpe * 10.0 * 0.35
        dsr_pts = dsr * 100.0 * 0.25
        wr_pts = win_rate * 100.0 * 0.20
        pf_pts = (profit_factor / 3.0) * 100.0 * 0.15
        dd_penalty = max_dd * 100.0 * 2.0 * 0.10

        score = sharpe_pts + dsr_pts + wr_pts + pf_pts - dd_penalty
        if dsr < 0.95 and dsr > 0:
            score = max(0.0, score - 15.0)  # Falsification failure penalty
        return round(max(0.0, min(100.0, score)), 1)

    def calculate_rankings(self, strategies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        for strat in strategies:
            summary = strat.get("latest_backtest", {})
            gates = strat.get("falsification_gates", {})
            strat["ranking_score"] = self._calculate_score(summary, gates)
            score = strat["ranking_score"]
            if score >= 80.0:
                strat["tier"] = "S-Tier (Superior Edge)"
            elif score >= 65.0:
                strat["tier"] = "A-Tier (Robust Edge)"
            elif score >= 50.0:
                strat["tier"] = "B-Tier (Marginal Edge)"
            else:
                strat["tier"] = "C-Tier (Sub-Hurdle)"

        # Sort descending by ranking_score
        strategies.sort(key=lambda s: s.get("ranking_score", 0.0), reverse=True)
        for idx, strat in enumerate(strategies, start=1):
            strat["rank"] = idx
        return strategies

    def sync_with_filesystem(self) -> List[Dict[str, Any]]:
        """Syncs data/strategies.json with files in strategies/*.py and active state."""
        existing = {s["file"]: s for s in self._read_raw() if "file" in s}
        active_strat = state_manager.get().get("active_strategy", "GoatFundedTraderXauusdScalper")
        clean_active = active_strat.replace(".py", "")

        os.makedirs(self._dir, exist_ok=True)
        py_files = sorted([f for f in os.listdir(self._dir) if f.endswith(".py")])

        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        updated_list: List[Dict[str, Any]] = []

        for py_file in py_files:
            clean_name = py_file.replace(".py", "")
            meta = self._infer_metadata(py_file)
            is_active_sys = (clean_name == clean_active)

            if py_file in existing:
                item = existing[py_file]
                # If system active strategy matches, sync status
                if is_active_sys and item.get("status") != "ACTIVE_LIVE":
                    item["status"] = "ACTIVE_LIVE"
                updated_list.append(item)
            else:
                # Initialize new strategy record
                default_status = "ACTIVE_LIVE" if is_active_sys else ("CRON_BACKTEST" if "Vsa" in clean_name else "DEACTIVATED")
                record = {
                    "id": py_file,
                    "name": clean_name,
                    "file": py_file,
                    "path": f"strategies/{py_file}",
                    "display_name": meta["display_name"],
                    "target_profile": meta["target_profile"],
                    "thesis": meta["thesis"],
                    "symbol": meta["symbol"],
                    "timeframe": meta["timeframe"],
                    "status": default_status,
                    "rank": 99,
                    "ranking_score": 0.0,
                    "tier": "C-Tier (Sub-Hurdle)",
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

        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

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
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        summary = bt_result.get("summary", {})
        gates = bt_result.get("falsification_gates", {})
        eq = bt_result.get("equity_curve", [])

        # Sample equity curve to 80 points max for storage efficiency
        step = max(1, len(eq) // 80) if len(eq) > 80 else 1
        compact_eq = eq[::step] if eq else []

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
                }
                s["backtest_equity_curve"] = compact_eq
                s["falsification_gates"] = gates
                s["updated_at"] = now_iso

                cron_cfg = s.setdefault("cron_config", {"enabled": False, "interval": "24h", "last_run": "", "drift_history": []})
                if is_cron:
                    cron_cfg["last_run"] = now_iso

                # Append snapshot to drift_history (keep last 25 entries)
                history = cron_cfg.setdefault("drift_history", [])
                history.append({
                    "timestamp": now_iso,
                    "sharpe": summary.get("sharpe", 0.0),
                    "dsr": summary.get("dsr", 0.0),
                    "win_rate": summary.get("win_rate", 0.0),
                    "max_drawdown": summary.get("max_drawdown", 0.0),
                    "trades": summary.get("trades", 0),
                    "profit_factor": summary.get("profit_factor", 0.0),
                })
                cron_cfg["drift_history"] = history[-25:]
                target_strat = s
                break

        ranked = self.calculate_rankings(strategies)
        self._write_raw(ranked)
        logger.info(f"[StrategyRegistry] Recorded backtest for {clean_name} (is_cron={is_cron})")
        return target_strat or {}

    def get_portfolio_summary(self) -> Dict[str, Any]:
        """
        Computes aggregate portfolio-level performance across ALL currently active strategies (ACTIVE_LIVE).
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
                "symbols": [],
                "best_performer": None
            }

        total_trades = 0
        total_wins = 0
        weighted_sharpe_sum = 0.0
        total_pnl = 0.0
        profit_factors = []
        symbols = []
        strategy_names = []

        for s in active_strats:
            name = s.get("name", "")
            strategy_names.append(name)
            sym = s.get("symbol", "")
            if sym and sym not in symbols:
                symbols.append(sym)

            bt = s.get("latest_backtest", {})
            trades = bt.get("trades", 0)
            win_rate = bt.get("win_rate", 0.0)
            sharpe = bt.get("sharpe", 0.0)
            pf = bt.get("profit_factor", 0.0)

            # Check live signals summary if available
            sig_sum = self.get_signals_summary(name)
            live_trades = sig_sum.get("total_signals", 0)
            live_stats = self.get_live_stats_for_strategy(name)
            
            if live_stats and live_stats.get("total_trades", 0) > 0:
                l_trades = live_stats["total_trades"]
                l_wins = live_stats["wins"]
                total_trades += l_trades
                total_wins += l_wins
                total_pnl += live_stats.get("total_pnl_pct", 0.0)
                weighted_sharpe_sum += sharpe * l_trades
            else:
                norm_win_rate = win_rate if win_rate <= 1.0 else (win_rate / 100.0)
                total_trades += trades
                total_wins += int(trades * norm_win_rate)
                weighted_sharpe_sum += sharpe * max(1, trades)

            if pf > 0:
                profit_factors.append(pf)

        blended_win_rate = round((total_wins / total_trades * 100.0), 1) if total_trades > 0 else 0.0
        blended_sharpe = round((weighted_sharpe_sum / max(1, total_trades)), 2) if total_trades > 0 else round(sum(s.get("latest_backtest", {}).get("sharpe", 0.0) for s in active_strats) / len(active_strats), 2)
        combined_pf = round(sum(profit_factors) / len(profit_factors), 2) if profit_factors else 0.0

        best = max(active_strats, key=lambda s: s.get("ranking_score", 0.0), default=None)

        return {
            "active_count": len(active_strats),
            "active_strategies": strategy_names,
            "blended_win_rate": blended_win_rate,
            "blended_sharpe": blended_sharpe,
            "total_trades": total_trades,
            "combined_profit_factor": combined_pf,
            "total_realized_pnl": round(total_pnl, 2),
            "symbols": symbols,
            "best_performer": best.get("name") if best else None
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
        clean_name = strategy_name.replace(".py", "")
        signals = signal_store.get_all()
        # Filter signals matching strategy
        strat_signals = [
            s for s in signals
            if clean_name in s.get("strategy", "") or s.get("strategy", "").replace(".py", "") == clean_name
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
            "profit_factor": profit_factor,
            "sharpe_live": sharpe_live,
            "total_pnl_pct": total_pnl,
        }

    def get_live_equity_for_strategy(self, strategy_name: str) -> List[Dict[str, Any]]:
        """Reconstructs live equity curve progression from closed trades for this strategy."""
        clean_name = strategy_name.replace(".py", "")
        signals = signal_store.get_all()
        strat_signals = [
            s for s in signals
            if clean_name in s.get("strategy", "") or s.get("strategy", "").replace(".py", "") == clean_name
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
        """Provides recent signals and trades summary for this strategy."""
        clean_name = strategy_name.replace(".py", "")
        signals = signal_store.get_all()
        strat_signals = [
            s for s in signals
            if clean_name in s.get("strategy", "") or s.get("strategy", "").replace(".py", "") == clean_name
        ]
        return {
            "total_signals": len(strat_signals),
            "recent_signals": strat_signals[:10],
        }

    def register_strategy(self, strat_data: Dict[str, Any]) -> Dict[str, Any]:
        """Registers a new strategy programmatically from the AI agent."""
        strategies = self.get_all(sync=True)
        py_file = strat_data.get("file") or f"{strat_data.get('name')}.py"
        clean_name = py_file.replace(".py", "")

        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
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

"""
server/plugin_loader.py
─────────────────────────────────────────────────────────────
Universal Plugin Discovery and Lifecycle Manager for NujinAI.

Discovers, inspects, and exposes modules from the plugins/ directory.
Supports both user-installed plugins and development symlinks (e.g. nujinPro).
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger("PluginManager")

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PLUGINS_DIR = os.path.join(_ROOT, "plugins")


class PluginManager:
    """Discovers and resolves plugins, their metadata, and their strategy paths."""

    @staticmethod
    def get_plugins_dir() -> str:
        return PLUGINS_DIR

    @classmethod
    def get_all_plugins(cls) -> List[Dict[str, Any]]:
        """
        Discovers all valid plugins installed under plugins/.
        A valid plugin is any subdirectory containing either plugin.json or a strategies/ folder.
        """
        plugins = []
        if not os.path.exists(PLUGINS_DIR):
            return plugins

        try:
            for entry in sorted(os.listdir(PLUGINS_DIR)):
                plugin_path = os.path.join(PLUGINS_DIR, entry)
                if not os.path.isdir(plugin_path):
                    continue

                manifest_file = os.path.join(plugin_path, "plugin.json")
                strat_dir = os.path.join(plugin_path, "strategies")

                # Must have manifest or strategies folder
                if not os.path.exists(manifest_file) and not os.path.exists(strat_dir):
                    continue

                manifest = {}
                if os.path.exists(manifest_file):
                    try:
                        with open(manifest_file, "r", encoding="utf-8") as f:
                            manifest = json.load(f)
                    except Exception as e:
                        logger.warning(f"[PluginManager] Could not read manifest for {entry}: {e}")

                num_strategies = 0
                if os.path.exists(strat_dir) and os.path.isdir(strat_dir):
                    num_strategies = len([f for f in os.listdir(strat_dir) if f.endswith(".py")])

                plugins.append({
                    "id": manifest.get("id", entry),
                    "name": manifest.get("name", entry.capitalize()),
                    "version": manifest.get("version", "1.0.0"),
                    "description": manifest.get("description", "Nujin Extension Plugin"),
                    "author": manifest.get("author", "Autonomous Enterprises"),
                    "tier": manifest.get("tier", "PRO"),
                    "is_pro": manifest.get("tier", "").upper() == "PRO" or manifest.get("is_pro", True),
                    "path": plugin_path,
                    "strategies_dir": strat_dir if os.path.exists(strat_dir) else None,
                    "strategy_count": num_strategies,
                    "features": manifest.get("features", []),
                })
        except Exception as e:
            logger.error(f"[PluginManager] Error scanning plugins: {e}")

        return plugins

    @classmethod
    def get_plugin_strategy_dirs(cls) -> List[str]:
        """Returns list of all existing strategy directories across all active plugins."""
        dirs = []
        for p in cls.get_all_plugins():
            sdir = p.get("strategies_dir")
            if sdir and os.path.exists(sdir):
                dirs.append(sdir)
        return dirs

    @classmethod
    def get_plugin_strategy_files(cls) -> List[Dict[str, Any]]:
        """
        Returns list of all strategy files found in all installed plugins.
        Each entry has: {filename, full_path, plugin_id, plugin_name, is_pro}
        """
        results = []
        for p in cls.get_all_plugins():
            sdir = p.get("strategies_dir")
            if not sdir or not os.path.exists(sdir):
                continue
            for fname in sorted(os.listdir(sdir)):
                if fname.endswith(".py") and not fname.startswith("__"):
                    results.append({
                        "filename": fname,
                        "strategy_name": fname.replace(".py", ""),
                        "path": os.path.join(sdir, fname),
                        "plugin_id": p["id"],
                        "plugin_name": p["name"],
                        "is_pro": p.get("is_pro", True),
                    })
        return results

    @classmethod
    def resolve_strategy_path(cls, strategy_name: str) -> Optional[str]:
        """
        Resolves the full filesystem path for a strategy, checking:
        1. core strategies/<strategy_name>.py
        2. any installed plugins/<plugin>/strategies/<strategy_name>.py
        """
        clean_name = strategy_name.replace(".py", "").strip()
        core_path = os.path.join(_ROOT, "strategies", f"{clean_name}.py")
        if os.path.exists(core_path):
            return core_path

        # Check in plugins
        for p in cls.get_all_plugins():
            sdir = p.get("strategies_dir")
            if sdir and os.path.exists(sdir):
                candidate = os.path.join(sdir, f"{clean_name}.py")
                if os.path.exists(candidate):
                    return candidate

        return None


plugin_manager = PluginManager()

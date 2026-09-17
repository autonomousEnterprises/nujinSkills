# Nujin Plugins Directory

This directory is the auto-discovery mount point for Nujin plugins and proprietary add-ons (such as `nujinPro`).

## For End Users (Customers)

If you purchased or received a Nujin plugin (such as **NujinPro**):
1. Extract or place the plugin folder here (e.g., `plugins/nujinPro` or `plugins/pro`).
2. Verify the plugin folder contains a `plugin.json` file and a `strategies/` directory.
3. Run `python tools/strategy_manager.py sync` or restart the Nujin server.
4. The strategies, tools, and visual telemetry from your plugin will immediately be active and accessible to the Nujin AI Agent.

## For Developers (Working across multiple repos)

If you are developing both `nujinSkills` and `nujinPro` locally:
- Do not commit proprietary plugins into this repo.
- Link your local repo clone here using a symbolic link:
  ```bash
  ln -s /path/to/nujinPro plugins/pro
  ```
- All subfolders in `plugins/*` (except this file, `__init__.py`, and `.gitkeep`) are strictly ignored by `.gitignore`.

# Reference: Developer Guide — Extending NujinAI (Backend, Frontend & Tools)

## 1. System Architecture Overview

**NujinAI** is engineered with a modular, decoupled architecture:
- **Backend (`server/`):** Python 3.10+ FastAPI service, `StateManager` with POSIX file locks, Binance REST/WS feeds, Telegram bot dispatcher, and vectorized backtest engine.
- **Frontend Cockpit (`frontend/`):** React 18, TypeScript, Tailwind CSS, Vite, and TradingView Lightweight Charts.
- **CLI Tool Suite (`tools/`):** Agent-agnostic CLI utilities conforming to a strict execution contract for AI agents (Antigravity, Claude Code, Hermes, OpenClaw).

---

## 2. Extending the Backend (`server/`)

### A. Adding a New REST Endpoint
Add endpoints directly in `server/main.py`:
```python
@app.get("/api/custom/metric")
async def get_custom_metric():
    state = state_manager.get()
    return {"metric": state.get("custom_metric", 0.0)}
```

### B. Adding State Fields (`server/state_manager.py`)
Update default schema in `StateManager.__init__` to preserve backwards compatibility. All writes must invoke `state_manager.patch(...)` or `state_manager.set_full(...)` to ensure atomic file locking.

### C. Broadcasting Custom WebSocket Events
To stream real-time events to the frontend Cockpit:
```python
from server.websocket import manager

await manager.broadcast({
    "event_type": "CUSTOM_EVENT",
    "payload": {"status": "SUCCESS", "timestamp": time.time()}
})
```

---

## 3. Extending the Frontend Cockpit (`frontend/`)

### A. Adding a New Screen
1. Create component in `frontend/src/components/MyNewDeck.tsx`.
2. Add screen key in `frontend/src/App.tsx`.
3. Map hotkey in `useEffect` listener in `App.tsx` (e.g. `F5` or `Ctrl+5`).
4. Register tab in `frontend/src/components/Header.tsx`.

### B. Handling WebSocket Events in React
In `frontend/src/hooks/useWebSocket.ts`, add event case in `ws.onmessage`:
```typescript
case "CUSTOM_EVENT":
  setCustomState(data.payload);
  break;
```

### C. Build & Verification
After editing frontend code:
```bash
python tools/frontend_control.py build
```
Verify the build completes without errors and compiles into `frontend/dist/`.

---

## 4. Authoring New CLI Tools (`tools/`)

All scripts in `tools/` must strictly conform to the **Nujin Tool Authoring Standard**:

```python
#!/usr/bin/env python3
import argparse
import json
import os
import sys

TOOL_NAME = "[MyCustomTool]"  # Standard prefix for AI agent log parsing

def action_run(param: str):
    print(f"{TOOL_NAME} Executing action with param: {param}")
    result = {"status": "SUCCESS", "param": param}
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Description for AI agent")
    parser.add_argument("action", choices=["run", "status"], help="Action to execute")
    parser.add_argument("--param", default="default_value", help="Parameter description")
    args = parser.parse_args()

    if args.action == "run":
        action_run(args.param)
    elif args.action == "status":
        print(f"{TOOL_NAME} Status OK")
```

### Mandatory Tool Rules:
1. `#!/usr/bin/env python3` shebang on line 1.
2. `TOOL_NAME = "[Prefix]"` constant used on all `print()` outputs.
3. Flat positional `action` argument with explicit `choices=[...]` (never use nested subparsers).
4. Use standard library or approved scientific packages (`numpy`, `polars`, `pandas`, `scipy`).
5. Support `.venv/bin/python` auto-detection when invoking subprocesses.
6. Verify tool compliance using:
   ```bash
   python tools/autoresearch_miner.py improve-tool --tool <your_tool.py>
   ```

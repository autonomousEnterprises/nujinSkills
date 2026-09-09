import logging
import os
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional

from server.websocket import manager
from server.telegram_bot import telegram_gateway
from server.bot_runner import bot_supervisor
from server.data_manager import generate_sample_ohlcv, fetch_real_binance_klines
from server.backtest_engine import run_real_backtest

# ── Unified State Manager — single source of truth for all consumers ──────────
from server.state_manager import state_manager, signal_store

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("NujinSkillsServer")

app = FastAPI(
    title="NujinSkills Telemetry & Signal Gateway API",
    version="1.0.0",
    description="24/7 Backend Telemetry Hub, WebSocket Dispatcher, and Telegram Signal Gateway"
)

# Enable CORS for Frontend UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class EventEnvelope(BaseModel):
    event_type: str
    payload: Dict[str, Any]

class DeployBotRequest(BaseModel):
    strategy: str
    mode: Optional[str] = "dry-run"

class SelectStrategyRequest(BaseModel):
    strategy: str

@app.get("/api/health")
async def health_check():
    return {
        "status": "ONLINE",
        "service": "NujinSkills Telemetry Server",
        "connections": len(manager.active_connections),
        "bot_status": bot_supervisor.get_status()
    }

@app.get("/api/candles")
async def get_candles(symbol: str = "BTC/USDT", count: int = 500, mode: str = "live"):
    if mode == "live":
        data = fetch_real_binance_klines(symbol=symbol, interval="15m", count=count)
    else:
        data = generate_sample_ohlcv(symbol, count)
    return {"symbol": symbol, "mode": mode, "data": data}


@app.get("/api/widgets")
async def get_widgets():
    return {"widgets": list(manager.widget_state.values())}

@app.get("/api/signals")
async def get_signals():
    signals_list = signal_store.get_all()
    active = signal_store.get_active()
    return {"signals": signals_list, "active_signal": active}

@app.post("/api/broadcast")
async def broadcast_event(envelope: EventEnvelope):
    logger.info(f"Broadcast event received: {envelope.event_type}")
    await manager.broadcast(envelope.model_dump())

    if envelope.event_type == "SIGNAL_TRIGGERED":
        telegram_gateway.format_and_send_signal(envelope.payload)
        signal_store.add(envelope.payload)          # ← StateManager handles file I/O + signals_count bump
    elif envelope.event_type == "TELEGRAM_ALERT":
        telegram_gateway.format_and_send_signal(envelope.payload)
    elif envelope.event_type == "UPSERT_WIDGET" and envelope.payload.get("component") == "MetricCard":
        telegram_gateway.format_and_send_dsr_alert(envelope.payload)
    return {"status": "SUCCESS", "event_type": envelope.event_type}


@app.post("/api/bot/deploy")
async def deploy_bot(req: DeployBotRequest):
    logger.info(f"Activating & deploying strategy for system: {req.strategy}")
    bt_result = run_real_backtest(req.strategy, save_as_active=True)
    res = bot_supervisor.deploy_strategy(req.strategy, req.mode)
    await manager.broadcast({"event_type": "STATE_UPDATED", "payload": bt_result["state"]})
    return {**res, "state": bt_result["state"]}

@app.post("/api/bot/stop")
async def stop_bot():
    res = bot_supervisor.stop_bot()
    new_state = state_manager.patch({"status": "STOPPED"})
    await manager.broadcast({"event_type": "STATE_UPDATED", "payload": new_state})
    return res

@app.get("/api/bot/status")
async def get_bot_status():
    return bot_supervisor.get_status()

@app.post("/api/strategies/select")
async def select_and_run_strategy(req: SelectStrategyRequest):
    logger.info(f"Strategy backtest preview requested: {req.strategy}")
    result = run_real_backtest(req.strategy, save_as_active=False)
    await manager.broadcast({"event_type": "BACKTEST_UPDATED", "payload": result})
    return result

@app.get("/api/state")
async def get_system_state():
    """Return current system state from StateManager (single source of truth)."""
    return state_manager.get()


class UpdateStateRequest(BaseModel):
    active_strategy: Optional[str] = None
    target_profile: Optional[str] = None
    status: Optional[str] = None
    backtest_summary: Optional[Dict[str, Any]] = None


@app.post("/api/state")
async def update_system_state(req: UpdateStateRequest):
    """Patch or deploy strategy — all writes go through StateManager."""
    if req.active_strategy:
        result = run_real_backtest(req.active_strategy, save_as_active=True)
        new_state = result.get("state", state_manager.get())
        await manager.broadcast({"event_type": "STATE_UPDATED", "payload": new_state})
        return {"status": "SUCCESS", "state": new_state}

    updates: Dict[str, Any] = {}
    if req.target_profile:   updates["target_profile"]   = req.target_profile
    if req.status:           updates["status"]            = req.status
    if req.backtest_summary: updates["backtest_summary"]  = req.backtest_summary

    new_state = state_manager.patch(updates)
    await manager.broadcast({"event_type": "STATE_UPDATED", "payload": new_state})
    return {"status": "SUCCESS", "state": new_state}


@app.get("/api/backtest")
async def get_backtest_results(strategy: Optional[str] = None):
    if strategy:
        return run_real_backtest(strategy, save_as_active=False)
    active_strat = state_manager.get().get("active_strategy", "PropFirmVsaWickRejection")
    return run_real_backtest(active_strat, save_as_active=False)

@app.get("/api/signals/stats")
async def get_live_signal_stats():
    """Live performance stats — delegates to SignalStore (single source of truth)."""
    return signal_store.get_stats()


@app.get("/api/strategies")
async def list_strategies():
    strategies_dir = os.path.join(os.getcwd(), "strategies")
    os.makedirs(strategies_dir, exist_ok=True)
    
    strategy_files = []
    for file_name in os.listdir(strategies_dir):
        if file_name.endswith(".py"):
            file_path = os.path.join(strategies_dir, file_name)
            stat = os.stat(file_path)
            strategy_files.append({
                "name": file_name,
                "path": f"strategies/{file_name}",
                "size_bytes": stat.st_size,
                "last_modified": stat.st_mtime
            })
            
    return {"strategies": strategy_files, "total": len(strategy_files)}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            logger.debug(f"WS received: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)


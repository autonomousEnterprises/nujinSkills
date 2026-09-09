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
from server.data_manager import generate_sample_ohlcv
from server.backtest_engine import run_real_backtest

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
async def get_candles(symbol: str = "BTC/USDT", count: int = 200):
    return {"symbol": symbol, "data": generate_sample_ohlcv(symbol, count)}

@app.get("/api/widgets")
async def get_widgets():
    return {"widgets": list(manager.widget_state.values())}

@app.post("/api/broadcast")
async def broadcast_event(envelope: EventEnvelope):
    logger.info(f"Broadcast event received: {envelope.event_type}")
    await manager.broadcast(envelope.model_dump())
    if envelope.event_type in ["SIGNAL_TRIGGERED", "TELEGRAM_ALERT"]:
        telegram_gateway.format_and_send_signal(envelope.payload)
    elif envelope.event_type == "UPSERT_WIDGET" and envelope.payload.get("component") == "MetricCard":
        telegram_gateway.format_and_send_dsr_alert(envelope.payload)
    return {"status": "SUCCESS", "event_type": envelope.event_type}

@app.post("/api/bot/deploy")
async def deploy_bot(req: DeployBotRequest):
    return bot_supervisor.deploy_strategy(req.strategy, req.mode)

@app.post("/api/bot/stop")
async def stop_bot():
    return bot_supervisor.stop_bot()

@app.get("/api/bot/status")
async def get_bot_status():
    return bot_supervisor.get_status()

@app.post("/api/strategies/select")
async def select_and_run_strategy(req: SelectStrategyRequest):
    logger.info(f"Strategy selected via UI: {req.strategy}")
    result = run_real_backtest(req.strategy)
    await manager.broadcast({"event_type": "STATE_UPDATED", "payload": result["state"]})
    await manager.broadcast({"event_type": "BACKTEST_UPDATED", "payload": result})
    return result

@app.get("/api/state")
async def get_system_state():
    state_file = os.path.join(os.getcwd(), "data", "state.json")
    if os.path.exists(state_file):
        try:
            with open(state_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read state file: {e}")
    
    # Default fallback state
    return {
        "active_strategy": "PropFirmVsaWickRejection",
        "target_profile": "Prop Firm Challenge",
        "status": "ACTIVE_DEPLOYED",
        "backtest_summary": {
            "sharpe": 1.77,
            "win_rate": 0.556,
            "max_drawdown": 0.015,
            "mdd_99": 0.0331,
            "dsr": 0.96,
            "trades": 18
        },
        "signals_count": 1,
        "last_updated": "Just now"
    }

class UpdateStateRequest(BaseModel):
    active_strategy: Optional[str] = None
    target_profile: Optional[str] = None
    status: Optional[str] = None
    backtest_summary: Optional[Dict[str, Any]] = None

@app.post("/api/state")
async def update_system_state(req: UpdateStateRequest):
    if req.active_strategy:
        result = run_real_backtest(req.active_strategy)
        return {"status": "SUCCESS", "state": result["state"]}

    state_file = os.path.join(os.getcwd(), "data", "state.json")
    current_state = await get_system_state()
    
    if req.target_profile:
        current_state["target_profile"] = req.target_profile
    if req.status:
        current_state["status"] = req.status
    if req.backtest_summary:
        current_state["backtest_summary"] = req.backtest_summary
        
    os.makedirs(os.path.dirname(state_file), exist_ok=True)
    with open(state_file, "w") as f:
        json.dump(current_state, f, indent=2)
        
    await manager.broadcast({"event_type": "STATE_UPDATED", "payload": current_state})
    return {"status": "SUCCESS", "state": current_state}

@app.get("/api/backtest")
async def get_backtest_results():
    state = await get_system_state()
    active_strat = state.get("active_strategy", "PropFirmVsaWickRejection")
    return run_real_backtest(active_strat)

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


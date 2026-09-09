import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional

from server.websocket import manager
from server.telegram_bot import telegram_gateway
from server.bot_runner import bot_supervisor
from server.data_manager import generate_sample_ohlcv

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("NujinSkillServer")

app = FastAPI(
    title="NujinSkill Telemetry & Signal Gateway API",
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

@app.get("/api/health")
async def health_check():
    return {
        "status": "ONLINE",
        "service": "NujinSkill Telemetry Server",
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
    
    # 1. Dispatch to WebSockets
    await manager.broadcast(envelope.model_dump())
    
    # 2. Relay to Telegram Gateway if signal or audit alert
    if envelope.event_type in ["SIGNAL_TRIGGERED", "TELEGRAM_ALERT"]:
        telegram_gateway.format_and_send_signal(envelope.payload)
    elif envelope.event_type == "UPSERT_WIDGET" and envelope.payload.get("component") == "MetricCard":
        telegram_gateway.format_and_send_dsr_alert(envelope.payload)
        
    return {"status": "SUCCESS", "event_type": envelope.event_type}

@app.post("/api/bot/deploy")
async def deploy_bot(req: DeployBotRequest):
    result = bot_supervisor.deploy_strategy(req.strategy, req.mode)
    return result

@app.post("/api/bot/stop")
async def stop_bot():
    return bot_supervisor.stop_bot()

@app.get("/api/bot/status")
async def get_bot_status():
    return bot_supervisor.get_status()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection open and listen for ping/pong or client messages
            data = await websocket.receive_text()
            logger.debug(f"WS received: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

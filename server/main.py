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
    signals_file = os.path.join(os.getcwd(), "data", "signals.json")
    signals_list = []
    if os.path.exists(signals_file):
        try:
            with open(signals_file, "r") as f:
                signals_list = json.load(f)
        except Exception as e:
            logger.error(f"Error reading signals file: {e}")

    # Fallback initial sample signals if file is empty
    if len(signals_list) == 0:
        signals_list = [
            {
                "id": 1,
                "time": 1725883200,
                "pair": "BTC/USDT",
                "action": "BUY",
                "price": 63404.0,
                "stop_loss": 61819.0,
                "take_profit": 65948.0,
                "status": "ACTIVE_IN_POSITION",
                "exit_price": None,
                "exit_reason": None,
                "pnl_pct": 1.25,
                "annotation": "VSA Wick Rejection",
                "reasoning_md": "Lower wick expansion (> 40%) with Volume Z-Score > 1.0 absorbing seller liquidity.",
                "strategy": "PropFirmVsaWickRejectionStrategy"
            },
            {
                "id": 2,
                "time": 1725868800,
                "pair": "BTC/USDT",
                "action": "BUY",
                "price": 62150.0,
                "stop_loss": 60907.0,
                "take_profit": 64325.0,
                "status": "CLOSED",
                "exit_price": 64325.0,
                "exit_reason": "TAKE_PROFIT",
                "pnl_pct": 3.50,
                "annotation": "Trap Fade Sweep",
                "reasoning_md": "Asian Session Low sweep reversal into passive limit buy order block.",
                "strategy": "TrapFadeStrategy"
            }
        ]

    active = next((s for s in signals_list if s.get("status") == "ACTIVE_IN_POSITION"), signals_list[0] if len(signals_list) > 0 else None)
    return {"signals": signals_list, "active_signal": active}

@app.post("/api/broadcast")
async def broadcast_event(envelope: EventEnvelope):
    logger.info(f"Broadcast event received: {envelope.event_type}")
    await manager.broadcast(envelope.model_dump())

    if envelope.event_type == "SIGNAL_TRIGGERED":
        telegram_gateway.format_and_send_signal(envelope.payload)
        
        # Persist to data/signals.json on disk
        signals_file = os.path.join(os.getcwd(), "data", "signals.json")
        signals_list = []
        if os.path.exists(signals_file):
            try:
                with open(signals_file, "r") as f:
                    signals_list = json.load(f)
            except Exception as e:
                logger.error(f"Error reading signals file before write: {e}")

        # Construct persistent signal entry
        sig_data = envelope.payload
        sig_entry = {
            "id": len(signals_list) + 1,
            "time": sig_data.get("time", 1725883200),
            "pair": sig_data.get("pair", "BTC/USDT"),
            "action": sig_data.get("action", "BUY"),
            "price": float(sig_data.get("price", 63404.0)),
            "stop_loss": float(sig_data.get("stop_loss", sig_data.get("price", 63404.0) * 0.975)),
            "take_profit": float(sig_data.get("take_profit", sig_data.get("price", 63404.0) * 1.04)),
            "status": sig_data.get("status", "ACTIVE_IN_POSITION"),
            "exit_price": sig_data.get("exit_price"),
            "exit_reason": sig_data.get("exit_reason"),
            "pnl_pct": float(sig_data.get("pnl_pct", 0.0)),
            "annotation": sig_data.get("annotation", "AI Live Signal"),
            "reasoning_md": sig_data.get("reasoning_md", "AI Agent executed live signal rule condition."),
            "strategy": sig_data.get("strategy", "PropFirmVsaWickRejectionStrategy")
        }
        signals_list.insert(0, sig_entry)
        
        with open(signals_file, "w") as f:
            json.dump(signals_list, f, indent=2)
            
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
    state_file = os.path.join(os.getcwd(), "data", "state.json")
    current_state = await get_system_state()
    current_state["status"] = "STOPPED"
    with open(state_file, "w") as f:
        json.dump(current_state, f, indent=2)
    await manager.broadcast({"event_type": "STATE_UPDATED", "payload": current_state})
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
        result = run_real_backtest(req.active_strategy, save_as_active=True)
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
async def get_backtest_results(strategy: Optional[str] = None):
    if strategy:
        return run_real_backtest(strategy, save_as_active=False)
    state = await get_system_state()
    active_strat = state.get("active_strategy", "PropFirmVsaWickRejection")
    return run_real_backtest(active_strat, save_as_active=False)

@app.get("/api/signals/stats")
async def get_live_signal_stats():
    """Compute live performance stats from all persisted signals since strategy activation."""
    import math
    signals_file = os.path.join(os.getcwd(), "data", "signals.json")
    signals_list = []
    if os.path.exists(signals_file):
        try:
            with open(signals_file, "r") as f:
                signals_list = json.load(f)
        except Exception:
            pass

    # Closed trades only (have exit_reason and pnl_pct set)
    closed = [s for s in signals_list if s.get("exit_reason") and s.get("pnl_pct") is not None]
    open_trades = [s for s in signals_list if s.get("status") == "ACTIVE_IN_POSITION"]

    total_trades = len(closed)
    wins = [s for s in closed if s.get("pnl_pct", 0) > 0]
    losses = [s for s in closed if s.get("pnl_pct", 0) <= 0]

    win_rate = len(wins) / total_trades if total_trades > 0 else 0.0
    gross_profit = sum(s.get("pnl_pct", 0) for s in wins)
    gross_loss = abs(sum(s.get("pnl_pct", 0) for s in losses))
    profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else (99.0 if gross_profit > 0 else 0.0)
    total_pnl = round(sum(s.get("pnl_pct", 0) for s in closed), 2)
    avg_win = round(gross_profit / len(wins), 2) if wins else 0.0
    avg_loss = round(gross_loss / len(losses), 2) if losses else 0.0

    # Sharpe since activation (annualized, daily returns proxy)
    returns = [s.get("pnl_pct", 0) for s in closed]
    if len(returns) > 1:
        mean_r = sum(returns) / len(returns)
        variance = sum((r - mean_r) ** 2 for r in returns) / len(returns)
        std_r = math.sqrt(variance) if variance > 0 else 1e-8
        sharpe_live = round((mean_r / std_r) * math.sqrt(252), 2)
    else:
        sharpe_live = 0.0

    # Max consecutive losses
    max_consec_loss = 0
    cur_consec = 0
    for s in closed:
        if s.get("pnl_pct", 0) <= 0:
            cur_consec += 1
            max_consec_loss = max(max_consec_loss, cur_consec)
        else:
            cur_consec = 0

    return {
        "total_trades": total_trades,
        "open_trades": len(open_trades),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": round(win_rate, 4),
        "profit_factor": profit_factor,
        "sharpe_live": sharpe_live,
        "total_pnl_pct": total_pnl,
        "avg_win_pct": avg_win,
        "avg_loss_pct": avg_loss,
        "gross_profit_pct": round(gross_profit, 2),
        "gross_loss_pct": round(gross_loss, 2),
        "max_consecutive_losses": max_consec_loss
    }


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


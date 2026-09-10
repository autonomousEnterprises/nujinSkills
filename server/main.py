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
from server.data_manager import fetch_real_binance_klines
from server.backtest_engine import run_real_backtest
from server.xauusd_streamer import xauusd_engine

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

class StartTradeRequest(BaseModel):
    side: str
    entry_price: Optional[float] = None
    account_size: Optional[float] = 100000.0
    lots: Optional[float] = 1.0

@app.get("/api/health")
async def health_check():
    return {
        "status": "ONLINE",
        "service": "NujinSkills Telemetry Server",
        "connections": len(manager.active_connections),
        "bot_status": bot_supervisor.get_status(),
        "telegram_status": {
            "configured": telegram_gateway.is_configured,
            "has_token": bool(telegram_gateway.bot_token),
            "has_chat_id": bool(telegram_gateway.chat_id)
        }
    }

@app.get("/api/system/status")
async def get_system_status():
    return {
        "status": "ONLINE",
        "connections": len(manager.active_connections),
        "bot": bot_supervisor.get_status(),
        "telegram": {
            "configured": telegram_gateway.is_configured,
            "has_token": bool(telegram_gateway.bot_token),
            "has_chat_id": bool(telegram_gateway.chat_id)
        },
        "active_strategy": state_manager.get().get("active_strategy", "PropFirmVsaWickRejection")
    }

@app.get("/api/candles")
async def get_candles(symbol: Optional[str] = None, count: int = 1500, mode: str = "live"):
    """
    Returns real OHLCV candles from Binance public API.
    Auto-detects symbol and timeframe based on active strategy (XAU/USD 1m vs BTC/USDT 15m).
    """
    if not symbol:
        active_strat = state_manager.get().get("active_strategy", "GoatFundedTraderXauusdScalper")
        is_gold = ("XAU" in active_strat.upper()) or ("GOAT" in active_strat.upper())
        symbol = "XAU/USD" if is_gold else "BTC/USDT"

    is_xau = ("XAU" in symbol.upper()) or ("GOLD" in symbol.upper()) or ("OANDA" in symbol.upper()) or ("PAXG" in symbol.upper()) or ("GC" in symbol.upper())
    interval = "1m" if is_xau else "15m"
    try:
        if is_xau:
            from server.data_manager import fetch_real_oanda_candles
            data = fetch_real_oanda_candles(interval=interval, count=count)
        else:
            data = fetch_real_binance_klines(symbol=symbol, interval=interval, count=count)
    except Exception as e:
        logger.error(f"[Candles] Failed to fetch real data for {symbol}: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Real market data unavailable for {symbol}. Error: {str(e)}"
        )
    return {"symbol": symbol, "timeframe": interval, "mode": mode, "data": data}


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


# ── XAUUSD & Goat Funded Trader Prop Scalping Endpoints ──────────────────────
@app.on_event("startup")
async def startup_event():
    import asyncio
    logger.info("[NujinSkillsServer] Launching XAUUSD Live Keyless Streamer & Signal Monitor...")
    asyncio.create_task(xauusd_engine.run_live_feed(manager.broadcast))


@app.get("/api/xauusd/quote")
async def get_xauusd_quote():
    """Live XAUUSD real-time quote, session filter status, indicators & active signal."""
    return {
        "quote": xauusd_engine.current_quote,
        "session": xauusd_engine.is_session_active(),
        "indicators": xauusd_engine.compute_indicators(),
        "signal": xauusd_engine.generate_signal()
    }


@app.get("/api/xauusd/rules/gft")
async def get_gft_rules(account_size: float = 100000.0):
    """Calculates strict Goat Funded Trader prop firm drawdown limits and 15% consistency cap."""
    profit_target = account_size * 0.08
    return {
        "account_size": account_size,
        "daily_drawdown_limit_3pct": round(account_size * 0.03, 2),
        "max_drawdown_limit_6pct": round(account_size * 0.06, 2),
        "recommended_daily_loss_budget": round(account_size * 0.015, 2),
        "recommended_per_trade_risk": round(account_size * 0.005, 2),
        "consistency_15pct_daily_profit_cap": round(profit_target * 0.15, 2),
        "min_holding_seconds": 120,
        "max_holding_seconds": 900,
        "trading_sessions": [
            {"session": "London", "window_utc": "07:30 - 10:30 UTC"},
            {"session": "New York", "window_utc": "12:45 - 16:30 UTC"}
        ]
    }


@app.post("/api/xauusd/trade/start")
async def start_xauusd_trade(req: StartTradeRequest):
    """Starts tracking a manual XAUUSD scalp trade with 2m-15m countdown timer."""
    status = xauusd_engine.start_manual_trade(
        side=req.side,
        entry_price=req.entry_price,
        account_size=req.account_size or 100000.0,
        lots=req.lots or 1.0
    )
    await manager.broadcast({"event_type": "XAUUSD_TRADE_STARTED", "payload": status})
    return status


@app.get("/api/xauusd/trade/status")
async def get_xauusd_trade_status():
    """Returns active trade timer (RED if < 120s, GREEN if >= 120s, ALERT if > 900s) and PnL."""
    return xauusd_engine.get_active_trade_status()


@app.post("/api/xauusd/trade/close")
async def close_xauusd_trade():
    """Closes active trade and logs result."""
    res = xauusd_engine.close_manual_trade()
    await manager.broadcast({"event_type": "XAUUSD_TRADE_CLOSED", "payload": res})
    return res



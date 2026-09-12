import logging
import os
import sys
import time
import json
import shutil
import subprocess
import threading
from datetime import datetime, timezone
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
from server.state_manager import state_manager, signal_store, strategy_registry

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

class UpdateStrategyStatusRequest(BaseModel):
    strategy: str
    status: str  # ACTIVE_LIVE | CRON_BACKTEST | DEACTIVATED
    exclusive: Optional[bool] = False

class RunStrategyBacktestRequest(BaseModel):
    strategy: str

class CloseSignalRequest(BaseModel):
    id: Optional[int] = None
    strategy: Optional[str] = None
    exit_price: float
    exit_reason: Optional[str] = "MANUAL_CLOSE"
    pnl_pct: Optional[float] = None

class ClearSignalsRequest(BaseModel):
    strategy: Optional[str] = None

class StopBotRequest(BaseModel):
    strategy: Optional[str] = None

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
async def get_candles(symbol: Optional[str] = None, count: int = 20000, mode: str = "live"):
    """
    Returns real OHLCV candles from CME / Binance / OANDA public APIs or local cache bridged to current time.
    Auto-detects symbol and timeframe based on active strategy (S&P 500 1m vs XAU/USD 1m vs BTC/USDT 15m).
    """
    if not symbol:
        active_strat = state_manager.get().get("active_strategy", "OpeningFlushReversalScalper")
        is_sp = any(k in active_strat.upper() for k in ["SP", "ES", "OPENING"])
        is_gold = any(k in active_strat.upper() for k in ["XAU", "GOAT"])
        symbol = "S&P 500 (ES)" if is_sp else ("XAU/USD" if is_gold else "BTC/USDT")

    is_sp = any(k in symbol.upper() for k in ["SP", "ES", "S&P", "US500", "OPENING"])
    is_xau = any(k in symbol.upper() for k in ["XAU", "GOLD", "OANDA", "PAXG", "GC"])
    interval = "1m" if (is_xau or is_sp) else "15m"
    try:
        if is_sp:
            csv_path = "data/sp500_candles_1m.csv"
            if os.path.exists(csv_path):
                import pandas as pd
                from server.data_manager import bridge_candles_to_now
                df = pd.read_csv(csv_path)
                df = bridge_candles_to_now(df, interval="1m", symbol=symbol)
                records = df.tail(count).to_dict(orient="records") if (count and count > 0 and count < len(df)) else df.to_dict(orient="records")
                data = [
                    {
                        "time": int(r.get("timestamp", r.get("time", 0))),
                        "open": round(float(r["open"]), 2),
                        "high": round(float(r["high"]), 2),
                        "low": round(float(r["low"]), 2),
                        "close": round(float(r["close"]), 2),
                        "volume": round(float(r.get("volume", 10.0)), 4)
                    }
                    for r in records
                ]
            else:
                raise FileNotFoundError(f"Dataset {csv_path} not found")
        elif is_xau:
            from server.data_manager import fetch_real_oanda_candles
            data = fetch_real_oanda_candles(interval=interval, count=count)
        else:
            data = fetch_real_binance_klines(symbol=symbol, interval=interval, count=count)
    except Exception as e:
        logger.error(f"[Candles] Failed to fetch real data for {symbol}: {e}")
        # Robust fallback to cached dataset with automatic bridging up to current time
        csv_path = "data/sp500_candles_1m.csv" if is_sp else ("data/xauusd_candles_1m.csv" if is_xau else "data/candles_15m.csv")
        if os.path.exists(csv_path):
            try:
                import pandas as pd
                from server.data_manager import bridge_candles_to_now
                df = pd.read_csv(csv_path)
                df = bridge_candles_to_now(df, interval=interval, symbol=symbol)
                records = df.tail(count).to_dict(orient="records") if (count and count > 0 and count < len(df)) else df.to_dict(orient="records")
                data = [
                    {
                        "time": int(r.get("timestamp", r.get("time", 0))),
                        "open": round(float(r["open"]), 2),
                        "high": round(float(r["high"]), 2),
                        "low": round(float(r["low"]), 2),
                        "close": round(float(r["close"]), 2),
                        "volume": round(float(r.get("volume", 10.0)), 4)
                    }
                    for r in records
                ]
            except Exception as e_csv:
                raise HTTPException(
                    status_code=503,
                    detail=f"Real market data unavailable for {symbol}. Error: {str(e)} (Cache fallback error: {e_csv})"
                )
        else:
            raise HTTPException(
                status_code=503,
                detail=f"Real market data unavailable for {symbol}. Error: {str(e)}"
            )
    return {"symbol": symbol, "timeframe": interval, "mode": mode, "data": data}


@app.get("/api/widgets")
async def get_widgets():
    return {"widgets": list(manager.widget_state.values())}

@app.get("/api/signals")
async def get_signals(strategy: Optional[str] = None):
    signals_list = signal_store.get_all(strategy)
    active = signal_store.get_active(strategy)
    all_actives = signal_store.get_active_signals()
    return {
        "signals": signals_list,
        "active_signal": active,
        "active_signals": all_actives,
        "total": len(signals_list)
    }

@app.post("/api/signals/clear")
async def clear_signals(req: Optional[ClearSignalsRequest] = None):
    strat = req.strategy if req else None
    remaining = signal_store.clear(strat)
    await manager.broadcast({"event_type": "SIGNALS_CLEARED", "payload": {"strategy": strat, "remaining": len(remaining)}})
    
    # Broadcast updated strategy live metrics & portfolio summary
    all_strats = strategy_registry.get_all(sync=False)
    portfolio = strategy_registry.get_portfolio_summary()
    distribution = strategy_registry.get_distribution_analytics()
    await manager.broadcast({
        "event_type": "STRATEGIES_UPDATED",
        "payload": {
            "strategies": all_strats,
            "portfolio_summary": portfolio,
            "distribution_analytics": distribution
        }
    })
    return {"status": "SUCCESS", "message": f"Signals cleared{' for ' + strat if strat else ''}."}

@app.post("/api/signals/close")
async def close_signal_position(req: CloseSignalRequest):
    closed = signal_store.close_position(
        signal_id=req.id,
        strategy=req.strategy,
        exit_price=req.exit_price,
        exit_reason=req.exit_reason or "MANUAL_CLOSE",
        pnl_pct=req.pnl_pct
    )
    if not closed:
        raise HTTPException(status_code=404, detail="No active position found matching criteria")
    await manager.broadcast({"event_type": "SIGNAL_CLOSED", "payload": closed})

    # Broadcast updated strategy live metrics & portfolio summary
    all_strats = strategy_registry.get_all(sync=False)
    portfolio = strategy_registry.get_portfolio_summary()
    distribution = strategy_registry.get_distribution_analytics()
    await manager.broadcast({
        "event_type": "STRATEGIES_UPDATED",
        "payload": {
            "strategies": all_strats,
            "portfolio_summary": portfolio,
            "distribution_analytics": distribution
        }
    })
    return {"status": "SUCCESS", "closed_signal": closed}

def play_system_alert(action: str = "SIGNAL"):
    """
    Plays an audible system chime on Linux in a non-blocking background thread.
    Tries paplay, canberra-gtk-play, pw-play, aplay, and terminal bell fallback.
    """
    def _play():
        try:
            is_buy = "BUY" in action.upper() or "LONG" in action.upper()
            sound_theme = "complete" if is_buy else "bell"
            sound_path = f"/usr/share/sounds/freedesktop/stereo/{sound_theme}.oga"

            played = False
            # 1. Prefer paplay (direct PulseAudio/PipeWire, ultra-low latency)
            if shutil.which("paplay") and os.path.exists(sound_path):
                subprocess.Popen(
                    ["paplay", sound_path],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                played = True

            # 2. Canberra GTK play
            if not played and shutil.which("canberra-gtk-play"):
                subprocess.Popen(
                    ["canberra-gtk-play", "-i", sound_theme],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                played = True

            # 3. pw-play (PipeWire)
            if not played and shutil.which("pw-play") and os.path.exists(sound_path):
                subprocess.Popen(
                    ["pw-play", sound_path],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                played = True

            # Terminal bell fallback
            sys.stdout.write("\a")
            sys.stdout.flush()
            logger.info(f"[SystemAlert] Played desktop audio chime for action: {action} (played={played})")
        except Exception as e:
            logger.warning(f"[SystemAlert] Audio playback error: {e}")

    threading.Thread(target=_play, daemon=True).start()


@app.post("/api/broadcast")
async def broadcast_event(envelope: EventEnvelope):
    logger.info(f"Broadcast event received: {envelope.event_type}")
    await manager.broadcast(envelope.model_dump())

    if envelope.event_type == "SIGNAL_TRIGGERED":
        # Play local system tone in background
        play_system_alert(envelope.payload.get("action", ""))

        # Resolve strategy name if missing in payload
        if not envelope.payload.get("strategy"):
            envelope.payload["strategy"] = state_manager.get().get("active_strategy", "PropFirmVsaWickRejection")
        signal_store.add(envelope.payload)          # ← StateManager handles file I/O + signals_count bump
        telegram_gateway.format_and_send_signal(envelope.payload)

        # Broadcast updated strategy live metrics & portfolio summary
        all_strats = strategy_registry.get_all(sync=False)
        portfolio = strategy_registry.get_portfolio_summary()
        distribution = strategy_registry.get_distribution_analytics()
        await manager.broadcast({
            "event_type": "STRATEGIES_UPDATED",
            "payload": {
                "strategies": all_strats,
                "portfolio_summary": portfolio,
                "distribution_analytics": distribution
            }
        })
    elif envelope.event_type == "TELEGRAM_ALERT":
        play_system_alert(envelope.payload.get("action", ""))
        telegram_gateway.format_and_send_signal(envelope.payload)
    elif envelope.event_type == "UPSERT_WIDGET" and envelope.payload.get("component") == "MetricCard":
        telegram_gateway.format_and_send_dsr_alert(envelope.payload)
    return {"status": "SUCCESS", "event_type": envelope.event_type}


@app.post("/api/bot/deploy")
async def deploy_bot(req: DeployBotRequest):
    logger.info(f"Activating & deploying strategy for system: {req.strategy}")
    bt_result = run_real_backtest(req.strategy, save_as_active=True)
    bot_supervisor.set_broadcast_callback(manager.broadcast)
    res = bot_supervisor.deploy_strategy(req.strategy, req.mode)
    await manager.broadcast({"event_type": "STATE_UPDATED", "payload": bt_result["state"]})
    return {**res, "state": bt_result["state"]}

@app.post("/api/bot/stop")
async def stop_bot(req: Optional[StopBotRequest] = None):
    strat = req.strategy if req else None
    res = bot_supervisor.stop_bot(strat)
    if strat:
        state_manager.update_status(strat, "DEACTIVATED")
    else:
        for s in state_manager.get().get("active_strategies", []):
            state_manager.update_status(s, "DEACTIVATED")
        state_manager.patch({"status": "STOPPED"})
    new_state = state_manager.get()
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
async def get_live_signal_stats(strategy: Optional[str] = None):
    """Live performance stats — delegates to SignalStore (single source of truth)."""
    return signal_store.get_stats(strategy)


@app.get("/api/strategies")
async def list_strategies():
    strategies_dir = os.path.join(os.getcwd(), "strategies")
    os.makedirs(strategies_dir, exist_ok=True)
    
    # Sync with registry so file list & registry always match
    managed = strategy_registry.get_all(sync=True)
    
    strategy_files = []
    for s in managed:
        file_name = s.get("file") or f"{s.get('name')}.py"
        file_path = os.path.join(strategies_dir, file_name)
        stat_size = 0
        stat_mtime = 0
        if os.path.exists(file_path):
            st = os.stat(file_path)
            stat_size = st.st_size
            stat_mtime = st.st_mtime
        strategy_files.append({
            "name": file_name,
            "path": f"strategies/{file_name}",
            "display_name": s.get("display_name", file_name.replace(".py", "")),
            "size_bytes": stat_size,
            "last_modified": stat_mtime,
            "status": s.get("status", "DEACTIVATED"),
            "rank": s.get("rank", 99),
            "tier": s.get("tier", "C-Tier"),
            "sharpe": s.get("latest_backtest", {}).get("sharpe", 0.0),
            "win_rate": s.get("latest_backtest", {}).get("win_rate", 0.0),
        })
        
    return {"strategies": strategy_files, "total": len(strategy_files)}


@app.post("/api/strategies/sync")
async def sync_strategies_endpoint():
    """Explicit endpoint to force strategy filesystem re-scan & WebSocket broadcast."""
    all_strats = strategy_registry.sync_with_filesystem()
    portfolio = strategy_registry.get_portfolio_summary()
    distribution = strategy_registry.get_distribution_analytics()
    payload = {
        "strategies": all_strats,
        "portfolio_summary": portfolio,
        "distribution_analytics": distribution
    }
    await manager.broadcast({"event_type": "STRATEGIES_UPDATED", "payload": payload})
    return {"status": "SUCCESS", "total": len(all_strats), **payload}


# ── Strategy Management System Endpoints ─────────────────────────────────────
@app.get("/api/strategies/manage")
async def get_managed_strategies():
    """Returns full list of managed strategies with rankings, stats, portfolio summary, and distribution analytics."""
    strats = strategy_registry.get_all(sync=True)
    portfolio = strategy_registry.get_portfolio_summary()
    distribution = strategy_registry.get_distribution_analytics()
    return {
        "strategies": strats,
        "total": len(strats),
        "portfolio_summary": portfolio,
        "distribution_analytics": distribution
    }


@app.get("/api/strategies/manage/portfolio")
async def get_portfolio_overview():
    """Returns aggregated portfolio performance across all active strategies plus drift distribution."""
    return {
        "portfolio_summary": strategy_registry.get_portfolio_summary(),
        "distribution_analytics": strategy_registry.get_distribution_analytics()
    }


@app.post("/api/strategies/manage/status")
async def update_managed_strategy_status(req: UpdateStrategyStatusRequest):
    """Update strategy lifecycle status: ACTIVE_LIVE, CRON_BACKTEST, DEACTIVATED with multi-strategy support."""
    updated = strategy_registry.update_status(req.strategy, req.status, exclusive=bool(req.exclusive))
    if req.status == "ACTIVE_LIVE":
        bot_supervisor.deploy_strategy(req.strategy, mode="dry-run")
        await manager.broadcast({"event_type": "STATE_UPDATED", "payload": state_manager.get()})
    elif req.status in ("CRON_BACKTEST", "DEACTIVATED"):
        bot_supervisor.stop_strategy(req.strategy)
        await manager.broadcast({"event_type": "STATE_UPDATED", "payload": state_manager.get()})
    
    all_strats = strategy_registry.get_all(sync=False)
    portfolio = strategy_registry.get_portfolio_summary()
    distribution = strategy_registry.get_distribution_analytics()
    
    payload = {
        "strategies": all_strats,
        "portfolio_summary": portfolio,
        "distribution_analytics": distribution
    }
    await manager.broadcast({"event_type": "STRATEGIES_UPDATED", "payload": payload})
    return {"status": "SUCCESS", "strategy": updated, **payload}


@app.post("/api/strategies/manage/run-backtest")
async def run_managed_strategy_backtest(req: RunStrategyBacktestRequest):
    """Execute on-demand quantitative backtest for a strategy and update registry."""
    result = run_real_backtest(req.strategy, save_as_active=False)
    all_strats = strategy_registry.get_all(sync=False)
    portfolio = strategy_registry.get_portfolio_summary()
    distribution = strategy_registry.get_distribution_analytics()
    payload = {
        "strategies": all_strats,
        "portfolio_summary": portfolio,
        "distribution_analytics": distribution
    }
    await manager.broadcast({"event_type": "STRATEGIES_UPDATED", "payload": payload})
    return {"status": "SUCCESS", "result": result, **payload}


@app.post("/api/strategies/manage/cron-trigger")
async def trigger_cron_evaluations():
    """Trigger periodic backtest evaluations across all strategies marked CRON_BACKTEST."""
    strats = strategy_registry.get_all(sync=False)
    cron_targets = [s for s in strats if s.get("status") == "CRON_BACKTEST"]
    evaluated = []
    for s in cron_targets:
        try:
            res = run_real_backtest(s["file"], save_as_active=False)
            strategy_registry.record_backtest(s["name"], res, is_cron=True)
            evaluated.append(s["name"])
        except Exception as e:
            logger.error(f"[CronScheduler] Backtest failed for {s['name']}: {e}")
    all_strats = strategy_registry.get_all(sync=False)
    portfolio = strategy_registry.get_portfolio_summary()
    distribution = strategy_registry.get_distribution_analytics()
    payload = {
        "strategies": all_strats,
        "portfolio_summary": portfolio,
        "distribution_analytics": distribution
    }
    await manager.broadcast({"event_type": "STRATEGIES_UPDATED", "payload": payload})
    return {"status": "SUCCESS", "evaluated": evaluated, **payload}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            logger.debug(f"WS received: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ── Periodic Cron Backtest Background Loop (Daily / Once a day) ────────────
async def cron_backtest_scheduler():
    """Periodically evaluates CRON_BACKTEST strategies once a day (86400s) to track drift."""
    import asyncio
    while True:
        # Evaluate once every 24 hours (86,400 seconds)
        await asyncio.sleep(86400)
        try:
            strats = strategy_registry.get_all(sync=False)
            cron_targets = [s for s in strats if s.get("status") == "CRON_BACKTEST"]
            if cron_targets:
                logger.info(f"[CronScheduler] Daily evaluation of {len(cron_targets)} CRON_BACKTEST strategies...")
                for s in cron_targets:
                    try:
                        res = run_real_backtest(s["file"], save_as_active=False)
                        strategy_registry.record_backtest(s["name"], res, is_cron=True)
                    except Exception as e_c:
                        logger.warning(f"[CronScheduler] Error evaluating {s['name']}: {e_c}")
                all_strats = strategy_registry.get_all(sync=False)
                portfolio = strategy_registry.get_portfolio_summary()
                distribution = strategy_registry.get_distribution_analytics()
                await manager.broadcast({
                    "event_type": "STRATEGIES_UPDATED",
                    "payload": {
                        "strategies": all_strats,
                        "portfolio_summary": portfolio,
                        "distribution_analytics": distribution
                    }
                })
        except Exception as e:
            logger.error(f"[CronScheduler] Daily loop error: {e}")



# ── Real-Time Strategy File & Disk State Auto-Discovery Watcher ─────────────
async def strategy_auto_discovery_watcher():
    """
    Watches strategies/*.py directory and data/strategies.json for changes.
    When a new strategy is created (by AI agent, CLI tool, or user):
      1. Automatically registers it in strategy_registry.
      2. Automatically executes an initial quantitative backtest in a worker thread.
      3. Broadcasts STRATEGY_DISCOVERED and STRATEGIES_UPDATED over WebSocket.
    When an existing strategy is modified or deleted:
      Syncs filesystem and broadcasts STRATEGIES_UPDATED.
    """
    import asyncio
    strategies_dir = os.path.join(os.getcwd(), "strategies")
    os.makedirs(strategies_dir, exist_ok=True)
    strategies_json = os.path.join(os.getcwd(), "data", "strategies.json")

    def _get_strategies_snapshot():
        snap = {}
        if os.path.exists(strategies_dir):
            for fname in os.listdir(strategies_dir):
                if fname.endswith(".py"):
                    fpath = os.path.join(strategies_dir, fname)
                    try:
                        st = os.stat(fpath)
                        snap[fname] = (st.st_mtime, st.st_size)
                    except OSError:
                        pass
        return snap

    def _get_json_mtime():
        if os.path.exists(strategies_json):
            try:
                return os.path.getmtime(strategies_json)
            except OSError:
                return 0.0
        return 0.0

    known_files = _get_strategies_snapshot()
    last_json_mtime = _get_json_mtime()
    logger.info(f"[StrategyWatcher] Initialized real-time strategy watcher with {len(known_files)} strategies on disk.")

    while True:
        await asyncio.sleep(1.5)
        try:
            curr_files = _get_strategies_snapshot()
            curr_json_mtime = _get_json_mtime()

            new_files = set(curr_files.keys()) - set(known_files.keys())
            removed_files = set(known_files.keys()) - set(curr_files.keys())
            modified_files = {
                f for f in curr_files.keys() & known_files.keys()
                if curr_files[f] != known_files[f]
            }

            has_file_changes = bool(new_files or removed_files or modified_files)
            json_changed_externally = (curr_json_mtime != last_json_mtime and not has_file_changes)

            if has_file_changes:
                logger.info(f"[StrategyWatcher] Detected strategy changes: new={list(new_files)}, modified={list(modified_files)}, removed={list(removed_files)}")
                
                # Sync filesystem state with strategy registry
                all_strats = strategy_registry.sync_with_filesystem()

                # For brand new strategies, run an initial quantitative backtest in background thread
                for new_file in new_files:
                    clean_name = new_file.replace(".py", "")
                    meta = strategy_registry._infer_metadata(new_file)
                    logger.info(f"[StrategyWatcher] 🚀 New strategy discovered: {new_file} ({meta.get('display_name')}). Emitting discovery & running initial backtest...")
                    
                    # Notify frontend immediately of discovery
                    await manager.broadcast({
                        "event_type": "STRATEGY_DISCOVERED",
                        "payload": {
                            "strategy": clean_name,
                            "file": new_file,
                            "display_name": meta.get("display_name", clean_name),
                            "target_profile": meta.get("target_profile", ""),
                            "thesis": meta.get("thesis", ""),
                            "symbol": meta.get("symbol", "BTC/USDT"),
                            "timeframe": meta.get("timeframe", "15m")
                        }
                    })

                    try:
                        # Run real backtest in worker thread so we don't block the async event loop
                        await asyncio.to_thread(run_real_backtest, new_file, save_as_active=False)
                        logger.info(f"[StrategyWatcher] Initial backtest complete for {new_file}")
                    except Exception as bt_err:
                        logger.warning(f"[StrategyWatcher] Initial backtest error for {new_file}: {bt_err}")

                # Re-fetch after backtests
                all_strats = strategy_registry.get_all(sync=False)
                portfolio = strategy_registry.get_portfolio_summary()
                distribution = strategy_registry.get_distribution_analytics()

                await manager.broadcast({
                    "event_type": "STRATEGIES_UPDATED",
                    "payload": {
                        "strategies": all_strats,
                        "portfolio_summary": portfolio,
                        "distribution_analytics": distribution
                    }
                })

                known_files = curr_files
                last_json_mtime = _get_json_mtime()

            elif json_changed_externally:
                logger.info(f"[StrategyWatcher] data/strategies.json changed externally. Broadcasting update...")
                all_strats = strategy_registry.get_all(sync=False)
                portfolio = strategy_registry.get_portfolio_summary()
                distribution = strategy_registry.get_distribution_analytics()

                await manager.broadcast({
                    "event_type": "STRATEGIES_UPDATED",
                    "payload": {
                        "strategies": all_strats,
                        "portfolio_summary": portfolio,
                        "distribution_analytics": distribution
                    }
                })
                last_json_mtime = curr_json_mtime

        except Exception as e:
            logger.error(f"[StrategyWatcher] Auto-discovery loop error: {e}")


# ── XAUUSD & Goat Funded Trader Prop Scalping Endpoints ──────────────────────
@app.on_event("startup")
async def startup_event():
    import asyncio
    bot_supervisor.set_broadcast_callback(manager.broadcast)
    logger.info("[NujinSkillsServer] Launching XAUUSD Live Keyless Streamer & Signal Monitor...")
    asyncio.create_task(xauusd_engine.run_live_feed(manager.broadcast))
    logger.info("[NujinSkillsServer] Launching Periodic Strategy Cron Backtest Scheduler...")
    asyncio.create_task(cron_backtest_scheduler())
    logger.info("[NujinSkillsServer] Launching Strategy Auto-Discovery File Watcher...")
    asyncio.create_task(strategy_auto_discovery_watcher())

    # Automatically resume existing managed active strategies without running backtests
    try:
        active_strats = [s["name"] for s in strategy_registry.get_all(sync=False) if s.get("status") == "ACTIVE_LIVE"]
        for s_name in active_strats:
            bot_supervisor.deploy_strategy(s_name, mode="dry-run")
            logger.info(f"[NujinSkillsServer] Resumed managed active strategy: {s_name}")
    except Exception as e:
        logger.warning(f"[NujinSkillsServer] Error resuming active strategies on startup: {e}")



@app.get("/api/sp500/quote")
async def get_sp500_quote():
    """Live S&P 500 / ES real-time quote, session filter status, indicators & active signal."""
    csv_path = "data/sp500_candles_1m.csv"
    price = 7660.0
    open_p = 7661.0
    high_p = 7661.5
    low_p = 7659.5
    vol = 300.0
    chg = 0.0
    ts = int(time.time())
    if os.path.exists(csv_path):
        try:
            import pandas as pd
            from server.data_manager import bridge_candles_to_now
            df = pd.read_csv(csv_path)
            df = bridge_candles_to_now(df, interval="1m", symbol="S&P 500 (ES)")
            if not df.empty:
                last_r = df.iloc[-1]
                price = round(float(last_r["close"]), 2)
                open_p = round(float(last_r["open"]), 2)
                high_p = round(float(last_r["high"]), 2)
                low_p = round(float(last_r["low"]), 2)
                vol = round(float(last_r.get("volume", 100.0)), 1)
                ts = int(last_r.get("timestamp", time.time()))
                prev_c = float(df.iloc[-2]["close"]) if len(df) > 1 else price
                chg = round(((price - prev_c) / prev_c) * 100.0, 2)
        except Exception as e:
            logger.warning(f"[SP500 Quote] Error reading quote: {e}")
    
    # Check if currently in opening session window (US Open 13:30 - 14:30 UTC / 9:30 - 10:30 EST)
    now_dt = datetime.now(timezone.utc)
    is_us_open = (now_dt.weekday() < 5) and (
        (now_dt.hour == 13 and now_dt.minute >= 30) or
        (now_dt.hour == 14 and now_dt.minute <= 30)
    )
    is_london_open = (now_dt.weekday() < 5) and (
        (now_dt.hour == 7 and now_dt.minute >= 0) or
        (now_dt.hour == 8 and now_dt.minute <= 0)
    )
    session_active = is_us_open or is_london_open

    return {
        "quote": {
            "symbol": "S&P 500 (ES)",
            "price": price,
            "open": open_p,
            "high": high_p,
            "low": low_p,
            "volume": vol,
            "change_pct": chg,
            "timestamp": ts,
            "source": "cme_es_1m"
        },
        "session": {
            "active": session_active,
            "name": "US RTH Open (9:30-10:15 EST)" if is_us_open else ("London Open (08:00 BST)" if is_london_open else "Closed / Off-Hours"),
            "is_us_open": is_us_open
        }
    }


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
        "local_timezone": datetime.now().astimezone().tzname() or "Local",
        "trading_sessions": [
            {
                "session": "London",
                "window_local": f"{datetime(2026, 1, 1, 7, 30, tzinfo=timezone.utc).astimezone().strftime('%H:%M')} - {datetime(2026, 1, 1, 10, 30, tzinfo=timezone.utc).astimezone().strftime('%H:%M')} ({datetime.now().astimezone().tzname() or 'Local'})",
                "window_utc": "07:30 - 10:30 UTC"
            },
            {
                "session": "New York",
                "window_local": f"{datetime(2026, 1, 1, 12, 45, tzinfo=timezone.utc).astimezone().strftime('%H:%M')} - {datetime(2026, 1, 1, 16, 30, tzinfo=timezone.utc).astimezone().strftime('%H:%M')} ({datetime.now().astimezone().tzname() or 'Local'})",
                "window_utc": "12:45 - 16:30 UTC"
            }
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



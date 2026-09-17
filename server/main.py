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
from typing import Dict, Any, Optional, List

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
    strategy: Optional[str] = None
    strategy_name: Optional[str] = None
    mode: Optional[str] = "dry-run"

class SelectStrategyRequest(BaseModel):
    strategy: str

class UpdateStrategyStatusRequest(BaseModel):
    strategy: str
    status: str  # ACTIVE_LIVE | CRON_BACKTEST | DEACTIVATED
    exclusive: Optional[bool] = False

class RunStrategyBacktestRequest(BaseModel):
    strategy: str

class RemoveStrategyRequest(BaseModel):
    strategy: str

class CloseSignalRequest(BaseModel):
    id: Optional[int] = None
    strategy: Optional[str] = None
    exit_price: Optional[float] = None
    exit_reason: Optional[str] = "MANUAL_CLOSE"
    pnl_pct: Optional[float] = None

class ClearSignalsRequest(BaseModel):
    strategy: Optional[str] = None

class DeleteSignalRequest(BaseModel):
    id: int

class StopBotRequest(BaseModel):
    strategy: Optional[str] = None
    strategy_name: Optional[str] = None

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
        "active_strategy": strategy_registry.get_active_strategy_name()
    }

def _extract_primitives_for_response(strategy_name: Optional[str], candles_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not candles_data:
        return {"lines": [], "series": {}, "boxes": [], "levels": [], "hud_items": []}
    strat = strategy_name or strategy_registry.get_active_strategy_name()
    if not strat:
        return {"lines": [], "series": {}, "boxes": [], "levels": [], "hud_items": []}
    try:
        from server.chart_primitives import extract_strategy_primitives
        clean_name = strat.replace(".py", "")
        return extract_strategy_primitives(clean_name, candles_data)
    except Exception as e:
        logger.warning(f"[Primitives] Failed extracting visual primitives for {strat}: {e}")
        return {"lines": [], "series": {}, "boxes": [], "levels": [], "hud_items": []}

@app.get("/api/candles")
async def get_candles(
    symbol: Optional[str] = None, 
    count: int = 2500, 
    mode: str = "live",
    timeframe: Optional[str] = None,
    strategy: Optional[str] = None
):
    """
    Returns real OHLCV candles from CME / Binance / OANDA public APIs or local cache bridged to current time.
    Auto-detects symbol and timeframe based on selected strategy (e.g. 5m vs 1m vs 15m).
    """
    if strategy and not timeframe:
        clean_strat = strategy.replace(".py", "")
        rec = strategy_registry.get(clean_strat)
        if rec and rec.get("timeframe"):
            timeframe = rec.get("timeframe")
        if not symbol and rec and rec.get("symbol"):
            symbol = rec.get("symbol")

    if not symbol:
        active_strat = strategy or strategy_registry.get_active_strategy_name()
        clean_active = active_strat.replace(".py", "")
        rec = strategy_registry.get(clean_active)
        if rec and rec.get("symbol"):
            symbol = rec.get("symbol")
        else:
            is_sp = any(k in active_strat.upper() for k in ["SP", "ES", "OPENING"])
            is_gold = any(k in active_strat.upper() for k in ["XAU", "GOAT", "DISPLACEMENT"])
            symbol = "S&P 500 (ES)" if is_sp else ("XAU/USD" if is_gold else "BTC/USDT")

    is_sp = any(k in symbol.upper() for k in ["SP", "ES", "S&P", "US500", "OPENING"])
    is_xau = any(k in symbol.upper() for k in ["XAU", "GOLD", "OANDA", "GC"])
    interval = timeframe or ("1m" if (is_xau or is_sp) else "15m")

    # 1. First priority: Check live in-memory warm candles from running bot/providers (< 2ms)
    from server.providers.base import ProviderRegistry
    if is_sp:
        csv_path = "data/sp500_candles_1m.csv"
    elif is_xau:
        if interval == "5m":
            csv_path = "data/xauusd_candles_5m.csv"
            need_resample = not os.path.exists(csv_path)
            if not need_resample and os.path.exists("data/xauusd_candles_1m.csv"):
                try:
                    need_resample = os.path.getmtime("data/xauusd_candles_1m.csv") > os.path.getmtime(csv_path)
                except Exception:
                    pass
            if need_resample and os.path.exists("data/xauusd_candles_1m.csv"):
                import pandas as pd
                df_1m = pd.read_csv("data/xauusd_candles_1m.csv")
                df_1m['dt'] = pd.to_datetime(df_1m['timestamp'], unit='s', utc=True)
                df_1m = df_1m.set_index('dt').sort_index()
                resampled = df_1m.resample('5min', label='left', closed='left').agg({
                    'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'
                }).dropna()
                resampled['timestamp'] = (resampled.index.astype('int64') // 10**9).astype(int)
                resampled = resampled[['timestamp', 'open', 'high', 'low', 'close', 'volume']].reset_index(drop=True)
                resampled.to_csv(csv_path, index=False)
        else:
            csv_path = "data/xauusd_candles_1m.csv"
    else:
        if interval == "5m" and os.path.exists("data/btc_candles_5m.csv"):
            csv_path = "data/btc_candles_5m.csv"
        else:
            csv_path = "data/candles_15m.csv"

    try:
        provider = ProviderRegistry.get_provider(symbol, interval)
        if not provider.is_running:
            import asyncio
            asyncio.create_task(provider.start())

        # 1. First priority: If provider already has fresh in-memory candles (latest candle within 3 min), return directly
        now_ts = int(time.time())
        if provider._candles and len(provider._candles) >= 50:
            last_ts = int(provider._candles[-1].get("time") or provider._candles[-1].get("timestamp") or 0)
            if (now_ts - last_ts) <= 180:
                c_list = provider._candles
                data = c_list[-count:] if (count and count < len(c_list)) else c_list
                prims = _extract_primitives_for_response(strategy, data)
                return {"symbol": symbol, "timeframe": interval, "mode": mode, "data": data, "primitives": prims}

        # 2. Live Market Data Feed: Fetch fresh continuous bars directly from exchange / institutional stream
        if is_sp:
            from server.data_manager import fetch_real_sp500_candles
            data = fetch_real_sp500_candles(interval=interval, count=count)
            if provider and data:
                provider._candles = data
        elif is_xau:
            from server.data_manager import fetch_real_oanda_candles
            data = fetch_real_oanda_candles(interval=interval, count=count)
            if provider and data:
                provider._candles = data
            if interval == "1m":
                xauusd_engine.candles_1m = data
        else:
            data = fetch_real_binance_klines(symbol=symbol, interval=interval, count=count)
            if provider and data:
                provider._candles = data

        if data:
            prims = _extract_primitives_for_response(strategy, data)
            return {"symbol": symbol, "timeframe": interval, "mode": mode, "data": data, "primitives": prims}
    except Exception as e:
        logger.error(f"[Candles] Live fetch notice for {symbol}: {e}")
        # Robust fallback to cached dataset without synthetic bridging
        if os.path.exists(csv_path):
            try:
                import pandas as pd
                from server.data_manager import resample_candles
                df = pd.read_csv(csv_path)
                time_col = "timestamp" if "timestamp" in df.columns else "time"
                df = df.dropna(subset=[time_col, "close"]).sort_values(by=time_col)
                records = df.tail(count).to_dict(orient="records") if (count and count > 0) else df.to_dict(orient="records")
                base_candles = [
                    {
                        "time": int(r.get("timestamp", r.get("time", 0))),
                        "timestamp": int(r.get("timestamp", r.get("time", 0))),
                        "open": round(float(r["open"]), 2),
                        "high": round(float(r["high"]), 2),
                        "low": round(float(r["low"]), 2),
                        "close": round(float(r["close"]), 2),
                        "volume": round(float(r.get("volume", 10.0)), 4)
                    }
                    for r in records
                ]
                data = resample_candles(base_candles, interval) if interval not in ("1m", "15m") else base_candles
                data = data[-count:] if (count and count < len(data)) else data
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
    prims = _extract_primitives_for_response(strategy, data)
    return {"symbol": symbol, "timeframe": interval, "mode": mode, "data": data, "primitives": prims}


@app.get("/api/strategy/primitives")
async def get_strategy_primitives(
    strategy: Optional[str] = None,
    symbol: Optional[str] = None,
    timeframe: Optional[str] = None
):
    """
    Direct endpoint for querying Level 3 Visual Primitives (lines, boxes, levels, hud items)
    for any quantitative strategy.
    """
    strat = strategy or strategy_registry.get_active_strategy_name()
    if not strat:
        return {"lines": [], "series": {}, "boxes": [], "levels": [], "hud_items": []}
    candles_res = await get_candles(symbol=symbol, timeframe=timeframe, strategy=strat, count=2000)
    return candles_res.get("primitives", {"lines": [], "series": {}, "boxes": [], "levels": [], "hud_items": []})


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
 
@app.post("/api/signals/delete")
async def delete_signal_endpoint(req: DeleteSignalRequest):
    sigs = signal_store.get_all()
    remaining = [s for s in sigs if s.get("id") != req.id]
    from server.state_manager import _write_json_locked
    _write_json_locked(signal_store._path, remaining)
    state_manager.patch({"signals_count": len(remaining)})
    await manager.broadcast({"event_type": "SIGNAL_DELETED", "payload": {"id": req.id, "remaining": len(remaining)}})
    await manager.broadcast({"event_type": "SIGNALS_UPDATED", "payload": remaining})
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
    return {"status": "SUCCESS", "deleted_id": req.id, "total": len(remaining)}

@app.post("/api/signals/close")
@app.post("/api/strategy/close-position")
async def close_signal_position(req: CloseSignalRequest):
    exit_p = req.exit_price
    if not exit_p or exit_p <= 0:
        active_strat = req.strategy or ""
        if any(k in active_strat.lower() for k in ["xau", "gold", "goat"]):
            exit_p = float(xauusd_engine.current_quote.get("price") or 0.0)
        if not exit_p or exit_p <= 0:
            active_sig = signal_store.get_active(req.strategy) if req.strategy else None
            exit_p = float(active_sig.get("price") or 0.0) if active_sig else 0.0

    closed = signal_store.close_position(
        signal_id=req.id,
        strategy=req.strategy,
        exit_price=exit_p,
        exit_reason=req.exit_reason or "MANUAL_CLOSE",
        pnl_pct=req.pnl_pct
    )
    if not closed:
        raise HTTPException(status_code=404, detail="No active position found matching criteria")

    # Dispatch Telegram notification for trade exit
    try:
        telegram_gateway.format_and_send_trade_close(closed)
    except Exception as e_tg:
        logger.warning(f"[Main] Telegram trade close alert failed: {e_tg}")

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

@app.get("/api/status")
async def get_system_status():
    """Unified system status for cockpit telemetry and monitoring."""
    curr_state = state_manager.get()
    return {
        "status": "ONLINE",
        "timestamp": int(time.time()),
        "active_strategy": curr_state.get("active_strategy", ""),
        "active_strategies": bot_supervisor.active_strategies,
        "bot_status": bot_supervisor.get_status(),
        "telegram_configured": telegram_gateway.is_configured,
        "signals_count": curr_state.get("signals_count", 0),
        "open_positions_count": len(signal_store.get_active_signals())
    }

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
            envelope.payload["strategy"] = strategy_registry.get_active_strategy_name()
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
    elif envelope.event_type == "TELEGRAM_BROADCAST":
        msg_body = envelope.payload.get("message") or envelope.payload.get("text") or envelope.payload.get("body", "")
        msg_cat = envelope.payload.get("type") or envelope.payload.get("category", "general")
        msg_title = envelope.payload.get("title", "")
        telegram_gateway.broadcast_custom(msg_body, category=msg_cat, title=msg_title)
    elif envelope.event_type == "UPSERT_WIDGET" and envelope.payload.get("component") == "MetricCard":
        telegram_gateway.format_and_send_dsr_alert(envelope.payload)
    return {"status": "SUCCESS", "event_type": envelope.event_type}


@app.post("/api/bot/deploy")
async def deploy_bot(req: DeployBotRequest):
    raw_strat = req.strategy or req.strategy_name or strategy_registry.get_active_strategy_name()
    clean_strat = (raw_strat or "").replace(".py", "").strip()
    if not clean_strat or clean_strat == ".":
        raise HTTPException(
            status_code=400,
            detail="No strategy available to deploy. Please mine or register a strategy in strategies/ first."
        )
    strat_path = os.path.join(os.getcwd(), "strategies", f"{clean_strat}.py")
    if not os.path.exists(strat_path):
        raise HTTPException(
            status_code=404,
            detail=f"Strategy file '{clean_strat}.py' not found in strategies/. Please mine or register this strategy first."
        )
    strat = clean_strat
    logger.info(f"Activating & deploying strategy for system: {strat}")
    bt_result = run_real_backtest(strat, save_as_active=True)
    bot_supervisor.set_broadcast_callback(manager.broadcast)
    res = bot_supervisor.deploy_strategy(strat, req.mode or "dry-run")
    try:
        strategy_registry.update_status(strat, "ACTIVE_LIVE")
    except Exception as e_reg:
        logger.warning(f"Error updating registry for {strat}: {e_reg}")
    all_strats = strategy_registry.get_all(sync=False)
    portfolio = strategy_registry.get_portfolio_summary()
    distribution = strategy_registry.get_distribution_analytics()
    await manager.broadcast({"event_type": "STATE_UPDATED", "payload": bt_result["state"]})
    await manager.broadcast({
        "event_type": "STRATEGIES_UPDATED",
        "payload": {
            "strategies": all_strats,
            "portfolio_summary": portfolio,
            "distribution_analytics": distribution
        }
    })
    return {**res, "state": bt_result["state"], "strategies": all_strats}

@app.post("/api/bot/stop")
async def stop_bot(req: Optional[StopBotRequest] = None):
    strat = (req.strategy or req.strategy_name) if req else None
    res = bot_supervisor.stop_bot(strat)
    if strat:
        try:
            strategy_registry.update_status(strat, "DEACTIVATED")
        except Exception as e_s:
            logger.warning(f"Error deactivating {strat}: {e_s}")
    else:
        all_active = [s["name"] for s in strategy_registry.get_all(sync=False) if s.get("status") == "ACTIVE_LIVE"]
        active_state_strats = state_manager.get().get("active_strategies", [])
        to_stop = set(all_active + active_state_strats + list(bot_supervisor.runners.keys()))
        for s in to_stop:
            try:
                strategy_registry.update_status(s, "DEACTIVATED")
            except Exception as e_s:
                logger.warning(f"Error deactivating {s}: {e_s}")
        state_manager.patch({"status": "STOPPED", "active_strategies": [], "active_strategy": ""})
    new_state = state_manager.get()
    all_strats = strategy_registry.get_all(sync=False)
    portfolio = strategy_registry.get_portfolio_summary()
    distribution = strategy_registry.get_distribution_analytics()
    await manager.broadcast({"event_type": "STATE_UPDATED", "payload": new_state})
    await manager.broadcast({
        "event_type": "STRATEGIES_UPDATED",
        "payload": {
            "strategies": all_strats,
            "portfolio_summary": portfolio,
            "distribution_analytics": distribution
        }
    })
    return res

@app.post("/api/strategy/activate")
async def strategy_activate(req: DeployBotRequest):
    return await deploy_bot(req)

@app.post("/api/strategy/deactivate")
async def strategy_deactivate(req: Optional[StopBotRequest] = None):
    return await stop_bot(req)

@app.get("/api/bot/status")
async def get_bot_status():
    return bot_supervisor.get_status()

@app.post("/api/strategies/select")
async def select_and_run_strategy(req: SelectStrategyRequest):
    logger.info(f"Strategy selected for inspection: {req.strategy}")
    clean_name = req.strategy.replace(".py", "")
    strat_record = strategy_registry.get(clean_name)
    
    curr_sys_state = state_manager.get()
    is_active_sys = (clean_name == curr_sys_state.get("active_strategy"))
    trade_markers = strat_record.get("trade_markers") or (curr_sys_state.get("trade_markers", []) if is_active_sys else [])
    trades_detail = strat_record.get("trades_detail") or (curr_sys_state.get("trades_detail", []) if is_active_sys else [])
    
    # Return existing audited backtest if present and populated with trade markers
    if strat_record and strat_record.get("latest_backtest") and len(trade_markers) > 0 and len(trades_detail) > 0:
        logger.info(f"[SelectStrategy] Returning cached audited backtest with {len(trade_markers)} markers for {clean_name}")
        summary = strat_record.get("latest_backtest", {})
        gates = strat_record.get("falsification_gates", {})
        eq = strat_record.get("backtest_equity_curve", [])
        symbol = strat_record.get("symbol", "XAU/USD")
        timeframe = strat_record.get("timeframe", "1m")
        thesis = strat_record.get("thesis", f"Autonomous Alpha Model: {clean_name}")
        thesis_props = {
            "thesis": thesis,
            "counterparty": "Trapped breakout liquidity / volatility expansion",
            "invalidation": "Stop-loss triggered beyond structural extreme",
            "target_profile": strat_record.get("target_profile", f"{clean_name} Profile")
        }
        
        tp = strat_record.get("time_period") or {
            "start_time": summary.get("start_time"),
            "end_time": summary.get("end_time"),
            "start_date": summary.get("start_date"),
            "end_date": summary.get("end_date"),
            "duration_days": summary.get("duration_days"),
            "period_label": summary.get("period_label"),
            "candles_count": summary.get("candles_count")
        }

        result = {
            "strategy": clean_name,
            "symbol": symbol,
            "timeframe": timeframe,
            "summary": summary,
            "time_period": tp,
            "falsification_gates": gates,
            "equity_curve": eq,
            "thesis_props": thesis_props,
            "trade_markers": trade_markers,
            "trades_detail": trades_detail,
            "drift_history": strat_record.get("cron_config", {}).get("drift_history", []),
            "strategy_record": strat_record
        }
        await manager.broadcast({"event_type": "BACKTEST_UPDATED", "payload": result})
        return result

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
    active_strat = strategy_registry.get_active_strategy_name()
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
            "symbol": s.get("symbol", "XAU/USD" if any(k in file_name.upper() for k in ["XAU", "GOLD", "GOAT"]) else ("S&P 500 (ES)" if any(k in file_name.upper() for k in ["SP", "ES", "OPENING"]) else "BTC/USDT")),
            "timeframe": s.get("timeframe", "1m" if any(k in file_name.upper() for k in ["XAU", "GOLD", "GOAT", "SP", "ES", "OPENING"]) else "15m"),
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


@app.get("/api/portfolio/correlation")
async def get_portfolio_correlation(threshold: float = 0.50, strategies: Optional[str] = None, data_path: str = "data/candles_15m.csv"):
    """
    Returns pairwise correlation matrix, regime slicing attribution,
    ensemble metrics, and redundancy/complementarity audit flags.
    """
    try:
        from tools.portfolio_cynic import evaluate_portfolio
        s_list = [s.strip() for s in strategies.split(",") if s.strip()] if strategies else None
        report = evaluate_portfolio(strategy_names=s_list, data_path=data_path, correlation_threshold=threshold)
        return report
    except Exception as e:
        logger.error(f"[PortfolioCynic] Error computing portfolio correlation: {e}")
        return {
            "error": str(e),
            "strategies": [],
            "correlation_matrix": {},
            "spearman_matrix": {},
            "individual_metrics": {},
            "regime_breakdown": {},
            "portfolio_ensemble": {},
            "pairwise_analysis": []
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


@app.get("/api/strategies/manage/rankings")
async def get_strategy_rankings():
    """Returns sorted quantitative leaderboard with ranking breakdown, sub-scores, tiers, and tier distribution."""
    strats = strategy_registry.get_all(sync=False)
    strats_sorted = sorted(strats, key=lambda s: s.get("ranking_score", 0.0), reverse=True)
    distribution = strategy_registry.get_distribution_analytics()
    return {
        "status": "SUCCESS",
        "rankings": strats_sorted,
        "total": len(strats_sorted),
        "tier_distribution": distribution.get("tier_distribution", {}),
        "sharpe_distribution": distribution.get("sharpe_distribution", {})
    }


@app.post("/api/strategies/manage/rank")
async def recalculate_strategy_rankings():
    """
    Recalculates multi-pillar quantitative rankings and tiers across all strategies.
    Saves updated state to data/strategies.json and broadcasts STRATEGIES_UPDATED via WebSocket.
    """
    ranked = strategy_registry.recalculate_and_save()
    portfolio = strategy_registry.get_portfolio_summary()
    distribution = strategy_registry.get_distribution_analytics()
    payload = {
        "strategies": ranked,
        "portfolio_summary": portfolio,
        "distribution_analytics": distribution
    }
    await manager.broadcast({"event_type": "STRATEGIES_UPDATED", "payload": payload})
    return {
        "status": "SUCCESS",
        "message": f"Successfully recalculated rankings across {len(ranked)} strategies.",
        "top_strategy": ranked[0].get("name") if ranked else None,
        "total": len(ranked),
        **payload
    }


@app.post("/api/strategies/manage/remove")
async def remove_strategy_endpoint(req: RemoveStrategyRequest):
    """Safely remove a strategy from disk, re-sync registry, and broadcast update to Cockpit."""
    success = strategy_registry.remove_strategy(req.strategy)
    all_strats = strategy_registry.get_all(sync=True)
    portfolio = strategy_registry.get_portfolio_summary()
    distribution = strategy_registry.get_distribution_analytics()
    payload = {
        "strategies": all_strats,
        "portfolio_summary": portfolio,
        "distribution_analytics": distribution
    }
    await manager.broadcast({"event_type": "STRATEGIES_UPDATED", "payload": payload})
    await manager.broadcast({"event_type": "STATE_UPDATED", "payload": state_manager.get()})
    return {"status": "SUCCESS" if success else "NOT_FOUND", "strategy": req.strategy, **payload}


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

    # Pre-warm real-time market data providers so live candles are immediately warm
    from server.providers.base import ProviderRegistry
    for sym, tf in [("BTC/USDT", "15m"), ("XAU/USD", "1m"), ("S&P 500 (ES)", "1m")]:
        try:
            p = ProviderRegistry.get_provider(sym, tf)
            asyncio.create_task(p.start())
            logger.info(f"[NujinSkillsServer] Market provider pre-warmed for {sym} ({tf})")
        except Exception as e_p:
            logger.warning(f"[NujinSkillsServer] Error warming provider for {sym}: {e_p}")

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

    # 1. Primary: In-memory live ProviderRegistry quote to eliminate double-feed flickering
    from server.providers.base import ProviderRegistry
    try:
        provider = ProviderRegistry.get_provider("S&P 500 (ES)", "1m")
        if provider and provider._latest_quote and provider._latest_quote.get("price"):
            q = provider._latest_quote
            return {
                "quote": q,
                "session": {
                    "active": session_active,
                    "name": "US RTH Open (9:30-10:15 EST)" if is_us_open else ("London Open (08:00 BST)" if is_london_open else "Closed / Off-Hours"),
                    "is_us_open": is_us_open
                }
            }
    except Exception as e_prov:
        logger.debug(f"[SP500 Quote] Provider quote check: {e_prov}")

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
            df = pd.read_csv(csv_path)
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



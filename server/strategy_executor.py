from __future__ import annotations

import asyncio
import logging
import math
import os
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Callable

import numpy as np
import pandas as pd

from server.state_manager import state_manager, signal_store, strategy_registry
from server.telegram_bot import telegram_gateway
from server.providers.base import BaseMarketDataProvider, ProviderRegistry
from server.brokers.registry import broker_registry

logger = logging.getLogger("StrategyExecutor")

class StrategyEvaluator:
    """
    Evaluates algorithmic trading rules against incoming market candles.
    Supports GFT XAUUSD Momentum Train, Prop Firm VSA Wick Rejection, TrapFade, and generic strategies.
    """
    @staticmethod
    def is_session_active(strategy_name: str, timestamp: Optional[int] = None) -> Dict[str, Any]:
        """London Momentum: 07:30 - 10:30 UTC | New York Momentum: 12:45 - 16:30 UTC."""
        if timestamp and timestamp > 0:
            now_utc = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        else:
            now_utc = datetime.now(timezone.utc)
        current_minute_utc = now_utc.hour * 60 + now_utc.minute

        is_london = 450 <= current_minute_utc <= 630
        is_ny = 765 <= current_minute_utc <= 990
        active = is_london or is_ny

        session_name = "NONE"
        if is_london and is_ny:
            session_name = "LONDON_NY_OVERLAP"
        elif is_london:
            session_name = "LONDON_SESSION"
        elif is_ny:
            session_name = "NEW_YORK_SESSION"

        return {
            "is_active": active,
            "session_name": session_name,
            "is_london": is_london,
            "is_ny": is_ny
        }

    @staticmethod
    def evaluate(strategy_name: str, symbol: str, candles: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Evaluates candle indicators and checks for LONG or SHORT entry signals.
        Returns signal dictionary if triggered, else None.
        """
        if not candles or len(candles) < 25:
            return None

        clean_name = strategy_name.replace(".py", "")
        df = pd.DataFrame(candles)

        close = df["close"]
        high = df["high"]
        low = df["low"]
        vol = df["volume"]

        # Common indicators
        total_range = (high - low).replace(0, 1e-6)
        lower_wick = (np.minimum(close, df["open"]) - low) / total_range
        upper_wick = (high - np.maximum(close, df["open"])) / total_range

        vol_mean = vol.rolling(20).mean()
        vol_std = vol.rolling(20).std().replace(0, 1e-6)
        vol_z = (vol - vol_mean) / vol_std

        ema_9 = close.ewm(span=9, adjust=False).mean()
        ema_21 = close.ewm(span=21, adjust=False).mean()
        ema_200 = close.ewm(span=min(200, len(close)), adjust=False).mean()

        tr = np.maximum(high - low, np.maximum((high - close.shift(1)).abs(), (low - close.shift(1)).abs()))
        atr_14 = tr.rolling(14).mean()

        hh_15 = high.shift(1).rolling(15).max()
        ll_15 = low.shift(1).rolling(15).min()

        curr_i = len(df) - 1
        curr_bar = df.iloc[curr_i]
        curr_p = float(close.iloc[curr_i])
        curr_e9 = float(ema_9.iloc[curr_i])
        curr_e21 = float(ema_21.iloc[curr_i])
        curr_e200 = float(ema_200.iloc[curr_i])
        curr_vz = float(vol_z.iloc[curr_i]) if not np.isnan(vol_z.iloc[curr_i]) else 0.0
        curr_atr = float(atr_14.iloc[curr_i]) if not np.isnan(atr_14.iloc[curr_i]) else 2.50
        curr_hh15 = float(hh_15.iloc[curr_i]) if not np.isnan(hh_15.iloc[curr_i]) else curr_p
        curr_ll15 = float(ll_15.iloc[curr_i]) if not np.isnan(ll_15.iloc[curr_i]) else curr_p
        curr_lw = float(lower_wick.iloc[curr_i]) if not np.isnan(lower_wick.iloc[curr_i]) else 0.0
        curr_uw = float(upper_wick.iloc[curr_i]) if not np.isnan(upper_wick.iloc[curr_i]) else 0.0

        bar_ts = int(curr_bar.get("time", curr_bar.get("timestamp", 0)))
        is_xau = "XAU" in symbol.upper() or "GOLD" in symbol.upper() or "GOAT" in clean_name.upper()

        # Dynamic evaluation via strategy class Single Source of Truth
        try:
            from server.backtest_engine import load_strategy_instance
            strat_inst = load_strategy_instance(clean_name)
            if not strat_inst:
                logger.warning(f"[StrategyEvaluator] Strategy '{clean_name}' class could not be loaded from strategies/{clean_name}.py. No signal.")
                return None

            df_dyn = strat_inst.populate_indicators(df.copy(), {})
            df_dyn = strat_inst.populate_entry_trend(df_dyn, {})
            last_row = df_dyn.iloc[-1]

            is_l = bool(last_row.get("enter_long", 0) == 1)
            is_s = bool(last_row.get("enter_short", 0) == 1) if getattr(strat_inst, "can_short", True) else False

            # Prevent simultaneous long/short whipsaw
            if is_l and is_s:
                is_s = False

            if not is_l and not is_s:
                return None

            side = "BUY" if is_l else "SELL"
            stoploss_pct = abs(float(getattr(strat_inst, "stoploss", -0.02)))
            minimal_roi = getattr(strat_inst, "minimal_roi", {})
            roi_0 = float(minimal_roi.get("0", minimal_roi.get(0, 0.035 if not is_xau else 0.005))) if minimal_roi else (stoploss_pct * 1.5)
            atr_sl = getattr(strat_inst, "atr_sl_mult", None)
            atr_tp = getattr(strat_inst, "atr_tp_mult", None)
            atr_v = float(df_dyn['atr_14'].iloc[-1]) if ('atr_14' in df_dyn.columns and not np.isnan(df_dyn['atr_14'].iloc[-1])) else (curr_p * 0.005)

            # 1. Structural or Dynamic Stop Loss
            if "structural_sl" in last_row and not np.isnan(last_row["structural_sl"]):
                sl = round(float(last_row["structural_sl"]), 2)
            elif atr_sl is not None and atr_v > 0:
                sl = round(curr_p - atr_sl * atr_v if is_l else curr_p + atr_sl * atr_v, 2)
            else:
                sl = round(curr_p * (1.0 - stoploss_pct) if is_l else curr_p * (1.0 + stoploss_pct), 2)

            # 2. Structural or Dynamic Take Profit
            if "structural_tp" in last_row and not np.isnan(last_row["structural_tp"]):
                tp = round(float(last_row["structural_tp"]), 2)
            elif atr_tp is not None and atr_v > 0:
                tp = round(curr_p + atr_tp * atr_v if is_l else curr_p - atr_tp * atr_v, 2)
            elif minimal_roi:
                tp = round(curr_p * (1.0 + roi_0) if is_l else curr_p * (1.0 - roi_0), 2)
            else:
                tp = round(curr_p * (1.0 + stoploss_pct * 1.5) if is_l else curr_p * (1.0 - stoploss_pct * 1.5), 2)

            # 3. Strict Quantitative Sanity Bounds (Universal Risk Enforcement)
            if is_l:
                if sl >= curr_p or tp <= curr_p:
                    logger.error(f"[StrategyEvaluator] REJECTED inverted LONG signal for {clean_name}: Price={curr_p}, SL={sl}, TP={tp}")
                    return None
            else:
                if sl <= curr_p or tp >= curr_p:
                    logger.error(f"[StrategyEvaluator] REJECTED inverted SHORT signal for {clean_name}: Price={curr_p}, SL={sl}, TP={tp}")
                    return None

            is_sp = any(k in symbol.upper() for k in ["SP", "ES", "S&P", "US500"])
            if is_sp and abs(sl - curr_p) > 50.0:
                logger.error(f"[StrategyEvaluator] REJECTED excessive S&P stop loss ({abs(sl - curr_p):.2f} pts > 50 pts) for {clean_name}")
                return None
            if is_xau and abs(sl - curr_p) > 25.0:
                logger.error(f"[StrategyEvaluator] REJECTED excessive Gold stop loss (${abs(sl - curr_p):.2f} > $25) for {clean_name}")
                return None

            bar_sec = 60 if ("1m" in symbol or is_xau or is_sp) else 900
            min_bars = getattr(strat_inst, "min_bars", getattr(strat_inst, "min_hold_bars", 2 if is_xau else 1))
            max_bars = getattr(strat_inst, "max_bars", 15 if is_xau else 12)

            # 4. Strategy-Designed Smart Lot Sizer
            lots = None
            if "lot_size" in last_row and not np.isnan(last_row["lot_size"]) and float(last_row["lot_size"]) > 0:
                lots = float(last_row["lot_size"])
            elif hasattr(strat_inst, "calculate_lot_size") and callable(getattr(strat_inst, "calculate_lot_size")):
                try:
                    broker = broker_registry.get_broker()
                    acc_info = broker.get_account_info() if broker else {}
                    acc_bal = float(acc_info.get("equity") or acc_info.get("balance") or 100000.0)
                    lots = float(strat_inst.calculate_lot_size(
                        account_balance=acc_bal,
                        entry_price=curr_p,
                        stop_loss=sl,
                        symbol=symbol,
                        atr=atr_v,
                        z_score=curr_vz
                    ))
                except Exception as e_lots:
                    logger.warning(f"[StrategyEvaluator] Error calculating lot size via strategy lotsizer: {e_lots}")

            if lots is None or lots <= 0:
                lots = 0.10 if (is_xau or "USD" in symbol) else 1.0

            lots = round(lots, 2)

            return {
                "strategy": clean_name,
                "pair": symbol,
                "action": side,
                "price": curr_p,
                "time": bar_ts if bar_ts > 0 else int(time.time()),
                "stop_loss": sl,
                "take_profit": tp,
                "lots": lots,
                "lot_size": lots,
                "min_hold_seconds": min_bars * bar_sec,
                "max_hold_seconds": max_bars * bar_sec,
                "annotation": f"{clean_name} Signal ({lots:.2f} lots)",
                "reasoning_md": f"Systematic signal generated by {clean_name} ({side} {lots:.2f} lots @ ${curr_p:,.2f}) with SL: ${sl:,.2f}, TP: ${tp:,.2f}."
            }
        except Exception as e_dyn:
            logger.warning(f"[StrategyEvaluator] Error evaluating dynamic strategy {clean_name}: {e_dyn}")
            return None


class NativeStrategyRunner:
    """
    Active 24/7 Strategy Execution Runner.
    Listens to live market data from its assigned MarketDataProvider,
    evaluates strategy conditions on each bar/tick, triggers trade signals,
    and manages active open positions with automated SL/TP and time cutoff exits.
    """
    def __init__(self, strategy_name: str, broadcast_callback: Optional[Callable] = None):
        self.strategy_name = strategy_name.replace(".py", "")
        self.broadcast_callback = broadcast_callback
        self.is_running = False

        # Dynamically retrieve symbol and timeframe from Single Source of Truth
        from server.backtest_engine import resolve_strategy_metadata
        meta = resolve_strategy_metadata(self.strategy_name)
        self.symbol = meta["symbol"]
        self.timeframe = meta["timeframe"]

        self.provider: BaseMarketDataProvider = ProviderRegistry.get_provider(self.symbol, self.timeframe)
        self._last_evaluated_bar_time: int = 0

    async def start(self) -> None:
        if self.is_running:
            return
        self.is_running = True

        # Ensure market data provider is running
        if not self.provider.is_running:
            await self.provider.start()

        # Subscribe callbacks
        self.provider.subscribe_tick(self._on_market_tick)
        self.provider.subscribe_bar(self._on_market_bar)
        logger.info(f"[NativeStrategyRunner] Active for '{self.strategy_name}' on {self.symbol} ({self.timeframe})")

    async def stop(self) -> None:
        self.is_running = False
        self.provider.unsubscribe_tick(self._on_market_tick)
        self.provider.unsubscribe_bar(self._on_market_bar)
        logger.info(f"[NativeStrategyRunner] Stopped for '{self.strategy_name}'")

    async def _on_market_tick(self, quote: Dict[str, Any]) -> None:
        """Called on every real-time price tick. Checks open position exits."""
        if not self.is_running:
            return

        # Lifecycle Guard: If strategy is deactivated, only monitor exit of active position, then stop
        strat_record = strategy_registry.get(self.strategy_name)
        if not strat_record or strat_record.get("status") != "ACTIVE_LIVE":
            active_pos = signal_store.get_active(self.strategy_name)
            if active_pos:
                current_price = float(quote.get("price") or 0.0)
                if current_price > 0:
                    await self._evaluate_position_exit(active_pos, current_price)
            else:
                await self.stop()
            return

        current_price = float(quote.get("price") or 0.0)
        if current_price <= 0:
            return

        # 1. Check open position exit triggers
        active_pos = signal_store.get_active(self.strategy_name)
        if active_pos:
            await self._evaluate_position_exit(active_pos, current_price)

    async def _on_market_bar(self, bar: Dict[str, Any]) -> None:
        """Called when a candle bar finalizes. Checks for new strategy entry signals."""
        if not self.is_running:
            return

        # Strict Lifecycle Guard: If strategy is no longer ACTIVE_LIVE, immediately halt runner
        strat_record = strategy_registry.get(self.strategy_name)
        if not strat_record or strat_record.get("status") != "ACTIVE_LIVE":
            logger.info(f"[NativeStrategyRunner] Strategy '{self.strategy_name}' is not ACTIVE_LIVE (status: {strat_record.get('status') if strat_record else 'None'}). Halting runner.")
            await self.stop()
            return

        bar_time = int(bar.get("time") or bar.get("timestamp") or 0)
        if bar_time <= self._last_evaluated_bar_time:
            return
        self._last_evaluated_bar_time = bar_time

        # Check if there is already an active position for this strategy
        active_pos = signal_store.get_active(self.strategy_name)
        if active_pos:
            # Already in position — enforce 1 concurrent trade per strategy
            return

        # For XAU/USD, yield briefly so background authentic volume sync finishes
        if "XAU" in self.symbol or "GOLD" in self.symbol:
            await asyncio.sleep(1.2)

        # Evaluate strategy entry strictly on completed bars up to bar_time
        candles = self.provider.get_candles(count=1000)
        completed_candles = [
            c for c in candles 
            if int(c.get("time", c.get("timestamp", 0))) <= bar_time
        ]
        if not completed_candles or len(completed_candles) < 25:
            completed_candles = candles

        sig = StrategyEvaluator.evaluate(self.strategy_name, self.symbol, completed_candles)
        if sig:
            # Enforce Signal Cannibalization Guard: Prevent opposing wash trades across active strategies on same asset
            from server.bot_runner import check_signal_cannibalization
            conflict = check_signal_cannibalization(sig)
            if conflict:
                logger.warning(
                    f"[SignalConflictGuard] ⚠️ CANNIBALIZATION BLOCKED: Strategy '{self.strategy_name}' signaled {sig['action']} on {self.symbol}, "
                    f"but strategy '{conflict.get('strategy')}' already holds opposing position #{conflict.get('id')} ({conflict.get('action')}). "
                    f"Suppressing order."
                )
                sig["status"] = "CANCELLED_CONFLICT"
                sig["exit_reason"] = f"CONFLICT_WITH_{conflict.get('strategy')}"
                sig["annotation"] = f"Cannibalization Suppressed ({conflict.get('strategy')})"
                signal_store.add(sig)
                if self.broadcast_callback:
                    await self.broadcast_callback({
                        "event_type": "SIGNAL_CONFLICT_SUPPRESSED",
                        "payload": {
                            "incoming_strategy": self.strategy_name,
                            "conflicting_strategy": conflict.get("strategy"),
                            "symbol": self.symbol,
                            "action": sig["action"],
                            "conflicting_action": conflict.get("action")
                        }
                    })
                return

            await self._trigger_new_signal(sig)

    async def _trigger_new_signal(self, sig: Dict[str, Any]) -> None:
        """Saves signal to store, alerts Telegram, plays sound, and broadcasts to UI."""
        logger.info(f"[NativeStrategyRunner] 🚀 SIGNAL TRIGGERED for {self.strategy_name}: {sig['action']} @ {sig['price']}")

        # 1. Execute order via Active Execution Broker (Paper, TradeLocker, etc.)
        try:
            broker = broker_registry.get_broker()
            order_res = broker.execute_order(sig)
            sig["broker_order"] = order_res
            if order_res.get("status") == "REJECTED":
                logger.warning(f"[NativeStrategyRunner] Broker rejected order for {self.strategy_name}: {order_res.get('error')}")
                sig["status"] = "REJECTED_BY_BROKER"
                sig["exit_reason"] = f"BROKER_ERROR: {order_res.get('error')}"
        except Exception as e_broker:
            logger.error(f"[NativeStrategyRunner] Error executing order with broker: {e_broker}")

        # 2. Add to SignalStore (writes to data/signals.json & state.json)
        updated_signals = signal_store.add(sig)
        new_signal_entry = updated_signals[0]

        # 3. Dispatch to Telegram
        telegram_gateway.format_and_send_signal(new_signal_entry)

        # 4. Play desktop sound chime
        try:
            from server.main import play_system_alert
            play_system_alert(new_signal_entry.get("action", ""))
        except Exception:
            pass

        # 5. Broadcast to WebSocket clients
        if self.broadcast_callback:
            await self.broadcast_callback({
                "event_type": "SIGNAL_TRIGGERED",
                "payload": new_signal_entry
            })
            # Also broadcast updated portfolio & strategies stats
            all_strats = strategy_registry.get_all(sync=False)
            portfolio = strategy_registry.get_portfolio_summary()
            dist = strategy_registry.get_distribution_analytics()
            await self.broadcast_callback({
                "event_type": "STRATEGIES_UPDATED",
                "payload": {
                    "strategies": all_strats,
                    "portfolio_summary": portfolio,
                    "distribution_analytics": dist
                }
            })

    async def _evaluate_position_exit(self, pos: Dict[str, Any], current_price: float) -> None:
        """Monitors active trade against Take Profit, Stop Loss, and Holding Rules."""
        now_ts = int(time.time())
        entry_time = int(pos.get("time") or now_ts)
        elapsed_sec = max(0, now_ts - entry_time)

        side = pos.get("action", "BUY").upper()
        is_long = side in ("BUY", "LONG")
        entry_price = float(pos.get("price") or pos.get("entry_price") or current_price)
        tp = float(pos.get("take_profit") or 0.0)
        sl = float(pos.get("stop_loss") or 0.0)

        # Holding constraints (from signal payload or defaults)
        min_hold = int(pos.get("min_hold_seconds") or (120 if "XAU" in self.symbol else 30))
        max_hold = int(pos.get("max_hold_seconds") or (900 if "XAU" in self.symbol else 7200))

        exit_reason: Optional[str] = None

        # 1. Hard Stop Loss hit (SL protects against catastrophic loss regardless of min_hold)
        if is_long and current_price <= sl:
            exit_reason = "STOP_LOSS"
        elif not is_long and current_price >= sl:
            exit_reason = "STOP_LOSS"

        # 2. Take Profit reached (allowed once min_hold anti-arbitrage lock has passed)
        elif is_long and current_price >= tp and elapsed_sec >= min_hold:
            exit_reason = "TAKE_PROFIT"
        elif not is_long and current_price <= tp and elapsed_sec >= min_hold:
            exit_reason = "TAKE_PROFIT"

        # 3. Maximum holding duration exceeded (scalp cutoff)
        elif elapsed_sec >= max_hold:
            exit_reason = "TIME_CUTOFF"

        if exit_reason:
            logger.info(f"[NativeStrategyRunner] 🏁 Closing position #{pos['id']} ({pos['strategy']}): {exit_reason} @ {current_price}")
            # Route exit through Active Execution Broker
            try:
                broker = broker_registry.get_broker()
                broker_order_id = pos.get("broker_order", {}).get("order_id") or str(pos.get("id"))
                broker.close_position(broker_order_id, reason=exit_reason, current_price=current_price)
            except Exception as e_broker_close:
                logger.error(f"[NativeStrategyRunner] Error closing position on broker: {e_broker_close}")

            closed = signal_store.close_position(
                signal_id=pos["id"],
                strategy=self.strategy_name,
                exit_price=current_price,
                exit_reason=exit_reason
            )
            if closed:
                # Dispatch Telegram alert for closed trade
                telegram_gateway.format_and_send_trade_close(closed)

                # Broadcast to UI
                if self.broadcast_callback:
                    await self.broadcast_callback({"event_type": "SIGNAL_CLOSED", "payload": closed})
                    all_strats = strategy_registry.get_all(sync=False)
                    portfolio = strategy_registry.get_portfolio_summary()
                    dist = strategy_registry.get_distribution_analytics()
                    await self.broadcast_callback({
                        "event_type": "STRATEGIES_UPDATED",
                        "payload": {
                            "strategies": all_strats,
                            "portfolio_summary": portfolio,
                            "distribution_analytics": dist
                        }
                    })

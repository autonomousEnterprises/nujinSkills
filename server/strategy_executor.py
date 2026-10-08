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
from server.accounts_store import accounts_store
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
                    acc_bal = float(acc_info.get("equity") or acc_info.get("balance") or 5000.0)
                    if acc_bal <= 0:
                        acc_bal = 5000.0
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
                lots = 0.02 if (is_xau or "USD" in symbol) else 0.10

            lots = round(lots, 2)

            strat_max_bars = getattr(strat_inst, "time_invalidation_bars", getattr(strat_inst, "max_bars", None))
            max_hold_seconds = (strat_max_bars * bar_sec) if strat_max_bars is not None else None

            # 5. Dynamic Trailing Stop Configuration
            use_trailing = getattr(strat_inst, "trailing_stop", False)
            trail_pos = float(getattr(strat_inst, "trailing_stop_positive", 0.0002))
            trail_offset = float(getattr(strat_inst, "trailing_stop_positive_offset", 0.0003))
            atr_trail_m = float(getattr(strat_inst, "atr_trail_mult", 1.0))

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
                "atr": float(atr_v if atr_v and atr_v > 0 else 0.0),
                "atr_trail_mult": atr_trail_m,
                "min_hold_seconds": min_bars * bar_sec,
                "max_hold_seconds": max_hold_seconds,
                "trailing_stop": use_trailing,
                "trailing_offset": trail_offset,
                "trailing_buffer": trail_pos,
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

    def check_drawdown_safety(self) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Active Live Risk & Drawdown Circuit Breaker.
        Strictly enforces strategy-configured max_daily_drawdown_pct and max_total_drawdown_pct
        across connected broker accounts (e.g. Goat Funded Trader Prop Firm limits).
        Prevents funded account breaches by halting new entries when daily or total loss limits
        are reached, or when the remaining daily budget is less than 2.5x single trade risk ($75 safety buffer).
        """
        strat_inst = None
        try:
            from server.backtest_engine import load_strategy_instance
            strat_inst = load_strategy_instance(self.strategy_name)
        except Exception as e_st:
            logger.debug(f"[DrawdownGuard] Could not load strategy instance for {self.strategy_name}: {e_st}")

        # 1. Resolve Account & Pluggable Risk Profile
        primary_acc = None
        initial_balance = 5000.0
        try:
            if accounts_store:
                active_accs = accounts_store.get_all_active_accounts(broker_id="tradelocker", decrypt=False)
                if not active_accs:
                    active_accs = accounts_store.get_all_active_accounts(decrypt=False)
                if active_accs:
                    primary_acc = active_accs[0]
                    initial_balance = float(primary_acc.get("initial_balance") or primary_acc.get("balance") or 5000.0)
        except Exception:
            pass
        if initial_balance <= 0:
            initial_balance = 5000.0

        risk_profile = (primary_acc.get("risk_profile") if primary_acc else None) or {}

        # If user explicitly disabled drawdown guard on this account
        if risk_profile.get("disable_daily_guard") is True:
            return True, "Drawdown guard disabled by account risk profile", {"status": "BYPASSED"}

        # Respect account-level risk profile, falling back to strategy configuration, then generic defaults
        max_daily_dd_pct = float(risk_profile.get("max_daily_drawdown_pct") or getattr(strat_inst, "max_daily_drawdown_pct", 0.03))
        max_total_dd_pct = float(risk_profile.get("max_total_drawdown_pct") or getattr(strat_inst, "max_total_drawdown_pct", 0.05))
        trade_risk_pct = float(risk_profile.get("risk_per_trade_pct") or getattr(strat_inst, "max_risk_pct", getattr(strat_inst, "risk_per_trade_pct", 0.0060)))

        # 2. Check live broker equity/balance
        broker_equity = None
        broker_balance = None
        try:
            broker = broker_registry.get_broker()
            if broker and getattr(broker, "is_connected", False):
                info = broker.get_account_info()
                eq = float(info.get("equity") or 0.0)
                bal = float(info.get("balance") or 0.0)
                if eq > 0:
                    broker_equity = eq
                    broker_balance = bal
        except Exception as e_b:
            logger.debug(f"[DrawdownGuard] Broker info error: {e_b}")

        # 3. Calculate today's PnL from closed signals
        now_utc = datetime.now(timezone.utc)
        today_utc_str = now_utc.strftime("%Y-%m-%d")
        signals = signal_store.get_all()
        today_realized_usd = 0.0

        for s in signals:
            t = s.get("time") or s.get("entry_time") or 0
            dt = datetime.fromtimestamp(t, tz=timezone.utc)
            if dt.strftime("%Y-%m-%d") == today_utc_str:
                if s.get("status") == "CLOSED" or s.get("exit_price"):
                    if s.get("pnl_usd") is not None:
                        today_realized_usd += float(s["pnl_usd"])
                    else:
                        entry_p = float(s.get("price") or s.get("entry_price") or 0.0)
                        exit_p = float(s.get("exit_price") or 0.0)
                        lots = float(s.get("lots") or s.get("lot_size") or 0.01)
                        pair = s.get("pair") or s.get("symbol") or "XAU/USD"
                        c_mult = 100.0 if ("XAU" in pair.upper() or "GOLD" in pair.upper()) else 1.0
                        action = (s.get("action") or "BUY").upper()
                        if entry_p > 0 and exit_p > 0:
                            diff = (exit_p - entry_p) if action in ("BUY", "LONG") else (entry_p - exit_p)
                            today_realized_usd += (diff * lots * c_mult)

        # 4. Losses and budget calculation
        max_daily_loss_usd = round(initial_balance * max_daily_dd_pct, 2)
        max_total_loss_usd = round(initial_balance * max_total_dd_pct, 2)
        single_trade_risk_usd = round(initial_balance * trade_risk_pct, 2)

        broker_loss = (initial_balance - broker_equity) if (broker_equity and broker_equity < initial_balance) else 0.0
        signals_loss = abs(today_realized_usd) if today_realized_usd < 0 else 0.0
        today_loss_usd = round(max(broker_loss, signals_loss), 2)
        remaining_budget_usd = round(max(0.0, max_daily_loss_usd - today_loss_usd), 2)
        buffer_required_usd = round(single_trade_risk_usd * 2.5, 2)

        details = {
            "strategy": self.strategy_name,
            "day_key": today_utc_str,
            "initial_balance": initial_balance,
            "current_equity": broker_equity or (initial_balance - today_loss_usd),
            "today_loss_usd": today_loss_usd,
            "today_realized_pnl_usd": round(today_realized_usd, 2),
            "max_daily_loss_usd": max_daily_loss_usd,
            "max_daily_dd_pct": max_daily_dd_pct,
            "remaining_budget_usd": remaining_budget_usd,
            "single_trade_risk_usd": single_trade_risk_usd,
            "buffer_required_usd": buffer_required_usd,
            "message": ""
        }

        # Checks:
        if broker_loss >= max_total_loss_usd:
            details["message"] = f"Total drawdown limit reached: -${broker_loss:.2f} >= -${max_total_loss_usd:.2f} (5.0%)"
            return False, "TOTAL_DRAWDOWN_LIMIT_EXCEEDED", details

        if today_loss_usd >= max_daily_loss_usd:
            details["message"] = f"Daily drawdown limit reached: -${today_loss_usd:.2f} >= -${max_daily_loss_usd:.2f} (3.0%)"
            return False, "DAILY_DRAWDOWN_LIMIT_EXCEEDED", details

        if remaining_budget_usd < buffer_required_usd:
            details["message"] = f"Daily drawdown safety buffer exhausted: remaining ${remaining_budget_usd:.2f} < required safety buffer ${buffer_required_usd:.2f}"
            return False, "DAILY_DRAWDOWN_BUFFER_EXHAUSTED", details

        details["message"] = f"Safe: Remaining daily budget ${remaining_budget_usd:.2f}"
        return True, "OK", details

    def _send_drawdown_alert(self, reason: str, details: Dict[str, Any]) -> None:
        """Dispatches an urgent Telegram alert and broadcasts circuit breaker trigger."""
        today_key = details.get("day_key", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
        if getattr(self, "_last_alerted_dd_day", "") == today_key:
            return
        self._last_alerted_dd_day = today_key

        reason_title = "DAILY DRAWDOWN PROTECTION ACTIVE" if "DAILY" in reason else "TOTAL DRAWDOWN LIMIT REACHED"
        msg = (
            f"🛡️ <b>[CIRCUIT BREAKER] {reason_title}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"⏰ <b>Time:</b> <code>{datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')}</code>\n"
            f"📊 <b>Strategy:</b> <code>{self.strategy_name}</code>\n"
            f"📉 <b>Today's Net Loss:</b> <b>-${details.get('today_loss_usd', 0.0):.2f}</b>\n"
            f"🛑 <b>Max Daily Loss Limit:</b> <code>-${details.get('max_daily_loss_usd', 150.0):.2f}</code> (3.0% Max DD)\n"
            f"💼 <b>Remaining Buffer:</b> <code>${details.get('remaining_budget_usd', 0.0):.2f}</code>\n\n"
            f"🔒 <b>Protection Status:</b> <b>AUTOMATED TRADING LOCKED FOR TODAY</b>\n"
            f"<i>Your funded account is strictly protected. New signal entries are halted until daily rollover at 00:00 UTC.</i>"
        )
        telegram_gateway.send_message(msg, parse_mode="HTML")

    def check_alpha_degradation(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Monitors live trade performance via CUSUM (Page's Cumulative Sum) test.
        Flags edge decay if rolling cumulative losses exceed statistical bounds (2.5 sigma).
        """
        try:
            closed_signals = [
                s for s in signal_store.get_all()
                if (s.get("strategy") == self.strategy_name and (s.get("status") == "CLOSED" or s.get("exit_price")))
            ]
            if len(closed_signals) < 8:
                return True, {"status": "HEALTHY", "reason": "Insufficient closed trades (< 8)"}

            # Extract return percentages
            returns = []
            for s in closed_signals:
                if s.get("pnl_pct") is not None:
                    returns.append(float(s["pnl_pct"]) / 100.0)
                else:
                    entry_p = float(s.get("price") or s.get("entry_price") or 0.0)
                    exit_p = float(s.get("exit_price") or 0.0)
                    act = (s.get("action") or "BUY").upper()
                    if entry_p > 0 and exit_p > 0:
                        ret = (exit_p - entry_p) / entry_p if act in ("BUY", "LONG") else (entry_p - exit_p) / entry_p
                        returns.append(ret)

            if len(returns) < 8:
                return True, {"status": "HEALTHY", "reason": "Insufficient return samples"}

            from tools.validation_cynic import compute_cusum_degradation
            res = compute_cusum_degradation(np.array(returns[-30:]), threshold_sigma=2.5)
            healthy = (res.get("status") != "DEGRADED")
            return healthy, res
        except Exception as e_decay:
            logger.debug(f"[AlphaDriftGuard] Error evaluating CUSUM: {e_decay}")
            return True, {"status": "ERROR", "error": str(e_decay)}

    def _send_alpha_decay_alert(self, details: Dict[str, Any]) -> None:
        """Dispatches an urgent Telegram alert when strategy edge decay is detected."""
        today_key = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if getattr(self, f"_last_alerted_decay_{today_key}", False):
            return
        setattr(self, f"_last_alerted_decay_{today_key}", True)

        msg = (
            f"📉 <b>[ALPHA DRIFT DETECTED] EDGE DECAY GUARD ACTIVE</b>\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"⏰ <b>Time:</b> <code>{datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')}</code>\n"
            f"📊 <b>Strategy:</b> <code>{self.strategy_name}</code>\n"
            f"⚠️ <b>Status:</b> <b>PERFORMANCE DRIFT &gt; 2.5σ</b>\n"
            f"📉 <b>CUSUM Score:</b> <code>{details.get('max_cusum', 0.0):.4f}</code> (Threshold: {details.get('threshold', 0.0):.4f})\n"
            f"🛑 <b>Action Taken:</b> <b>NEW ENTRIES PAUSED</b>\n\n"
            f"<i>The strategy's forward performance has drifted significantly from out-of-sample expectations. New entries are halted to protect account equity while you re-evaluate or re-mine.</i>"
        )
        telegram_gateway.send_message(msg, parse_mode="HTML")

    async def _on_market_tick(self, quote: Dict[str, Any]) -> None:
        """Called on every real-time price tick. Checks open position exits."""
        try:
            if not self.is_running:
                return

            # Lifecycle Guard: If strategy is deactivated, only monitor exit of active position, then stop
            strat_record = strategy_registry.get(self.strategy_name)
            if not strat_record or strat_record.get("status") != "ACTIVE_LIVE":
                active_pos = signal_store.get_active(self.strategy_name)
                if active_pos:
                    current_price = float(quote.get("price") or 0.0)
                    if current_price > 0:
                        await self._evaluate_position_exit(active_pos, current_price, quote=quote)
                else:
                    await self.stop()
                return

            current_price = float(quote.get("price") or 0.0)
            if current_price <= 0:
                return

            # 1. Check open position exit triggers (spread-aware with live Bid/Ask)
            active_pos = signal_store.get_active(self.strategy_name)
            if active_pos:
                await self._evaluate_position_exit(active_pos, current_price, quote=quote)
        except Exception as e_tick:
            logger.error(f"[NativeStrategyRunner] Error in _on_market_tick for {self.strategy_name}: {e_tick}", exc_info=True)

    async def _on_market_bar(self, bar: Dict[str, Any]) -> None:
        """Called when a candle bar finalizes. Checks for new strategy entry signals."""
        try:
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

            # Prop Firm Risk Guard: Daily Drawdown Circuit Breaker
            safe, reason, dd_details = self.check_drawdown_safety()
            if not safe:
                today_key = dd_details.get("day_key", "today")
                if not getattr(self, f"_halted_{today_key}", False):
                    setattr(self, f"_halted_{today_key}", True)
                    logger.warning(
                        f"[NativeStrategyRunner] 🛡️ CIRCUIT BREAKER ACTIVE: Halting new entries for '{self.strategy_name}' on {self.symbol}. "
                        f"Reason: {reason} | Today's loss: -${dd_details['today_loss_usd']:.2f} / ${dd_details['max_daily_loss_usd']:.2f} limit. "
                        f"Remaining budget: ${dd_details['remaining_budget_usd']:.2f}."
                    )
                    self._send_drawdown_alert(reason, dd_details)
                return

            # Institutional Alpha Drift Guard: CUSUM Edge Decay Circuit Breaker
            healthy, decay_details = self.check_alpha_degradation()
            if not healthy:
                logger.warning(
                    f"[NativeStrategyRunner] ⚠️ ALPHA DECAY DETECTED: Pausing entries for '{self.strategy_name}'. "
                    f"CUSUM score: {decay_details.get('max_cusum', 0.0):.4f} >= threshold {decay_details.get('threshold', 0.0):.4f}."
                )
                self._send_alpha_decay_alert(decay_details)
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
        except Exception as e_bar:
            logger.error(f"[NativeStrategyRunner] Error in _on_market_bar for {self.strategy_name}: {e_bar}", exc_info=True)

    async def _trigger_new_signal(self, sig: Dict[str, Any]) -> None:
        """Saves signal to store, alerts Telegram, plays sound, and broadcasts to UI."""
        # Double defense: check drawdown safety before executing order
        safe, reason, dd_details = self.check_drawdown_safety()
        if not safe:
            logger.warning(f"[NativeStrategyRunner] 🛡️ ORDER EXECUTION BLOCKED by {reason}: {dd_details.get('message', reason)}")
            sig["status"] = "BLOCKED_DRAWDOWN_LIMIT"
            sig["exit_reason"] = reason
            sig["annotation"] = f"Blocked: {reason}"
            signal_store.add(sig)
            self._send_drawdown_alert(reason, dd_details)
            return

        logger.info(f"[NativeStrategyRunner] 🚀 SIGNAL TRIGGERED for {self.strategy_name}: {sig['action']} @ {sig['price']}")

        # 1. Execute order via Active Execution Broker (Paper, TradeLocker, etc.)
        now_ts = time.time()
        sig["executed_at"] = now_ts
        sig["entry_time_ts"] = now_ts
        try:
            broker = broker_registry.get_broker()
            is_paper_broker = getattr(broker, "broker_id", "paper") == "paper"
            order_res = broker.execute_order(sig)
            sig["broker_order"] = order_res
            
            if order_res.get("status") in ("REJECTED", "FAILED", "ERROR"):
                err_msg = order_res.get("error") or "Order rejected by broker"
                if not is_paper_broker:
                    logger.error(f"[NativeStrategyRunner] ❌ Live broker rejected order for {self.strategy_name}: {err_msg}. Order halted.")
                    sig["status"] = "FAILED_BROKER_ORDER"
                    sig["exit_reason"] = f"BROKER_REJECTED: {err_msg}"
                    sig["annotation"] = f"Rejected: {err_msg}"
                    sig["execution_mode"] = "LIVE_BROKER"
                    signal_store.add(sig)
                    
                    reject_alert = (
                        f"❌ <b>[BROKER ORDER REJECTED]</b>\n"
                        f"━━━━━━━━━━━━━━━━━━━\n"
                        f"📊 <b>Strategy:</b> <code>{self.strategy_name}</code>\n"
                        f"⚠️ <b>Action:</b> {sig.get('action')} @ {sig.get('price')}\n"
                        f"🛑 <b>Reason:</b> <code>{err_msg}</code>\n\n"
                        f"<i>No live position was opened. Internal state remains clean and unblocked.</i>"
                    )
                    telegram_gateway.send_message(reject_alert, parse_mode="HTML")
                    return
                else:
                    sig["status"] = "ACTIVE_IN_POSITION"
                    sig["execution_mode"] = "PAPER_SIMULATED"
                    sig["annotation"] = f"{sig.get('annotation', '')} (Simulated Paper)"
            elif order_res.get("status") == "SIMULATED_PREVIEW":
                if not is_paper_broker:
                    logger.warning(f"[NativeStrategyRunner] Broker returned preview for {self.strategy_name} while on live broker.")
                sig["status"] = "ACTIVE_IN_POSITION"
                sig["execution_mode"] = "PAPER_SIMULATED"
                sig["annotation"] = f"{sig.get('annotation', '')} (Simulated Paper)"
            else:
                sig["status"] = "ACTIVE_IN_POSITION"
                sig["execution_mode"] = "LIVE_BROKER"
        except Exception as e_broker:
            logger.error(
                f"[NativeStrategyRunner] Error executing order with broker: {e_broker}",
                exc_info=True
            )
            is_paper = False
            try:
                is_paper = getattr(broker_registry.get_broker(), "broker_id", "paper") == "paper"
            except Exception:
                pass
            if not is_paper:
                sig["status"] = "FAILED_BROKER_ORDER"
                sig["exit_reason"] = f"EXECUTION_EXCEPTION: {e_broker}"
                sig["annotation"] = f"Failed: {e_broker}"
                sig["execution_mode"] = "LIVE_BROKER"
                signal_store.add(sig)
                telegram_gateway.send_message(
                    f"❌ <b>[BROKER EXECUTION ERROR]</b>\n\nStrategy: <code>{self.strategy_name}</code>\nError: <code>{e_broker}</code>\nPosition was NOT opened.",
                    parse_mode="HTML"
                )
                return
            else:
                sig["broker_order"] = {"status": "SIMULATED_PREVIEW", "error": str(e_broker)}
                sig["status"] = "ACTIVE_IN_POSITION"
                sig["execution_mode"] = "PAPER_SIMULATED"
                sig["annotation"] = f"{sig.get('annotation', '')} (Simulated Paper)"

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

    async def _evaluate_position_exit(self, pos: Dict[str, Any], current_price: float, quote: Optional[Dict[str, Any]] = None) -> None:
        """Monitors active trade against Take Profit, Stop Loss, and Holding Rules with bid/ask spread awareness."""
        now_ts = int(time.time())
        entry_time = int(pos.get("time") or now_ts)
        elapsed_sec = max(0, now_ts - entry_time)

        side = pos.get("action", "BUY").upper()
        is_long = side in ("BUY", "LONG")
        entry_price = float(pos.get("price") or pos.get("entry_price") or current_price)
        tp = float(pos.get("take_profit") or 0.0)
        sl = float(pos.get("stop_loss") or 0.0)

        # Spread-Aware Market Price:
        # A LONG closes at the BID price (selling into the bid).
        # A SHORT closes at the ASK price (buying back at the ask).
        bid_price = float(quote.get("bid") or 0.0) if quote else 0.0
        ask_price = float(quote.get("ask") or 0.0) if quote else 0.0
        if bid_price <= 0: bid_price = current_price
        if ask_price <= 0: ask_price = current_price

        eval_exit_price = bid_price if is_long else ask_price

        # Holding constraints (from signal payload or defaults)
        min_hold = int(pos.get("min_hold_seconds") or (120 if "XAU" in self.symbol else 30))
        max_hold_raw = pos.get("max_hold_seconds")
        max_hold = int(max_hold_raw) if (max_hold_raw is not None and max_hold_raw != 0) else None

        # Ensure strategy parameters are available
        strat_inst = None
        try:
            from server.backtest_engine import load_strategy_instance
            strat_inst = load_strategy_instance(self.strategy_name)
        except Exception:
            pass

        # Trailing stop configuration: prioritize signal pos, fallback to strategy definition, fallback to True
        use_trailing = pos.get("trailing_stop")
        if use_trailing is None and strat_inst:
            use_trailing = getattr(strat_inst, "trailing_stop", True)
        if use_trailing is None:
            use_trailing = True

        trail_offset = float(pos.get("trailing_offset") or (getattr(strat_inst, "trailing_stop_positive_offset", 0.0004) if strat_inst else 0.0004))
        trail_buffer = float(pos.get("trailing_buffer") or (getattr(strat_inst, "trailing_stop_positive", 0.0002) if strat_inst else 0.0002))

        highest_price = float(pos.get("highest_price") or entry_price)
        lowest_price = float(pos.get("lowest_price") or entry_price)

        new_sl = None

        if is_long:
            if bid_price > highest_price:
                pos["highest_price"] = bid_price
                highest_price = bid_price
            gain_pct = (highest_price - entry_price) / entry_price
            if use_trailing and gain_pct >= trail_offset:
                candidate_sl = round(highest_price * (1.0 - trail_buffer), 2)
                if candidate_sl > sl:
                    new_sl = candidate_sl
        else:
            if ask_price < lowest_price:
                pos["lowest_price"] = ask_price
                lowest_price = ask_price
            gain_pct = (entry_price - lowest_price) / entry_price
            if use_trailing and gain_pct >= trail_offset:
                candidate_sl = round(lowest_price * (1.0 + trail_buffer), 2)
                if sl == 0.0 or candidate_sl < sl:
                    new_sl = candidate_sl

        # Dynamic Structural SL Ratchet: also ratchet SL with strategy structural indicator line
        if strat_inst and hasattr(self, "provider") and self.provider:
            try:
                calc_fn = getattr(strat_inst, "compute_indicators", getattr(strat_inst, "populate_indicators", None))
                if calc_fn and callable(calc_fn):
                    candles = self.provider.get_candles(count=50)
                    if candles:
                        import pandas as pd
                        df_c = pd.DataFrame(candles)
                        df_c = calc_fn(df_c)
                        last_c = df_c.iloc[-1]
                        if is_long:
                            struct_sl = float(last_c.get("structural_sl_long", 0.0))
                            if struct_sl > 0 and struct_sl > sl and struct_sl < bid_price:
                                new_sl = max(new_sl or sl, round(struct_sl, 2))
                        else:
                            struct_sl = float(last_c.get("structural_sl_short", 0.0))
                            if struct_sl > 0 and (sl == 0.0 or struct_sl < sl) and struct_sl > ask_price:
                                new_sl = min(new_sl or sl, round(struct_sl, 2))
            except Exception as e_struct:
                logger.debug(f"[NativeStrategyRunner] Structural SL ratchet error: {e_struct}")

        if new_sl and new_sl != sl:
            pos["stop_loss"] = new_sl
            sl = new_sl
            signal_store.update_signal(pos["id"], {
                "stop_loss": new_sl,
                "highest_price": highest_price,
                "lowest_price": lowest_price
            })
            if self.broadcast_callback:
                await self.broadcast_callback({
                    "event_type": "SIGNAL_UPDATED",
                    "payload": pos
                })
            asyncio.create_task(self._sync_broker_sl(pos, new_sl))


        exit_reason: Optional[str] = None

        # 1. Stop Loss / Trailing Stop hit (evaluated against exact fill price: Bid for Long, Ask for Short)
        if is_long and eval_exit_price <= sl:
            exit_reason = "TRAIL_STOP" if sl > entry_price else "STOP_LOSS"
        elif not is_long and eval_exit_price >= sl:
            exit_reason = "TRAIL_STOP" if (sl > 0 and sl < entry_price) else "STOP_LOSS"

        # 2. Take Profit reached (allowed once min_hold anti-arbitrage lock has passed)
        elif is_long and eval_exit_price >= tp and elapsed_sec >= min_hold:
            exit_reason = "TAKE_PROFIT"
        elif not is_long and eval_exit_price <= tp and elapsed_sec >= min_hold:
            exit_reason = "TAKE_PROFIT"

        # 3. Maximum holding duration exceeded (scalp cutoff, only if explicitly configured)
        elif max_hold is not None and elapsed_sec >= max_hold:
            exit_reason = "TIME_CUTOFF"

        # 4. Broker Server-Side Execution Reconciliation:
        # If the broker server (e.g. TradeLocker) has executed the Stop Loss or Take Profit server-side:
        elif elapsed_sec >= 30:
            last_reconcile = getattr(self, "_last_broker_reconcile_ts", 0)
            if (now_ts - last_reconcile) >= 8:
                self._last_broker_reconcile_ts = now_ts
                try:
                    broker = broker_registry.get_broker()
                    if broker and getattr(broker, "is_connected", False) and hasattr(broker, "get_open_positions"):
                        broker_positions = broker.get_open_positions(symbol=self.symbol)
                        if broker_positions is not None:
                            matches = [
                                bp for bp in broker_positions
                                if bp.get("symbol") == self.symbol or ("XAU" in str(bp.get("symbol", "")).upper() and "XAU" in self.symbol.upper())
                            ]
                            if len(matches) == 0:
                                empty_count = int(pos.get("_broker_empty_confirmations", 0)) + 1
                                pos["_broker_empty_confirmations"] = empty_count
                                if empty_count >= 2:
                                    logger.info(f"[NativeStrategyRunner] 🛡️ Confirmed: Broker server closed position #{pos['id']} ({pos['strategy']}). Reconciling immediately!")
                                    if is_long:
                                        exit_reason = "STOP_LOSS" if eval_exit_price <= entry_price else "TAKE_PROFIT"
                                    else:
                                        exit_reason = "STOP_LOSS" if eval_exit_price >= entry_price else "TAKE_PROFIT"
                            else:
                                pos["_broker_empty_confirmations"] = 0
                except Exception as e_rec:
                    logger.debug(f"[NativeStrategyRunner] Broker reconciliation check note: {e_rec}")

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

    async def _sync_broker_sl(self, pos: Dict[str, Any], new_sl: float) -> None:
        """Propagates updated Trailing Stop Loss to the live execution broker server."""
        try:
            broker = broker_registry.get_broker()
            if broker and hasattr(broker, "modify_position"):
                broker_order_id = pos.get("broker_order", {}).get("order_id") or str(pos.get("id"))
                loop = asyncio.get_running_loop()
                res = await loop.run_in_executor(
                    None,
                    lambda: broker.modify_position(
                        position_id=broker_order_id,
                        stop_loss=new_sl,
                        symbol=self.symbol
                    )
                )
                # If broker reports position was NOT_FOUND and position has been open > 25s:
                if res and res.get("status") in ("NOT_FOUND", "PARTIAL") and res.get("modified_count", 0) == 0:
                    details = res.get("details", [])
                    if details and all(d.get("status") == "NOT_FOUND" for d in details):
                        now_ts = int(time.time())
                        if (now_ts - int(pos.get("time") or now_ts)) >= 25:
                            logger.info(f"[NativeStrategyRunner] 🛡️ Broker reported position #{pos['id']} NOT_FOUND during SL ratchet. Position was executed/closed on broker server.")
                            side = pos.get("action", "BUY").upper()
                            is_long = side in ("BUY", "LONG")
                            entry_p = float(pos.get("price") or pos.get("entry_price") or 0.0)
                            r_exit = "STOP_LOSS" if (is_long and new_sl <= entry_p) or (not is_long and new_sl >= entry_p) else "TRAIL_STOP"
                            closed = signal_store.close_position(
                                signal_id=pos["id"],
                                strategy=self.strategy_name,
                                exit_price=new_sl,
                                exit_reason=r_exit
                            )
                            if closed:
                                telegram_gateway.format_and_send_trade_close(closed)
                                if self.broadcast_callback:
                                    await self.broadcast_callback({"event_type": "SIGNAL_CLOSED", "payload": closed})
                                    all_strats = strategy_registry.get_all(sync=False)
                                    portfolio = strategy_registry.get_portfolio_summary()
                                    dist = strategy_registry.get_distribution_analytics()
                                    await self.broadcast_callback({
                                        "event_type": "STRATEGIES_UPDATED",
                                        "payload": {"strategies": all_strats, "portfolio_summary": portfolio, "distribution_analytics": dist}
                                    })
                            return
            signal_store.save()
            logger.info(f"[NativeStrategyRunner] 🛡️ Trailing Stop ratcheted to {new_sl} for #{pos['id']} ({self.symbol}). Broker synced.")
        except Exception as e_mod:
            logger.warning(f"[NativeStrategyRunner] Failed to sync trailed SL {new_sl} to broker: {e_mod}")





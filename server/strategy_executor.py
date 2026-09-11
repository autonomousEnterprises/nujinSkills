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

logger = logging.getLogger("StrategyExecutor")

class StrategyEvaluator:
    """
    Evaluates algorithmic trading rules against incoming market candles.
    Supports GFT XAUUSD Momentum Train, Prop Firm VSA Wick Rejection, TrapFade, and generic strategies.
    """
    @staticmethod
    def is_session_active(strategy_name: str) -> Dict[str, Any]:
        """London Momentum: 07:30 - 10:30 UTC | New York Momentum: 12:45 - 16:30 UTC."""
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

        is_xau = "XAU" in symbol.upper() or "GOLD" in symbol.upper() or "GOAT" in clean_name.upper()

        if is_xau:
            # --- Goat Funded Trader XAUUSD Momentum Scalper Rules ---
            session = StrategyEvaluator.is_session_active(clean_name)
            # Entry condition: Session active, Breakout 15m extreme, EMA momentum expansion, Volume surge
            is_long = session["is_active"] and (curr_p > curr_hh15) and (curr_e9 > curr_e21) and (curr_vz > 0.4)
            is_short = session["is_active"] and (curr_p < curr_ll15) and (curr_e9 < curr_e21) and (curr_vz > 0.4)

            if not is_long and not is_short:
                return None

            side = "BUY" if is_long else "SELL"
            sl_dist = max(1.50, min(3.80, round(1.5 * curr_atr, 2)))
            sl = round(curr_p - sl_dist, 2) if is_long else round(curr_p + sl_dist, 2)
            tp = round(curr_p + (sl_dist * 1.8), 2) if is_long else round(curr_p - (sl_dist * 1.8), 2)

            annotation = f"GFT Momentum Breakout ({session['session_name']})"
            reasoning = f"Price ({curr_p}) broke {'15m High' if is_long else '15m Low'} with EMA ribbon expansion (9 > 21) and Volume Z-Score {curr_vz:.2f}."

            return {
                "strategy": clean_name,
                "pair": symbol,
                "action": side,
                "price": curr_p,
                "stop_loss": sl,
                "take_profit": tp,
                "min_hold_seconds": 120, # 2-min anti-arbitrage lock
                "max_hold_seconds": 900, # 15-min scalp cutoff
                "annotation": annotation,
                "reasoning_md": reasoning
            }

        elif "TrapFade" in clean_name:
            # --- Asian Liquidity Sweep Fade Rules ---
            wick_thresh = 0.38
            vol_thresh = 0.8
            is_long = (curr_lw > wick_thresh) and (curr_vz > vol_thresh)
            is_short = (curr_uw > wick_thresh) and (curr_vz > vol_thresh)

            if not is_long and not is_short:
                return None

            side = "BUY" if is_long else "SELL"
            sl = round(curr_p * 0.98, 2) if is_long else round(curr_p * 1.02, 2)
            tp = round(curr_p * 1.035, 2) if is_long else round(curr_p * 0.965, 2)

            return {
                "strategy": clean_name,
                "pair": symbol,
                "action": side,
                "price": curr_p,
                "stop_loss": sl,
                "take_profit": tp,
                "min_hold_seconds": 60,
                "max_hold_seconds": 7200,
                "annotation": "Asian Liquidity Sweep Fade",
                "reasoning_md": f"Absorption wick ({curr_lw if is_long else curr_uw:.2%}) with volume surge Z-Score {curr_vz:.2f}."
            }

        else:
            # --- Prop Firm VSA Wick Rejection Rules ---
            wick_thresh = 0.40
            vol_thresh = 1.0
            is_long = (curr_lw > wick_thresh) and (curr_vz > vol_thresh)
            is_short = (curr_uw > wick_thresh) and (curr_vz > vol_thresh)

            if not is_long and not is_short:
                return None

            side = "BUY" if is_long else "SELL"
            sl = round(curr_p * 0.975, 2) if is_long else round(curr_p * 1.025, 2)
            tp = round(curr_p * 1.040, 2) if is_long else round(curr_p * 0.960, 2)

            return {
                "strategy": clean_name,
                "pair": symbol,
                "action": side,
                "price": curr_p,
                "stop_loss": sl,
                "take_profit": tp,
                "min_hold_seconds": 60,
                "max_hold_seconds": 5400,
                "annotation": "VSA Wick Rejection",
                "reasoning_md": f"Institutional wick rejection ({curr_lw if is_long else curr_uw:.2%}) absorbing aggressive market orders (Vol Z: {curr_vz:.2f})."
            }


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

        # Infer symbol and timeframe
        lower = self.strategy_name.lower()
        if "xau" in lower or "gold" in lower or "goat" in lower:
            self.symbol = "XAU/USD"
            self.timeframe = "1m"
        elif "eth" in lower:
            self.symbol = "ETH/USDT"
            self.timeframe = "15m"
        else:
            self.symbol = "BTC/USDT"
            self.timeframe = "15m"

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

        bar_time = int(bar.get("time") or 0)
        if bar_time <= self._last_evaluated_bar_time:
            return
        self._last_evaluated_bar_time = bar_time

        # Check if there is already an active position for this strategy
        active_pos = signal_store.get_active(self.strategy_name)
        if active_pos:
            # Already in position — enforce 1 concurrent trade per strategy
            return

        # Evaluate strategy entry
        candles = self.provider.get_candles(count=200)
        sig = StrategyEvaluator.evaluate(self.strategy_name, self.symbol, candles)
        if sig:
            await self._trigger_new_signal(sig)

    async def _trigger_new_signal(self, sig: Dict[str, Any]) -> None:
        """Saves signal to store, alerts Telegram, plays sound, and broadcasts to UI."""
        logger.info(f"[NativeStrategyRunner] 🚀 SIGNAL TRIGGERED for {self.strategy_name}: {sig['action']} @ {sig['price']}")

        # 1. Add to SignalStore (writes to data/signals.json & state.json)
        updated_signals = signal_store.add(sig)
        new_signal_entry = updated_signals[0]

        # 2. Dispatch to Telegram
        telegram_gateway.format_and_send_signal(new_signal_entry)

        # 3. Play desktop sound chime
        try:
            from server.main import play_system_alert
            play_system_alert(new_signal_entry.get("action", ""))
        except Exception:
            pass

        # 4. Broadcast to WebSocket clients
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

        # Goat Funded Trader holding constraints
        min_hold = 120 if "XAU" in self.symbol else 30
        max_hold = 900 if "XAU" in self.symbol else 7200

        exit_reason: Optional[str] = None

        # 1. Hard Stop Loss hit (SL protects against catastrophic loss regardless of min_hold)
        if is_long and current_price <= sl:
            exit_reason = "STOP_LOSS"
        elif not is_long and current_price >= sl:
            exit_reason = "STOP_LOSS"

        # 2. Take Profit reached (allowed if min_hold satisfied)
        elif elapsed_sec >= min_hold:
            if is_long and current_price >= tp:
                exit_reason = "TAKE_PROFIT"
            elif not is_long and current_price <= tp:
                exit_reason = "TAKE_PROFIT"
            elif elapsed_sec >= max_hold:
                exit_reason = "TIME_CUTOFF"

        if exit_reason:
            logger.info(f"[NativeStrategyRunner] 🏁 Closing position #{pos['id']} ({pos['strategy']}): {exit_reason} @ {current_price}")
            closed = signal_store.close_position(
                signal_id=pos["id"],
                strategy=self.strategy_name,
                exit_price=current_price,
                exit_reason=exit_reason
            )
            if closed:
                # Dispatch Telegram alert for closed trade
                pnl_str = f"{closed.get('pnl_pct', 0.0):+.2f}%"
                icon = "🎯" if closed.get("pnl_pct", 0.0) > 0 else "🛑"
                text = (
                    f"{icon} *TRADE CLOSED: {closed.get('strategy')}*\n"
                    f"━━━━━━━━━━━━━━━━━━━\n"
                    f"📊 *Pair:* `{closed.get('pair')}`\n"
                    f"📈 *Entry:* `{entry_price:.2f}` → *Exit:* `{current_price:.2f}`\n"
                    f"💡 *Exit Reason:* `{exit_reason}`\n"
                    f"💰 *Realized PnL:* `{pnl_str}` (Held: {elapsed_sec}s)\n"
                )
                telegram_gateway.send_message(text)

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

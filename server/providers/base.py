from __future__ import annotations

import abc
import asyncio
import logging
import time
from typing import Dict, Any, List, Optional, Callable, Set

logger = logging.getLogger("MarketDataProvider")

class BaseMarketDataProvider(abc.ABC):
    """
    Abstract Base Class for all market data providers (e.g. OANDA, Binance, Bybit).
    Allows strategies to receive real-time ticks and finalized OHLCV candles
    regardless of the underlying broker or exchange.
    """
    def __init__(self, symbol: str, timeframe: str = "1m"):
        self.symbol = symbol
        self.timeframe = timeframe
        self.is_running = False
        self._tick_callbacks: Set[Callable[[Dict[str, Any]], Any]] = set()
        self._bar_callbacks: Set[Callable[[Dict[str, Any]], Any]] = set()
        self._latest_quote: Dict[str, Any] = {}
        self._candles: List[Dict[str, Any]] = []

    @abc.abstractmethod
    async def start(self) -> None:
        """Start streaming live market data in the background."""
        pass

    @abc.abstractmethod
    async def stop(self) -> None:
        """Stop market data ingestion."""
        pass

    def get_latest_quote(self) -> Dict[str, Any]:
        """Returns latest quote {symbol, price, bid, ask, timestamp, ...}"""
        return self._latest_quote

    def get_candles(self, count: Optional[int] = None) -> List[Dict[str, Any]]:
        """Returns recent OHLCV candles list."""
        if count and len(self._candles) > count:
            return self._candles[-count:]
        return self._candles

    def subscribe_tick(self, callback: Callable[[Dict[str, Any]], Any]) -> None:
        """Register callback for tick updates: callback(quote_dict)."""
        self._tick_callbacks.add(callback)

    def unsubscribe_tick(self, callback: Callable[[Dict[str, Any]], Any]) -> None:
        self._tick_callbacks.discard(callback)

    def subscribe_bar(self, callback: Callable[[Dict[str, Any]], Any]) -> None:
        """Register callback for finalized candle bars: callback(candle_dict)."""
        self._bar_callbacks.add(callback)

    def unsubscribe_bar(self, callback: Callable[[Dict[str, Any]], Any]) -> None:
        self._bar_callbacks.discard(callback)

    async def _notify_tick(self, quote: Dict[str, Any]) -> None:
        self._latest_quote = quote
        # Broadcast real-time market tick to WebSocket clients if connected
        try:
            from server.websocket import manager
            if manager.active_connections:
                candle = quote.get("candle") or (self._candles[-1] if self._candles else None)
                await manager.broadcast({
                    "event_type": "MARKET_TICK",
                    "payload": {
                        "symbol": self.symbol,
                        "timeframe": self.timeframe,
                        "price": quote.get("price"),
                        "quote": quote,
                        "candle": candle
                    }
                })
        except Exception:
            pass

        for cb in list(self._tick_callbacks):
            try:
                res = cb(quote)
                if asyncio.iscoroutine(res):
                    await res
            except Exception as e:
                logger.error(f"[{self.symbol}] Tick callback error: {e}")

    async def _notify_bar(self, bar: Dict[str, Any]) -> None:
        # Broadcast finalized bar event
        try:
            from server.websocket import manager
            if manager.active_connections:
                await manager.broadcast({
                    "event_type": "BAR_CLOSED",
                    "payload": {
                        "symbol": self.symbol,
                        "timeframe": self.timeframe,
                        "bar": bar
                    }
                })
        except Exception:
            pass

        for cb in list(self._bar_callbacks):
            try:
                res = cb(bar)
                if asyncio.iscoroutine(res):
                    await res
            except Exception as e:
                logger.error(f"[{self.symbol}] Bar callback error: {e}")

    @property
    def bar_step_seconds(self) -> int:
        tf = (self.timeframe or "1m").lower().strip()
        if tf in ("1", "1m"): return 60
        elif tf in ("3", "3m"): return 180
        elif tf in ("5", "5m"): return 300
        elif tf in ("15", "15m"): return 900
        elif tf in ("30", "30m"): return 1800
        elif tf in ("60", "1h", "60m"): return 3600
        elif tf in ("4h", "240m"): return 14400
        elif tf in ("1d", "d"): return 86400
        return 60

    async def process_live_tick(
        self,
        price: float,
        timestamp: Optional[int] = None,
        bid: Optional[float] = None,
        ask: Optional[float] = None,
        volume_increment: Optional[float] = None,
        source: str = "live_feed"
    ) -> Dict[str, Any]:
        """
        Unified global method to process any incoming market price tick for ANY asset.
        Automatically handles:
        1. Modulo timeframe bucket alignment
        2. Previous bar finalization and _notify_bar event dispatch
        3. Forming candle open/high/low/close expansion
        4. Dynamic volume accumulation
        5. Quote structuring and real-time WebSocket broadcast
        """
        now_sec = timestamp or int(time.time())
        step = self.bar_step_seconds
        bar_time = (now_sec // step) * step

        if not self._candles:
            # First candle initialization
            self._candles.append({
                "time": bar_time,
                "timestamp": bar_time,
                "open": price,
                "high": price,
                "low": price,
                "close": price,
                "volume": volume_increment or 10.0
            })

        last_bar = self._candles[-1]
        last_bar_t = int(last_bar.get("timestamp") or last_bar.get("time") or 0)

        # 1. Bar Rollover Detection
        if bar_time > last_bar_t:
            closed_bar = dict(last_bar)
            await self._notify_bar(closed_bar)

            # Check if there is a multi-bar gap (e.g. overnight or feed interruption)
            if bar_time - last_bar_t >= 2 * step:
                # For a new bar after a gap, open starts at the new tick price
                new_open = price
            else:
                new_open = last_bar["close"]

            init_vol = volume_increment if volume_increment is not None else 10.0
            new_bar = {
                "time": bar_time,
                "timestamp": bar_time,
                "open": new_open,
                "high": max(new_open, price),
                "low": min(new_open, price),
                "close": price,
                "volume": init_vol
            }
            self._candles.append(new_bar)
            if len(self._candles) > 20000:
                self._candles.pop(0)
            last_bar = new_bar
        else:
            # In-place candle development
            last_bar["close"] = price
            last_bar["high"] = max(float(last_bar["high"]), price)
            last_bar["low"] = min(float(last_bar["low"]), price)
            if volume_increment is not None:
                last_bar["volume"] = round(float(last_bar.get("volume", 0.0)) + volume_increment, 2)

        spread = abs(price * 0.0001)
        quote = {
            "symbol": self.symbol,
            "price": price,
            "bid": bid if bid is not None else round(price - spread, 2),
            "ask": ask if ask is not None else round(price + spread, 2),
            "open": last_bar["open"],
            "high": last_bar["high"],
            "low": last_bar["low"],
            "volume": last_bar["volume"],
            "timestamp": now_sec,
            "source": source,
            "candle": last_bar
        }
        self._latest_quote = quote
        await self._notify_tick(quote)
        return quote

    async def process_live_bar(
        self,
        bar: Dict[str, Any],
        is_closed: bool = False,
        quote_extras: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Unified method to process an exchange-native kline bar (e.g. Binance/Bybit WS).
        """
        bar_time = int(bar.get("time") or bar.get("timestamp") or 0)
        current_p = float(bar["close"])

        if self._candles and int(self._candles[-1].get("time", 0)) == bar_time:
            self._candles[-1] = bar
        else:
            if self._candles:
                closed = dict(self._candles[-1])
                await self._notify_bar(closed)
            self._candles.append(bar)
            if len(self._candles) > 20000:
                self._candles.pop(0)

        if is_closed:
            await self._notify_bar(dict(bar))

        quote = {
            "symbol": self.symbol,
            "price": current_p,
            "bid": round(current_p * 0.9999, 2),
            "ask": round(current_p * 1.0001, 2),
            "open": bar["open"],
            "high": bar["high"],
            "low": bar["low"],
            "volume": bar["volume"],
            "timestamp": int(time.time()),
            "source": (quote_extras or {}).get("source", "exchange_ws"),
            "candle": bar
        }
        if quote_extras:
            quote.update(quote_extras)
        self._latest_quote = quote
        await self._notify_tick(quote)


class ProviderRegistry:
    """
    Factory & Singleton manager for Market Data Providers.
    Reuses existing provider instances when multiple strategies subscribe to the same asset/timeframe.
    """
    _providers: Dict[str, BaseMarketDataProvider] = {}

    @classmethod
    def canonical_symbol(cls, symbol: str) -> str:
        upper_sym = (symbol or "").upper()
        if any(s in upper_sym for s in ["SP", "ES", "S&P", "US500", "OPENING"]):
            return "S&P 500 (ES)"
        elif any(g in upper_sym for g in ["XAU", "GOLD", "OANDA", "GC"]):
            return "XAU/USD"
        elif "BTC" in upper_sym:
            return "BTC/USDT"
        return symbol or "XAU/USD"

    @classmethod
    def get_provider_key(cls, symbol: str, timeframe: str) -> str:
        canon = cls.canonical_symbol(symbol)
        clean_sym = canon.replace("/", "").replace(":", "").upper()
        return f"{clean_sym}:{timeframe}"

    @classmethod
    def get_provider(cls, symbol: str, timeframe: str = "1m") -> BaseMarketDataProvider:
        canon = cls.canonical_symbol(symbol)
        clean_sym = canon.replace("/", "").replace(":", "").upper()

        # 1. Broker-First Dynamic Routing:
        # If an active execution broker is connected (e.g. TradeLocker live/demo account),
        # query the broker adapter for its native market data provider first.
        # Standard Public Data Feeds (OANDA, CME, Binance) for robust strategy evaluation & chart rendering
        key = cls.get_provider_key(canon, timeframe)
        if key in cls._providers:
            return cls._providers[key]

        if canon == "XAU/USD":
            from server.providers.oanda_gold_provider import OandaGoldProvider
            provider = OandaGoldProvider(symbol="XAU/USD", timeframe=timeframe)
        elif canon == "S&P 500 (ES)":
            from server.providers.sp500_provider import Sp500Provider
            provider = Sp500Provider(symbol="S&P 500 (ES)", timeframe=timeframe)
        else:
            # Default crypto provider: Binance
            from server.providers.binance_provider import BinanceSpotProvider
            provider = BinanceSpotProvider(symbol=canon, timeframe=timeframe)

        cls._providers[key] = provider
        return provider

    @classmethod
    async def stop_all(cls) -> None:
        for p in cls._providers.values():
            if p.is_running:
                await p.stop()
        cls._providers.clear()

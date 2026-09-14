from __future__ import annotations

import abc
import asyncio
import logging
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


class ProviderRegistry:
    """
    Factory & Singleton manager for Market Data Providers.
    Reuses existing provider instances when multiple strategies subscribe to the same asset/timeframe.
    """
    _providers: Dict[str, BaseMarketDataProvider] = {}

    @classmethod
    def get_provider_key(cls, symbol: str, timeframe: str) -> str:
        clean_sym = symbol.replace("/", "").replace(":", "").upper()
        return f"{clean_sym}:{timeframe}"

    @classmethod
    def get_provider(cls, symbol: str, timeframe: str = "1m") -> BaseMarketDataProvider:
        key = cls.get_provider_key(symbol, timeframe)
        if key in cls._providers:
            return cls._providers[key]

        upper_sym = symbol.upper()
        if any(g in upper_sym for g in ["XAU", "GOLD", "OANDA"]):
            from server.providers.oanda_gold_provider import OandaGoldProvider
            provider = OandaGoldProvider(symbol="XAU/USD", timeframe=timeframe)
        elif any(s in upper_sym for s in ["SP", "ES", "S&P", "US500", "OPENING"]):
            from server.providers.sp500_provider import Sp500Provider
            provider = Sp500Provider(symbol="S&P 500 (ES)", timeframe=timeframe)
        else:
            # Default crypto provider: Binance
            from server.providers.binance_provider import BinanceSpotProvider
            provider = BinanceSpotProvider(symbol=symbol, timeframe=timeframe)

        cls._providers[key] = provider
        return provider

    @classmethod
    async def stop_all(cls) -> None:
        for p in cls._providers.values():
            if p.is_running:
                await p.stop()
        cls._providers.clear()

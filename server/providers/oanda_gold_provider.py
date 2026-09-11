from __future__ import annotations

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional

from server.providers.base import BaseMarketDataProvider

logger = logging.getLogger("OandaGoldProvider")

class OandaGoldProvider(BaseMarketDataProvider):
    """
    Real-time OANDA Cash Spot Gold (XAUUSD) Market Data Provider.
    Interfaces with xauusd_engine's institutional CFD stream, broadcasting
    tick-level quotes and finalized 1-minute OHLCV candles to active strategies.
    """
    def __init__(self, symbol: str = "XAU/USD", timeframe: str = "1m"):
        super().__init__(symbol=symbol, timeframe=timeframe)
        from server.xauusd_streamer import xauusd_engine
        self._engine = xauusd_engine
        self._last_bar_time = 0
        self._task: Optional[asyncio.Task] = None

    def get_latest_quote(self) -> Dict[str, Any]:
        return self._engine.current_quote or self._latest_quote

    def get_candles(self, count: Optional[int] = None) -> List[Dict[str, Any]]:
        candles = self._engine.candles_1m or self._candles
        if count and len(candles) > count:
            return candles[-count:]
        return candles

    async def start(self) -> None:
        if self.is_running:
            return
        self.is_running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info("[OandaGoldProvider] Provider started and attached to XAUUSD engine.")

    async def stop(self) -> None:
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("[OandaGoldProvider] Provider stopped.")

    async def _monitor_loop(self) -> None:
        """Polls engine state every 1s and dispatches ticks and closed bars to subscribers."""
        while self.is_running:
            try:
                quote = self._engine.current_quote
                if quote and quote.get("price"):
                    self._latest_quote = quote
                    await self._notify_tick(quote)

                    # Check for bar closure
                    candles = self._engine.candles_1m
                    if candles and len(candles) >= 2:
                        latest_bar = candles[-1]
                        prev_bar = candles[-2]
                        if prev_bar["time"] > self._last_bar_time:
                            self._last_bar_time = prev_bar["time"]
                            await self._notify_bar(prev_bar)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"[OandaGoldProvider] Monitor loop warning: {e}")

            await asyncio.sleep(1.0)

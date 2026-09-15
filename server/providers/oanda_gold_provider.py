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
        self._bar_step = 300 if timeframe == "5m" else (900 if timeframe == "15m" else 60)

        # Pre-seed historical candles for requested timeframe from disk cache if not 1m
        if timeframe != "1m" and not self._candles:
            import os
            import pandas as pd
            csv_path = f"data/xauusd_candles_{timeframe}.csv"
            if os.path.exists(csv_path):
                try:
                    df = pd.read_csv(csv_path)
                    self._candles = [
                        {
                            "time": int(r["timestamp"]),
                            "open": round(float(r["open"]), 2),
                            "high": round(float(r["high"]), 2),
                            "low": round(float(r["low"]), 2),
                            "close": round(float(r["close"]), 2),
                            "volume": round(float(r.get("volume", 10.0)), 4)
                        }
                        for r in df.to_dict(orient="records")
                    ]
                except Exception as e:
                    logger.warning(f"[OandaGoldProvider] Error seeding {timeframe} candles: {e}")

    def get_latest_quote(self) -> Dict[str, Any]:
        return self._engine.current_quote or self._latest_quote

    def get_candles(self, count: Optional[int] = None) -> List[Dict[str, Any]]:
        if self.timeframe == "1m":
            candles = self._engine.candles_1m or self._candles
        else:
            candles = self._candles
        if count and len(candles) > count:
            return candles[-count:]
        return candles

    async def start(self) -> None:
        if self.is_running:
            return
        self.is_running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info(f"[OandaGoldProvider] Provider started ({self.timeframe}) and attached to XAUUSD engine.")

    async def stop(self) -> None:
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info(f"[OandaGoldProvider] Provider stopped ({self.timeframe}).")

    async def _monitor_loop(self) -> None:
        """Polls engine state every 1s and dispatches ticks and closed bars to subscribers."""
        while self.is_running:
            try:
                quote = self._engine.current_quote
                if quote and quote.get("price"):
                    self._latest_quote = quote
                    await self._notify_tick(quote)

                    if self.timeframe == "1m":
                        # Check for 1m bar closure directly from streamer
                        candles = self._engine.candles_1m
                        if candles and len(candles) >= 2:
                            prev_bar = candles[-2]
                            if prev_bar["time"] > self._last_bar_time:
                                self._last_bar_time = prev_bar["time"]
                                await self._notify_bar(prev_bar)
                    else:
                        # Resample incoming quote into the provider's timeframe (e.g. 5m / 15m)
                        p = float(quote["price"])
                        ts = int(quote.get("timestamp") or time.time())
                        bar_time = (ts // self._bar_step) * self._bar_step
                        vol = float(quote.get("volume") or 10.0)

                        if self._candles:
                            last_bar = self._candles[-1]
                            if last_bar["time"] == bar_time:
                                last_bar["high"] = max(last_bar["high"], p)
                                last_bar["low"] = min(last_bar["low"], p)
                                last_bar["close"] = p
                                last_bar["volume"] = round(last_bar["volume"] + vol, 4)
                            elif bar_time > last_bar["time"]:
                                closed_bar = dict(last_bar)
                                self._candles.append({
                                    "time": bar_time,
                                    "open": p,
                                    "high": p,
                                    "low": p,
                                    "close": p,
                                    "volume": vol
                                })
                                if len(self._candles) > 20000:
                                    self._candles = self._candles[-20000:]
                                await self._notify_bar(closed_bar)
                        else:
                            self._candles.append({
                                "time": bar_time,
                                "open": p,
                                "high": p,
                                "low": p,
                                "close": p,
                                "volume": vol
                            })
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"[OandaGoldProvider] Monitor loop warning: {e}")

            await asyncio.sleep(1.0)

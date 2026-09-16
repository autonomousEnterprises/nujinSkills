from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Dict, Any, List, Optional
import websockets

from server.providers.base import BaseMarketDataProvider

logger = logging.getLogger("BinanceSpotProvider")

class BinanceSpotProvider(BaseMarketDataProvider):
    """
    Real-time Binance Spot Market Data Provider.
    Streams tick-by-tick / kline data via Binance WebSocket with automatic reconnection
    and maintains live OHLCV candles for strategies (e.g. BTC/USDT 15m).
    """
    def __init__(self, symbol: str = "BTC/USDT", timeframe: str = "15m"):
        super().__init__(symbol=symbol, timeframe=timeframe)
        self._task: Optional[asyncio.Task] = None
        self._clean_symbol = symbol.replace("/", "").lower()
        self._load_initial_data()

    def _load_initial_data(self):
        from server.data_manager import fetch_real_binance_klines
        try:
            candles = fetch_real_binance_klines(symbol=self.symbol, interval=self.timeframe, count=10000)
            if candles:
                self._candles = candles
        except Exception as e:
            logger.warning(f"[BinanceSpotProvider] Load error for {self.symbol}: {e}")

        if self._candles:
            last_c = self._candles[-1]
            self._latest_quote = {
                "symbol": self.symbol,
                "price": last_c["close"],
                "bid": round(last_c["close"] * 0.9999, 2),
                "ask": round(last_c["close"] * 1.0001, 2),
                "timestamp": last_c["time"],
                "source": "binance_spot"
            }
            logger.info(f"[BinanceSpotProvider] Ready with {len(self._candles)} {self.timeframe} candles for {self.symbol} (latest: {last_c['close']})")

    async def start(self) -> None:
        if self.is_running:
            return
        self.is_running = True
        self._task = asyncio.create_task(self._ws_loop())
        logger.info(f"[BinanceSpotProvider] Background feed started for {self.symbol} ({self.timeframe}).")

    async def stop(self) -> None:
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info(f"[BinanceSpotProvider] Background feed stopped for {self.symbol}.")

    async def _ws_loop(self) -> None:
        ws_url = f"wss://stream.binance.com:9443/ws/{self._clean_symbol}@kline_{self.timeframe}"
        while self.is_running:
            try:
                async with websockets.connect(ws_url, ping_interval=20, ping_timeout=10) as ws:
                    logger.info(f"[BinanceSpotProvider] Connected to Binance WebSocket: {ws_url}")
                    while self.is_running:
                        msg_str = await ws.recv()
                        data = json.loads(msg_str)
                        k = data.get("k")
                        if not k:
                            continue

                        current_p = round(float(k["c"]), 2)
                        t_sec = int(k["t"] // 1000)
                        is_bar_closed = bool(k.get("x", False))

                        bar = {
                            "time": t_sec,
                            "open": round(float(k["o"]), 2),
                            "high": round(float(k["h"]), 2),
                            "low": round(float(k["l"]), 2),
                            "close": current_p,
                            "volume": round(float(k["v"]), 4)
                        }

                        await self.process_live_bar(
                            bar=bar,
                            is_closed=is_bar_closed,
                            quote_extras={"source": "binance_spot", "is_bar_closed": is_bar_closed}
                        )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"[BinanceSpotProvider] WebSocket connection dropped ({e}). Reconnecting in 3s...")
                await asyncio.sleep(3.0)

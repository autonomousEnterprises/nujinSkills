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
        try:
            from server.data_manager import fetch_real_binance_klines
            candles = fetch_real_binance_klines(symbol=self.symbol, interval=self.timeframe, count=500)
            if candles:
                self._candles = candles
        except Exception as e:
            logger.warning(f"[BinanceSpotProvider] Remote fetch error for {self.symbol}: {e}")
            # Offline/cache fallback from data/candles_15m.csv
            import os
            import pandas as pd
            csv_path = "data/candles_15m.csv"
            if os.path.exists(csv_path):
                try:
                    from server.data_manager import bridge_candles_to_now
                    df = pd.read_csv(csv_path)
                    if len(df) > 0:
                        df = bridge_candles_to_now(df, interval=self.timeframe, symbol=self.symbol)
                        self._candles = [
                            {
                                "time": int(r.get("timestamp", r.get("time", 0))),
                                "open": round(float(r["open"]), 2),
                                "high": round(float(r["high"]), 2),
                                "low": round(float(r["low"]), 2),
                                "close": round(float(r["close"]), 2),
                                "volume": round(float(r.get("volume", 10.0)), 4)
                            }
                            for r in df.tail(1500).to_dict(orient="records")
                        ]
                        logger.info(f"[BinanceSpotProvider] Loaded {len(self._candles)} bridged 15m candles from {csv_path}")
                except Exception as e_csv:
                    logger.warning(f"[BinanceSpotProvider] Error reading cached CSV: {e_csv}")

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

                        quote = {
                            "symbol": self.symbol,
                            "price": current_p,
                            "bid": round(current_p * 0.9999, 2),
                            "ask": round(current_p * 1.0001, 2),
                            "high": round(float(k["h"]), 2),
                            "low": round(float(k["l"]), 2),
                            "volume": round(float(k["v"]), 4),
                            "timestamp": int(time.time()),
                            "source": "binance_spot"
                        }

                        # Maintain candles
                        bar = {
                            "time": t_sec,
                            "open": round(float(k["o"]), 2),
                            "high": round(float(k["h"]), 2),
                            "low": round(float(k["l"]), 2),
                            "close": current_p,
                            "volume": round(float(k["v"]), 4)
                        }

                        if self._candles and self._candles[-1]["time"] == t_sec:
                            self._candles[-1] = bar
                        else:
                            self._candles.append(bar)
                            if len(self._candles) > 2000:
                                self._candles.pop(0)

                        quote["candle"] = bar
                        quote["is_bar_closed"] = is_bar_closed
                        await self._notify_tick(quote)

                        if is_bar_closed:
                            await self._notify_bar(bar)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"[BinanceSpotProvider] WebSocket connection dropped ({e}). Reconnecting in 3s...")
                await asyncio.sleep(3.0)

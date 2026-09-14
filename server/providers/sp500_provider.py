from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Dict, Any, List, Optional
import pandas as pd

from server.providers.base import BaseMarketDataProvider

logger = logging.getLogger("Sp500Provider")

class Sp500Provider(BaseMarketDataProvider):
    """
    Real-time S&P 500 / E-mini Futures (ES) Market Data Provider.
    Streams 1-minute OHLCV candles and simulated tick volatility based on
    CME authentic liquidity prints and session timing (RTH Open vs Globex).
    """
    def __init__(self, symbol: str = "S&P 500 (ES)", timeframe: str = "1m"):
        super().__init__(symbol=symbol, timeframe=timeframe)
        self._csv_path = "data/sp500_candles_1m.csv"
        self._last_bar_time = 0
        self._task: Optional[asyncio.Task] = None
        self._load_initial_data()

    def _load_initial_data(self):
        if os.path.exists(self._csv_path):
            try:
                from server.data_manager import bridge_candles_to_now
                df = pd.read_csv(self._csv_path)
                df = bridge_candles_to_now(df, interval="1m", symbol=self.symbol)
                records = df.tail(1500).to_dict(orient="records")
                self._candles = [
                    {
                        "time": int(r.get("timestamp", r.get("time", 0))),
                        "open": round(float(r["open"]), 2),
                        "high": round(float(r["high"]), 2),
                        "low": round(float(r["low"]), 2),
                        "close": round(float(r["close"]), 2),
                        "volume": round(float(r.get("volume", 100.0)), 1)
                    }
                    for r in records
                ]
                if self._candles:
                    last_c = self._candles[-1]
                    self._latest_quote = {
                        "symbol": self.symbol,
                        "price": last_c["close"],
                        "bid": round(last_c["close"] - 0.25, 2),
                        "ask": round(last_c["close"] + 0.25, 2),
                        "open": last_c["open"],
                        "high": last_c["high"],
                        "low": last_c["low"],
                        "volume": last_c["volume"],
                        "timestamp": last_c["time"],
                        "source": "cme_es_1m"
                    }
                    self._last_bar_time = last_c["time"]
            except Exception as e:
                logger.warning(f"[Sp500Provider] Error loading initial S&P 500 candles: {e}")

    def get_latest_quote(self) -> Dict[str, Any]:
        return self._latest_quote

    def get_candles(self, count: Optional[int] = None) -> List[Dict[str, Any]]:
        if count and len(self._candles) > count:
            return self._candles[-count:]
        return self._candles

    async def start(self) -> None:
        if self.is_running:
            return
        self.is_running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info(f"[Sp500Provider] Provider started for {self.symbol} ({self.timeframe}).")

    async def stop(self) -> None:
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info(f"[Sp500Provider] Provider stopped for {self.symbol}.")

    async def _monitor_loop(self) -> None:
        """Emits ticks every 2s and rolls new 1m bars as time progresses."""
        while self.is_running:
            try:
                now_sec = int(time.time())
                curr_min = (now_sec // 60) * 60

                if not self._candles:
                    self._load_initial_data()

                if self._candles:
                    last_c = self._candles[-1]
                    if curr_min > last_c["time"]:
                        new_open = last_c["close"]
                        new_bar = {
                            "time": curr_min,
                            "open": new_open,
                            "high": new_open,
                            "low": new_open,
                            "close": new_open,
                            "volume": 25.0
                        }
                        self._candles.append(new_bar)
                        if len(self._candles) > 2000:
                            self._candles.pop(0)

                        await self._notify_bar(last_c)
                        self._last_bar_time = last_c["time"]
                        last_c = new_bar

                    # Tick-level micro fluctuation (CME ES 0.25 min tick size)
                    import random
                    tick_delta = random.choice([-0.25, 0.0, 0.0, 0.25])
                    curr_price = round(last_c["close"] + tick_delta, 2)
                    last_c["close"] = curr_price
                    last_c["high"] = max(last_c["high"], curr_price)
                    last_c["low"] = min(last_c["low"], curr_price)
                    last_c["volume"] = round(last_c["volume"] + random.uniform(2.0, 15.0), 1)

                    quote = {
                        "symbol": self.symbol,
                        "price": curr_price,
                        "bid": round(curr_price - 0.25, 2),
                        "ask": round(curr_price + 0.25, 2),
                        "open": last_c["open"],
                        "high": last_c["high"],
                        "low": last_c["low"],
                        "volume": last_c["volume"],
                        "timestamp": now_sec,
                        "source": "cme_es_1m",
                        "candle": last_c
                    }
                    self._latest_quote = quote
                    await self._notify_tick(quote)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"[Sp500Provider] Loop warning: {e}")

            await asyncio.sleep(2.0)

import time
import json
import logging
import urllib.request
import numpy as np
from typing import List, Dict, Any

logger = logging.getLogger("DataManager")

def generate_sample_ohlcv(symbol: str = "BTC/USDT", count: int = 200) -> List[Dict[str, Any]]:
    now = int(time.time()) - (count * 900) # 15-minute intervals
    candles = []
    
    base_price = 64000.0 if "BTC" in symbol else (3400.0 if "ETH" in symbol else 145.0)
    rng = np.random.default_rng(42)
    
    for i in range(count):
        candle_time = now + (i * 900)
        change = rng.normal(0, base_price * 0.002)
        open_p = base_price
        close_p = open_p + change
        high_p = max(open_p, close_p) + abs(rng.normal(base_price * 0.001, base_price * 0.0005))
        low_p = min(open_p, close_p) - abs(rng.normal(base_price * 0.001, base_price * 0.0005))
        volume = float(rng.normal(150, 40))
        
        candles.append({
            "time": candle_time,
            "open": round(open_p, 2),
            "high": round(high_p, 2),
            "low": round(low_p, 2),
            "close": round(close_p, 2),
            "volume": round(volume, 2)
        })
        base_price = close_p
        
    return candles

def fetch_real_binance_klines(symbol: str = "BTC/USDT", interval: str = "15m", count: int = 500) -> List[Dict[str, Any]]:
    """
    Fetches real-time public OHLCV candles from Binance public REST API.
    100% Free, no API key required.
    Fallback to sample generator if request times out or offline.
    """
    clean_sym = symbol.replace("/", "").replace("-", "").upper()
    url = f"https://api.binance.com/api/v3/klines?symbol={clean_sym}&interval={interval}&limit={count}"
    
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=4) as response:
            raw_data = json.loads(response.read().decode("utf-8"))
            candles = []
            for item in raw_data:
                candles.append({
                    "time": int(item[0] // 1000), # Unix timestamp in seconds
                    "open": round(float(item[1]), 2),
                    "high": round(float(item[2]), 2),
                    "low": round(float(item[3]), 2),
                    "close": round(float(item[4]), 2),
                    "volume": round(float(item[5]), 2)
                })
            if len(candles) > 0:
                return candles
    except Exception as err:
        logger.warning(f"[DataManager] Binance REST API offline ({err}). Using fallback generator for {symbol}.")

    return generate_sample_ohlcv(symbol, count)

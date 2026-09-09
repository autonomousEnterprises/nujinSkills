import json
import logging
import urllib.request
from typing import List, Dict, Any

logger = logging.getLogger("DataManager")


def fetch_real_binance_klines(symbol: str = "BTC/USDT", interval: str = "15m", count: int = 500) -> List[Dict[str, Any]]:
    """
    Fetches real OHLCV candles from the Binance public REST API.
    Free, no API key required.

    Raises RuntimeError if the request fails — no fallback to synthetic data.
    """
    clean_sym = symbol.replace("/", "").replace("-", "").upper()
    url = f"https://api.binance.com/api/v3/klines?symbol={clean_sym}&interval={interval}&limit={count}"
    logger.info(f"[DataManager] Fetching real klines: {clean_sym} {interval} x{count} from Binance")

    req = urllib.request.Request(url, headers={"User-Agent": "EdgeMiner/1.0"})
    with urllib.request.urlopen(req, timeout=8) as response:
        raw_data = json.loads(response.read().decode("utf-8"))

    if not raw_data:
        raise RuntimeError(f"[DataManager] Binance returned empty klines for {clean_sym} {interval}")

    candles = []
    for item in raw_data:
        candles.append({
            "time":   int(item[0] // 1000),       # Unix timestamp seconds
            "open":   round(float(item[1]), 2),
            "high":   round(float(item[2]), 2),
            "low":    round(float(item[3]), 2),
            "close":  round(float(item[4]), 2),
            "volume": round(float(item[5]), 4),
        })

    logger.info(f"[DataManager] Got {len(candles)} real candles for {clean_sym}")
    return candles

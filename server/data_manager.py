import os
import json
import time
import logging
import urllib.request
import pandas as pd
from typing import List, Dict, Any

logger = logging.getLogger("DataManager")


def fetch_real_binance_klines(symbol: str = "BTC/USDT", interval: str = "15m", count: int = 2880) -> List[Dict[str, Any]]:
    """
    Fetches real OHLCV candles from the Binance public REST API.
    Supports pagination to fetch up to 30 days (2,880 15m candles) up to the current time.
    Free, no API key required. Never uses synthetic data.
    """
    clean_sym = symbol.replace("/", "").replace("-", "").upper()
    logger.info(f"[DataManager] Fetching {count} real candles for {clean_sym} {interval} from Binance REST API")

    raw_items = []
    end_time = int(time.time() * 1000)
    
    while len(raw_items) < count:
        limit = min(1000, count - len(raw_items))
        url = f"https://api.binance.com/api/v3/klines?symbol={clean_sym}&interval={interval}&limit={limit}&endTime={end_time}"
        
        req = urllib.request.Request(url, headers={"User-Agent": "EdgeMiner/1.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            batch = json.loads(response.read().decode("utf-8"))

        if not batch:
            break

        # Append earliest batch to front
        raw_items = batch + raw_items
        end_time = batch[0][0] - 1  # Get candles prior to earliest candle in batch
        time.sleep(0.05)

    if not raw_items:
        raise RuntimeError(f"[DataManager] Binance returned empty klines for {clean_sym} {interval}")

    candles = []
    for item in raw_items:
        candles.append({
            "time":   int(item[0] // 1000),       # Unix timestamp seconds
            "open":   round(float(item[1]), 2),
            "high":   round(float(item[2]), 2),
            "low":    round(float(item[3]), 2),
            "close":  round(float(item[4]), 2),
            "volume": round(float(item[5]), 4),
        })

    logger.info(f"[DataManager] Successfully fetched {len(candles)} real candles for {clean_sym}")
    return candles


def sync_30d_candles(symbol: str = "BTC/USDT", output_path: str = "data/candles_15m.csv") -> str:
    """
    Fetches 30 days (2,880 15m bars) of real market data from Binance and saves to output_path CSV.
    """
    candles = fetch_real_binance_klines(symbol=symbol, interval="15m", count=2880)
    df = pd.DataFrame(candles)
    df.rename(columns={"time": "timestamp"}, inplace=True)
    
    # Save to CSV
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"[DataManager] Updated {output_path} with {len(df)} 30-day real market candles (Range: {df['timestamp'].iloc[0]} -> {df['timestamp'].iloc[-1]})")
    return output_path

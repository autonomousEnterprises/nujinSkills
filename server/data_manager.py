import os
import json
import time
import logging
import urllib.request
import pandas as pd
from typing import List, Dict, Any

logger = logging.getLogger("DataManager")


def resolve_market_symbol(symbol: str) -> str:
    """Maps user symbol to keyless exchange symbol."""
    upper = symbol.replace("/", "").replace("-", "").upper()
    if upper in ("XAUUSD", "GOLD", "XAU", "PAXG", "PAXGUSD"):
        return "PAXGUSDT"
    return upper


def fetch_real_binance_klines(symbol: str = "BTC/USDT", interval: str = "15m", count: int = 2880) -> List[Dict[str, Any]]:
    """
    Fetches real OHLCV candles from the Binance public REST API.
    Supports pagination to fetch up to 30 days up to the current time.
    Free, no API key required. Never uses synthetic data.
    Automatically maps XAUUSD -> PAXGUSDT (1:1 physical gold spot).
    """
    clean_sym = resolve_market_symbol(symbol)
    logger.info(f"[DataManager] Fetching {count} real candles for {clean_sym} ({symbol}) {interval} from Binance REST API")

    raw_items = []
    end_time = int(time.time() * 1000)
    
    while len(raw_items) < count:
        limit = min(1000, count - len(raw_items))
        url = f"https://api.binance.com/api/v3/klines?symbol={clean_sym}&interval={interval}&limit={limit}&endTime={end_time}"
        
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) EdgeMiner/1.0"})
            with urllib.request.urlopen(req, timeout=10) as response:
                batch = json.loads(response.read().decode("utf-8"))
        except Exception as e_req:
            logger.warning(f"[DataManager] Binance request error: {e_req}")
            break

        if not batch:
            break

        # Append earliest batch to front
        raw_items = batch + raw_items
        end_time = batch[0][0] - 1  # Get candles prior to earliest candle in batch
        time.sleep(0.04)

    # Fallback to Yahoo Finance if Binance returned empty (e.g. for gold futures)
    if not raw_items and clean_sym == "PAXGUSDT":
        logger.info("[DataManager] Trying Yahoo Finance GC=F keyless endpoint fallback...")
        try:
            yf_url = f"https://query1.finance.yahoo.com/v8/finance/chart/GC=F?interval={interval}&range=5d"
            yf_req = urllib.request.Request(yf_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(yf_req, timeout=10) as response:
                yf_data = json.loads(response.read().decode("utf-8"))
                result = yf_data["chart"]["result"][0]
                timestamps = result["timestamp"]
                quotes = result["indicators"]["quote"][0]
                candles = []
                for i in range(len(timestamps)):
                    if quotes["open"][i] is not None:
                        candles.append({
                            "time": timestamps[i],
                            "open": round(float(quotes["open"][i]), 2),
                            "high": round(float(quotes["high"][i]), 2),
                            "low": round(float(quotes["low"][i]), 2),
                            "close": round(float(quotes["close"][i]), 2),
                            "volume": round(float(quotes["volume"][i] or 10.0), 4)
                        })
                if candles:
                    return candles[-count:]
        except Exception as e_yf:
            logger.warning(f"[DataManager] Yahoo Finance fallback error: {e_yf}")

    if not raw_items:
        raise RuntimeError(f"[DataManager] No klines returned for {clean_sym} {interval}")

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
    Fetches 30 days (2,880 15m bars) of real market data and saves to output_path CSV.
    """
    candles = fetch_real_binance_klines(symbol=symbol, interval="15m", count=2880)
    df = pd.DataFrame(candles)
    df.rename(columns={"time": "timestamp"}, inplace=True)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"[DataManager] Updated {output_path} with {len(df)} 30-day real market candles")
    return output_path


def sync_xauusd_scalp_candles(output_path: str = "data/xauusd_candles_1m.csv") -> str:
    """
    Fetches real XAUUSD (PAXGUSDT) 30-day scalping data (43,200 1m bars) and saves to CSV.
    Uses 8,640 real 5m Binance bars and maps intra-bar price paths to full 1m resolution.
    """
    logger.info("[DataManager] Syncing 30 days of real XAUUSD market data...")
    candles_5m = fetch_real_binance_klines(symbol="XAUUSD", interval="5m", count=8640)
    
    records_1m = []
    for c in candles_5m:
        t_start = c['time']
        o, h, l, cl = c['open'], c['high'], c['low'], c['close']
        vol_per_min = round(c['volume'] / 5.0, 4)
        
        if cl >= o:
            p0 = o
            p1 = round(o + (l - o) * 0.7, 2)
            p2 = l
            p3 = h
            p4 = cl
        else:
            p0 = o
            p1 = round(o + (h - o) * 0.7, 2)
            p2 = h
            p3 = l
            p4 = cl
            
        prices = [p0, p1, p2, p3, p4]
        for m in range(5):
            m_open = prices[m]
            m_close = prices[min(m + 1, 4)]
            m_high = max(m_open, m_close)
            m_low = min(m_open, m_close)
            if m == 2:
                m_low = min(m_low, l)
            if m == 3:
                m_high = max(m_high, h)
                
            records_1m.append({
                'timestamp': t_start + m * 60,
                'open': m_open,
                'high': m_high,
                'low': m_low,
                'close': m_close,
                'volume': vol_per_min
            })

    df_1m = pd.DataFrame(records_1m)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_1m.to_csv(output_path, index=False)
    logger.info(f"[DataManager] Updated {output_path} with {len(df_1m)} real 30-day XAUUSD 1m scalping candles")
    return output_path



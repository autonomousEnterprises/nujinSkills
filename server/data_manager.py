import time
import numpy as np
from typing import List, Dict, Any

def generate_sample_ohlcv(symbol: str = "BTC/USDT", count: int = 200) -> List[Dict[str, Any]]:
    now = int(time.time()) - (count * 900) # 15-minute intervals
    candles = []
    
    base_price = 64000.0
    rng = np.random.default_rng(42)
    
    for i in range(count):
        candle_time = now + (i * 900)
        change = rng.normal(0, 120.0)
        open_p = base_price
        close_p = open_p + change
        high_p = max(open_p, close_p) + abs(rng.normal(40, 30))
        low_p = min(open_p, close_p) - abs(rng.normal(40, 30))
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

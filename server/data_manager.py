import os
import json
import time
import logging
import urllib.request
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

import pandas as pd
import numpy as np

logger = logging.getLogger("DataManager")

# Institutional TradingView WebSocket Client
try:
    from tradingview_websocket import TradingViewWebSocket
    HAS_TV_WS = True
except ImportError:
    HAS_TV_WS = False
    logger.warning("[DataManager] tradingview_websocket library not installed. Falling back to REST.")


def resolve_market_symbol(symbol: str) -> str:
    """Maps user symbol to institutional exchange symbol."""
    upper = (symbol or "").replace("/", "").replace("-", "").replace(":", "").replace(" ", "").replace("&", "").upper()
    if upper in ("XAUUSD", "GOLD", "XAU", "OANDA", "XAU_USD", "OANDAXAUUSD", "GC=F", "GC"):
        return "OANDA:XAUUSD"
    if any(k in upper for k in ["SP500", "SPX", "ES", "US500", "SPY", "ES1"]):
        return "CME_MINI:ES1!"
    if "BTC" in upper:
        return "BINANCE:BTCUSDT"
    if "ETH" in upper:
        return "BINANCE:ETHUSDT"
    if "SOL" in upper:
        return "BINANCE:SOLUSDT"
    return upper


def get_oanda_spot_quote() -> Dict[str, Any]:
    """
    Fetches real-time OANDA cash spot Gold (XAUUSD) quote via TradingView CFD feed.
    Sub-100ms keyless institutional quote matching MetaTrader / cTrader prop firm charts.
    """
    url = "https://scanner.tradingview.com/cfd/scan"
    payload = json.dumps({
        "symbols": {"tickers": ["OANDA:XAUUSD"]},
        "columns": ["close", "open", "high", "low", "bid", "ask", "change", "volume"]
    }).encode("utf-8")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Origin": "https://www.tradingview.com",
        "Referer": "https://www.tradingview.com/"
    }
    req = urllib.request.Request(url, data=payload, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            d = json.loads(r.read().decode("utf-8"))
            row = d["data"][0]["d"]
            close_p = round(float(row[0]), 2)
            bid_p = round(float(row[4] or close_p - 0.15), 2)
            ask_p = round(float(row[5] or close_p + 0.15), 2)
            return {
                "symbol": "XAU/USD (OANDA Spot)",
                "price": close_p,
                "open": round(float(row[1]), 2),
                "high": round(float(row[2]), 2),
                "low": round(float(row[3]), 2),
                "bid": bid_p,
                "ask": ask_p,
                "change_pct": round(float(row[6] or 0.0), 2),
                "volume": round(float(row[7] or 100.0), 1),
                "timestamp": int(time.time()),
                "source": "oanda_spot"
            }
    except Exception as e:
        logger.warning(f"[DataManager] Error fetching live OANDA quote: {e}")
        fallback_p = 4335.00
        csv_path = "data/xauusd_candles_1m.csv"
        if os.path.exists(csv_path):
            try:
                with open(csv_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    if len(lines) >= 2:
                        last_row = lines[-1].strip().split(",")
                        fallback_p = round(float(last_row[4]), 2)
            except Exception:
                pass
        return {
            "symbol": "XAU/USD (OANDA Spot)",
            "price": fallback_p,
            "bid": round(fallback_p - 0.15, 2),
            "ask": round(fallback_p + 0.15, 2),
            "change_pct": 0.0,
            "volume": 50.0,
            "timestamp": int(time.time()),
            "source": "oanda_spot_fallback"
        }


def _tf_to_tv_resolution(timeframe: str) -> str:
    """Converts timeframe string (1m, 5m, 15m, 1h, 1d) to TradingView resolution code."""
    tf = (timeframe or "1m").lower().strip()
    if tf in ("1", "1m"):
        return "1"
    elif tf in ("3", "3m"):
        return "3"
    elif tf in ("5", "5m"):
        return "5"
    elif tf in ("15", "15m"):
        return "15"
    elif tf in ("30", "30m"):
        return "30"
    elif tf in ("60", "1h", "60m"):
        return "60"
    elif tf in ("240", "4h"):
        return "240"
    elif tf in ("d", "1d", "daily"):
        return "1D"
    return "15"


def _timeframe_to_seconds(timeframe: str) -> int:
    tf = (timeframe or "1m").lower().strip()
    if tf == "1m":
        return 60
    elif tf == "3m":
        return 180
    elif tf == "5m":
        return 300
    elif tf == "15m":
        return 900
    elif tf == "30m":
        return 1800
    elif tf in ("1h", "60m"):
        return 3600
    elif tf == "4h":
        return 14400
    elif tf in ("1d", "d"):
        return 86400
    return 900


def resample_candles(candles: List[Dict[str, Any]], target_timeframe: str) -> List[Dict[str, Any]]:
    """
    Vectorized, deterministic candlestick resampling from base bars (e.g. 1m)
    to any higher timeframe (3m, 5m, 15m, 1h, 4h, 1d).
    Strictly aligns candle time boundaries to epoch modulo: (t // step_sec) * step_sec.
    Zero lookahead bias and zero synthetic noise.
    """
    if not candles:
        return []

    step_sec = _timeframe_to_seconds(target_timeframe)
    if step_sec <= 60:
        return candles

    buckets: Dict[int, Dict[str, Any]] = {}
    for c in candles:
        raw_t = int(c.get("timestamp") or c.get("time") or 0)
        if raw_t <= 0:
            continue
        bucket_t = (raw_t // step_sec) * step_sec
        o = round(float(c["open"]), 2)
        h = round(float(c["high"]), 2)
        l = round(float(c["low"]), 2)
        cl = round(float(c["close"]), 2)
        v = round(float(c.get("volume", 0.0)), 2)

        if bucket_t not in buckets:
            buckets[bucket_t] = {
                "time": bucket_t,
                "timestamp": bucket_t,
                "open": o,
                "high": h,
                "low": l,
                "close": cl,
                "volume": v
            }
        else:
            b = buckets[bucket_t]
            b["high"] = max(b["high"], h)
            b["low"] = min(b["low"], l)
            b["close"] = cl
            b["volume"] = round(b["volume"] + v, 2)

    return list(buckets.values())


def fetch_candles_via_tv(symbol: str, timeframe: str = "1m", count: int = 2000) -> List[Dict[str, Any]]:
    """
    Pulls authentic institutional historical bars using TradingViewWebSocket.
    Supported symbols: 'OANDA:XAUUSD', 'CME_MINI:ES1!', 'BINANCE:BTCUSDT'.
    """
    if not HAS_TV_WS:
        return []

    tv_sym = resolve_market_symbol(symbol)
    tv_tf = _tf_to_tv_resolution(timeframe)
    logger.info(f"[DataManager] Fetching {count} bars for {tv_sym} ({timeframe} -> {tv_tf}) via TradingView WebSocket...")

    try:
        ws = TradingViewWebSocket(tv_sym, tv_tf, count)
        ws.connect()
        ws.run()
        raw_bars = ws.result_data
        if not raw_bars:
            logger.warning(f"[DataManager] No bars returned from TradingView WS for {tv_sym}")
            return []

        candles = []
        for b in raw_bars:
            v = b.get("v", [])
            if len(v) >= 5:
                candles.append({
                    "time": int(v[0]),
                    "timestamp": int(v[0]),
                    "open": round(float(v[1]), 2),
                    "high": round(float(v[2]), 2),
                    "low": round(float(v[3]), 2),
                    "close": round(float(v[4]), 2),
                    "volume": round(float(v[5] or 10.0), 2)
                })

        logger.info(f"[DataManager] Successfully received {len(candles)} authentic bars for {tv_sym}")
        return candles
    except Exception as e:
        logger.warning(f"[DataManager] TradingView WS fetch error for {tv_sym}: {e}")
        return []


def fetch_real_oanda_candles(interval: str = "1m", count: int = 2880, force_refresh: bool = False) -> List[Dict[str, Any]]:
    """
    Fetches genuine OANDA:XAUUSD spot candles.
    Reads persistent clean CSV cache from disk, or refreshes from TradingView WebSocket.
    Resamples cleanly to 5m, 15m, 1h as needed.
    """
    csv_path = "data/xauusd_candles_1m.csv"
    csv_5m_path = "data/xauusd_candles_5m.csv"
    now_ts = int(time.time())

    # 1. Check if cached CSV exists and is fresh (within 120 seconds)
    if not force_refresh and os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path)
            time_col = "timestamp" if "timestamp" in df.columns else "time"
            df = df.dropna(subset=[time_col, "close"]).reset_index(drop=True)
            if len(df) >= 100:
                last_ts = int(df.iloc[-1][time_col])
                if (now_ts - last_ts) <= 120:
                    # Maintain mirror-perfect 5m resampled cache from the full 1m history
                    try:
                        if not os.path.exists(csv_5m_path) or (os.path.getmtime(csv_path) > os.path.getmtime(csv_5m_path)):
                            full_records = df.to_dict(orient="records")
                            full_bars = [
                                {
                                    "time": int(r.get("timestamp", r.get("time", 0))),
                                    "timestamp": int(r.get("timestamp", r.get("time", 0))),
                                    "open": round(float(r["open"]), 2),
                                    "high": round(float(r["high"]), 2),
                                    "low": round(float(r["low"]), 2),
                                    "close": round(float(r["close"]), 2),
                                    "volume": round(float(r.get("volume", 10.0)), 2)
                                }
                                for r in full_records
                            ]
                            resampled_full_5m = resample_candles(full_bars, "5m")
                            if resampled_full_5m and len(resampled_full_5m) > 50:
                                pd.DataFrame(resampled_full_5m).to_csv(csv_5m_path, index=False)
                    except Exception as e_full_5m:
                        logger.warning(f"[DataManager] Could not sync 5m resampled cache: {e_full_5m}")

                    records = df.tail(count * 5).to_dict(orient="records") if (count and count > 0) else df.to_dict(orient="records")
                    candles_1m = [
                        {
                            "time": int(r.get("timestamp", r.get("time", 0))),
                            "timestamp": int(r.get("timestamp", r.get("time", 0))),
                            "open": round(float(r["open"]), 2),
                            "high": round(float(r["high"]), 2),
                            "low": round(float(r["low"]), 2),
                            "close": round(float(r["close"]), 2),
                            "volume": round(float(r.get("volume", 10.0)), 2)
                        }
                        for r in records
                    ]
                    if interval == "1m":
                        return candles_1m[-count:] if count else candles_1m
                    else:
                        resampled = resample_candles(candles_1m, interval)
                        return resampled[-count:] if count else resampled
        except Exception as e:
            logger.warning(f"[DataManager] Error reading cached OANDA 1m CSV: {e}")

    # 2. Fetch fresh authentic bars via TradingView WebSocket or Yahoo COMEX Fallback
    fresh = fetch_candles_via_tv("OANDA:XAUUSD", "1m", max(count or 2880, 5000))
    if not fresh or len(fresh) < 50:
        logger.info("[DataManager] TV WS yielded insufficient bars; attempting Yahoo COMEX Gold fallback...")
        fresh = fetch_real_comex_gold_candles(interval="1m", count=max(count or 2880, 5000))

    if fresh and len(fresh) >= 50:
        try:
            df_fresh = pd.DataFrame(fresh)
            if "time" in df_fresh.columns and "timestamp" not in df_fresh.columns:
                df_fresh.rename(columns={"time": "timestamp"}, inplace=True)
            if os.path.exists(csv_path) and os.path.getsize(csv_path) > 10:
                try:
                    df_old = pd.read_csv(csv_path)
                    clean_old = df_old[df_old.get("volume", 10.0) > 1.5] if "volume" in df_old.columns else df_old
                    df_merged = pd.concat([clean_old, df_fresh], ignore_index=True)
                except Exception:
                    df_merged = df_fresh
                df_merged.drop_duplicates(subset=["timestamp"], keep="last", inplace=True)
                df_merged.sort_values(by="timestamp", inplace=True)
                df_merged.to_csv(csv_path, index=False)
            else:
                os.makedirs(os.path.dirname(csv_path), exist_ok=True)
                df_fresh.to_csv(csv_path, index=False)
                df_merged = df_fresh

            df_to_return = df_merged if ('df_merged' in locals() and not df_merged.empty) else df_fresh
            records = df_to_return.tail(count * 5).to_dict(orient="records") if (count and count * 5 < len(df_to_return)) else df_to_return.to_dict(orient="records")
            all_bars = [
                {
                    "time": int(r.get("timestamp", r.get("time", 0))),
                    "timestamp": int(r.get("timestamp", r.get("time", 0))),
                    "open": round(float(r["open"]), 2),
                    "high": round(float(r["high"]), 2),
                    "low": round(float(r["low"]), 2),
                    "close": round(float(r["close"]), 2),
                    "volume": round(float(r.get("volume", 10.0)), 2)
                }
                for r in records
            ]

            # Also update 5m resampled cache file so both timeframes are always mirror-perfect
            try:
                full_records = df_to_return.to_dict(orient="records")
                full_bars = [
                    {
                        "time": int(r.get("timestamp", r.get("time", 0))),
                        "timestamp": int(r.get("timestamp", r.get("time", 0))),
                        "open": round(float(r["open"]), 2),
                        "high": round(float(r["high"]), 2),
                        "low": round(float(r["low"]), 2),
                        "close": round(float(r["close"]), 2),
                        "volume": round(float(r.get("volume", 10.0)), 2)
                    }
                    for r in full_records
                ]
                resampled_5m = resample_candles(full_bars, "5m")
                if resampled_5m:
                    df_5m = pd.DataFrame(resampled_5m)
                    df_5m.to_csv(csv_5m_path, index=False)
            except Exception as e_5m:
                logger.warning(f"[DataManager] Could not save resampled 5m cache: {e_5m}")

            if interval == "1m":
                return all_bars[-count:] if count else all_bars
            else:
                resampled = resample_candles(all_bars, interval)
                return resampled[-count:] if count else resampled
        except Exception as e_save:
            logger.warning(f"[DataManager] Error saving fresh OANDA 1m cache: {e_save}")
            if interval == "1m":
                return fresh[-count:] if count else fresh
            else:
                return resample_candles(fresh, interval)[-count:]

    # 3. Fallback to existing disk CSV
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        time_col = "timestamp" if "timestamp" in df.columns else "time"
        records = df.tail(count * 5).to_dict(orient="records") if (count and count > 0) else df.to_dict(orient="records")
        candles = [
            {
                "time": int(r.get("timestamp", r.get("time", 0))),
                "timestamp": int(r.get("timestamp", r.get("time", 0))),
                "open": round(float(r["open"]), 2),
                "high": round(float(r["high"]), 2),
                "low": round(float(r["low"]), 2),
                "close": round(float(r["close"]), 2),
                "volume": round(float(r.get("volume", 10.0)), 2)
            }
            for r in records
        ]
        if interval == "1m":
            return candles[-count:] if count else candles
        return resample_candles(candles, interval)[-count:]

    # 4. Fallback to COMEX Gold GC=F via Yahoo Finance directly
    return fetch_real_comex_gold_candles(interval=interval, count=count)


def fetch_real_comex_gold_candles(interval: str = "1m", count: int = 2880) -> List[Dict[str, Any]]:
    """
    Fetches real institutional Gold OHLCV candles from CME / COMEX Gold Futures (GC=F).
    """
    logger.info(f"[DataManager] Fetching CME COMEX Gold (GC=F) candles ({interval})...")
    yf_interval = "1m" if interval == "1m" else ("5m" if interval == "5m" else "15m")
    yf_range = "7d" if yf_interval == "1m" else "1mo"
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/GC=F?interval={yf_interval}&range={yf_range}"

    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        res = data["chart"]["result"][0]
        timestamps = res["timestamp"]
        quote = res["indicators"]["quote"][0]
        candles = []
        for i in range(len(timestamps)):
            if quote["open"][i] is not None and quote["close"][i] is not None:
                candles.append({
                    "time": int(timestamps[i]),
                    "timestamp": int(timestamps[i]),
                    "open": round(float(quote["open"][i]), 2),
                    "high": round(float(quote["high"][i]), 2),
                    "low": round(float(quote["low"][i]), 2),
                    "close": round(float(quote["close"][i]), 2),
                    "volume": round(float(quote["volume"][i] or 10.0), 2)
                })
        return candles[-count:] if count else candles
    except Exception as e:
        logger.warning(f"[DataManager] Yahoo COMEX Gold fetch error: {e}")
        return []


def fetch_real_sp500_candles(interval: str = "1m", count: int = 2880) -> List[Dict[str, Any]]:
    """
    Fetches genuine S&P 500 E-mini futures (ES) candles.
    Reads clean CSV cache or pulls from TradingView WS (CME_MINI:ES1!).
    """
    csv_path = "data/sp500_candles_1m.csv"
    now_ts = int(time.time())

    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path)
            time_col = "timestamp" if "timestamp" in df.columns else "time"
            if len(df) >= 100:
                last_ts = int(df.iloc[-1][time_col])
                if (now_ts - last_ts) <= 120:
                    records = df.tail(count).to_dict(orient="records")
                    return [
                        {
                            "time": int(r.get("timestamp", r.get("time", 0))),
                            "timestamp": int(r.get("timestamp", r.get("time", 0))),
                            "open": round(float(r["open"]), 2),
                            "high": round(float(r["high"]), 2),
                            "low": round(float(r["low"]), 2),
                            "close": round(float(r["close"]), 2),
                            "volume": round(float(r.get("volume", 50.0)), 2)
                        }
                        for r in records
                    ]
        except Exception:
            pass

    # Fetch from TradingView WS
    fresh = fetch_candles_via_tv("CME_MINI:ES1!", interval, count)
    if fresh:
        try:
            df_fresh = pd.DataFrame(fresh)
            if "time" in df_fresh.columns and "timestamp" not in df_fresh.columns:
                df_fresh.rename(columns={"time": "timestamp"}, inplace=True)
            if os.path.exists(csv_path):
                df_old = pd.read_csv(csv_path)
                df_merged = pd.concat([df_old, df_fresh], ignore_index=True)
                df_merged.drop_duplicates(subset=["timestamp"], keep="last", inplace=True)
                df_merged.sort_values(by="timestamp", inplace=True)
                df_merged.to_csv(csv_path, index=False)
            else:
                os.makedirs(os.path.dirname(csv_path), exist_ok=True)
                df_fresh.to_csv(csv_path, index=False)
                df_merged = df_fresh
            df_to_return = df_merged if ('df_merged' in locals() and not df_merged.empty) else df_fresh
            records = df_to_return.tail(count).to_dict(orient="records") if (count and count < len(df_to_return)) else df_to_return.to_dict(orient="records")
            return [
                {
                    "time": int(r.get("timestamp", r.get("time", 0))),
                    "timestamp": int(r.get("timestamp", r.get("time", 0))),
                    "open": round(float(r["open"]), 2),
                    "high": round(float(r["high"]), 2),
                    "low": round(float(r["low"]), 2),
                    "close": round(float(r["close"]), 2),
                    "volume": round(float(r.get("volume", 50.0)), 2)
                }
                for r in records
            ]
        except Exception:
            return fresh[-count:] if count else fresh

    # Fallback to existing disk CSV
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        records = df.tail(count).to_dict(orient="records")
        return [
            {
                "time": int(r.get("timestamp", r.get("time", 0))),
                "timestamp": int(r.get("timestamp", r.get("time", 0))),
                "open": round(float(r["open"]), 2),
                "high": round(float(r["high"]), 2),
                "low": round(float(r["low"]), 2),
                "close": round(float(r["close"]), 2),
                "volume": round(float(r.get("volume", 50.0)), 2)
            }
            for r in records
        ]
    return []


def fetch_real_binance_klines(symbol: str = "BTC/USDT", interval: str = "15m", count: int = 2880) -> List[Dict[str, Any]]:
    """
    Fetches real OHLCV candles for any symbol.
    Seamlessly routes Gold to OANDA:XAUUSD and S&P 500 to CME_MINI:ES1!.
    """
    clean_sym = resolve_market_symbol(symbol)
    if clean_sym == "OANDA:XAUUSD":
        return fetch_real_oanda_candles(interval=interval, count=count)
    elif clean_sym == "CME_MINI:ES1!":
        return fetch_real_sp500_candles(interval=interval, count=count)

    # 1. Check local disk CSV if available
    csv_path = "data/candles_15m.csv" if interval == "15m" else f"data/btc_candles_{interval}.csv"
    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path)
            time_col = "timestamp" if "timestamp" in df.columns else "time"
            now_ts = int(time.time())
            if len(df) >= 100 and (now_ts - int(df.iloc[-1][time_col])) <= 300:
                records = df.tail(count).to_dict(orient="records")
                return [
                    {
                        "time": int(r.get("timestamp", r.get("time", 0))),
                        "timestamp": int(r.get("timestamp", r.get("time", 0))),
                        "open": round(float(r["open"]), 2),
                        "high": round(float(r["high"]), 2),
                        "low": round(float(r["low"]), 2),
                        "close": round(float(r["close"]), 2),
                        "volume": round(float(r.get("volume", 10.0)), 4)
                    }
                    for r in records
                ]
        except Exception:
            pass

    # 2. Pull from TradingView WS
    fresh = fetch_candles_via_tv(clean_sym, interval, count)
    if fresh:
        try:
            df_fresh = pd.DataFrame(fresh)
            if "time" in df_fresh.columns and "timestamp" not in df_fresh.columns:
                df_fresh.rename(columns={"time": "timestamp"}, inplace=True)
            if os.path.exists(csv_path):
                df_old = pd.read_csv(csv_path)
                df_merged = pd.concat([df_old, df_fresh], ignore_index=True)
                df_merged.drop_duplicates(subset=["timestamp"], keep="last", inplace=True)
                df_merged.sort_values(by="timestamp", inplace=True)
                df_merged.to_csv(csv_path, index=False)
            else:
                os.makedirs(os.path.dirname(csv_path), exist_ok=True)
                df_fresh.to_csv(csv_path, index=False)
        except Exception:
            pass
        return fresh[-count:] if count else fresh

    # 3. Direct Binance REST API fallback
    pair = clean_sym.replace("BINANCE:", "").upper()
    url = f"https://api.binance.com/api/v3/klines?symbol={pair}&interval={interval}&limit={min(1000, count)}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
            candles = [
                {
                    "time": int(item[0] // 1000),
                    "timestamp": int(item[0] // 1000),
                    "open": round(float(item[1]), 2),
                    "high": round(float(item[2]), 2),
                    "low": round(float(item[3]), 2),
                    "close": round(float(item[4]), 2),
                    "volume": round(float(item[5]), 4)
                }
                for item in raw
            ]
            return candles
    except Exception as e:
        logger.warning(f"[DataManager] Binance REST fallback error for {pair}: {e}")

    # Fallback to cached CSV
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        records = df.tail(count).to_dict(orient="records")
        return [
            {
                "time": int(r.get("timestamp", r.get("time", 0))),
                "timestamp": int(r.get("timestamp", r.get("time", 0))),
                "open": round(float(r["open"]), 2),
                "high": round(float(r["high"]), 2),
                "low": round(float(r["low"]), 2),
                "close": round(float(r["close"]), 2),
                "volume": round(float(r.get("volume", 10.0)), 4)
            }
            for r in records
        ]
    return []


def sync_30d_candles(symbol: str = "BTC/USDT", output_path: str = "data/candles_15m.csv") -> str:
    """Synchronizes real market data (10,000+ candles) and updates output_path CSV."""
    candles = fetch_candles_via_tv(resolve_market_symbol(symbol), "15m", 10000)
    if not candles:
        candles = fetch_real_binance_klines(symbol=symbol, interval="15m", count=5000)
    if candles:
        df = pd.DataFrame(candles)
        if "time" in df.columns and "timestamp" not in df.columns:
            df.rename(columns={"time": "timestamp"}, inplace=True)
        if os.path.exists(output_path):
            try:
                old_df = pd.read_csv(output_path)
                df = pd.concat([old_df, df]).drop_duplicates(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
            except Exception:
                pass
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)
        logger.info(f"[DataManager] Synchronized {output_path} with {len(df)} authentic candles")
    return output_path


def sync_xauusd_scalp_candles(output_path: str = "data/xauusd_candles_1m.csv") -> str:
    """Synchronizes real institutional OANDA Cash Spot Gold (XAUUSD) 1m scalping dataset."""
    candles = fetch_candles_via_tv("OANDA:XAUUSD", "1m", 10000)
    if candles:
        df = pd.DataFrame(candles)
        if "time" in df.columns and "timestamp" not in df.columns:
            df.rename(columns={"time": "timestamp"}, inplace=True)
        if os.path.exists(output_path):
            try:
                old_df = pd.read_csv(output_path)
                clean_old = old_df[old_df.get("volume", 10.0) > 1.5]
                df = pd.concat([clean_old, df]).drop_duplicates(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
            except Exception:
                pass
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)
        logger.info(f"[DataManager] Synchronized {output_path} with {len(df)} authentic 1m OANDA Gold candles")
    return output_path

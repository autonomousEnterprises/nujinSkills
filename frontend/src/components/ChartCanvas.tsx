import React, { useEffect, useRef, useState, useMemo } from 'react';
import { createChart, ColorType, IChartApi, ISeriesApi, SeriesMarker, Time } from 'lightweight-charts';
import { SignalData } from '../hooks/useWebSocket';
import { Layers, Activity, BarChart2, TrendingUp } from 'lucide-react';

interface TradeDetail {
  id: number;
  entry_time: number;
  entry_price: number;
  stop_loss: number;
  take_profit: number;
  exit_time: number;
  exit_price: number;
  exit_reason: string;
  pnl_pct: number;
}

interface PositionBoxCoord {
  id: number | string;
  x: number;
  width: number;
  yEntry: number;
  yProfitTop: number;
  profitHeight: number;
  yLossTop: number;
  lossHeight: number;
  tpPrice: number;
  slPrice: number;
  entryPrice: number;
  pnlPct: number;
  isLong: boolean;
}

interface LegendValues {
  time?: number;
  open?: number;
  high?: number;
  low?: number;
  close?: number;
  changePct?: number;
  ema9?: number;
  ema21?: number;
  ema200?: number;
  hh15?: number;
  ll15?: number;
  volume?: number;
}

export interface InspectableSignal {
  id: string | number;
  source: 'BACKTEST' | 'LIVE';
  side: string;
  entry_time: number;
  entry_price: number;
  exit_time?: number;
  exit_price?: number;
  exit_reason?: string;
  pnl_pct?: number;
  stop_loss: number;
  take_profit: number;
  isLiveActive?: boolean;
}

interface ChartCanvasProps {
  latestSignal: SignalData | null;
  signals?: SignalData[];
  theme?: 'dark' | 'light';
  selectedStrategy?: string;
  tradeMarkers?: any[];
  tradesDetail?: TradeDetail[];
  activeStrategy?: string;
}

// ── Quantitative Indicator Calculation Utilities ──
function calculateEMA(data: { time: Time; close: number }[], period: number) {
  if (!data || data.length === 0) return [];
  const k = 2 / (period + 1);
  const result: { time: Time; value: number }[] = [];
  let ema = data[0].close;

  for (let i = 0; i < data.length; i++) {
    const close = data[i].close;
    if (i === 0) {
      ema = close;
    } else {
      ema = close * k + ema * (1 - k);
    }
    result.push({
      time: data[i].time,
      value: Number(ema.toFixed(2)),
    });
  }
  return result;
}

function calculateHHLL(data: { time: Time; high: number; low: number }[], period: number = 15) {
  if (!data || data.length === 0) return { hh: [], ll: [] };
  const hh: { time: Time; value: number }[] = [];
  const ll: { time: Time; value: number }[] = [];

  for (let i = 0; i < data.length; i++) {
    if (i < 1) continue;
    const start = Math.max(0, i - period);
    const end = i; // shift(1) - prior 15 bars only
    let maxH = -Infinity;
    let minL = Infinity;
    for (let j = start; j < end; j++) {
      if (data[j].high > maxH) maxH = data[j].high;
      if (data[j].low < minL) minL = data[j].low;
    }
    hh.push({ time: data[i].time, value: Number(maxH.toFixed(2)) });
    ll.push({ time: data[i].time, value: Number(minL.toFixed(2)) });
  }
  return { hh, ll };
}

function calculateVolumeSeries(data: { time: Time; open: number; close: number; volume?: number }[]) {
  if (!data || data.length === 0) return [];
  const volWindow = 20;

  return data.map((c, i) => {
    const v = c.volume || 10;
    const isUp = c.close >= c.open;

    // Rolling volume Z-Score surge calculation
    let isSurge = false;
    if (i >= volWindow) {
      let sum = 0;
      for (let j = i - volWindow; j < i; j++) {
        sum += data[j].volume || 10;
      }
      const mean = sum / volWindow;
      let sumSq = 0;
      for (let j = i - volWindow; j < i; j++) {
        const diff = (data[j].volume || 10) - mean;
        sumSq += diff * diff;
      }
      const std = Math.sqrt(sumSq / volWindow) || 1e-6;
      const z = (v - mean) / std;
      if (z > 0.4) isSurge = true;
    }

    let barColor = isUp ? 'rgba(38, 166, 154, 0.45)' : 'rgba(239, 83, 80, 0.45)';
    if (isSurge) {
      barColor = isUp ? 'rgba(38, 166, 154, 0.95)' : 'rgba(239, 83, 80, 0.95)';
    }

    return {
      time: c.time,
      value: v,
      color: barColor,
    };
  });
}

export const ChartCanvas: React.FC<ChartCanvasProps> = ({
  latestSignal,
  signals = [],
  theme = 'dark',
  selectedStrategy = 'GoatFundedTraderXauusdScalper.py',
  tradeMarkers = [],
  tradesDetail = [],
  activeStrategy = 'GoatFundedTraderXauusdScalper',
}) => {
  const isDark = theme === 'dark';
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  // Series References
  const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const ema9SeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const ema21SeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const ema200SeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const hh15SeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const ll15SeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<'Histogram'> | null>(null);

  // Strategy & Symbol Setup
  const isXauActive =
    (activeStrategy || selectedStrategy || '').toLowerCase().includes('xau') ||
    (activeStrategy || selectedStrategy || '').toLowerCase().includes('goat');
  const [selectedSymbol, setSelectedSymbol] = useState<string>(isXauActive ? 'XAU/USD' : 'XAU/USD');
  const [isWsConnected, setIsWsConnected] = useState<boolean>(false);
  const [lastLivePrice, setLastLivePrice] = useState<number | null>(null);

  // Indicator Toggles
  const [showRibbon, setShowRibbon] = useState<boolean>(true);
  const [showMacroEma, setShowMacroEma] = useState<boolean>(true);
  const [showRanges, setShowRanges] = useState<boolean>(true);
  const [showVolume, setShowVolume] = useState<boolean>(true);
  const [showPositionBox, setShowPositionBox] = useState<boolean>(true);

  // Crosshair Hover / Latest Candle Legend Readout
  const [hoverLegend, setHoverLegend] = useState<LegendValues | null>(null);

  // Sync symbol if active strategy changes
  useEffect(() => {
    const isGold =
      (activeStrategy || selectedStrategy || '').toLowerCase().includes('xau') ||
      (activeStrategy || selectedStrategy || '').toLowerCase().includes('goat');
    setSelectedSymbol(isGold ? 'XAU/USD' : 'BTC/USDT');
  }, [activeStrategy, selectedStrategy]);

  const [candles, setCandles] = useState<any[]>([]);
  const activeCandleRef = useRef<{ time: Time; open: number; high: number; low: number; close: number; volume: number } | null>(null);
  const [displayMarkers, setDisplayMarkers] = useState<SeriesMarker<Time>[]>([]);
  const [positionBoxes, setPositionBoxes] = useState<PositionBoxCoord[]>([]);
  const [selectedSignalIndex, setSelectedSignalIndex] = useState<number | null>(null);
  const inspectedSignalRef = useRef<InspectableSignal | null>(null);
  const candlesRef = useRef<any[]>([]);
  const showPositionBoxRef = useRef<boolean>(true);
  const updateBoxCoordinatesRef = useRef<() => void>(() => {});
  const initialCenteredRef = useRef<boolean>(false);
  const priceLinesRef = useRef<any[]>([]);

  // Compute indicator series datasets
  const ema9Data = useMemo(() => calculateEMA(candles, 9), [candles]);
  const ema21Data = useMemo(() => calculateEMA(candles, 21), [candles]);
  const ema200Data = useMemo(() => calculateEMA(candles, Math.min(200, candles.length || 200)), [candles]);
  const { hh: hh15Data, ll: ll15Data } = useMemo(() => calculateHHLL(candles, 15), [candles]);
  const volumeData = useMemo(() => calculateVolumeSeries(candles), [candles]);

  // Latest candle fallback for legend when not hovering
  const latestCandleLegend: LegendValues = useMemo(() => {
    if (!candles || candles.length === 0) return {};
    const last = candles[candles.length - 1];
    const chg = last.open ? ((last.close - last.open) / last.open) * 100 : 0;
    const lastE9 = ema9Data[ema9Data.length - 1]?.value;
    const lastE21 = ema21Data[ema21Data.length - 1]?.value;
    const lastE200 = ema200Data[ema200Data.length - 1]?.value;
    const lastHh = hh15Data[hh15Data.length - 1]?.value;
    const lastLl = ll15Data[ll15Data.length - 1]?.value;
    const lastVol = volumeData[volumeData.length - 1]?.value;

    return {
      time: Number(last.time),
      open: last.open,
      high: last.high,
      low: last.low,
      close: last.close,
      changePct: chg,
      ema9: lastE9,
      ema21: lastE21,
      ema200: lastE200,
      hh15: lastHh,
      ll15: lastLl,
      volume: lastVol,
    };
  }, [candles, ema9Data, ema21Data, ema200Data, hh15Data, ll15Data, volumeData]);

  const activeLegend = hoverLegend || latestCandleLegend;

  // 1. Fetch Initial Candles
  const fetchCandles = () => {
    const isGold = selectedSymbol.toLowerCase().includes('xau') || selectedSymbol.toLowerCase().includes('gold');
    const apiSym = isGold ? 'XAUUSD' : selectedSymbol;
    const url = `/api/candles?symbol=${encodeURIComponent(apiSym)}&count=8000&mode=live`;
    fetch(url)
      .then((res) => res.json())
      .then((data) => {
        if (data.data && data.data.length > 0) {
          setCandles(data.data);
          const lastC = data.data[data.data.length - 1];
          if (lastC) {
            setLastLivePrice(lastC.close);
            activeCandleRef.current = {
              time: lastC.time,
              open: lastC.open,
              high: lastC.high,
              low: lastC.low,
              close: lastC.close,
              volume: lastC.volume || 10.0,
            };
          }
        }
      })
      .catch((err) => console.log('Failed to fetch candles:', err));
  };

  useEffect(() => {
    fetchCandles();
  }, [selectedSymbol]);

  // 2. Real-time Live Price Feed
  useEffect(() => {
    const isGold = selectedSymbol.toLowerCase().includes('xau') || selectedSymbol.toLowerCase().includes('gold') || selectedSymbol.toLowerCase().includes('gc');

    if (isGold) {
      setIsWsConnected(true);
      const pollOandaGold = async () => {
        try {
          const res = await fetch('/api/xauusd/quote');
          const data = await res.json();
          if (data?.quote?.price) {
            const p = parseFloat(data.quote.price);
            if (isNaN(p) || p <= 0) return;

            // Reject anomalous spikes (> $15 deviation from last active candle close)
            if (activeCandleRef.current && Math.abs(p - activeCandleRef.current.close) > 15.0) {
              console.warn('[ChartCanvas] Outlier price quote rejected:', p, 'vs last close:', activeCandleRef.current.close);
              return;
            }

            setLastLivePrice(p);

            if (data.quote.candle && data.quote.candle.time) {
              const c = data.quote.candle;
              const liveCandle = {
                time: Number(c.time) as Time,
                open: Number(c.open),
                high: Number(c.high),
                low: Number(c.low),
                close: Number(c.close),
                volume: Number(c.volume || 10.0),
              };

              if (activeCandleRef.current && Number(c.time) - (activeCandleRef.current.time as number) > 120) {
                fetchCandles();
                return;
              }

              activeCandleRef.current = liveCandle;
              if (candleSeriesRef.current) {
                candleSeriesRef.current.update(liveCandle);
              }
              return;
            }

            const rawTs = data.quote.timestamp ? parseInt(data.quote.timestamp) : Math.floor(Date.now() / 1000);
            const minuteTime = (Math.floor(rawTs / 60) * 60) as Time;

            if (candleSeriesRef.current) {
              let cur = activeCandleRef.current;
              if (!cur || (cur.time as number) < (minuteTime as number)) {
                if (cur && (minuteTime as number) - (cur.time as number) > 120) {
                  fetchCandles();
                  return;
                }
                const openPrice = cur ? cur.close : p;
                cur = {
                  time: minuteTime,
                  open: openPrice,
                  high: Math.max(openPrice, p),
                  low: Math.min(openPrice, p),
                  close: p,
                  volume: data.quote.volume_1m || 10.0,
                };
              } else {
                cur = {
                  ...cur,
                  time: cur.time,
                  high: Math.max(cur.high, p),
                  low: Math.min(cur.low, p),
                  close: p,
                };
              }
              activeCandleRef.current = cur;
              candleSeriesRef.current.update(cur);
            }
          }
        } catch (e) {
          console.error('Error polling OANDA Spot Gold quote:', e);
        }
      };

      pollOandaGold();
      const intv = setInterval(pollOandaGold, 2000);
      return () => clearInterval(intv);
    }

    const cleanSym = selectedSymbol.replace('/', '').toLowerCase();
    const interval = '15m';
    const wsUrl = `wss://stream.binance.com:9443/ws/${cleanSym}@kline_${interval}`;
    let ws: WebSocket | null = null;

    try {
      ws = new WebSocket(wsUrl);
      ws.onopen = () => setIsWsConnected(true);
      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.e === 'kline') {
            const k = msg.k;
            const updatedCandle = {
              time: Math.floor(k.t / 1000) as Time,
              open: parseFloat(k.o),
              high: parseFloat(k.h),
              low: parseFloat(k.l),
              close: parseFloat(k.c),
              volume: parseFloat(k.v),
            };
            setLastLivePrice(updatedCandle.close);
            if (candleSeriesRef.current) {
              candleSeriesRef.current.update(updatedCandle);
            }
          }
        } catch (e) {
          console.error('Error parsing WS kline:', e);
        }
      };
      ws.onerror = () => setIsWsConnected(false);
      ws.onclose = () => setIsWsConnected(false);
    } catch (e) {
      setIsWsConnected(false);
    }

    return () => {
      if (ws) ws.close();
    };
  }, [selectedSymbol]);

  // ── Unified Inspectable Signals (Backtest Trades + Past & Current Live Signals) ──
  const allInspectableSignals: InspectableSignal[] = useMemo(() => {
    const list: InspectableSignal[] = [];

    // 1. Backtest trades
    if (tradesDetail && tradesDetail.length > 0) {
      for (const t of tradesDetail) {
        list.push({
          id: t.id,
          source: 'BACKTEST',
          side: (t as any).side || 'LONG',
          entry_time: t.entry_time,
          entry_price: t.entry_price,
          exit_time: t.exit_time,
          exit_price: t.exit_price,
          exit_reason: t.exit_reason,
          pnl_pct: t.pnl_pct,
          stop_loss: t.stop_loss,
          take_profit: t.take_profit,
          isLiveActive: t.exit_reason === 'ACTIVE_IN_POSITION' || (t as any).status === 'ACTIVE_IN_POSITION',
        });
      }
    }

    // 2. Past live signals from WebSocket
    if (signals && signals.length > 0) {
      for (let i = 0; i < signals.length; i++) {
        const s = signals[i];
        if (!s.timestamp || (!s.entry_price && !s.price)) continue;
        const entryPrice = Number(s.entry_price || s.price);
        const isBuy = s.action === 'BUY' || s.action === 'LONG';
        const entryTime = Math.floor(s.timestamp / 1000);
        if (list.some((existing) => Math.abs(existing.entry_time - entryTime) < 2)) continue;
        list.push({
          id: `live-${i}`,
          source: 'LIVE',
          side: s.action || 'LONG',
          entry_time: entryTime,
          entry_price: entryPrice,
          exit_time: s.exit_price ? entryTime : undefined,
          exit_price: s.exit_price,
          exit_reason: s.exit_reason,
          pnl_pct: s.pnl_pct || 0,
          stop_loss: s.stop_loss || (isBuy ? entryPrice * 0.9975 : entryPrice * 1.0025),
          take_profit: s.take_profit || (isBuy ? entryPrice * 1.0030 : entryPrice * 0.9970),
          isLiveActive: s.status === 'ACTIVE_IN_POSITION',
        });
      }
    }

    // 3. Latest signal if not already present
    if (latestSignal && (latestSignal.entry_price || latestSignal.price)) {
      const entryPrice = Number(latestSignal.entry_price || latestSignal.price);
      const isBuy = latestSignal.action === 'BUY' || latestSignal.action === 'LONG';
      const entryTime = latestSignal.timestamp
        ? Math.floor(latestSignal.timestamp / 1000)
        : (candles.length > 0 ? (candles[candles.length - 1].time as number) : 0);
      const exists = list.some((existing) => Math.abs(existing.entry_time - entryTime) < 2);
      if (!exists) {
        const isClosed = Boolean(
          latestSignal.exit_price ||
          latestSignal.exit_reason ||
          latestSignal.status === 'COMPLETED' ||
          latestSignal.status === 'CLOSED'
        );
        list.push({
          id: 'live-latest',
          source: 'LIVE',
          side: latestSignal.action || 'LONG',
          entry_time: entryTime,
          entry_price: entryPrice,
          exit_time: latestSignal.exit_price ? entryTime : undefined,
          exit_price: latestSignal.exit_price,
          exit_reason: latestSignal.exit_reason,
          pnl_pct: latestSignal.pnl_pct || 0,
          stop_loss: latestSignal.stop_loss || (isBuy ? entryPrice * 0.9975 : entryPrice * 1.0025),
          take_profit: latestSignal.take_profit || (isBuy ? entryPrice * 1.0030 : entryPrice * 0.9970),
          isLiveActive: !isClosed && latestSignal.status === 'ACTIVE_IN_POSITION',
        });
      }
    }

    list.sort((a, b) => a.entry_time - b.entry_time);
    return list;
  }, [tradesDetail, signals, latestSignal, candles.length]);

  // Sync Default Selected Signal Index to Latest
  useEffect(() => {
    if (allInspectableSignals.length > 0) {
      setSelectedSignalIndex((prev) => {
        if (prev === null || prev < 0 || prev >= allInspectableSignals.length) {
          return allInspectableSignals.length - 1;
        }
        return prev;
      });
    } else {
      setSelectedSignalIndex(null);
    }
  }, [allInspectableSignals.length]);

  const inspectedSignal =
    selectedSignalIndex !== null && selectedSignalIndex >= 0 && selectedSignalIndex < allInspectableSignals.length
      ? allInspectableSignals[selectedSignalIndex]
      : null;

  inspectedSignalRef.current = inspectedSignal;
  candlesRef.current = candles;
  showPositionBoxRef.current = showPositionBox;

  // Center Chart onto Given Signal
  const centerOnTrade = (trade: InspectableSignal) => {
    if (!chartRef.current || !trade || !trade.entry_time) return;
    try {
      inspectedSignalRef.current = trade;
      const t = trade.entry_time;
      const tExit = trade.exit_time || (t + 15 * 60);
      const span = Math.max(tExit - t, 3600);
      chartRef.current.timeScale().setVisibleRange({
        from: (t - span * 3) as Time,
        to: (tExit + span * 3) as Time,
      });
      setTimeout(() => {
        if (updateBoxCoordinatesRef.current) {
          updateBoxCoordinatesRef.current();
        }
      }, 40);
    } catch (e) {}
  };

  // Resolve Active Live Signal (Used EXCLUSIVELY for plotting full-width Entry, SL, TP lines)
  const activeLiveSignal = useMemo(() => {
    if (latestSignal) {
      const isClosed = Boolean(
        latestSignal.exit_price ||
        latestSignal.exit_reason ||
        latestSignal.status === 'COMPLETED' ||
        latestSignal.status === 'CLOSED'
      );
      const entryPrice = Number(latestSignal.entry_price || latestSignal.price || 0);
      if (!isClosed && entryPrice > 0 && latestSignal.status === 'ACTIVE_IN_POSITION') {
        const isBuy = latestSignal.action === 'BUY' || latestSignal.action === 'LONG';
        return {
          entry: entryPrice,
          sl: Number(latestSignal.stop_loss || (isBuy ? entryPrice * 0.9975 : entryPrice * 1.0025)),
          tp: Number(latestSignal.take_profit || (isBuy ? entryPrice * 1.0030 : entryPrice * 0.9970)),
          side: latestSignal.action || (isBuy ? 'LONG' : 'SHORT'),
          isLive: true,
        };
      }
    }

    if (tradesDetail && tradesDetail.length > 0) {
      const openTrade = tradesDetail.find(
        (tr) => tr.exit_reason === 'ACTIVE_IN_POSITION' || (tr as any).status === 'ACTIVE_IN_POSITION'
      );
      if (openTrade && openTrade.entry_price > 0) {
        return {
          entry: openTrade.entry_price,
          sl: openTrade.stop_loss,
          tp: openTrade.take_profit,
          side: (openTrade as any).side || 'LONG',
          isLive: true,
        };
      }
    }

    return null;
  }, [latestSignal, tradesDetail]);

  // Trade Levels of Inspected Signal (for HUD Legend Readout)
  const inspectedTradeLevels = useMemo(() => {
    if (!inspectedSignal) return null;
    const entry = inspectedSignal.entry_price;
    const sl = inspectedSignal.stop_loss;
    const tp = inspectedSignal.take_profit;
    const risk = Math.abs(entry - sl);
    const reward = Math.abs(tp - entry);
    const rr = risk > 0 ? (reward / risk).toFixed(2) : '1.20';
    return {
      entry,
      sl,
      tp,
      rr,
      side: inspectedSignal.side,
      isLive: inspectedSignal.isLiveActive,
    };
  }, [inspectedSignal]);

  // 3. Trade Markers (Backtest + Live)
  useEffect(() => {
    if (candles.length === 0) return;
    const maxTime = candles[candles.length - 1].time as number;
    const candleTimeSet = new Set(candles.map((c) => c.time as number));

    const validMarkers: SeriesMarker<Time>[] = [];
    if (tradeMarkers && tradeMarkers.length > 0) {
      for (const m of tradeMarkers) {
        const t = Number(m.time);
        if (candleTimeSet.has(t)) {
          validMarkers.push({
            time: t as Time,
            position: m.position || 'aboveBar',
            color: m.color || '#38bdf8',
            shape: m.shape || 'arrowUp',
            text: m.text || '',
          });
        }
      }
    }

    if (activeLiveSignal) {
      const isBuy = activeLiveSignal.side === 'BUY' || activeLiveSignal.side === 'LONG';
      validMarkers.push({
        time: maxTime as Time,
        position: isBuy ? 'belowBar' : 'aboveBar',
        color: isBuy ? '#10b981' : '#ef4444',
        shape: isBuy ? 'arrowUp' : 'arrowDown',
        text: `LIVE: ${activeLiveSignal.side} @ $${activeLiveSignal.entry.toFixed(2)}`,
      });
    }

    validMarkers.sort((a, b) => (a.time as number) - (b.time as number));
    setDisplayMarkers(validMarkers);
  }, [selectedStrategy, tradeMarkers, candles, activeLiveSignal]);

  // 4. Precision Clamped Position Box Resolution for Inspected Signal
  const updateBoxCoordinates = () => {
    const target = inspectedSignalRef.current;
    if (
      !showPositionBoxRef.current ||
      !target ||
      !target.entry_price ||
      !chartRef.current ||
      !candleSeriesRef.current ||
      !chartContainerRef.current
    ) {
      setPositionBoxes([]);
      return;
    }

    const currentCandles = candlesRef.current;
    if (!currentCandles || currentCandles.length === 0) {
      setPositionBoxes([]);
      return;
    }

    const chart = chartRef.current;
    const series = candleSeriesRef.current;
    const containerHeight = chartContainerRef.current.clientHeight || 400;
    const containerWidth = chartContainerRef.current.clientWidth || 800;

    // Helper: interpolate Y coordinate even if price is off-screen
    const getYForPrice = (price: number): number => {
      const directY = series.priceToCoordinate(price);
      if (directY !== null && !isNaN(directY)) {
        return directY;
      }
      // If outside visible price scale, extrapolate linearly
      const pTop = series.coordinateToPrice(10);
      const pBottom = series.coordinateToPrice(containerHeight - 10);
      if (pTop !== null && pBottom !== null && pTop !== pBottom) {
        const slope = (containerHeight - 20) / (pBottom - pTop);
        const interpolatedY = 10 + (price - pTop) * slope;
        if (!isNaN(interpolatedY)) {
          return interpolatedY;
        }
      }
      return price > target.entry_price ? -50 : containerHeight + 50;
    };

    // Helper: binary search to find closest candle index in currentCandles
    const findCandleIndex = (timeSec: number): number => {
      let low = 0, high = currentCandles.length - 1;
      while (low <= high) {
        const mid = Math.floor((low + high) / 2);
        const t = currentCandles[mid].time as number;
        if (t === timeSec) return mid;
        if (t < timeSec) low = mid + 1;
        else high = mid - 1;
      }
      if (low >= currentCandles.length) return currentCandles.length - 1;
      if (high < 0) return 0;
      return Math.abs((currentCandles[low].time as number) - timeSec) < Math.abs((currentCandles[high].time as number) - timeSec)
        ? low
        : high;
    };

    // Robust X coordinates using logicalToCoordinate (supports off-screen coordinates)
    const entryIdx = findCandleIndex(target.entry_time);
    let x1Raw = chart.timeScale().logicalToCoordinate(entryIdx as any);
    if (x1Raw === null) {
      x1Raw = chart.timeScale().timeToCoordinate(target.entry_time as Time);
    }

    let x2Raw: number | null = null;
    if (target.isLiveActive || !target.exit_time) {
      const lastIdx = currentCandles.length - 1;
      const lastX = chart.timeScale().logicalToCoordinate(lastIdx as any);
      x2Raw = lastX !== null ? lastX + 80 : containerWidth - 65;
    } else {
      const exitIdx = findCandleIndex(target.exit_time);
      x2Raw = chart.timeScale().logicalToCoordinate(exitIdx as any);
      if (x2Raw === null) {
        x2Raw = chart.timeScale().timeToCoordinate(target.exit_time as Time);
      }
    }

    if (x1Raw === null && x2Raw === null) {
      setPositionBoxes([]);
      return;
    }

    const startX = x1Raw !== null ? x1Raw : (x2Raw! - 100);
    const endX = x2Raw !== null ? x2Raw : (x1Raw! + 100);
    const leftX = Math.min(startX, endX);
    const rightX = Math.max(startX, endX);
    const width = Math.max(rightX - leftX, 28);

    // If box is completely outside visible horizontal range (by over 400px), skip
    if (rightX < -400 || leftX > containerWidth + 400) {
      setPositionBoxes([]);
      return;
    }

    const yEntry = getYForPrice(target.entry_price);
    const ySL = getYForPrice(target.stop_loss);
    const yTP = getYForPrice(target.take_profit);

    const isLong = target.take_profit >= target.entry_price;
    let yProfitTop: number, profitHeight: number, yLossTop: number, lossHeight: number;

    if (isLong) {
      // Long: TP is higher price (lower Y in screen coords)
      yProfitTop = yTP;
      profitHeight = Math.max(yEntry - yTP, 2);
      yLossTop = yEntry;
      lossHeight = Math.max(ySL - yEntry, 2);
    } else {
      // Short: SL is higher price (lower Y in screen coords)
      yLossTop = ySL;
      lossHeight = Math.max(yEntry - ySL, 2);
      yProfitTop = yEntry;
      profitHeight = Math.max(yTP - yEntry, 2);
    }

    setPositionBoxes([
      {
        id: typeof target.id === 'number' ? target.id : (target.id || 999),
        x: leftX,
        width,
        yEntry,
        yProfitTop,
        profitHeight,
        yLossTop,
        lossHeight,
        tpPrice: target.take_profit,
        slPrice: target.stop_loss,
        entryPrice: target.entry_price,
        pnlPct: target.pnl_pct || 0,
        isLong,
      },
    ]);
  };

  updateBoxCoordinatesRef.current = updateBoxCoordinates;

  // 5. Initialize Lightweight Chart & Add Indicator Series
  useEffect(() => {
    if (!chartContainerRef.current || candles.length === 0) return;

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: isDark ? '#0d1117' : '#ffffff' },
        textColor: isDark ? '#8b949e' : '#334155',
        fontFamily: 'JetBrains Mono, monospace',
      },
      grid: {
        vertLines: { color: isDark ? '#161b22' : '#f1f5f9' },
        horzLines: { color: isDark ? '#161b22' : '#f1f5f9' },
      },
      crosshair: {
        vertLine: { color: isDark ? '#30363d' : '#cbd5e1' },
        horzLine: { color: isDark ? '#30363d' : '#cbd5e1' },
      },
      timeScale: {
        timeVisible: true,
        secondsVisible: false,
        borderColor: isDark ? '#30363d' : '#e2e8f0',
      },
      rightPriceScale: {
        borderColor: isDark ? '#30363d' : '#e2e8f0',
        scaleMargins: {
          top: 0.08,
          bottom: 0.22, // leaves lower 22% for volume sub-pane
        },
      },
    });

    // 1. Candlestick Series
    const candleSeries = chart.addCandlestickSeries({
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderVisible: false,
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350',
    });
    candleSeries.setData(candles);

    if (displayMarkers.length > 0) {
      candleSeries.setMarkers(displayMarkers);
    }

    // 2. Volume Histogram (Bottom Sub-Pane)
    const volumeSeries = chart.addHistogramSeries({
      priceFormat: { type: 'volume' },
      priceScaleId: 'volume_pane',
    });
    chart.priceScale('volume_pane').applyOptions({
      scaleMargins: { top: 0.82, bottom: 0 },
    });
    volumeSeries.setData(volumeData);
    volumeSeries.applyOptions({ visible: showVolume });

    // 3. Fast Ribbon EMA 9 (Aqua / Sky Blue)
    const ema9Series = chart.addLineSeries({
      color: '#38bdf8',
      lineWidth: 2,
      priceLineVisible: false,
      lastValueVisible: false,
      crosshairMarkerVisible: true,
    });
    ema9Series.setData(ema9Data);
    ema9Series.applyOptions({ visible: showRibbon });

    // 4. Medium Ribbon EMA 21 (Amber / Orange)
    const ema21Series = chart.addLineSeries({
      color: '#f59e0b',
      lineWidth: 2,
      priceLineVisible: false,
      lastValueVisible: false,
      crosshairMarkerVisible: true,
    });
    ema21Series.setData(ema21Data);
    ema21Series.applyOptions({ visible: showRibbon });

    // 5. Macro Baseline EMA 200 (Purple / Violet)
    const ema200Series = chart.addLineSeries({
      color: '#a855f7',
      lineWidth: 2,
      priceLineVisible: false,
      lastValueVisible: false,
      crosshairMarkerVisible: true,
    });
    ema200Series.setData(ema200Data);
    ema200Series.applyOptions({ visible: showMacroEma });

    // 6. 15-Minute Dynamic Range HH15 & LL15 (Step / Dashed Breakout Channels)
    const hh15Series = chart.addLineSeries({
      color: '#10b981',
      lineWidth: 1,
      lineStyle: 2, // Dashed
      priceLineVisible: false,
      lastValueVisible: false,
      crosshairMarkerVisible: false,
    });
    const ll15Series = chart.addLineSeries({
      color: '#f43f5e',
      lineWidth: 1,
      lineStyle: 2, // Dashed
      priceLineVisible: false,
      lastValueVisible: false,
      crosshairMarkerVisible: false,
    });
    hh15Series.setData(hh15Data);
    ll15Series.setData(ll15Data);
    hh15Series.applyOptions({ visible: showRanges });
    ll15Series.applyOptions({ visible: showRanges });

    // 7. Crosshair Hover Subscription for Dynamic Legend Readout
    chart.subscribeCrosshairMove((param) => {
      if (!param.time || !param.seriesData) {
        setHoverLegend(null);
        return;
      }
      const cData = param.seriesData.get(candleSeries) as any;
      const e9 = param.seriesData.get(ema9Series) as any;
      const e21 = param.seriesData.get(ema21Series) as any;
      const e200 = param.seriesData.get(ema200Series) as any;
      const hh = param.seriesData.get(hh15Series) as any;
      const ll = param.seriesData.get(ll15Series) as any;
      const vol = param.seriesData.get(volumeSeries) as any;

      if (cData) {
        const chg = cData.open ? ((cData.close - cData.open) / cData.open) * 100 : 0;
        setHoverLegend({
          time: Number(param.time),
          open: cData.open,
          high: cData.high,
          low: cData.low,
          close: cData.close,
          changePct: chg,
          ema9: e9?.value,
          ema21: e21?.value,
          ema200: e200?.value,
          hh15: hh?.value,
          ll15: ll?.value,
          volume: vol?.value,
        });
      }
    });

    chart.timeScale().fitContent();

    chartRef.current = chart;
    candleSeriesRef.current = candleSeries;
    volumeSeriesRef.current = volumeSeries;
    ema9SeriesRef.current = ema9Series;
    ema21SeriesRef.current = ema21Series;
    ema200SeriesRef.current = ema200Series;
    hh15SeriesRef.current = hh15Series;
    ll15SeriesRef.current = ll15Series;

    const handleRangeChange = () => {
      requestAnimationFrame(() => {
        if (updateBoxCoordinatesRef.current) {
          updateBoxCoordinatesRef.current();
        }
      });
    };

    chart.timeScale().subscribeVisibleLogicalRangeChange(handleRangeChange);
    chart.timeScale().subscribeVisibleTimeRangeChange(handleRangeChange);

    let wheelTimer: any = null;
    const handleWheel = () => {
      clearTimeout(wheelTimer);
      wheelTimer = setTimeout(() => {
        if (updateBoxCoordinatesRef.current) {
          updateBoxCoordinatesRef.current();
        }
      }, 30);
    };

    const container = chartContainerRef.current;
    container.addEventListener('wheel', handleWheel, { passive: true });
    container.addEventListener('pointerup', handleRangeChange);

    const resizeObserver = new ResizeObserver(() => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
          height: chartContainerRef.current.clientHeight,
        });
        if (updateBoxCoordinatesRef.current) {
          updateBoxCoordinatesRef.current();
        }
      }
    });

    resizeObserver.observe(chartContainerRef.current);
    setTimeout(() => {
      if (updateBoxCoordinatesRef.current) {
        updateBoxCoordinatesRef.current();
      }
    }, 100);

    return () => {
      chart.timeScale().unsubscribeVisibleLogicalRangeChange(handleRangeChange);
      chart.timeScale().unsubscribeVisibleTimeRangeChange(handleRangeChange);
      container.removeEventListener('wheel', handleWheel);
      container.removeEventListener('pointerup', handleRangeChange);
      clearTimeout(wheelTimer);
      resizeObserver.disconnect();
      chart.remove();
    };
  }, [candles, isDark]);

  // Auto-center chart on latest trade on initial dataset load
  useEffect(() => {
    if (!initialCenteredRef.current && chartRef.current && allInspectableSignals.length > 0) {
      const target = allInspectableSignals[allInspectableSignals.length - 1];
      if (target) {
        initialCenteredRef.current = true;
        setTimeout(() => {
          centerOnTrade(target);
        }, 120);
      }
    }
  }, [allInspectableSignals.length, candles.length]);

  // Sync Dynamic Indicator Visibility Toggles
  useEffect(() => {
    if (ema9SeriesRef.current) ema9SeriesRef.current.applyOptions({ visible: showRibbon });
    if (ema21SeriesRef.current) ema21SeriesRef.current.applyOptions({ visible: showRibbon });
  }, [showRibbon]);

  useEffect(() => {
    if (ema200SeriesRef.current) ema200SeriesRef.current.applyOptions({ visible: showMacroEma });
  }, [showMacroEma]);

  useEffect(() => {
    if (hh15SeriesRef.current) hh15SeriesRef.current.applyOptions({ visible: showRanges });
    if (ll15SeriesRef.current) ll15SeriesRef.current.applyOptions({ visible: showRanges });
  }, [showRanges]);

  useEffect(() => {
    if (volumeSeriesRef.current) volumeSeriesRef.current.applyOptions({ visible: showVolume });
  }, [showVolume]);

  // Sync Markers to Candlestick Series
  useEffect(() => {
    if (candleSeriesRef.current) {
      candleSeriesRef.current.setMarkers(displayMarkers);
    }
  }, [displayMarkers]);

  // Sync Dynamic Entry, SL, and TP Price Lines ONLY for Active Signal
  useEffect(() => {
    if (!candleSeriesRef.current) return;

    // Remove previous price lines
    priceLinesRef.current.forEach((line) => {
      try {
        candleSeriesRef.current?.removePriceLine(line);
      } catch (e) {}
    });
    priceLinesRef.current = [];

    // CRITICAL: Entry, SL, and TP horizontal lines appear ONLY when an active signal exists
    if (!activeLiveSignal || !activeLiveSignal.entry) return;

    const isGold = selectedSymbol.toLowerCase().includes('xau') || selectedSymbol.toLowerCase().includes('gold');
    const formatPrice = (p: number) => (isGold ? `$${p.toFixed(2)}` : (p >= 1000 ? `$${p.toFixed(1)}` : `$${p.toFixed(4)}`));
    const isBuy = activeLiveSignal.side === 'BUY' || activeLiveSignal.side === 'LONG';

    const lines: any[] = [];

    // TP Line (Emerald Green)
    if (activeLiveSignal.tp) {
      const tpLine = candleSeriesRef.current.createPriceLine({
        price: activeLiveSignal.tp,
        color: '#10b981',
        lineWidth: 2,
        lineStyle: 0,
        axisLabelVisible: true,
        title: `TP: ${formatPrice(activeLiveSignal.tp)}`,
      });
      lines.push(tpLine);
    }

    // Entry Line (Sky Blue Dashed)
    if (activeLiveSignal.entry) {
      const entryLine = candleSeriesRef.current.createPriceLine({
        price: activeLiveSignal.entry,
        color: '#38bdf8',
        lineWidth: 2,
        lineStyle: 2,
        axisLabelVisible: true,
        title: `Entry (${activeLiveSignal.side || (isBuy ? 'LONG' : 'SHORT')}): ${formatPrice(activeLiveSignal.entry)}`,
      });
      lines.push(entryLine);
    }

    // SL Line (Rose Red)
    if (activeLiveSignal.sl) {
      const slLine = candleSeriesRef.current.createPriceLine({
        price: activeLiveSignal.sl,
        color: '#ef4444',
        lineWidth: 2,
        lineStyle: 0,
        axisLabelVisible: true,
        title: `SL: ${formatPrice(activeLiveSignal.sl)}`,
      });
      lines.push(slLine);
    }

    priceLinesRef.current = lines;
  }, [activeLiveSignal, selectedSymbol]);

  useEffect(() => {
    if (chartRef.current && candleSeriesRef.current) {
      if (updateBoxCoordinatesRef.current) {
        updateBoxCoordinatesRef.current();
      }
      setTimeout(() => {
        if (updateBoxCoordinatesRef.current) {
          updateBoxCoordinatesRef.current();
        }
      }, 40);
    }
  }, [allInspectableSignals, selectedSignalIndex, showPositionBox, displayMarkers]);

  const cleanStrategyName = (activeStrategy || selectedStrategy || '').replace('.py', '');

  return (
    <div className={`w-full h-full relative overflow-hidden flex flex-col ${isDark ? 'bg-[#0d1117]' : 'bg-white'}`}>
      {/* ── Chart Top Toolbar: Symbol, Strategy, & Indicator Toggles ── */}
      <div
        className={`h-11 border-b px-4 flex items-center justify-between text-xs select-none shrink-0 transition-colors ${
          isDark ? 'bg-[#161b22] border-[#30363d] text-white' : 'bg-white border-slate-200 text-slate-800'
        }`}
      >
        {/* Left: Symbol & Strategy */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 font-bold tracking-wide">
            <span className={`w-2 h-2 rounded-full ${isWsConnected ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`} />
            <span className="text-amber-400 font-mono text-sm font-bold">{selectedSymbol}</span>
            <span className="px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300 text-[10px] font-mono">
              {isXauActive ? '1m' : '15m'}
            </span>
          </div>

          <span className="text-slate-600 hidden sm:inline">|</span>

          <div className="hidden md:flex items-center gap-1.5 text-[11px] font-mono">
            <Activity className="w-3.5 h-3.5 text-indigo-400" />
            <span className="text-slate-400">Strategy:</span>
            <span className="font-semibold text-indigo-300">{cleanStrategyName}</span>
          </div>
        </div>

        {/* Middle: Signals Walkthrough / Inspector */}
        {allInspectableSignals.length > 0 ? (
          <div className="hidden lg:flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-800/90 border border-slate-700/80 font-mono text-[11px] shadow-sm">
            <span className="text-slate-400 font-semibold">Signal:</span>

            {/* Previous Signal Button */}
            <button
              onClick={() => {
                const cur = selectedSignalIndex ?? allInspectableSignals.length - 1;
                if (cur <= 0) return;
                const nextIdx = cur - 1;
                setSelectedSignalIndex(nextIdx);
                centerOnTrade(allInspectableSignals[nextIdx]);
              }}
              disabled={(selectedSignalIndex ?? allInspectableSignals.length - 1) <= 0}
              className="px-1.5 py-0.5 rounded bg-slate-700 hover:bg-slate-600 disabled:opacity-25 disabled:cursor-not-allowed text-white text-[10px] transition-all"
              title="Previous Historical / Past Signal"
            >
              ◀
            </button>

            {/* Index Counter */}
            <span className="text-sky-300 font-bold">
              #{(selectedSignalIndex ?? allInspectableSignals.length - 1) + 1}/{allInspectableSignals.length}
            </span>

            {/* Signal Badge: Side + PnL or LIVE */}
            {inspectedSignal?.isLiveActive ? (
              <span className="flex items-center gap-1 px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-[10px] font-bold animate-pulse">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                LIVE {inspectedSignal.side}
              </span>
            ) : (
              <span
                className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                  (inspectedSignal?.pnl_pct ?? 0) >= 0
                    ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                    : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                }`}
              >
                {inspectedSignal?.side} {(inspectedSignal?.pnl_pct ?? 0) >= 0 ? '+' : ''}
                {(inspectedSignal?.pnl_pct ?? 0).toFixed(2)}%
                {inspectedSignal?.source === 'LIVE' && (
                  <span className="ml-1 text-[9px] text-amber-400 font-mono font-normal">LIVE</span>
                )}
              </span>
            )}

            {/* Next Signal Button */}
            <button
              onClick={() => {
                const cur = selectedSignalIndex ?? allInspectableSignals.length - 1;
                if (cur >= allInspectableSignals.length - 1) return;
                const nextIdx = cur + 1;
                setSelectedSignalIndex(nextIdx);
                centerOnTrade(allInspectableSignals[nextIdx]);
              }}
              disabled={(selectedSignalIndex ?? allInspectableSignals.length - 1) >= allInspectableSignals.length - 1}
              className="px-1.5 py-0.5 rounded bg-slate-700 hover:bg-slate-600 disabled:opacity-25 disabled:cursor-not-allowed text-white text-[10px] transition-all"
              title="Next Historical / Past Signal"
            >
              ▶
            </button>

            {/* Jump to Latest Button */}
            <button
              onClick={() => {
                const lastIdx = allInspectableSignals.length - 1;
                setSelectedSignalIndex(lastIdx);
                centerOnTrade(allInspectableSignals[lastIdx]);
              }}
              className="ml-1 px-1.5 py-0.5 rounded bg-indigo-900/60 hover:bg-indigo-800 text-indigo-200 border border-indigo-700/50 text-[9px] uppercase font-bold transition-all"
              title="Jump to Latest Signal"
            >
              Latest
            </button>

            {/* Quick Live Position Jump Indicator */}
            {activeLiveSignal && (
              <button
                onClick={() => {
                  const liveIdx = allInspectableSignals.findIndex((s) => s.isLiveActive);
                  if (liveIdx >= 0) {
                    setSelectedSignalIndex(liveIdx);
                    centerOnTrade(allInspectableSignals[liveIdx]);
                  }
                }}
                className="ml-1 px-1.5 py-0.5 rounded bg-emerald-950/90 hover:bg-emerald-900 text-emerald-300 border border-emerald-600/50 text-[9px] uppercase font-bold transition-all flex items-center gap-1 animate-pulse"
                title="Jump to Active Live Signal"
              >
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                Active
              </button>
            )}
          </div>
        ) : (
          <div className="hidden lg:flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-800/90 border border-slate-700/80 font-mono text-[11px] shadow-sm">
            <span className="text-slate-400 font-semibold">Signal:</span>
            <span className="flex items-center gap-1.5 text-slate-400">
              <span className="w-1.5 h-1.5 rounded-full bg-slate-500" />
              NONE ACTIVE (SCANNING)
            </span>
          </div>
        )}

        {/* Right: Strategy Indicators Toggles */}
        <div className="flex items-center gap-1.5 font-mono text-[10px]">
          <span className="text-slate-500 mr-1 hidden lg:inline font-bold uppercase text-[9px]">Indicators:</span>

          {/* Ribbon 9/21 Toggle */}
          <button
            onClick={() => setShowRibbon(!showRibbon)}
            className={`px-2 py-1 rounded border flex items-center gap-1.5 transition-all ${
              showRibbon
                ? isDark
                  ? 'bg-sky-950/70 border-sky-500/70 text-sky-300 shadow-sm'
                  : 'bg-sky-50 border-sky-300 text-sky-700'
                : isDark
                ? 'bg-slate-900 border-slate-800 text-slate-500 hover:text-slate-400'
                : 'bg-slate-100 border-slate-200 text-slate-400'
            }`}
            title="Toggle Momentum Ribbon (EMA 9 Fast & EMA 21 Medium)"
          >
            <span className="w-1.5 h-1.5 rounded-full bg-sky-400" />
            <span>EMA 9/21</span>
          </button>

          {/* Macro EMA 200 Toggle */}
          <button
            onClick={() => setShowMacroEma(!showMacroEma)}
            className={`px-2 py-1 rounded border flex items-center gap-1.5 transition-all ${
              showMacroEma
                ? isDark
                  ? 'bg-purple-950/70 border-purple-500/70 text-purple-300 shadow-sm'
                  : 'bg-purple-50 border-purple-300 text-purple-700'
                : isDark
                ? 'bg-slate-900 border-slate-800 text-slate-500 hover:text-slate-400'
                : 'bg-slate-100 border-slate-200 text-slate-400'
            }`}
            title="Toggle Macro Baseline (EMA 200 Trend Filter)"
          >
            <span className="w-1.5 h-1.5 rounded-full bg-purple-400" />
            <span>EMA 200</span>
          </button>

          {/* 15m Range Channel Toggle */}
          <button
            onClick={() => setShowRanges(!showRanges)}
            className={`px-2 py-1 rounded border flex items-center gap-1.5 transition-all ${
              showRanges
                ? isDark
                  ? 'bg-emerald-950/70 border-emerald-500/70 text-emerald-300 shadow-sm'
                  : 'bg-emerald-50 border-emerald-300 text-emerald-700'
                : isDark
                ? 'bg-slate-900 border-slate-800 text-slate-500 hover:text-slate-400'
                : 'bg-slate-100 border-slate-200 text-slate-400'
            }`}
            title="Toggle 15m Dynamic Range Channels (HH15 & LL15)"
          >
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            <span>HH/LL 15m</span>
          </button>

          {/* Volume Histogram Toggle */}
          <button
            onClick={() => setShowVolume(!showVolume)}
            className={`px-2 py-1 rounded border flex items-center gap-1.5 transition-all ${
              showVolume
                ? isDark
                  ? 'bg-teal-950/70 border-teal-500/70 text-teal-300 shadow-sm'
                  : 'bg-teal-50 border-teal-300 text-teal-700'
                : isDark
                ? 'bg-slate-900 border-slate-800 text-slate-500 hover:text-slate-400'
                : 'bg-slate-100 border-slate-200 text-slate-400'
            }`}
            title="Toggle Volume Histogram with Z-Score Surge Detection"
          >
            <BarChart2 className="w-3 h-3" />
            <span>Volume</span>
          </button>

          {/* Position Boxes Toggle */}
          <button
            onClick={() => setShowPositionBox(!showPositionBox)}
            className={`px-2 py-1 rounded border flex items-center gap-1.5 transition-all ${
              showPositionBox
                ? isDark
                  ? 'bg-indigo-950/70 border-indigo-500/70 text-indigo-300 shadow-sm'
                  : 'bg-indigo-50 border-indigo-300 text-indigo-700'
                : isDark
                ? 'bg-slate-900 border-slate-800 text-slate-500 hover:text-slate-400'
                : 'bg-slate-100 border-slate-200 text-slate-400'
            }`}
            title="Toggle Risk/Reward Position Boxes"
          >
            <Layers className="w-3 h-3" />
            <span>R:R Box</span>
          </button>
        </div>
      </div>

      {/* ── Dynamic TradingView-Style Indicator Legend HUD ── */}
      <div
        className={`px-4 py-1.5 border-b flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] font-mono select-none shrink-0 transition-colors ${
          isDark ? 'bg-[#0d1117] border-[#21262d] text-slate-400' : 'bg-slate-50 border-slate-200 text-slate-600'
        }`}
      >
        {/* OHLCV Readout */}
        <div className="flex items-center gap-2">
          <span>
            O: <span className="font-semibold text-slate-200">${activeLegend.open?.toFixed(2) || '–'}</span>
          </span>
          <span>
            H: <span className="font-semibold text-slate-200">${activeLegend.high?.toFixed(2) || '–'}</span>
          </span>
          <span>
            L: <span className="font-semibold text-slate-200">${activeLegend.low?.toFixed(2) || '–'}</span>
          </span>
          <span>
            C:{' '}
            <span className={`font-bold ${activeLegend.changePct && activeLegend.changePct >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
              ${activeLegend.close?.toFixed(2) || '–'} (
              {activeLegend.changePct != null ? `${activeLegend.changePct >= 0 ? '+' : ''}${activeLegend.changePct.toFixed(2)}%` : '–'})
            </span>
          </span>
        </div>

        <div className="h-3 w-[1px] bg-slate-700 hidden sm:block" />

        {/* Strategy Indicator Real-Time Values */}
        <div className="flex items-center gap-3 flex-wrap">
          {showRibbon && (
            <>
              <span className="flex items-center gap-1 text-sky-400 font-semibold">
                <span className="w-1.5 h-1.5 rounded-full bg-sky-400" />
                EMA(9): <span>${activeLegend.ema9?.toFixed(2) || '–'}</span>
              </span>
              <span className="flex items-center gap-1 text-amber-400 font-semibold">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                EMA(21): <span>${activeLegend.ema21?.toFixed(2) || '–'}</span>
              </span>
            </>
          )}

          {showMacroEma && (
            <span className="flex items-center gap-1 text-purple-400 font-semibold">
              <span className="w-1.5 h-1.5 rounded-full bg-purple-400" />
              EMA(200): <span>${activeLegend.ema200?.toFixed(2) || '–'}</span>
            </span>
          )}

          {showRanges && (
            <>
              <span className="flex items-center gap-1 text-emerald-400 font-semibold">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                HH15: <span>${activeLegend.hh15?.toFixed(2) || '–'}</span>
              </span>
              <span className="flex items-center gap-1 text-rose-400 font-semibold">
                <span className="w-1.5 h-1.5 rounded-full bg-rose-400" />
                LL15: <span>${activeLegend.ll15?.toFixed(2) || '–'}</span>
              </span>
            </>
          )}

          {showVolume && (
            <span className="flex items-center gap-1 text-teal-400 font-semibold">
              <BarChart2 className="w-3 h-3 text-teal-400" />
              Vol: <span>{activeLegend.volume?.toLocaleString() || '–'}</span>
            </span>
          )}

          {inspectedTradeLevels && (
            <>
              <div className="h-3 w-[1px] bg-slate-700 hidden sm:block" />
              <span className="text-sky-400 font-semibold">
                Entry: <span className="font-bold text-slate-200">${isXauActive ? inspectedTradeLevels.entry.toFixed(2) : inspectedTradeLevels.entry.toFixed(1)}</span>
              </span>
              <span className="text-emerald-400 font-semibold">
                TP: <span className="font-bold text-slate-200">${isXauActive ? inspectedTradeLevels.tp.toFixed(2) : inspectedTradeLevels.tp.toFixed(1)}</span>
              </span>
              <span className="text-rose-400 font-semibold">
                SL: <span className="font-bold text-slate-200">${isXauActive ? inspectedTradeLevels.sl.toFixed(2) : inspectedTradeLevels.sl.toFixed(1)}</span>
              </span>
              <span className="text-amber-400 font-semibold">
                R:R: <span className="font-bold text-slate-200">{inspectedTradeLevels.rr}</span>
              </span>
            </>
          )}
        </div>
      </div>

      {/* ── Chart Canvas & Overlaid Risk/Reward Boxes ── */}
      <div ref={chartContainerRef} className="w-full flex-1 relative">
        {positionBoxes.length > 0 && showPositionBox && (
          <svg className="absolute inset-0 w-full h-full pointer-events-none z-10 overflow-hidden">
            <defs>
              <linearGradient id="profitGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#26a69a" stopOpacity="0.25" />
                <stop offset="100%" stopColor="#26a69a" stopOpacity="0.08" />
              </linearGradient>
              <linearGradient id="lossGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#ef5350" stopOpacity="0.08" />
                <stop offset="100%" stopColor="#ef5350" stopOpacity="0.25" />
              </linearGradient>
            </defs>

            {positionBoxes.map((box) => {
              const labelWidth = 68;
              const containerW = chartContainerRef.current?.clientWidth || 800;
              const containerH = chartContainerRef.current?.clientHeight || 400;
              const labelX = Math.max(
                box.x + 4,
                Math.min(box.x + box.width - labelWidth - 4, containerW - labelWidth - 12)
              );
              const textX = labelX + labelWidth / 2;

              // Correct vertical positioning for Long vs Short:
              // Long: TP is top of profit zone (yProfitTop), SL is bottom of loss zone (yLossTop + lossHeight)
              // Short: SL is top of loss zone (yLossTop), TP is bottom of profit zone (yProfitTop + profitHeight)
              const rawTPY = box.isLong
                ? box.yProfitTop + 2
                : box.yProfitTop + box.profitHeight - 18;
              const rawSLY = box.isLong
                ? box.yLossTop + box.lossHeight - 18
                : box.yLossTop + 2;

              const clampedEntryY = Math.max(12, Math.min(containerH - 24, box.yEntry - 8));
              const clampedTPY = Math.max(12, Math.min(containerH - 24, rawTPY));
              const clampedSLY = Math.max(12, Math.min(containerH - 24, rawSLY));

              return (
                <g key={box.id}>
                  {/* Green Profit Zone Box */}
                  <rect
                    x={box.x}
                    y={box.yProfitTop}
                    width={box.width}
                    height={box.profitHeight}
                    fill="url(#profitGrad)"
                    stroke="#26a69a"
                    strokeWidth="1.5"
                    strokeDasharray="4 2"
                  />
                  {/* Red Loss Zone Box */}
                  <rect
                    x={box.x}
                    y={box.yLossTop}
                    width={box.width}
                    height={box.lossHeight}
                    fill="url(#lossGrad)"
                    stroke="#ef5350"
                    strokeWidth="1.5"
                    strokeDasharray="4 2"
                  />
                  {/* Entry Price Line */}
                  <line
                    x1={box.x}
                    y1={box.yEntry}
                    x2={box.x + box.width}
                    y2={box.yEntry}
                    stroke="#38bdf8"
                    strokeWidth="1.5"
                    strokeDasharray="3 3"
                  />

                  {/* Entry Price Label */}
                  <rect
                    x={labelX}
                    y={clampedEntryY}
                    width={labelWidth}
                    height="16"
                    rx="3"
                    fill="rgba(56, 189, 248, 0.92)"
                  />
                  <text
                    x={textX}
                    y={clampedEntryY + 11}
                    fill="#041829"
                    fontSize="9"
                    fontWeight="bold"
                    fontFamily="monospace"
                    textAnchor="middle"
                  >
                    ENTRY: ${isXauActive ? box.entryPrice.toFixed(1) : box.entryPrice.toFixed(0)}
                  </text>

                  {/* TP Label */}
                  <rect
                    x={labelX}
                    y={clampedTPY}
                    width={labelWidth}
                    height="16"
                    rx="3"
                    fill="rgba(38, 166, 154, 0.92)"
                  />
                  <text
                    x={textX}
                    y={clampedTPY + 11}
                    fill="#ffffff"
                    fontSize="9"
                    fontWeight="bold"
                    fontFamily="monospace"
                    textAnchor="middle"
                  >
                    TP: ${isXauActive ? box.tpPrice.toFixed(1) : box.tpPrice.toFixed(0)}
                  </text>

                  {/* SL Label */}
                  <rect
                    x={labelX}
                    y={clampedSLY}
                    width={labelWidth}
                    height="16"
                    rx="3"
                    fill="rgba(239, 83, 80, 0.92)"
                  />
                  <text
                    x={textX}
                    y={clampedSLY + 11}
                    fill="#ffffff"
                    fontSize="9"
                    fontWeight="bold"
                    fontFamily="monospace"
                    textAnchor="middle"
                  >
                    SL: ${isXauActive ? box.slPrice.toFixed(1) : box.slPrice.toFixed(0)}
                  </text>
                </g>
              );
            })}
          </svg>
        )}
      </div>
    </div>
  );
};

export default ChartCanvas;

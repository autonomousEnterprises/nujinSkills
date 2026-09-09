import React, { useEffect, useRef, useState } from 'react';
import { createChart, ColorType, IChartApi, ISeriesApi, SeriesMarker, Time } from 'lightweight-charts';
import { SignalData } from '../hooks/useWebSocket';

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
  id: number;
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
}

interface ChartCanvasProps {
  latestSignal: SignalData | null;
  theme?: 'dark' | 'light';
  selectedStrategy?: string;
  tradeMarkers?: any[];
  tradesDetail?: TradeDetail[];
  activeStrategy?: string;
}

export const ChartCanvas: React.FC<ChartCanvasProps> = ({
  latestSignal,
  theme = 'dark',
  selectedStrategy = 'PropFirmVsaWickRejection.py',
  tradeMarkers = [],
  tradesDetail = [],
  activeStrategy = 'PropFirmVsaWickRejection'
}) => {
  const isDark = theme === 'dark';
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);

  // Live vs Backtest Mode & Multi-Asset Selection State
  const [chartMode, setChartMode] = useState<'LIVE' | 'BACKTEST'>('LIVE');
  const [selectedSymbol, setSelectedSymbol] = useState<string>('BTC/USDT');
  const [isWsConnected, setIsWsConnected] = useState<boolean>(false);
  const [lastLivePrice, setLastLivePrice] = useState<number | null>(null);
  const [showPositionBox, setShowPositionBox] = useState<boolean>(true);

  const [candles, setCandles] = useState<any[]>([]);
  const [displayMarkers, setDisplayMarkers] = useState<SeriesMarker<Time>[]>([]);
  const [positionBoxes, setPositionBoxes] = useState<PositionBoxCoord[]>([]);
  const [activeTradeLevels, setActiveTradeLevels] = useState<{ entry: number; sl: number; tp: number; rr: string } | null>(null);

  // 1. Fetch Initial Candles (Live or Backtest mode)
  const fetchCandles = () => {
    const url = `/api/candles?symbol=${encodeURIComponent(selectedSymbol)}&count=2880&mode=${chartMode === 'LIVE' ? 'live' : 'backtest'}`;
    fetch(url)
      .then((res) => res.json())
      .then((data) => {
        if (data.data && data.data.length > 0) {
          setCandles(data.data);
          if (candleSeriesRef.current) {
            candleSeriesRef.current.setData(data.data);
          }
          const lastC = data.data[data.data.length - 1];
          if (lastC) setLastLivePrice(lastC.close);
        }
      })
      .catch((err) => console.log('Failed to fetch candles:', err));
  };

  useEffect(() => {
    fetchCandles();
  }, [chartMode, selectedSymbol]);

  // 2. Binance 100% Free Public Real-Time WebSocket Stream (when in LIVE mode)
  useEffect(() => {
    if (chartMode !== 'LIVE') {
      setIsWsConnected(false);
      return;
    }

    const cleanSym = selectedSymbol.replace('/', '').toLowerCase();
    const wsUrl = `wss://stream.binance.com:9443/ws/${cleanSym}@kline_15m`;
    let ws: WebSocket | null = null;

    try {
      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setIsWsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.e === 'kline') {
            const k = msg.k;
            const updatedCandle = {
              time: Math.floor(k.t / 1000),
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
          console.error('Error parsing Binance WS kline:', e);
        }
      };

      ws.onerror = () => setIsWsConnected(false);
      ws.onclose = () => setIsWsConnected(false);
    } catch (e) {
      setIsWsConnected(false);
    }

    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [chartMode, selectedSymbol]);

  // 3. Trade Markers & Active Open Position Levels Resolution
  useEffect(() => {
    if (candles.length === 0) return;
    const minTime = candles[0].time as number;
    const maxTime = candles[candles.length - 1].time as number;

    // ACTIVE TRADE LEVELS & POSITION BOX: Only active if there is an OPEN active trade!
    let currentOpenTrade: any = null;

    if (latestSignal && latestSignal.status === 'ACTIVE_IN_POSITION') {
      currentOpenTrade = latestSignal;
    } else if (tradesDetail && tradesDetail.length > 0) {
      const last = tradesDetail[tradesDetail.length - 1];
      if (last.exit_reason === 'ACTIVE_IN_POSITION') {
        currentOpenTrade = last;
      }
    }

    if (currentOpenTrade) {
      const entry = currentOpenTrade.entry_price;
      const sl = currentOpenTrade.stop_loss;
      const tp = currentOpenTrade.take_profit;
      const risk = Math.abs(entry - sl);
      const reward = Math.abs(tp - entry);
      const rr = risk > 0 ? (reward / risk).toFixed(2) : '0.00';
      setActiveTradeLevels({ entry, sl, tp, rr });
    } else {
      // All historical trades are closed — do NOT draw active price lines across chart
      setActiveTradeLevels(null);
    }

    // Process trade markers for historical & live trades
    if (tradeMarkers && tradeMarkers.length > 0) {
      const filtered = tradeMarkers.filter((m) => (m.time as number) >= minTime && (m.time as number) <= maxTime);

      const validMarkers: SeriesMarker<Time>[] = filtered.map((m) => {
        return {
          time: m.time as Time,
          position: m.position,
          color: m.color,
          shape: m.shape,
          text: m.text,
        };
      });
      setDisplayMarkers(validMarkers);
    }
  }, [selectedStrategy, tradeMarkers, tradesDetail, candles, latestSignal]);

  // 4. Precision Clamped Position Box Resolution (ONLY FOR OPEN ACTIVE SIGNALS)
  const updateBoxCoordinates = () => {
    if (!showPositionBox || !chartRef.current || !candleSeriesRef.current || !chartContainerRef.current || candles.length === 0) {
      setPositionBoxes([]);
      return;
    }

    // Check if there is an active open trade currently in position
    let targetTrade: TradeDetail | null = null;
    if (tradesDetail && tradesDetail.length > 0) {
      const last = tradesDetail[tradesDetail.length - 1];
      if (last.exit_reason === 'ACTIVE_IN_POSITION') {
        targetTrade = last;
      }
    } else if (latestSignal && latestSignal.status === 'ACTIVE_IN_POSITION') {
      targetTrade = {
        id: 99,
        entry_time: latestSignal.timestamp ? Math.floor(latestSignal.timestamp / 1000) : candles[candles.length - 1]?.time,
        entry_price: latestSignal.entry_price || 0,
        stop_loss: latestSignal.stop_loss || 0,
        take_profit: latestSignal.take_profit || 0,
        exit_time: candles[candles.length - 1]?.time,
        exit_price: 0,
        exit_reason: 'ACTIVE_IN_POSITION',
        pnl_pct: 0
      };
    }

    // If NO active open signal, do NOT render position boxes for closed trades!
    if (!targetTrade || !targetTrade.entry_price) {
      setPositionBoxes([]);
      return;
    }

    const chart = chartRef.current;
    const series = candleSeriesRef.current;
    const containerHeight = chartContainerRef.current.clientHeight || 400;

    const yEntryRaw = series.priceToCoordinate(targetTrade.entry_price);
    if (yEntryRaw === null) {
      setPositionBoxes([]);
      return;
    }

    const x1Raw = chart.timeScale().timeToCoordinate(targetTrade.entry_time as Time);
    const x2Raw = chart.timeScale().timeToCoordinate(candles[candles.length - 1].time as Time);

    const getBoundedY = (price: number) => {
      const y = series.priceToCoordinate(price);
      if (y === null || isNaN(y)) {
        return price > targetTrade.entry_price ? 0 : containerHeight;
      }
      return Math.max(0, Math.min(containerHeight, y));
    };

    const yEntry = yEntryRaw;
    const ySL = getBoundedY(targetTrade.stop_loss);
    const yTP = getBoundedY(targetTrade.take_profit);

    const startX = x1Raw !== null ? x1Raw : 20;
    const endX = x2Raw !== null ? x2Raw : startX + 120;

    const leftX = Math.min(startX, endX);
    const rightX = Math.max(startX, endX);
    const width = Math.max(rightX - leftX, 30);

    const isLong = targetTrade.take_profit >= targetTrade.entry_price;
    let yProfitTop: number, profitHeight: number, yLossTop: number, lossHeight: number;

    if (isLong) {
      yProfitTop = yTP;
      profitHeight = Math.max(yEntry - yTP, 2);
      yLossTop = yEntry;
      lossHeight = Math.max(ySL - yEntry, 2);
    } else {
      yProfitTop = yEntry;
      profitHeight = Math.max(yTP - yEntry, 2);
      yLossTop = ySL;
      lossHeight = Math.max(yEntry - ySL, 2);
    }

    setPositionBoxes([{
      id: targetTrade.id,
      x: leftX,
      width,
      yEntry,
      yProfitTop,
      profitHeight,
      yLossTop,
      lossHeight,
      tpPrice: targetTrade.take_profit,
      slPrice: targetTrade.stop_loss,
      entryPrice: targetTrade.entry_price,
      pnlPct: targetTrade.pnl_pct
    }]);
  };

  // 5. Initialize Lightweight Chart & Price Lines
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
      },
    });

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

    // Horizontal Price Lines on Price Scale ONLY FOR ACTIVE OPEN TRADES
    if (activeTradeLevels) {
      if (activeTradeLevels.tp) {
        candleSeries.createPriceLine({
          price: activeTradeLevels.tp,
          color: '#26a69a',
          lineWidth: 2,
          lineStyle: 0,
          axisLabelVisible: true,
          title: `TP: $${activeTradeLevels.tp.toFixed(0)}`,
        });
      }
      if (activeTradeLevels.entry) {
        candleSeries.createPriceLine({
          price: activeTradeLevels.entry,
          color: '#38bdf8',
          lineWidth: 1,
          lineStyle: 2,
          axisLabelVisible: true,
          title: `Entry: $${activeTradeLevels.entry.toFixed(0)}`,
        });
      }
      if (activeTradeLevels.sl) {
        candleSeries.createPriceLine({
          price: activeTradeLevels.sl,
          color: '#ef5350',
          lineWidth: 2,
          lineStyle: 0,
          axisLabelVisible: true,
          title: `SL: $${activeTradeLevels.sl.toFixed(0)}`,
        });
      }
    }

    chart.timeScale().fitContent();

    chartRef.current = chart;
    candleSeriesRef.current = candleSeries;

    const handleRangeChange = () => {
      requestAnimationFrame(updateBoxCoordinates);
    };

    chart.timeScale().subscribeVisibleLogicalRangeChange(handleRangeChange);
    chart.timeScale().subscribeVisibleTimeRangeChange(handleRangeChange);

    const resizeObserver = new ResizeObserver(() => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
          height: chartContainerRef.current.clientHeight,
        });
        updateBoxCoordinates();
      }
    });

    resizeObserver.observe(chartContainerRef.current);
    setTimeout(updateBoxCoordinates, 100);

    return () => {
      chart.timeScale().unsubscribeVisibleLogicalRangeChange(handleRangeChange);
      chart.timeScale().unsubscribeVisibleTimeRangeChange(handleRangeChange);
      resizeObserver.disconnect();
      chart.remove();
    };
  }, [candles, displayMarkers, activeTradeLevels, isDark]);

  useEffect(() => {
    if (chartRef.current && candleSeriesRef.current) {
      setTimeout(updateBoxCoordinates, 50);
    }
  }, [tradesDetail, activeTradeLevels, displayMarkers, showPositionBox]);

  // 6. Live Signal Handling
  useEffect(() => {
    if (!latestSignal || !candleSeriesRef.current) return;

    const isBuy = latestSignal.action === 'BUY';

    if (latestSignal.status === 'ACTIVE_IN_POSITION' && latestSignal.entry_price && latestSignal.stop_loss && latestSignal.take_profit) {
      const entry = latestSignal.entry_price;
      const sl = latestSignal.stop_loss;
      const tp = latestSignal.take_profit;
      const risk = Math.abs(entry - sl);
      const reward = Math.abs(tp - entry);
      const rr = risk > 0 ? (reward / risk).toFixed(2) : '0.00';
      setActiveTradeLevels({ entry, sl, tp, rr });
    }

    const newMarker: SeriesMarker<Time> = {
      time: (latestSignal.timestamp ? Math.floor(latestSignal.timestamp / 1000) : candles[candles.length - 1]?.time) as Time,
      position: isBuy ? 'belowBar' : 'aboveBar',
      color: isBuy ? '#26a69a' : '#ef5350',
      shape: isBuy ? 'arrowUp' : 'arrowDown',
      text: `${latestSignal.action} @ $${latestSignal.entry_price?.toFixed(0) || lastLivePrice?.toFixed(0)}`,
    };

    setDisplayMarkers((prev) => [...prev, newMarker]);
  }, [latestSignal]);

  return (
    <div className={`w-full h-full relative overflow-hidden flex flex-col ${isDark ? 'bg-[#0d1117]' : 'bg-white'}`}>
      {/* Top Floating Control Toolbar */}
      <div className={`absolute top-3 left-3 right-3 z-20 flex flex-wrap items-center justify-between gap-3 p-2.5 rounded-lg border backdrop-blur-md transition-colors ${
        isDark ? 'bg-[#161b22]/90 border-[#30363d] text-white' : 'bg-white/90 border-slate-200 text-slate-800 shadow-md'
      }`}>
        <div className="flex items-center gap-3">
          {/* Symbol Selector */}
          <select
            value={selectedSymbol}
            onChange={(e) => setSelectedSymbol(e.target.value)}
            className={`px-3 py-1.5 rounded-md text-xs font-bold font-mono border focus:outline-none focus:ring-1 ${
              isDark
                ? 'bg-[#0d1117] border-[#30363d] text-white focus:ring-emerald-500'
                : 'bg-slate-50 border-slate-300 text-slate-900 focus:ring-emerald-600'
            }`}
          >
            <option value="BTC/USDT">BTC/USDT (15m)</option>
            <option value="ETH/USDT">ETH/USDT (15m)</option>
            <option value="SOL/USDT">SOL/USDT (15m)</option>
          </select>

          {/* Mode Switcher Pills (LIVE vs BACKTEST) */}
          <div className={`flex items-center p-0.5 rounded-md border text-[11px] font-bold font-mono ${
            isDark ? 'bg-[#0d1117] border-[#30363d]' : 'bg-slate-100 border-slate-300'
          }`}>
            <button
              onClick={() => setChartMode('LIVE')}
              className={`px-2.5 py-1 rounded transition-colors flex items-center gap-1.5 ${
                chartMode === 'LIVE'
                  ? 'bg-emerald-600 text-white shadow-sm'
                  : isDark ? 'text-slate-400 hover:text-slate-200' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <span className={`w-1.5 h-1.5 rounded-full ${isWsConnected ? 'bg-white animate-pulse' : 'bg-rose-400'}`} />
              LIVE CHART (Binance Stream)
            </button>

            <button
              onClick={() => setChartMode('BACKTEST')}
              className={`px-2.5 py-1 rounded transition-colors flex items-center gap-1.5 ${
                chartMode === 'BACKTEST'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : isDark ? 'text-slate-400 hover:text-slate-200' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              📊 BACKTEST CHART
            </button>

            {/* Position Box Shaded Overlay Toggle */}
            <button
              onClick={() => setShowPositionBox(!showPositionBox)}
              className={`px-2.5 py-1 rounded transition-colors flex items-center gap-1 ml-1 ${
                showPositionBox
                  ? 'bg-indigo-950 text-indigo-300 border border-indigo-700 font-bold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
              title="Toggle Shaded Position Box Overlay"
            >
              {showPositionBox ? '📦 Box Overlay: ON' : '📦 Box Overlay: OFF'}
            </button>
          </div>

          <span className="text-xs text-slate-500 font-mono hidden sm:inline border-l border-slate-700 pl-3">
            Inspecting Strategy: <strong className="text-indigo-400">{selectedStrategy}</strong>
          </span>
        </div>

        {/* Active Open Signal Trade Levels Pill (ONLY WHEN AN OPEN POSITION EXISTS) */}
        {activeTradeLevels ? (
          <div className={`backdrop-blur border px-3.5 py-2 rounded-lg flex items-center gap-4 shadow-lg ${
            isDark ? 'bg-[#161b22]/90 border-[#30363d]' : 'bg-white/90 border-slate-200 shadow'
          }`}>
            <div className="flex items-center gap-1.5">
              <span className="text-slate-400 text-[10px] uppercase font-bold">Entry:</span>
              <span className="text-sky-400 font-bold">${activeTradeLevels.entry.toFixed(0)}</span>
            </div>
            <div className={`h-3 w-[1px] ${isDark ? 'bg-[#30363d]' : 'bg-slate-300'}`} />
            <div className="flex items-center gap-1.5">
              <span className="text-slate-400 text-[10px] uppercase font-bold">Stop Loss (SL):</span>
              <span className="text-rose-400 font-bold">${activeTradeLevels.sl.toFixed(0)}</span>
            </div>
            <div className={`h-3 w-[1px] ${isDark ? 'bg-[#30363d]' : 'bg-slate-300'}`} />
            <div className="flex items-center gap-1.5">
              <span className="text-slate-400 text-[10px] uppercase font-bold">Take Profit (TP):</span>
              <span className="text-emerald-400 font-bold">${activeTradeLevels.tp.toFixed(0)}</span>
            </div>
            <div className={`h-3 w-[1px] ${isDark ? 'bg-[#30363d]' : 'bg-slate-300'}`} />
            <div className="flex items-center gap-1.5">
              <span className="text-slate-400 text-[10px] uppercase font-bold">R : R Ratio:</span>
              <span className="text-indigo-400 font-bold">1 : {activeTradeLevels.rr}</span>
            </div>
          </div>
        ) : (
          <div className="text-[10px] text-slate-500 font-mono flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-slate-500" />
            NO OPEN POSITION (ALL TRADES CLOSED)
          </div>
        )}
      </div>

      {/* SVG Container strictly relative to Chart Canvas */}
      <div ref={chartContainerRef} className="w-full h-full relative">
        {showPositionBox && positionBoxes.length > 0 && (
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

            {positionBoxes.map((box) => (
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
                {/* Labels on Right Side of Position Box */}
                <rect
                  x={box.x + box.width - 64}
                  y={box.yProfitTop + 2}
                  width="60"
                  height="16"
                  rx="3"
                  fill="rgba(38, 166, 154, 0.9)"
                />
                <text
                  x={box.x + box.width - 34}
                  y={box.yProfitTop + 13}
                  fill="#ffffff"
                  fontSize="9"
                  fontWeight="bold"
                  fontFamily="monospace"
                  textAnchor="middle"
                >
                  TP: ${box.tpPrice.toFixed(0)}
                </text>

                <rect
                  x={box.x + box.width - 64}
                  y={box.yLossTop + box.lossHeight - 18}
                  width="60"
                  height="16"
                  rx="3"
                  fill="rgba(239, 83, 80, 0.9)"
                />
                <text
                  x={box.x + box.width - 34}
                  y={box.yLossTop + box.lossHeight - 7}
                  fill="#ffffff"
                  fontSize="9"
                  fontWeight="bold"
                  fontFamily="monospace"
                  textAnchor="middle"
                >
                  SL: ${box.slPrice.toFixed(0)}
                </text>
              </g>
            ))}
          </svg>
        )}
      </div>
    </div>
  );
};

export default ChartCanvas;

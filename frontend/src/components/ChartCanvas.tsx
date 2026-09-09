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
        console.log(`[BinanceLiveWS] Connected to live 15m stream for ${selectedSymbol}`);
        setIsWsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg && msg.e === 'kline' && msg.k) {
            const k = msg.k;
            const updatedCandle = {
              time: Math.floor(k.t / 1000) as Time,
              open: parseFloat(k.o),
              high: parseFloat(k.h),
              low: parseFloat(k.l),
              close: parseFloat(k.c),
              volume: parseFloat(k.v)
            };

            setLastLivePrice(updatedCandle.close);
            if (candleSeriesRef.current) {
              candleSeriesRef.current.update(updatedCandle as any);
            }
          }
        } catch (e) {
          console.error('[BinanceLiveWS] Error parsing tick:', e);
        }
      };

      ws.onerror = (err) => {
        console.warn('[BinanceLiveWS] WebSocket error:', err);
        setIsWsConnected(false);
      };

      ws.onclose = () => {
        setIsWsConnected(false);
      };
    } catch (err) {
      console.error('[BinanceLiveWS] Failed to connect WebSocket:', err);
      setIsWsConnected(false);
    }

    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [chartMode, selectedSymbol]);

  // 3. Trade Markers & Position Boxes logic (when in BACKTEST mode or signal received)

  useEffect(() => {
    if (candles.length === 0) return;
    const minTime = candles[0].time as number;
    const maxTime = candles[candles.length - 1].time as number;

    if (tradeMarkers && tradeMarkers.length > 0) {
      const validMarkers: SeriesMarker<Time>[] = tradeMarkers
        .filter((m) => (m.time as number) >= minTime && (m.time as number) <= maxTime)
        .map((m) => ({
          time: m.time as Time,
          position: m.position,
          color: m.color,
          shape: m.shape,
          text: m.text,
        }));
      setDisplayMarkers(validMarkers);

      const buyMarkers = tradeMarkers.filter((m) => m.stop_loss && m.take_profit && m.entry_price);
      if (buyMarkers.length > 0) {
        const lastBuy = buyMarkers[buyMarkers.length - 1];
        const entry = lastBuy.entry_price;
        const sl = lastBuy.stop_loss;
        const tp = lastBuy.take_profit;
        const risk = Math.abs(entry - sl);
        const reward = Math.abs(tp - entry);
        const rr = risk > 0 ? (reward / risk).toFixed(2) : '0.00';
        setActiveTradeLevels({ entry, sl, tp, rr });
      }
    } else {
      const computed: SeriesMarker<Time>[] = [];
      const cleanName = selectedStrategy.replace('.py', '');
      const wickThresh = cleanName.includes('TrapFade') ? 0.38 : 0.40;
      const stoplossPct = cleanName.includes('TrapFade') ? 0.02 : 0.025;
      const takeprofitPct = cleanName.includes('TrapFade') ? 0.035 : 0.040;
      const maxBars = cleanName.includes('TrapFade') ? 8 : 6;

      let i = 20;
      let lastLevels = null;

      while (i < candles.length - 2) {
        const c = candles[i];
        const totalRange = Math.max(c.high - c.low, 1);
        const lowerWick = (Math.min(c.close, c.open) - c.low) / totalRange;

        if (lowerWick > wickThresh) {
          const entryPrice = c.close;
          const sl = Math.round(entryPrice * (1.0 - stoplossPct));
          const tp = Math.round(entryPrice * (1.0 + takeprofitPct));
          const rr = (takeprofitPct / stoplossPct).toFixed(2);
          lastLevels = { entry: entryPrice, sl, tp, rr };

          if ((c.time as number) >= minTime && (c.time as number) <= maxTime) {
            computed.push({
              time: c.time as Time,
              position: 'belowBar',
              color: '#26a69a',
              shape: 'arrowUp',
              text: `BUY $${(entryPrice / 1000).toFixed(1)}k`,
            });
          }

          const exitIdx = Math.min(i + maxBars, candles.length - 1);
          const exitC = candles[exitIdx];
          const pnl = (((exitC.close - entryPrice) / entryPrice) * 100).toFixed(1);

          if ((exitC.time as number) >= minTime && (exitC.time as number) <= maxTime) {
            computed.push({
              time: exitC.time as Time,
              position: 'aboveBar',
              color: exitC.close >= entryPrice ? '#26a69a' : '#ef5350',
              shape: 'arrowDown',
              text: `EXIT ${pnl}%`,
            });
          }

          i = exitIdx + 1;
        } else {
          i++;
        }
      }

      setDisplayMarkers(computed);
      if (lastLevels) setActiveTradeLevels(lastLevels);
    }
  }, [selectedStrategy, tradeMarkers, candles]);

  // 3. TradingView Position Box Coordinate Resolution (Renders Position Box on Right Edge to Latest Bar)
  const updateBoxCoordinates = () => {
    if (!chartRef.current || !candleSeriesRef.current || candles.length === 0) return;
    const chart = chartRef.current;
    const series = candleSeriesRef.current;

    // Pick current / latest trade for position box
    const targetTrade: TradeDetail | null = tradesDetail.length > 0 ? tradesDetail[tradesDetail.length - 1] : (
      activeTradeLevels ? {
        id: 99,
        entry_time: candles[Math.max(0, candles.length - 30)]?.time || 1788523533,
        entry_price: activeTradeLevels.entry,
        stop_loss: activeTradeLevels.sl,
        take_profit: activeTradeLevels.tp,
        exit_time: candles[candles.length - 1]?.time || 1788555933,
        exit_price: activeTradeLevels.entry * 1.01,
        exit_reason: 'ACTIVE_TRADE',
        pnl_pct: 1.0
      } : null
    );

    if (!targetTrade) {
      setPositionBoxes([]);
      return;
    }

    const x1 = chart.timeScale().timeToCoordinate(targetTrade.entry_time as Time);
    const x2 = chart.timeScale().timeToCoordinate(candles[candles.length - 1].time as Time);
    const yEntry = series.priceToCoordinate(targetTrade.entry_price);
    const ySL = series.priceToCoordinate(targetTrade.stop_loss);
    const yTP = series.priceToCoordinate(targetTrade.take_profit);

    if (yEntry !== null && ySL !== null && yTP !== null) {
      const startX = x1 !== null ? Math.max(x1, 60) : 100;
      const endX = x2 !== null ? Math.max(x2, startX + 50) : startX + 150;
      const width = Math.max(endX - startX, 40);

      const yProfitTop = Math.min(yEntry, yTP);
      const profitHeight = Math.max(Math.abs(yEntry - yTP), 2);

      const yLossTop = Math.min(yEntry, ySL);
      const lossHeight = Math.max(Math.abs(yEntry - ySL), 2);

      setPositionBoxes([
        {
          id: targetTrade.id,
          x: startX,
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
        }
      ]);
    }
  };

  // 4. Initialize Lightweight Chart & Price Lines
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

    // Horizontal Price Lines on Price Scale
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
  }, [tradesDetail, activeTradeLevels, displayMarkers]);

  // 5. Live Signal Handling
  useEffect(() => {
    if (!latestSignal || !candleSeriesRef.current) return;

    const series = candleSeriesRef.current;
    const isBuy = latestSignal.action === 'BUY';

    const liveMarker: SeriesMarker<Time> = {
      time: (latestSignal.time || Math.floor(Date.now() / 1000)) as Time,
      position: isBuy ? 'belowBar' : 'aboveBar',
      color: isBuy ? '#238636' : '#da3633',
      shape: isBuy ? 'arrowUp' : 'arrowDown',
      text: `LIVE ${latestSignal.action}`,
    };

    const minTime = candles[0]?.time as number;
    const maxTime = candles[candles.length - 1]?.time as number;

    const validMarkers = [...displayMarkers, liveMarker]
      .filter((m) => (m.time as number) >= minTime && (m.time as number) <= maxTime)
      .sort((a, b) => (a.time as number) - (b.time as number));

    series.setMarkers(validMarkers);

    if (latestSignal.stop_loss) {
      series.createPriceLine({
        price: latestSignal.stop_loss,
        color: '#ef5350',
        lineWidth: 2,
        lineStyle: 0,
        axisLabelVisible: true,
        title: `LIVE SL: $${latestSignal.stop_loss}`,
      });
    }

    if (latestSignal.take_profit) {
      series.createPriceLine({
        price: latestSignal.take_profit,
        color: '#26a69a',
        lineWidth: 2,
        lineStyle: 0,
        axisLabelVisible: true,
        title: `LIVE TP: $${latestSignal.take_profit}`,
      });
    }
  }, [latestSignal, displayMarkers, candles]);

  return (
    <div className={`w-full h-full relative ${isDark ? 'bg-[#0d1117]' : 'bg-white'}`}>
      {/* Sleek Top Controls Banner: Symbol Selector, Live Stream vs Backtest Mode Toggle */}
      <div className="absolute top-3 left-3 z-20 flex flex-col gap-2 font-mono text-xs select-none">
        <div className={`backdrop-blur border px-3.5 py-2 rounded-lg flex flex-wrap items-center gap-3 shadow-lg ${
          isDark ? 'bg-[#161b22]/90 border-[#30363d] text-[#8b949e]' : 'bg-white/90 border-slate-200 text-slate-700 shadow'
        }`}>
          {/* Symbol Selector Dropdown */}
          <div className="flex items-center gap-2">
            <select
              value={selectedSymbol}
              onChange={(e) => setSelectedSymbol(e.target.value)}
              className={`px-2 py-1 rounded border font-bold text-xs outline-none cursor-pointer transition-colors ${
                isDark ? 'bg-[#0d1117] border-[#30363d] text-white hover:border-emerald-500' : 'bg-slate-50 border-slate-300 text-slate-900'
              }`}
            >
              <option value="BTC/USDT">BTC/USDT (15m)</option>
              <option value="ETH/USDT">ETH/USDT (15m)</option>
              <option value="SOL/USDT">SOL/USDT (15m)</option>
              <option value="BNB/USDT">BNB/USDT (15m)</option>
              <option value="XRP/USDT">XRP/USDT (15m)</option>
            </select>
          </div>

          <div className={`h-4 w-[1px] ${isDark ? 'bg-[#30363d]' : 'bg-slate-300'}`} />

          {/* Mode Switcher Toggle Buttons */}
          <div className="flex items-center p-0.5 rounded border border-slate-700/60 bg-slate-950/60">
            <button
              onClick={() => setChartMode('LIVE')}
              className={`px-2.5 py-1 rounded text-[10px] font-bold flex items-center gap-1.5 transition-all ${
                chartMode === 'LIVE'
                  ? 'bg-emerald-600 text-white shadow'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <span>⚡ LIVE CHART (Binance Stream)</span>
            </button>

            <button
              onClick={() => setChartMode('BACKTEST')}
              className={`px-2.5 py-1 rounded text-[10px] font-bold flex items-center gap-1.5 transition-all ${
                chartMode === 'BACKTEST'
                  ? 'bg-indigo-600 text-white shadow'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <span>📊 BACKTEST CHART</span>
            </button>
          </div>

          <div className={`h-4 w-[1px] ${isDark ? 'bg-[#30363d]' : 'bg-slate-300'}`} />

          {/* Live Status & Ticker Badge */}
          {chartMode === 'LIVE' ? (
            <div className="flex items-center gap-2">
              <span className={`px-2 py-0.5 rounded text-[10px] font-bold flex items-center gap-1 border ${
                isWsConnected
                  ? 'bg-emerald-950/90 text-emerald-400 border-emerald-600'
                  : 'bg-amber-950/90 text-amber-400 border-amber-600'
              }`}>
                <span className={`w-2 h-2 rounded-full ${isWsConnected ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`} />
                {isWsConnected ? 'LIVE BINANCE WS' : 'CONNECTING WS...'}
              </span>
              {lastLivePrice && (
                <span className="text-emerald-400 font-bold text-xs font-mono">
                  ${lastLivePrice.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                </span>
              )}
            </div>
          ) : (
            <div className="flex items-center gap-1.5 text-xs">
              <span className="text-slate-400">Inspecting Strategy:</span>
              <span className="text-amber-400 font-bold">{selectedStrategy}</span>
            </div>
          )}
        </div>


        {activeTradeLevels && (
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
        )}
      </div>

      {/* SVG Overlay: Native TradingView Position Box (Shaded Green Profit & Red Loss Zones) */}
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

      <div ref={chartContainerRef} className="w-full h-full" />
    </div>
  );
};

export default ChartCanvas;

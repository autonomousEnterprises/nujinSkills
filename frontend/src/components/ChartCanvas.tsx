import React, { useEffect, useRef, useState } from 'react';
import { createChart, ColorType, IChartApi, ISeriesApi, SeriesMarker, Time } from 'lightweight-charts';
import { SignalData } from '../hooks/useWebSocket';

interface ChartCanvasProps {
  latestSignal: SignalData | null;
  theme?: 'dark' | 'light';
  selectedStrategy?: string;
  tradeMarkers?: any[];
  activeStrategy?: string;
}

export const ChartCanvas: React.FC<ChartCanvasProps> = ({
  latestSignal,
  theme = 'dark',
  selectedStrategy = 'PropFirmVsaWickRejection.py',
  tradeMarkers = [],
  activeStrategy = 'PropFirmVsaWickRejection'
}) => {
  const isDark = theme === 'dark';
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const [candles, setCandles] = useState<any[]>([]);
  const [displayMarkers, setDisplayMarkers] = useState<SeriesMarker<Time>[]>([]);

  // 1. Fetch Candle Data
  useEffect(() => {
    fetch('/api/candles?count=200')
      .then((res) => res.json())
      .then((data) => {
        if (data.data) {
          setCandles(data.data);
        }
      })
      .catch((err) => {
        console.log('Failed to fetch candles from API:', err);
      });
  }, []);

  // 2. Compute or Sync Backtest Trade Markers for selectedStrategy
  useEffect(() => {
    if (tradeMarkers && tradeMarkers.length > 0) {
      const formatted: SeriesMarker<Time>[] = tradeMarkers.map((m) => ({
        time: m.time as Time,
        position: m.position,
        color: m.color,
        shape: m.shape,
        text: m.text,
      }));
      setDisplayMarkers(formatted);
    } else if (candles.length > 0) {
      // Fallback dynamic computation based on selected strategy
      const computed: SeriesMarker<Time>[] = [];
      const cleanName = selectedStrategy.replace('.py', '');
      const step = cleanName.includes('TrapFade') ? 9 : 13;
      const wickThresh = cleanName.includes('TrapFade') ? 0.38 : 0.40;

      candles.forEach((c: any, idx: number) => {
        const totalRange = Math.max(c.high - c.low, 1);
        const lowerWick = (Math.min(c.close, c.open) - c.low) / totalRange;

        if (idx > 20 && lowerWick > wickThresh && idx % step === 0) {
          computed.push({
            time: c.time as Time,
            position: 'belowBar',
            color: '#26a69a',
            shape: 'arrowUp',
            text: `BUY @ ${c.close.toFixed(0)}`,
          });

          const exitIdx = Math.min(idx + 5, candles.length - 1);
          if (exitIdx > idx) {
            computed.push({
              time: candles[exitIdx].time as Time,
              position: 'aboveBar',
              color: '#ef5350',
              shape: 'arrowDown',
              text: `EXIT @ ${candles[exitIdx].close.toFixed(0)}`,
            });
          }
        }
      });
      setDisplayMarkers(computed);
    }
  }, [selectedStrategy, tradeMarkers, candles]);

  // 3. Initialize Lightweight Chart with Light/Dark Theme Support
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

    chart.timeScale().fitContent();

    chartRef.current = chart;
    candleSeriesRef.current = candleSeries;

    const resizeObserver = new ResizeObserver(() => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
          height: chartContainerRef.current.clientHeight,
        });
      }
    });

    resizeObserver.observe(chartContainerRef.current);

    return () => {
      resizeObserver.disconnect();
      chart.remove();
    };
  }, [candles, displayMarkers, isDark]);

  // 4. Render Live Signals & Combine with Backtest Markers
  useEffect(() => {
    if (!latestSignal || !candleSeriesRef.current) return;

    const series = candleSeriesRef.current;
    const isBuy = latestSignal.action === 'BUY';

    const liveMarker: SeriesMarker<Time> = {
      time: (latestSignal.time || Math.floor(Date.now() / 1000)) as Time,
      position: isBuy ? 'belowBar' : 'aboveBar',
      color: isBuy ? '#238636' : '#da3633',
      shape: isBuy ? 'arrowUp' : 'arrowDown',
      text: `LIVE SIGNAL ${latestSignal.action}: ${latestSignal.annotation || activeStrategy}`,
    };

    const combined = [...displayMarkers, liveMarker].sort((a, b) => (a.time as number) - (b.time as number));
    series.setMarkers(combined);

    if (latestSignal.stop_loss) {
      series.createPriceLine({
        price: latestSignal.stop_loss,
        color: '#ef5350',
        lineWidth: 1,
        lineStyle: 2,
        axisLabelVisible: true,
        title: 'SL Invalidation',
      });
    }

    if (latestSignal.take_profit) {
      series.createPriceLine({
        price: latestSignal.take_profit,
        color: '#26a69a',
        lineWidth: 1,
        lineStyle: 2,
        axisLabelVisible: true,
        title: 'TP Target',
      });
    }
  }, [latestSignal, displayMarkers, activeStrategy]);

  return (
    <div className={`w-full h-full relative ${isDark ? 'bg-[#0d1117]' : 'bg-white'}`}>
      {/* Dynamic Top Information Bar */}
      <div className={`absolute top-3 left-3 z-10 backdrop-blur border px-3 py-1.5 rounded font-mono text-xs flex flex-wrap items-center gap-3 ${
        isDark ? 'bg-[#161b22]/90 border-[#30363d] text-[#8b949e]' : 'bg-slate-50/90 border-slate-200 text-slate-600 shadow-sm'
      }`}>
        <div>
          <span className={`${isDark ? 'text-white' : 'text-slate-900'} font-bold`}>BTC/USDT</span> • 15m Timeframe
        </div>
        <div className={`h-3 w-[1px] ${isDark ? 'bg-[#30363d]' : 'bg-slate-300'}`} />
        <div className="flex items-center gap-1.5">
          <span className="text-slate-400">Inspecting:</span>
          <span className="text-amber-400 font-bold">{selectedStrategy}</span>
        </div>
        <div className={`h-3 w-[1px] ${isDark ? 'bg-[#30363d]' : 'bg-slate-300'}`} />
        <div className="text-emerald-500 font-semibold flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span>{displayMarkers.length} Backtest Trades Plotted</span>
        </div>
        <div className={`h-3 w-[1px] ${isDark ? 'bg-[#30363d]' : 'bg-slate-300'}`} />
        <div className="flex items-center gap-1.5">
          <span className="text-slate-400">System Active:</span>
          <span className="px-2 py-0.5 rounded bg-emerald-950/80 border border-emerald-700 text-emerald-400 text-[10px] font-bold">
            {activeStrategy}
          </span>
        </div>
      </div>
      <div ref={chartContainerRef} className="w-full h-full" />
    </div>
  );
};

export default ChartCanvas;

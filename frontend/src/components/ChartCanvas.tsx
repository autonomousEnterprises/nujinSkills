import React, { useEffect, useRef, useState } from 'react';
import { createChart, ColorType, IChartApi, ISeriesApi, SeriesMarker, Time } from 'lightweight-charts';
import { SignalData } from '../hooks/useWebSocket';

interface ChartCanvasProps {
  latestSignal: SignalData | null;
}

export const ChartCanvas: React.FC<ChartCanvasProps> = ({ latestSignal }) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const [candles, setCandles] = useState<any[]>([]);

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
        console.log('Failed to fetch candles from API, using client fallback:', err);
        const now = Math.floor(Date.now() / 1000) - 200 * 900;
        const fallback = [];
        let price = 64000;
        for (let i = 0; i < 200; i++) {
          const change = (Math.random() - 0.49) * 150;
          const open = price;
          const close = open + change;
          fallback.push({
            time: (now + i * 900) as Time,
            open: Math.round(open),
            high: Math.round(Math.max(open, close) + Math.random() * 50),
            low: Math.round(Math.min(open, close) - Math.random() * 50),
            close: Math.round(close),
          });
          price = close;
        }
        setCandles(fallback);
      });
  }, []);

  // 2. Initialize Lightweight Chart
  useEffect(() => {
    if (!chartContainerRef.current || candles.length === 0) return;

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: '#0d1117' },
        textColor: '#8b949e',
        fontFamily: 'JetBrains Mono, monospace',
      },
      grid: {
        vertLines: { color: '#161b22' },
        horzLines: { color: '#161b22' },
      },
      crosshair: {
        vertLine: { color: '#30363d' },
        horzLine: { color: '#30363d' },
      },
      timeScale: {
        timeVisible: true,
        secondsVisible: false,
        borderColor: '#30363d',
      },
      rightPriceScale: {
        borderColor: '#30363d',
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
  }, [candles]);

  // 3. Render Agent Signal Markers & Price Lines
  useEffect(() => {
    if (!latestSignal || !candleSeriesRef.current) return;

    const series = candleSeriesRef.current;
    const isBuy = latestSignal.action === 'BUY';

    // Add Entry Marker using lightweight-charts setMarkers API
    const marker: SeriesMarker<Time> = {
      time: (latestSignal.time || Math.floor(Date.now() / 1000)) as Time,
      position: isBuy ? 'belowBar' : 'aboveBar',
      color: isBuy ? '#26a69a' : '#ef5350',
      shape: isBuy ? 'arrowUp' : 'arrowDown',
      text: `${latestSignal.action}: ${latestSignal.annotation}`,
    };

    series.setMarkers([marker]);

    // Draw Stop Loss Line
    if (latestSignal.stop_loss) {
      series.createPriceLine({
        price: latestSignal.stop_loss,
        color: '#ef5350',
        lineWidth: 1,
        lineStyle: 2, // Dashed
        axisLabelVisible: true,
        title: 'SL (Invalidation)',
      });
    }

    // Draw Take Profit Line
    if (latestSignal.take_profit) {
      series.createPriceLine({
        price: latestSignal.take_profit,
        color: '#26a69a',
        lineWidth: 1,
        lineStyle: 2, // Dashed
        axisLabelVisible: true,
        title: 'TP (AI Target)',
      });
    }
  }, [latestSignal]);

  return (
    <div className="w-full h-full relative bg-[#0d1117]">
      <div className="absolute top-3 left-3 z-10 bg-[#161b22]/90 backdrop-blur border border-[#30363d] px-3 py-1.5 rounded font-mono text-xs text-[#8b949e]">
        <span className="text-white font-bold">BTC/USDT</span> • 15m Timeframe • TradingView Lightweight Canvas
      </div>
      <div ref={chartContainerRef} className="w-full h-full" />
    </div>
  );
};

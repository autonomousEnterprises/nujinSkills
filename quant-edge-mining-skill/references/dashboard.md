TradingView Lightweight Charts is an ideal choice for this setup: it is completely free, open-source (Apache 2.0), under 45 KB, and renders via HTML5 Canvas with native support for high-frequency tick streams, series markers, and price lines.

To make the AI agent capable of communicating visually on the chart alongside its Telegram feed, you need a decoupled **Event-Driven Architecture** where the agent emits structured state payloads that both Telegram and the web UI consume.

---

### System Architecture: The Dual-Output Bus

```
           [ AI Strategy / Edge Engine ]
                        │
         Dispatches Structured JSON Event
                        │
         ┌──────────────┴──────────────┐
         ▼                             ▼
┌──────────────────┐         ┌──────────────────┐
│  Telegram Relay  │         │  FastAPI / WS    │
│  (Human Alerts)  │         │  Backend Server  │
└──────────────────┘         └─────────┬────────┘
                                       │ WebSocket
                                       ▼
                             ┌──────────────────┐
                             │ Next.js / React  │
                             │ Lightweight Chart│
                             └──────────────────┘

```

When the AI discovers an edge or triggers an entry/exit, it emits a single normalized payload:

```json
{
  "event": "SIGNAL_TRIGGERED",
  "pair": "BTC/USDT",
  "time": 1773295200,
  "action": "BUY",
  "price": 64250.0,
  "stop_loss": 63400.0,
  "take_profit": 65950.0,
  "annotation": "Absorption Sweep (Hurst < 0.42, Wick > 60%)",
  "reasoning_md": "**Counterparty Trap**: Breakout buyers absorbed at resistance."
}

```

* **Telegram Gateway:** Formats the markdown into a mobile push alert.
* **Web UI (Lightweight Charts):** Ingests the same payload over a WebSocket and renders a native series marker with dynamic stop/target lines.

---

### Frontend Implementation: Lightweight Charts + Dynamic Signals

Below is a complete, production-ready React / TypeScript component showing how to initialize the candlestick series, stream candle updates, and project entry markers, target price lines, and stop-loss levels onto the chart.

```tsx
import React, { useEffect, useRef } from 'react';
import { 
  createChart, 
  ColorType, 
  IChartApi, 
  ISeriesApi, 
  CandlestickSeries, 
  createSeriesMarkers 
} from 'lightweight-charts';

interface SignalPayload {
  time: number; // Unix timestamp in seconds
  action: 'BUY' | 'SELL';
  price: number;
  stop_loss: number;
  take_profit: number;
  annotation: string;
}

export const AgentTradingChart: React.FC<{ ohlcvData: any[]; latestSignal?: SignalPayload }> = ({
  ohlcvData,
  latestSignal,
}) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    // 1. Initialize Chart
    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: '#0d1117' },
        textColor: '#8b949e',
      },
      grid: {
        vertLines: { color: '#161b22' },
        horzLines: { color: '#161b22' },
      },
      timeScale: {
        timeVisible: true,
        secondsVisible: false,
      },
    });

    // 2. Add Candlestick Series
    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderVisible: false,
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350',
    });

    candleSeries.setData(ohlcvData);
    chart.timeScale().fitContent();

    chartRef.current = chart;
    candleSeriesRef.current = candleSeries;

    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, []);

  // 3. Render Agent Signals, Targets, and Markers
  useEffect(() => {
    if (!latestSignal || !candleSeriesRef.current) return;

    const series = candleSeriesRef.current;

    // Add entry arrow marker on the specific candle
    createSeriesMarkers(series, [
      {
        time: latestSignal.time as any,
        position: latestSignal.action === 'BUY' ? 'belowBar' : 'aboveBar',
        color: latestSignal.action === 'BUY' ? '#26a69a' : '#ef5350',
        shape: latestSignal.action === 'BUY' ? 'arrowUp' : 'arrowDown',
        text: `${latestSignal.action}: ${latestSignal.annotation}`,
      },
    ]);

    // Draw Take-Profit & Stop-Loss horizontal lines
    series.createPriceLine({
      price: latestSignal.take_profit,
      color: '#26a69a',
      lineWidth: 1,
      lineStyle: 2, // Dashed
      axisLabelVisible: true,
      title: 'TP (AI Target)',
    });

    series.createPriceLine({
      price: latestSignal.stop_loss,
      color: '#ef5350',
      lineWidth: 1,
      lineStyle: 2, // Dashed
      axisLabelVisible: true,
      title: 'SL (Invalidation)',
    });
  }, [latestSignal]);

  return <div ref={chartContainerRef} style={{ width: '100%', height: '550px' }} />;
};

```

---

### How the Agent Reports Visually

To make the AI agent treat the chart as an active visualization surface rather than just an afterthought, add a dedicated tool to its skill definition:

* **`plot_strategy_insight(event_type, time, price, annotations, levels)`**:
* The agent calls this tool when it wants to visually emphasize a market structure—such as marking an **FVG (Fair Value Gap)**, highlighting an **absorption sweep**, or showing where the trailing stop just shifted.
* Instead of generating an image file (which is static and heavy), the agent outputs coordinates and metadata that Lightweight Charts renders as native canvas lines, markers, or shaded bands.

The AI can create any visualisation tools depending on the current mining. 



---

### Dashboard Layout Suggestion

A cohesive terminal layout pairs the visual canvas with the agent's analytical audit trail:

both charts and the stream has screen witdh and height, but swappable from one screen to another. so I hav fullscren the chart with indicators etc, and in the other screen the report. 
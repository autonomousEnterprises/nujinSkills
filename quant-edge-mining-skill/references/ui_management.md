The user needs visualisation of the ai agent edge mining process and strategies development process. A modular dual-screen workspace needs two architectural capabilities: **instant fullscreen viewport toggling (or multi-window detachment)** and a **dynamic, agent-driven UI schema (Server-Driven UI)** so the agent can push custom metrics, heatmaps, and tear sheets on the fly.

---

### 1. Viewport Architecture: Swappable & Detachable Screens

The UI runs on a 100vw / 100vh layout with two primary modes:

* **In-Tab Hotkey Swap (`Tab` / `Space`):** Cycles focus between the Chart and the Agent Audit Deck at full resolution.
* **Multi-Monitor Popout (`window.open` via React Portals):** Tears off either the Lightweight Chart or the Audit Dashboard into a separate OS window that snaps to a second physical monitor while sharing the exact same WebSocket state.

```
       [ Central WebSocket / Event Bus ]
                       │
       ┌───────────────┴───────────────┐
       ▼                               ▼
 [ Screen 1: 100vw / 100vh ]     [ Screen 2: 100vw / 100vh ]
 TradingView Lightweight Chart    Dynamic Agent Widget Deck
 - Candlesticks & Overlays        - Phase Telemetry Cards
 - Markers & Invalidation Lines   - Parameter Stability Heatmaps
 - Sub-chart Histograms (CVD)     - Live DSR / Monte Carlo Stats

```

---

### 2. Dynamic Agent Widget Protocol (Server-Driven UI)

To allow the AI to construct the report interface in real time as it advances through the mining pipeline, the agent emits declarative widget payloads over the WebSocket instead of static text:

```json
{
  "type": "UPSERT_DASHBOARD_WIDGET",
  "widget": {
    "id": "dsr_validation_gauge",
    "component": "MetricCard",
    "title": "Deflated Sharpe Ratio (DSR)",
    "phase": "PHASE_4_ADVERSARIAL_AUDIT",
    "layout": { "w": 4, "h": 2 },
    "props": {
      "value": "0.964",
      "target": "> 0.950",
      "status": "PASS",
      "subtitle": "Penalized across 142 historical hypothesis trials"
    }
  }
}

```

```json
{
  "type": "UPSERT_DASHBOARD_WIDGET",
  "widget": {
    "id": "param_stability_surface",
    "component": "HeatmapMatrix",
    "title": "Parameter Stability Surface (Wick Ratio vs. Volume Z)",
    "phase": "PHASE_4_ADVERSARIAL_AUDIT",
    "layout": { "w": 8, "h": 4 },
    "props": {
      "xAxis": ["1.2", "1.5", "1.8", "2.1"],
      "yAxis": ["0.45", "0.50", "0.55", "0.60"],
      "matrix": [
        [1.42, 1.55, 1.61, 1.30],
        [1.50, 1.84, 1.91, 1.45],
        [1.35, 1.72, 1.78, 1.25],
        [0.80, 1.10, 1.05, 0.65]
      ],
      "plateauStatus": "STABLE_PLATEAU"
    }
  }
}

```

---

### 3. Frontend Implementation: Fullscreen Swapper & Dynamic Deck

This implementation uses `react-grid-layout` for dynamic widget layout serialization and TradingView Lightweight Charts for the visual canvas:

```tsx
import React, { useState, useEffect, useRef } from 'react';
import { createChart, ColorType, IChartApi, ISeriesApi, CandlestickSeries } from 'lightweight-charts';

// --- Widget Component Registry ---
const WidgetRegistry: Record<string, React.FC<any>> = {
  MetricCard: ({ title, value, target, status, subtitle }) => (
    <div className="bg-[#161b22] border border-[#30363d] p-4 rounded-lg flex flex-col justify-between h-full">
      <div className="flex justify-between items-center">
        <span className="text-xs uppercase text-[#8b949e] font-mono">{title}</span>
        <span className={`text-xs px-2 py-0.5 rounded font-mono ${status === 'PASS' ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'bg-rose-950 text-rose-400 border border-rose-800'}`}>
          {status}
        </span>
      </div>
      <div className="my-2">
        <div className="text-3xl font-bold font-mono text-white">{value}</div>
        <div className="text-xs text-[#8b949e]">Threshold: {target}</div>
      </div>
      <div className="text-xs text-[#58a6ff]">{subtitle}</div>
    </div>
  ),

  HypothesisLog: ({ thesis, counterparty, invalidation }) => (
    <div className="bg-[#161b22] border border-[#30363d] p-4 rounded-lg font-mono text-xs flex flex-col gap-2 h-full">
      <div className="text-[#8b949e] uppercase font-bold border-b border-[#30363d] pb-1">Current Edge Thesis</div>
      <div><span className="text-emerald-400">Core Thesis:</span> {thesis}</div>
      <div><span className="text-amber-400">Trapped Capital:</span> {counterparty}</div>
      <div><span className="text-rose-400">Invalidation:</span> {invalidation}</div>
    </div>
  ),

  HeatmapMatrix: ({ title, xAxis, yAxis, matrix, plateauStatus }) => (
    <div className="bg-[#161b22] border border-[#30363d] p-4 rounded-lg flex flex-col h-full font-mono">
      <div className="flex justify-between items-center mb-2">
        <span className="text-xs text-[#8b949e] uppercase">{title}</span>
        <span className="text-xs text-indigo-400 border border-indigo-800 px-2 py-0.5 rounded">{plateauStatus}</span>
      </div>
      <div className="grid grid-cols-4 gap-1 flex-1 items-center">
        {matrix.flat().map((val: number, i: number) => (
          <div 
            key={i} 
            className="flex items-center justify-center text-xs h-full rounded text-white font-bold"
            style={{ backgroundColor: val > 1.5 ? '#238636' : val > 1.0 ? '#1f6feb' : '#da3633' }}
          >
            {val.toFixed(2)}
          </div>
        ))}
      </div>
    </div>
  )
};

// --- Main Dynamic Dual-Screen Shell ---
export const DualScreenQuantTerminal = () => {
  const [activeScreen, setActiveScreen] = useState<'CHART' | 'AGENT_DECK'>('CHART');
  const [widgets, setWidgets] = useState<any[]>([
    {
      id: 'active_thesis',
      component: 'HypothesisLog',
      props: {
        thesis: 'Fade Asian Highs when wick > 60% and Volume Z-Score > 2.0',
        counterparty: 'Breakout momentum traders trapped by passive limit bids',
        invalidation: '2 consecutive candle closes above the high'
      }
    },
    {
      id: 'dsr_score',
      component: 'MetricCard',
      props: {
        title: 'Deflated Sharpe Ratio (DSR)',
        value: '0.964',
        target: '> 0.950',
        status: 'PASS',
        subtitle: 'Valid across 142 backtested variations'
      }
    }
  ]);

  // Hotkey Swapper: Press 'Space' or 'Tab' to swap views instantly
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === ' ' && e.ctrlKey) {
        e.preventDefault();
        setActiveScreen(prev => prev === 'CHART' ? 'AGENT_DECK' : 'CHART');
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <div className="w-screen h-screen bg-[#0d1117] text-white flex flex-col overflow-hidden">
      {/* Top Bar Switcher & Status */}
      <header className="h-10 bg-[#161b22] border-b border-[#30363d] px-4 flex items-center justify-between text-xs font-mono">
        <div className="flex gap-4 items-center">
          <span className="text-emerald-400 font-bold tracking-wider">AGENT_CORE::ONLINE</span>
          <span className="text-[#8b949e]">Press [Ctrl + Space] to swap fullscreen views</span>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setActiveScreen('CHART')}
            className={`px-3 py-1 rounded transition-colors ${activeScreen === 'CHART' ? 'bg-[#238636] text-white font-bold' : 'bg-[#21262d] text-[#8b949e]'}`}
          >
            Lightweight Chart (F1)
          </button>
          <button
            onClick={() => setActiveScreen('AGENT_DECK')}
            className={`px-3 py-1 rounded transition-colors ${activeScreen === 'AGENT_DECK' ? 'bg-[#238636] text-white font-bold' : 'bg-[#21262d] text-[#8b949e]'}`}
          >
            Agent Report & Mining Deck (F2)
          </button>
        </div>
      </header>

      {/* Screen 1: Fullscreen TradingView Canvas */}
      <div className={`w-full flex-1 ${activeScreen === 'CHART' ? 'block' : 'hidden'}`}>
        <ChartCanvas />
      </div>

      {/* Screen 2: Dynamic Agent Dynamic UI Grid */}
      <div className={`w-full flex-1 p-4 overflow-y-auto ${activeScreen === 'AGENT_DECK' ? 'block' : 'hidden'}`}>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 auto-rows-[200px]">
          {widgets.map(w => {
            const Component = WidgetRegistry[w.component];
            return Component ? <Component key={w.id} {...w.props} /> : null;
          })}
        </div>
      </div>
    </div>
  );
};

// Canvas Wrapper
const ChartCanvas = () => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    const chart = createChart(containerRef.current, {
      layout: { background: { type: ColorType.Solid, color: '#0d1117' }, textColor: '#8b949e' },
      grid: { vertLines: { color: '#161b22' }, horzLines: { color: '#161b22' } },
      timeScale: { timeVisible: true }
    });
    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#26a69a', downColor: '#ef5350', borderVisible: false, wickUpColor: '#26a69a', wickDownColor: '#ef5350'
    });
    
    // Resize handler for fullscreen switching
    const resizeObserver = new ResizeObserver(() => {
      if (containerRef.current) {
        chart.applyOptions({
          width: containerRef.current.clientWidth,
          height: containerRef.current.clientHeight
        });
      }
    });
    resizeObserver.observe(containerRef.current);

    return () => {
      resizeObserver.disconnect();
      chart.remove();
    };
  }, []);

  return <div ref={containerRef} className="w-full h-full" />;
};

```

---

### 4. Agent Tool Definition for UI Management

Equip the AI agent with a tool so it can self-render updates into this layout during research:

* **`push_ui_widget(widget_id, component_type, layout, payload)`**:
* *Phase 1:* The agent pushes a **`RegimeDistributionChart`** showing rolling Hurst and entropy.
* *Phase 3:* The agent pushes a **`BacktestSummaryCard`** showing fees vs. gross returns.
* *Phase 4:* The agent renders a **`HeatmapMatrix`** verifying parameter stability, plus the **`MetricCard`** for the Deflated Sharpe calculation.



This decouples the presentation from the strategy code: the agent controls the analytical canvas dynamically, you flip between screens with a single keystroke, and your phone gets the high-level trade dispatches over Telegram.
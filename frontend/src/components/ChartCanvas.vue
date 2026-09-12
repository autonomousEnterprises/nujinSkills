<template>
  <div class="relative w-full h-full flex flex-col font-mono select-none overflow-hidden bg-base-100">
    <!-- Top Bar: Strategy Selector, Trades/Jumps Navigator, Live Price -->
    <ChartTopBar
      :strategies="strategies"
      :cleanStrategyName="cleanStrategyName"
      :selectedStrategy="selectedStrategy"
      :activeStrategy="activeStrategy"
      :isGoldStrategy="isGoldStrategy"
      :allInspectableSignals="allInspectableSignals"
      :selectedSignalIndex="selectedSignalIndex"
      :inspectedSignal="inspectedSignal"
      :hasActiveLiveTrade="hasActiveLiveTrade"
      :lastLivePrice="lastLivePrice"
      :priceFlash="priceFlash"
      :isWsConnected="isWsConnected"
      @selectStrategy="emit('selectStrategy', $event)"
      @prevJump="prevJump"
      @nextJump="nextJump"
      @jumpToIndex="jumpToIndex"
      @jumpToLatest="jumpToLatest"
      @jumpToActive="jumpToActive"
    />

    <!-- Indicator & Trade Coordinates HUD Bar -->
    <ChartHudBar
      :legendData="legendData"
      :inspectedSignal="inspectedSignal"
      :selectedSignalIndex="selectedSignalIndex"
      :tradeRiskReward="tradeRiskReward"
      :isGoldStrategy="isGoldStrategy"
    />

    <!-- ── Lightweight Charts Main Canvas Container ── -->
    <div class="relative flex-1 w-full h-full overflow-hidden" ref="chartContainerRef">
      <!-- Loading indicator -->
      <div v-if="loadingCandles" class="absolute inset-0 flex items-center justify-center bg-base-100/70 backdrop-blur-xs z-30">
        <div class="flex items-center gap-2 text-primary font-bold text-xs bg-base-300 px-4 py-2 rounded-box border border-base-content/10 shadow-xl">
          <span class="loading loading-spinner loading-sm" />
          <span>SYNCING_HIGH_FREQUENCY_CANDLES...</span>
        </div>
      </div>

      <!-- ── Dynamic Trade Boxes for SL, Entry & TP (Precision Placed SVG Overlay) ── -->
      <svg v-if="positionBoxes.length > 0" class="absolute inset-0 w-full h-full pointer-events-none z-10 overflow-hidden">
        <defs>
          <linearGradient id="profitGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#26a69a" stop-opacity="0.25" />
            <stop offset="100%" stop-color="#26a69a" stop-opacity="0.08" />
          </linearGradient>
          <linearGradient id="lossGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#ef5350" stop-opacity="0.08" />
            <stop offset="100%" stop-color="#ef5350" stop-opacity="0.25" />
          </linearGradient>
        </defs>

        <g v-for="box in positionBoxes" :key="box.id">
          <!-- Green Profit Zone Box -->
          <rect
            :x="box.x"
            :y="box.yProfitTop"
            :width="box.width"
            :height="box.profitHeight"
            fill="url(#profitGrad)"
            stroke="#26a69a"
            stroke-width="1.5"
            stroke-dasharray="4 2"
          />
          <!-- Red Loss Zone Box -->
          <rect
            :x="box.x"
            :y="box.yLossTop"
            :width="box.width"
            :height="box.lossHeight"
            fill="url(#lossGrad)"
            stroke="#ef5350"
            stroke-width="1.5"
            stroke-dasharray="4 2"
          />
          <!-- Entry Price Line -->
          <line
            :x1="box.x"
            :y1="box.yEntry"
            :x2="box.x + box.width"
            :y2="box.yEntry"
            stroke="#38bdf8"
            stroke-width="1.5"
            stroke-dasharray="3 3"
          />

          <!-- Entry Price Pill Label -->
          <rect
            :x="getLabelX(box)"
            :y="getClampedY(box.yEntry - 8)"
            width="78"
            height="17"
            rx="3"
            fill="rgba(56, 189, 248, 0.92)"
          />
          <text
            :x="getLabelX(box) + 39"
            :y="getClampedY(box.yEntry - 8) + 12"
            fill="#041829"
            font-size="9"
            font-weight="bold"
            font-family="monospace"
            text-anchor="middle"
          >
            ENTRY: ${{ formatPrice(box.entryPrice) }}
          </text>

          <!-- TP Pill Label -->
          <rect
            :x="getLabelX(box)"
            :y="getClampedY(box.isLong ? box.yProfitTop + 2 : box.yProfitTop + box.profitHeight - 19)"
            width="78"
            height="17"
            rx="3"
            fill="rgba(38, 166, 154, 0.92)"
          />
          <text
            :x="getLabelX(box) + 39"
            :y="getClampedY(box.isLong ? box.yProfitTop + 2 : box.yProfitTop + box.profitHeight - 19) + 12"
            fill="#ffffff"
            font-size="9"
            font-weight="bold"
            font-family="monospace"
            text-anchor="middle"
          >
            TP: ${{ formatPrice(box.tpPrice) }}
          </text>

          <!-- SL Pill Label -->
          <rect
            :x="getLabelX(box)"
            :y="getClampedY(box.isLong ? box.yLossTop + box.lossHeight - 19 : box.yLossTop + 2)"
            width="78"
            height="17"
            rx="3"
            fill="rgba(239, 83, 80, 0.92)"
          />
          <text
            :x="getLabelX(box) + 39"
            :y="getClampedY(box.isLong ? box.yLossTop + box.lossHeight - 19 : box.yLossTop + 2) + 12"
            fill="#ffffff"
            font-size="9"
            font-weight="bold"
            font-family="monospace"
            text-anchor="middle"
          >
            SL: ${{ formatPrice(box.slPrice) }}
          </text>
        </g>
      </svg>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue';
import { createChart, ColorType, type IChartApi, type ISeriesApi, type Time } from 'lightweight-charts';
import ChartTopBar from './chart/ChartTopBar.vue';
import ChartHudBar from './chart/ChartHudBar.vue';
import { calculateEMA, calculateBollingerBands, calculateHHLL } from '../utils/indicators';
import { formatPrice as formatPriceUtil } from '../utils/formatters';
import type { SignalData, InspectableSignal, PositionBoxCoord, TradeDetail } from '../types';

interface StrategyItem {
  name: string;
  path?: string;
  size_bytes?: number;
  last_modified?: number;
  [key: string]: any;
}

const props = withDefaults(
  defineProps<{
    latestSignal?: SignalData | null;
    signals?: SignalData[];
    theme?: 'dark' | 'light';
    selectedStrategy?: string;
    tradeMarkers?: any[];
    tradesDetail?: TradeDetail[];
    activeStrategy?: string;
    strategies?: StrategyItem[];
  }>(),
  {
    theme: 'dark',
    selectedStrategy: 'GoatFundedTraderXauusdScalper.py',
    tradeMarkers: () => [],
    tradesDetail: () => [],
    strategies: () => [],
  }
);

const emit = defineEmits<{
  (e: 'selectStrategy', stratName: string): void;
}>();

function timeToLocal(originalTime: number): number {
  if (!originalTime) return 0;
  const d = new Date(originalTime * 1000);
  return (
    Date.UTC(
      d.getFullYear(),
      d.getMonth(),
      d.getDate(),
      d.getHours(),
      d.getMinutes(),
      d.getSeconds(),
      d.getMilliseconds()
    ) / 1000
  );
}

// ── State Variables ──
const chartContainerRef = ref<HTMLDivElement | null>(null);
let chart: IChartApi | null = null;
let candleSeries: ISeriesApi<'Candlestick'> | null = null;
let volumeSeries: ISeriesApi<'Histogram'> | null = null;
let ema9Series: ISeriesApi<'Line'> | null = null;
let ema21Series: ISeriesApi<'Line'> | null = null;
let ema200Series: ISeriesApi<'Line'> | null = null;
let bbUpperSeries: ISeriesApi<'Line'> | null = null;
let bbLowerSeries: ISeriesApi<'Line'> | null = null;
let hhSeries: ISeriesApi<'Line'> | null = null;
let llSeries: ISeriesApi<'Line'> | null = null;

const cleanStrategyName = computed(() => (props.selectedStrategy || props.activeStrategy || 'GoatFundedTraderXauusdScalper').replace('.py', ''));
const isGoldStrategy = computed(() => cleanStrategyName.value.toLowerCase().includes('xau') || cleanStrategyName.value.toLowerCase().includes('gold'));

const formatPrice = (p: number | undefined | null) => {
  if (p == null || isNaN(p)) return '–';
  return isGoldStrategy.value ? p.toFixed(2) : p.toFixed(1);
};

const selectedSymbol = ref(isGoldStrategy.value ? 'XAU/USD' : 'BTC/USDT');
const isWsConnected = ref(false);
const lastLivePrice = ref<number | null>(null);
const priceFlash = ref<'up' | 'down' | null>(null);
const loadingCandles = ref(false);

const legendData = ref<Record<string, any>>({});
const rawCandles = ref<any[]>([]);
const positionBoxes = ref<PositionBoxCoord[]>([]);

let binanceWs: WebSocket | null = null;
let oandaTimer: any = null;
let resizeObserver: ResizeObserver | null = null;

// ── Inspectable Trades & Jumps Logic ──
const allInspectableSignals = computed<InspectableSignal[]>(() => {
  const list: InspectableSignal[] = [];

  // 1. Backtest trades
  if (props.tradesDetail && props.tradesDetail.length > 0) {
    for (const t of props.tradesDetail) {
      list.push({
        id: t.id,
        source: 'BACKTEST',
        side: (t as any).side || ((t as any).action ? (t as any).action : 'LONG'),
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
  if (props.signals && props.signals.length > 0) {
    for (let i = 0; i < props.signals.length; i++) {
      const s = props.signals[i];
      const rawTime = s.time ? Number(s.time) : (s.timestamp ? Math.floor(s.timestamp / 1000) : 0);
      if (!rawTime || (!s.entry_price && !s.price)) continue;
      const entryPrice = Number(s.entry_price || s.price);
      const isBuy = s.action === 'BUY' || s.action === 'LONG';
      const entryTime = rawTime;
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

  // 3. Latest signal if not present
  if (props.latestSignal && (props.latestSignal.entry_price || props.latestSignal.price)) {
    const entryPrice = Number(props.latestSignal.entry_price || props.latestSignal.price);
    const isBuy = props.latestSignal.action === 'BUY' || props.latestSignal.action === 'LONG';
    const rawTime = props.latestSignal.time
      ? Number(props.latestSignal.time)
      : (props.latestSignal.timestamp ? Math.floor(props.latestSignal.timestamp / 1000) : (rawCandles.value.length > 0 ? Number(rawCandles.value[rawCandles.value.length - 1].time) : 0));
    const entryTime = rawTime;
    const exists = list.some((existing) => Math.abs(existing.entry_time - entryTime) < 2);
    if (!exists) {
      const isClosed = Boolean(
        props.latestSignal.exit_price ||
        props.latestSignal.exit_reason ||
        props.latestSignal.status === 'COMPLETED' ||
        props.latestSignal.status === 'CLOSED'
      );
      list.push({
        id: 'live-latest',
        source: 'LIVE',
        side: props.latestSignal.action || 'LONG',
        entry_time: entryTime,
        entry_price: entryPrice,
        exit_time: props.latestSignal.exit_price ? entryTime : undefined,
        exit_price: props.latestSignal.exit_price,
        exit_reason: props.latestSignal.exit_reason,
        pnl_pct: props.latestSignal.pnl_pct || 0,
        stop_loss: props.latestSignal.stop_loss || (isBuy ? entryPrice * 0.9975 : entryPrice * 1.0025),
        take_profit: props.latestSignal.take_profit || (isBuy ? entryPrice * 1.0030 : entryPrice * 0.9970),
        isLiveActive: !isClosed && props.latestSignal.status === 'ACTIVE_IN_POSITION',
      });
    }
  }

  list.sort((a, b) => a.entry_time - b.entry_time);
  return list;
});

const selectedSignalIndex = ref<number>(0);
const inspectedSignal = computed<InspectableSignal | null>(() => {
  if (allInspectableSignals.value.length === 0) return null;
  const idx = Math.max(0, Math.min(selectedSignalIndex.value, allInspectableSignals.value.length - 1));
  return allInspectableSignals.value[idx] || null;
});

const hasActiveLiveTrade = computed(() => allInspectableSignals.value.some((s) => s.isLiveActive));

const tradeRiskReward = computed(() => {
  if (!inspectedSignal.value) return null;
  const { entry_price, stop_loss, take_profit } = inspectedSignal.value;
  if (!entry_price || !stop_loss || !take_profit) return null;
  const risk = Math.abs(entry_price - stop_loss);
  const reward = Math.abs(take_profit - entry_price);
  if (risk <= 0) return null;
  return `1:${(reward / risk).toFixed(1)}`;
});

// ── Precision Coordinate Helper Functions for SVG Trade Boxes ──
const getYForPrice = (price: number): number => {
  if (!candleSeries || !chartContainerRef.value) return 0;
  const directY = candleSeries.priceToCoordinate(price);
  if (directY !== null && !isNaN(directY)) {
    return directY;
  }
  const containerH = chartContainerRef.value.clientHeight || 400;
  const pTop = candleSeries.coordinateToPrice(10);
  const pBottom = candleSeries.coordinateToPrice(containerH - 10);
  if (pTop !== null && pBottom !== null && pTop !== pBottom) {
    const slope = (containerH - 20) / (pBottom - pTop);
    const interpolatedY = 10 + (price - pTop) * slope;
    if (!isNaN(interpolatedY)) return interpolatedY;
  }
  return price > (inspectedSignal.value?.entry_price || 0) ? -50 : containerH + 50;
};

const findCandleIndex = (timeSec: number): number => {
  if (!rawCandles.value || rawCandles.value.length === 0) return -1;
  const firstT = Number(rawCandles.value[0].time);
  const lastT = Number(rawCandles.value[rawCandles.value.length - 1].time);
  if (timeSec < firstT || timeSec > lastT) return -1;

  let low = 0, high = rawCandles.value.length - 1;
  while (low <= high) {
    const mid = Math.floor((low + high) / 2);
    const t = Number(rawCandles.value[mid].time);
    if (t === timeSec) return mid;
    if (t < timeSec) low = mid + 1;
    else high = mid - 1;
  }
  if (low >= rawCandles.value.length) return rawCandles.value.length - 1;
  if (high < 0) return 0;
  return Math.abs(Number(rawCandles.value[low].time) - timeSec) < Math.abs(Number(rawCandles.value[high].time) - timeSec)
    ? low
    : high;
};

const updateBoxCoordinates = () => {
  const target = inspectedSignal.value;
  if (!target || !target.entry_price || !chart || !candleSeries || !chartContainerRef.value || rawCandles.value.length === 0) {
    positionBoxes.value = [];
    return;
  }

  const containerW = chartContainerRef.value.clientWidth || 800;
  const containerH = chartContainerRef.value.clientHeight || 400;

  const rawEntry = target.entry_time > 2000000000 ? target.entry_time / 1000 : target.entry_time;
  const rawExit = target.exit_time 
    ? (target.exit_time > 2000000000 ? target.exit_time / 1000 : target.exit_time) 
    : null;

  const localEntryTime = timeToLocal(rawEntry);
  const localExitTime = rawExit ? timeToLocal(rawExit) : null;

  const entryIdx = findCandleIndex(rawEntry);
  if (entryIdx < 0) {
    positionBoxes.value = [];
    return;
  }
  let x1Raw = chart.timeScale().logicalToCoordinate(entryIdx as any);
  if (x1Raw === null) {
    x1Raw = chart.timeScale().timeToCoordinate(localEntryTime as Time);
  }

  let x2Raw: number | null = null;
  if (target.isLiveActive || !localExitTime) {
    const lastIdx = rawCandles.value.length - 1;
    const lastX = chart.timeScale().logicalToCoordinate(lastIdx as any);
    x2Raw = lastX !== null ? lastX + 80 : containerW - 65;
  } else {
    const exitIdx = findCandleIndex(rawExit);
    x2Raw = chart.timeScale().logicalToCoordinate(exitIdx as any);
    if (x2Raw === null) {
      x2Raw = chart.timeScale().timeToCoordinate(localExitTime as Time);
    }
  }

  if (x1Raw === null && x2Raw === null) {
    positionBoxes.value = [];
    return;
  }

  const startX = x1Raw !== null ? x1Raw : (x2Raw! - 100);
  const endX = x2Raw !== null ? x2Raw : (x1Raw! + 100);
  const leftX = Math.min(startX, endX);
  const rightX = Math.max(startX, endX);
  const width = Math.max(rightX - leftX, 32);

  if (rightX < -400 || leftX > containerW + 400) {
    positionBoxes.value = [];
    return;
  }

  const yEntry = getYForPrice(target.entry_price);
  const ySL = getYForPrice(target.stop_loss);
  const yTP = getYForPrice(target.take_profit);

  const isLong = target.take_profit >= target.entry_price;
  let yProfitTop: number, profitHeight: number, yLossTop: number, lossHeight: number;

  if (isLong) {
    yProfitTop = yTP;
    profitHeight = Math.max(yEntry - yTP, 2);
    yLossTop = yEntry;
    lossHeight = Math.max(ySL - yEntry, 2);
  } else {
    yLossTop = ySL;
    lossHeight = Math.max(yEntry - ySL, 2);
    yProfitTop = yEntry;
    profitHeight = Math.max(yTP - yEntry, 2);
  }

  positionBoxes.value = [
    {
      id: target.id,
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
  ];
};

const getLabelX = (box: PositionBoxCoord) => {
  const labelWidth = 78;
  const containerW = chartContainerRef.value?.clientWidth || 800;
  return Math.max(
    box.x + 4,
    Math.min(box.x + box.width - labelWidth - 4, containerW - labelWidth - 12)
  );
};

const getClampedY = (y: number) => {
  const containerH = chartContainerRef.value?.clientHeight || 400;
  return Math.max(12, Math.min(containerH - 24, y));
};

// Center and zoom chart onto a specific trade jump
const centerOnTrade = (trade: InspectableSignal) => {
  if (!chart || !candleSeries || !trade || !trade.entry_time) return;
  if (!rawCandles.value || rawCandles.value.length === 0) return;
  try {
    const rawEntry = trade.entry_time > 2000000000 ? trade.entry_time / 1000 : trade.entry_time;
    const firstT = Number(rawCandles.value[0].time);
    const lastT = Number(rawCandles.value[rawCandles.value.length - 1].time);
    if (rawEntry < firstT || rawEntry > lastT) {
      console.warn(`[ChartCanvas] Trade entry time ${rawEntry} is outside candle range [${firstT}, ${lastT}]`);
      return;
    }
    const rawExit = trade.exit_time 
      ? (trade.exit_time > 2000000000 ? trade.exit_time / 1000 : trade.exit_time)
      : rawEntry + 15 * 60;

    const t = timeToLocal(rawEntry);
    const tExit = timeToLocal(rawExit);
    const span = Math.max(tExit - t, 3600);

    chart.timeScale().setVisibleRange({
      from: (t - span * 2.5) as Time,
      to: (tExit + span * 2.5) as Time,
    });

    setTimeout(() => {
      updateBoxCoordinates();
    }, 40);
  } catch (err) {
    console.warn('[ChartCanvas] centerOnTrade error:', err);
  }
};

// Jump navigation methods
const prevJump = () => {
  if (selectedSignalIndex.value > 0) {
    selectedSignalIndex.value--;
    centerOnTrade(allInspectableSignals.value[selectedSignalIndex.value]);
  }
};

const nextJump = () => {
  if (selectedSignalIndex.value < allInspectableSignals.value.length - 1) {
    selectedSignalIndex.value++;
    centerOnTrade(allInspectableSignals.value[selectedSignalIndex.value]);
  }
};

const jumpToIndex = (idx: number) => {
  if (idx >= 0 && idx < allInspectableSignals.value.length) {
    selectedSignalIndex.value = idx;
    centerOnTrade(allInspectableSignals.value[idx]);
  }
};

const jumpToLatest = () => {
  if (allInspectableSignals.value.length > 0) {
    jumpToIndex(allInspectableSignals.value.length - 1);
  }
};

const jumpToActive = () => {
  const activeIdx = allInspectableSignals.value.findIndex((s) => s.isLiveActive);
  if (activeIdx !== -1) {
    jumpToIndex(activeIdx);
  }
};

// Global Hotkeys for Jumping [Left Arrow / '[' : Prev, Right Arrow / ']' : Next]
const handleKeyDown = (e: KeyboardEvent) => {
  if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
  if (e.key === 'ArrowLeft' || e.key === '[') {
    prevJump();
  } else if (e.key === 'ArrowRight' || e.key === ']') {
    nextJump();
  }
};

// ── Chart Initialization & Lifecycle ──
const initChart = () => {
  if (!chartContainerRef.value) return;

  const isDark = props.theme === 'dark';
  chart = createChart(chartContainerRef.value, {
    layout: {
      background: { type: ColorType.Solid, color: isDark ? '#0d1322' : '#ffffff' },
      textColor: isDark ? '#c9d1d9' : '#334155',
      fontSize: 11,
      fontFamily: '"JetBrains Mono", monospace',
    },
    grid: {
      vertLines: { color: isDark ? 'rgba(48, 54, 61, 0.4)' : 'rgba(226, 232, 240, 0.8)' },
      horzLines: { color: isDark ? 'rgba(48, 54, 61, 0.4)' : 'rgba(226, 232, 240, 0.8)' },
    },
    crosshair: {
      mode: 0,
      vertLine: { color: isDark ? '#58a6ff' : '#0284c7', width: 1, style: 3 },
      horzLine: { color: isDark ? '#58a6ff' : '#0284c7', width: 1, style: 3 },
    },
    rightPriceScale: {
      borderColor: isDark ? '#30363d' : '#e2e8f0',
      scaleMargins: { top: 0.1, bottom: 0.2 },
    },
    timeScale: {
      borderColor: isDark ? '#30363d' : '#e2e8f0',
      timeVisible: true,
      secondsVisible: false,
    },
  });

  // Candlestick Series
  candleSeries = chart.addCandlestickSeries({
    upColor: '#26a69a',
    downColor: '#ef5350',
    borderVisible: false,
    wickUpColor: '#26a69a',
    wickDownColor: '#ef5350',
  });

  // Volume Series
  volumeSeries = chart.addHistogramSeries({
    color: 'rgba(38, 166, 154, 0.45)',
    priceFormat: { type: 'volume' },
    priceScaleId: '',
  });
  volumeSeries.priceScale().applyOptions({
    scaleMargins: { top: 0.82, bottom: 0 },
  });

  // EMA Lines
  ema9Series = chart.addLineSeries({ color: '#38bdf8', lineWidth: 1.5, title: 'EMA 9' });
  ema21Series = chart.addLineSeries({ color: '#818cf8', lineWidth: 1.5, title: 'EMA 21' });
  ema200Series = chart.addLineSeries({ color: '#f59e0b', lineWidth: 2, title: 'EMA 200' });

  // Bollinger Bands Lines
  bbUpperSeries = chart.addLineSeries({ color: '#c084fc', lineWidth: 1, lineStyle: 2, title: 'BB Upper' });
  bbLowerSeries = chart.addLineSeries({ color: '#c084fc', lineWidth: 1, lineStyle: 2, title: 'BB Lower' });

  // HH/LL 15
  hhSeries = chart.addLineSeries({ color: '#34d399', lineWidth: 1, lineStyle: 3, title: 'HH15' });
  llSeries = chart.addLineSeries({ color: '#f87171', lineWidth: 1, lineStyle: 3, title: 'LL15' });

  // Crosshair move handler (Coordinates HUD sync)
  chart.subscribeCrosshairMove((param) => {
    if (!param.time || !param.seriesData || !candleSeries) return;
    const cData: any = param.seriesData.get(candleSeries);
    if (cData) {
      legendData.value = {
        open: cData.open,
        high: cData.high,
        low: cData.low,
        close: cData.close,
        volume: volumeSeries ? (param.seriesData.get(volumeSeries) as any)?.value : undefined,
        changePct: cData.open ? ((cData.close - cData.open) / cData.open) * 100 : 0,
        ema9: ema9Series ? (param.seriesData.get(ema9Series) as any)?.value : undefined,
        ema21: ema21Series ? (param.seriesData.get(ema21Series) as any)?.value : undefined,
        ema200: ema200Series ? (param.seriesData.get(ema200Series) as any)?.value : undefined,
        hh15: hhSeries ? (param.seriesData.get(hhSeries) as any)?.value : undefined,
        ll15: llSeries ? (param.seriesData.get(llSeries) as any)?.value : undefined,
        bbUpper: bbUpperSeries ? (param.seriesData.get(bbUpperSeries) as any)?.value : undefined,
        bbLower: bbLowerSeries ? (param.seriesData.get(bbLowerSeries) as any)?.value : undefined,
      };
    }
  });

  // Subscribe timescale changes to keep Trade Boxes pinned dynamically during pan/zoom
  chart.timeScale().subscribeVisibleLogicalRangeChange(updateBoxCoordinates);
  chart.timeScale().subscribeVisibleTimeRangeChange(updateBoxCoordinates);

  const container = chartContainerRef.value;
  container.addEventListener('wheel', updateBoxCoordinates, { passive: true });
  container.addEventListener('pointerup', updateBoxCoordinates);

  // Resize handling
  resizeObserver = new ResizeObserver((entries) => {
    if (entries.length > 0 && chartContainerRef.value && chart) {
      const { width, height } = entries[0].contentRect;
      chart.applyOptions({ width, height });
      updateBoxCoordinates();
    }
  });
  resizeObserver.observe(chartContainerRef.value);

  loadCandles();
};

const loadCandles = async () => {
  if (!candleSeries || !chart) return;
  loadingCandles.value = true;

  try {
    const isGold = selectedSymbol.value.toLowerCase().includes('xau');
    const apiSym = isGold ? 'XAUUSD' : selectedSymbol.value;
    const res = await fetch(`/api/candles?symbol=${encodeURIComponent(apiSym)}&count=20000&mode=live`);
    const data = await res.json();

    if (data.data && data.data.length > 0) {
      rawCandles.value = data.data;
      const candles = data.data.map((c: any) => ({
        ...c,
        time: timeToLocal(Number(c.time)) as Time,
      }));

      candleSeries.setData(candles);

      // Volume with surge highlighting
      const volumes = candles.map((c: any) => ({
        time: c.time,
        value: c.volume || 10,
        color: c.close >= c.open ? 'rgba(38, 166, 154, 0.6)' : 'rgba(239, 83, 80, 0.6)',
      }));
      volumeSeries?.setData(volumes);

      // Quantitative Indicators
      const ema9 = calculateEMA(candles, 9);
      const ema21 = calculateEMA(candles, 21);
      const ema200 = calculateEMA(candles, Math.min(200, candles.length));
      const bb = calculateBollingerBands(candles, 20, 2.0);
      const hhll = calculateHHLL(candles, 15);

      ema9Series?.setData(ema9);
      ema21Series?.setData(ema21);
      ema200Series?.setData(ema200);

      if (isGold) {
        hhSeries?.setData(hhll.hh);
        llSeries?.setData(hhll.ll);
        bbUpperSeries?.setData([]);
        bbLowerSeries?.setData([]);
      } else {
        bbUpperSeries?.setData(bb.upper);
        bbLowerSeries?.setData(bb.lower);
        hhSeries?.setData([]);
        llSeries?.setData([]);
      }

      const last = candles[candles.length - 1];
      if (last) {
        lastLivePrice.value = last.close;
        legendData.value = {
          open: last.open,
          high: last.high,
          low: last.low,
          close: last.close,
          volume: last.volume,
          changePct: last.open ? ((last.close - last.open) / last.open) * 100 : 0,
          ema9: ema9[ema9.length - 1]?.value,
          ema21: ema21[ema21.length - 1]?.value,
          ema200: ema200[ema200.length - 1]?.value,
          hh15: hhll.hh[hhll.hh.length - 1]?.value,
          ll15: hhll.ll[hhll.ll.length - 1]?.value,
          bbUpper: bb.upper[bb.upper.length - 1]?.value,
          bbLower: bb.lower[bb.lower.length - 1]?.value,
        };
      }

      // Apply markers if present
      if (props.tradeMarkers && props.tradeMarkers.length > 0) {
        applyMarkers(props.tradeMarkers);
      }

      // If trades exist, auto-center on the latest trade
      if (allInspectableSignals.value.length > 0) {
        const latestIdx = allInspectableSignals.value.length - 1;
        selectedSignalIndex.value = latestIdx;
        centerOnTrade(allInspectableSignals.value[latestIdx]);
      } else {
        chart.timeScale().fitContent();
      }
    }
  } catch (err) {
    console.error('[ChartCanvas] Failed to load candles:', err);
  } finally {
    loadingCandles.value = false;
  }
};

const applyMarkers = (markers: any[]) => {
  if (!candleSeries || !rawCandles.value || rawCandles.value.length === 0) return;
  try {
    const firstTime = Number(rawCandles.value[0].time);
    const lastTime = Number(rawCandles.value[rawCandles.value.length - 1].time);

    // Filter markers that fall strictly within the loaded candle timeline.
    // Lightweight Charts clamps out-of-bounds timestamps to the first or last bar,
    // which previously caused all earlier backtest trades to pile into an erroneous vertical stack on the first candle.
    const validMarkers = markers.filter((m) => {
      if (!m || m.time === undefined || m.time === null) return false;
      const rawT = typeof m.time === 'number' && m.time > 2000000000 ? m.time / 1000 : Number(m.time);
      return rawT >= firstTime && rawT <= lastTime;
    });

    const formatted = validMarkers.map((m) => {
      const rawT = typeof m.time === 'number' && m.time > 2000000000 ? m.time / 1000 : Number(m.time);
      return {
        time: timeToLocal(rawT) as Time,
        position: m.position || (m.action === 'BUY' ? 'belowBar' : 'aboveBar'),
        color: m.color || (m.action === 'BUY' ? '#26a69a' : '#ef5350'),
        shape: m.shape || (m.action === 'BUY' ? 'arrowUp' : 'arrowDown'),
        text: m.text || m.action || 'SIGNAL',
      };
    });

    // Lightweight charts strictly requires markers to be sorted by time ascending
    formatted.sort((a, b) => Number(a.time) - Number(b.time));

    candleSeries.setMarkers(formatted);
  } catch (e) {
    console.warn('[ChartCanvas] Error applying markers:', e);
  }
};

// Live price streams
const startLiveFeeds = () => {
  const isGold = selectedSymbol.value.toLowerCase().includes('xau');

  if (isGold) {
    isWsConnected.value = true;
    const pollOanda = async () => {
      try {
        const res = await fetch('/api/xauusd/quote');
        const data = await res.json();
        if (data?.quote?.price) {
          const p = parseFloat(data.quote.price);
          if (!isNaN(p) && p > 0) {
            if (lastLivePrice.value !== null) {
              priceFlash.value = p >= lastLivePrice.value ? 'up' : 'down';
              setTimeout(() => { priceFlash.value = null; }, 500);
            }
            lastLivePrice.value = p;
          }
        }
      } catch {}
    };
    pollOanda();
    oandaTimer = setInterval(pollOanda, 2000);
  } else {
    try {
      binanceWs = new WebSocket('wss://stream.binance.com:9443/ws/btcusdt@kline_15m');
      binanceWs.onopen = () => { isWsConnected.value = true; };
      binanceWs.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg?.k?.c) {
            const p = parseFloat(msg.k.c);
            if (lastLivePrice.value !== null) {
              priceFlash.value = p >= lastLivePrice.value ? 'up' : 'down';
              setTimeout(() => { priceFlash.value = null; }, 500);
            }
            lastLivePrice.value = p;
          }
        } catch {}
      };
      binanceWs.onclose = () => { isWsConnected.value = false; };
    } catch {}
  }
};

const stopLiveFeeds = () => {
  if (oandaTimer) {
    clearInterval(oandaTimer);
    oandaTimer = null;
  }
  if (binanceWs) {
    binanceWs.close();
    binanceWs = null;
  }
  isWsConnected.value = false;
};

// ── Watchers ──
watch(selectedSymbol, () => {
  stopLiveFeeds();
  loadCandles();
  startLiveFeeds();
});

watch(() => props.selectedStrategy, (newStrat) => {
  if (newStrat) {
    const isGold = newStrat.toLowerCase().includes('xau') || newStrat.toLowerCase().includes('gold');
    selectedSymbol.value = isGold ? 'XAU/USD' : 'BTC/USDT';
  }
});

watch(() => props.theme, (newTheme) => {
  if (!chart) return;
  const isDark = newTheme === 'dark';
  chart.applyOptions({
    layout: {
      background: { type: ColorType.Solid, color: isDark ? '#0d1322' : '#ffffff' },
      textColor: isDark ? '#c9d1d9' : '#334155',
    },
    grid: {
      vertLines: { color: isDark ? 'rgba(48, 54, 61, 0.4)' : 'rgba(226, 232, 240, 0.8)' },
      horzLines: { color: isDark ? 'rgba(48, 54, 61, 0.4)' : 'rgba(226, 232, 240, 0.8)' },
    },
  });
});

watch(() => props.tradeMarkers, (newMarkers) => {
  if (newMarkers && !loadingCandles.value) applyMarkers(newMarkers);
}, { deep: true });

watch(() => props.tradesDetail, () => {
  if (allInspectableSignals.value.length > 0) {
    const latestIdx = allInspectableSignals.value.length - 1;
    selectedSignalIndex.value = latestIdx;
    centerOnTrade(allInspectableSignals.value[latestIdx]);
  }
}, { deep: true });

onMounted(() => {
  initChart();
  startLiveFeeds();
  window.addEventListener('keydown', handleKeyDown);
});

onUnmounted(() => {
  stopLiveFeeds();
  window.removeEventListener('keydown', handleKeyDown);
  if (chartContainerRef.value) {
    chartContainerRef.value.removeEventListener('wheel', updateBoxCoordinates);
    chartContainerRef.value.removeEventListener('pointerup', updateBoxCoordinates);
  }
  if (resizeObserver) resizeObserver.disconnect();
  if (chart) {
    chart.remove();
    chart = null;
  }
});
</script>

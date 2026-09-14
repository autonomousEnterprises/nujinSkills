<template>
  <div class="relative w-full h-full flex flex-col font-mono select-none overflow-hidden bg-base-100">
    <!-- Top Bar: Strategy Selector, Trades/Jumps Navigator, Live Price -->
    <ChartTopBar
      :strategies="strategies"
      :cleanStrategyName="cleanStrategyName"
      :selectedStrategy="selectedStrategy"
      :activeStrategy="activeStrategy"
      :isGoldStrategy="isGoldStrategy"
      :isSpStrategy="isSpStrategy"
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
      :isSpStrategy="isSpStrategy"
      :hudItems="currentHudItems"
      :strategyProfile="currentProfile"
      :isInspectingTrade="isInspectingTrade"
      @dismissInspection="dismissInspection"
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
            :y="box.yEntryLabel ?? getClampedY(box.yEntry - 9)"
            width="92"
            height="18"
            rx="3.5"
            fill="rgba(56, 189, 248, 0.95)"
            stroke="#0284c7"
            stroke-width="0.75"
          />
          <text
            :x="getLabelX(box) + 46"
            :y="(box.yEntryLabel ?? getClampedY(box.yEntry - 9)) + 12.5"
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
            :y="box.yTpLabel ?? getClampedY(box.isLong ? box.yProfitTop + 2 : box.yProfitTop + box.profitHeight - 19)"
            width="92"
            height="18"
            rx="3.5"
            fill="rgba(38, 166, 154, 0.95)"
            stroke="#0d9488"
            stroke-width="0.75"
          />
          <text
            :x="getLabelX(box) + 46"
            :y="(box.yTpLabel ?? getClampedY(box.isLong ? box.yProfitTop + 2 : box.yProfitTop + box.profitHeight - 19)) + 12.5"
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
            :y="box.ySlLabel ?? getClampedY(box.isLong ? box.yLossTop + box.lossHeight - 19 : box.yLossTop + 2)"
            width="92"
            height="18"
            rx="3.5"
            fill="rgba(239, 83, 80, 0.95)"
            stroke="#dc2626"
            stroke-width="0.75"
          />
          <text
            :x="getLabelX(box) + 46"
            :y="(box.ySlLabel ?? getClampedY(box.isLong ? box.yLossTop + box.lossHeight - 19 : box.yLossTop + 2)) + 12.5"
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
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue';
import { createChart, ColorType, type IChartApi, type ISeriesApi, type Time } from 'lightweight-charts';
import ChartTopBar from './chart/ChartTopBar.vue';
import ChartHudBar from './chart/ChartHudBar.vue';
import {
  getStrategyIndicatorProfile,
  type IndicatorPoint,
  type IndicatorChipData,
  type StrategyIndicatorProfile,
} from '../utils/indicators';
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
    targetedSignal?: SignalData | InspectableSignal | null;
    theme?: 'dark' | 'light';
    selectedStrategy?: string;
    tradeMarkers?: any[];
    tradesDetail?: TradeDetail[];
    activeStrategy?: string;
    strategies?: StrategyItem[];
    isActiveScreen?: boolean;
  }>(),
  {
    theme: 'dark',
    selectedStrategy: 'GoatFundedTraderXauusdScalper.py',
    tradeMarkers: () => [],
    tradesDetail: () => [],
    strategies: () => [],
    isActiveScreen: true,
  }
);

const emit = defineEmits<{
  (e: 'selectStrategy', stratName: string): void;
  (e: 'dismissSignal'): void;
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

// Dynamic indicator series and profile state
const activeIndicatorSeries = new Map<string, ISeriesApi<'Line'>>();
const currentProfile = ref<StrategyIndicatorProfile | null>(null);
const currentHudItems = ref<IndicatorChipData[]>([]);
const timeIndexMap = new Map<number, number>();
let indicatorCalculator: {
  seriesData: Record<string, IndicatorPoint[]>;
  getHudItems: (idx: number) => IndicatorChipData[];
} | null = null;

const cleanStrategyName = computed(() => (props.selectedStrategy || props.activeStrategy || 'OpeningFlushReversalScalper').replace('.py', ''));
const isGoldStrategy = computed(() => {
  const s = cleanStrategyName.value.toLowerCase();
  return s.includes('xau') || s.includes('gold') || s.includes('goat');
});
const isSpStrategy = computed(() => {
  const s = cleanStrategyName.value.toLowerCase();
  return s.includes('sp500') || s.includes('openingflush') || s.includes('es') || s.includes('reversal');
});

const formatPrice = (p: number | undefined | null) => {
  if (p == null || isNaN(p)) return '–';
  return (isGoldStrategy.value || isSpStrategy.value) ? p.toFixed(2) : p.toFixed(1);
};

const selectedSymbol = ref(isSpStrategy.value ? 'S&P 500 (ES)' : (isGoldStrategy.value ? 'XAU/USD' : 'BTC/USDT'));
const isWsConnected = ref(false);
const lastLivePrice = ref<number | null>(null);
const priceFlash = ref<'up' | 'down' | null>(null);
const loadingCandles = ref(false);

const legendData = ref<Record<string, any>>({});
const rawCandles = ref<any[]>([]);
const positionBoxes = ref<PositionBoxCoord[]>([]);
const isInspectingTrade = ref<boolean>(false);

let binanceWs: WebSocket | null = null;
let oandaTimer: any = null;
let periodicSyncTimer: any = null;
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
      const isClosed = Boolean(
        s.exit_price ||
        (s.exit_reason && s.exit_reason !== 'ACTIVE_IN_POSITION') ||
        s.status === 'COMPLETED' ||
        s.status === 'CLOSED'
      );
      const exitTime = s.exit_time
        ? Number(s.exit_time)
        : (isClosed ? ((s as any).closed_at || (s as any).exit_timestamp || undefined) : undefined);

      list.push({
        id: s.id != null ? s.id : `live-${i}`,
        source: 'LIVE',
        side: s.action || 'LONG',
        entry_time: entryTime,
        entry_price: entryPrice,
        exit_time: exitTime,
        exit_price: s.exit_price,
        exit_reason: s.exit_reason,
        pnl_pct: s.pnl_pct || 0,
        stop_loss: s.stop_loss || (isBuy ? entryPrice * 0.9975 : entryPrice * 1.0025),
        take_profit: s.take_profit || (isBuy ? entryPrice * 1.0030 : entryPrice * 0.9970),
        isLiveActive: !isClosed && (s.status === 'ACTIVE_IN_POSITION' || s.exit_reason === 'ACTIVE_IN_POSITION'),
      });
    }
  }

  // 3. Latest signal if not present
  if (props.latestSignal && (props.latestSignal.entry_price || props.latestSignal.price)) {
    const s = props.latestSignal;
    const entryPrice = Number(s.entry_price || s.price);
    const isBuy = s.action === 'BUY' || s.action === 'LONG';
    const rawTime = s.time
      ? Number(s.time)
      : (s.timestamp ? Math.floor(s.timestamp / 1000) : (rawCandles.value.length > 0 ? Number(rawCandles.value[rawCandles.value.length - 1].time) : 0));
    const entryTime = rawTime;
    const exists = list.some((existing) => Math.abs(existing.entry_time - entryTime) < 2);
    if (!exists) {
      const isClosed = Boolean(
        s.exit_price ||
        (s.exit_reason && s.exit_reason !== 'ACTIVE_IN_POSITION') ||
        s.status === 'COMPLETED' ||
        s.status === 'CLOSED'
      );
      const exitTime = s.exit_time
        ? Number(s.exit_time)
        : (isClosed ? ((s as any).closed_at || (s as any).exit_timestamp || undefined) : undefined);
      list.push({
        id: 'live-latest',
        source: 'LIVE',
        side: s.action || 'LONG',
        entry_time: entryTime,
        entry_price: entryPrice,
        exit_time: exitTime,
        exit_price: s.exit_price,
        exit_reason: s.exit_reason,
        pnl_pct: s.pnl_pct || 0,
        stop_loss: s.stop_loss || (isBuy ? entryPrice * 0.9975 : entryPrice * 1.0025),
        take_profit: s.take_profit || (isBuy ? entryPrice * 1.0030 : entryPrice * 0.9970),
        isLiveActive: !isClosed && s.status === 'ACTIVE_IN_POSITION',
      });
    }
  }

  // 4. Targeted signal from user selection in SignalDeck or Grid
  if (props.targetedSignal && (props.targetedSignal.entry_price || props.targetedSignal.price)) {
    const s = props.targetedSignal;
    const entryPrice = Number(s.entry_price || s.price);
    const isBuy = s.action === 'BUY' || s.action === 'LONG' || (s as any).side === 'BUY' || (s as any).side === 'LONG';
    const rawTime = s.time
      ? Number(s.time)
      : (s.timestamp ? Math.floor(s.timestamp / 1000) : (rawCandles.value.length > 0 ? Number(rawCandles.value[rawCandles.value.length - 1].time) : Math.floor(Date.now() / 1000)));
    const entryTime = rawTime;
    const existingIdx = list.findIndex(
      (existing) => (s.id != null && String(existing.id) === String(s.id)) || Math.abs(existing.entry_time - entryTime) < 2
    );
    const isClosed = Boolean(
      s.exit_price ||
      (s.exit_reason && s.exit_reason !== 'ACTIVE_IN_POSITION') ||
      s.status === 'COMPLETED' ||
      s.status === 'CLOSED'
    );
    const existingExitTime = existingIdx !== -1 ? list[existingIdx].exit_time : undefined;
    const exitTime = s.exit_time
      ? Number(s.exit_time)
      : (existingExitTime || (isClosed ? ((s as any).closed_at || (s as any).exit_timestamp || undefined) : undefined));

    const inspectable: InspectableSignal = {
      id: s.id ?? (existingIdx !== -1 ? list[existingIdx].id : 'targeted-signal'),
      source: existingIdx !== -1 ? list[existingIdx].source : 'LIVE',
      side: s.action || (s as any).side || (isBuy ? 'LONG' : 'SHORT'),
      entry_time: entryTime,
      entry_price: entryPrice,
      exit_time: exitTime,
      exit_price: s.exit_price ?? (existingIdx !== -1 ? list[existingIdx].exit_price : undefined),
      exit_reason: s.exit_reason ?? (existingIdx !== -1 ? list[existingIdx].exit_reason : undefined),
      pnl_pct: s.pnl_pct ?? (existingIdx !== -1 ? list[existingIdx].pnl_pct : 0),
      stop_loss: s.stop_loss || (existingIdx !== -1 ? list[existingIdx].stop_loss : (isBuy ? entryPrice * 0.9975 : entryPrice * 1.0025)),
      take_profit: s.take_profit || (existingIdx !== -1 ? list[existingIdx].take_profit : (isBuy ? entryPrice * 1.0030 : entryPrice * 0.9970)),
      isLiveActive: !isClosed && (s.status === 'ACTIVE_IN_POSITION' || s.exit_reason === 'ACTIVE_IN_POSITION'),
    };
    if (existingIdx !== -1) {
      list[existingIdx] = { ...list[existingIdx], ...inspectable };
    } else {
      list.push(inspectable);
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
  if (timeSec >= lastT) return rawCandles.value.length - 1;
  if (timeSec <= firstT) return 0;

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
  if (!isInspectingTrade.value && !props.targetedSignal) {
    positionBoxes.value = [];
    return;
  }

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

  const entryIdx = findCandleIndex(rawEntry);
  if (entryIdx < 0) {
    positionBoxes.value = [];
    return;
  }

  // Calculate dynamic bar spacing and visible logical range
  const barSpacing = chart.timeScale().options().barSpacing || 16;
  const halfBar = Math.max(barSpacing / 2, 4);
  const visRange = chart.timeScale().getVisibleLogicalRange();

  const entryCandleLocalTime = timeToLocal(Number(rawCandles.value[entryIdx].time));
  let x1Center = chart.timeScale().timeToCoordinate(entryCandleLocalTime as Time);
  if (x1Center === null) {
    x1Center = chart.timeScale().logicalToCoordinate(entryIdx as any);
  }
  if (x1Center === null && visRange) {
    x1Center = (entryIdx - visRange.from) * barSpacing;
  }

  let x2Center: number | null = null;
  const isTradeOpen = target.isLiveActive || !rawExit;

  if (isTradeOpen) {
    const lastIdx = rawCandles.value.length - 1;
    const lastCandleLocalTime = timeToLocal(Number(rawCandles.value[lastIdx].time));
    let lastX = chart.timeScale().timeToCoordinate(lastCandleLocalTime as Time);
    if (lastX === null) {
      lastX = chart.timeScale().logicalToCoordinate(lastIdx as any);
    }
    if (lastX === null && visRange) {
      lastX = (lastIdx - visRange.from) * barSpacing;
    }
    x2Center = lastX !== null ? (lastX + barSpacing * 4) : (containerW - 30);
  } else {
    let exitIdx = findCandleIndex(rawExit!);
    if (exitIdx < 0) {
      if (rawExit! >= Number(rawCandles.value[rawCandles.value.length - 1].time)) {
        exitIdx = rawCandles.value.length - 1;
      } else {
        exitIdx = Math.min(entryIdx + 5, rawCandles.value.length - 1);
      }
    }
    if (exitIdx < entryIdx) exitIdx = entryIdx;

    const exitCandleLocalTime = timeToLocal(Number(rawCandles.value[exitIdx].time));
    x2Center = chart.timeScale().timeToCoordinate(exitCandleLocalTime as Time);
    if (x2Center === null) {
      x2Center = chart.timeScale().logicalToCoordinate(exitIdx as any);
    }
    if (x2Center === null && visRange) {
      x2Center = (exitIdx - visRange.from) * barSpacing;
    }
  }

  if (x1Center === null && x2Center === null) {
    positionBoxes.value = [];
    return;
  }

  const startX = (x1Center !== null ? x1Center - halfBar : ((x2Center || 100) - barSpacing * 2));
  const endX = isTradeOpen
    ? (x2Center !== null ? x2Center : containerW - 30)
    : (x2Center !== null ? x2Center + halfBar : startX + barSpacing);

  let leftX = Math.min(startX, endX);
  let rightX = Math.max(startX, endX);
  let width = rightX - leftX;
  if (width < halfBar * 2) {
    width = halfBar * 2;
    rightX = leftX + width;
  }

  if (rightX < -500 || leftX > containerW + 500) {
    positionBoxes.value = [];
    return;
  }

  const yEntry = getYForPrice(target.entry_price);
  const ySL = getYForPrice(target.stop_loss);
  const yTP = getYForPrice(target.take_profit);

  const isLong = target.side === 'LONG' || target.side === 'BUY' || (target.take_profit >= target.entry_price);
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

  // ── Smart Label Collision Prevention ──
  const LABEL_H = 18;
  const MIN_GAP = 3;
  const STRIDE = LABEL_H + MIN_GAP;

  let idealEntryY = yEntry - (LABEL_H / 2);
  let idealTpY = isLong ? yTP : (yTP - LABEL_H);
  let idealSlY = isLong ? (ySL - LABEL_H) : ySL;

  // Clamp entry Y to visible chart interior
  idealEntryY = Math.max(22, Math.min(containerH - 45, idealEntryY));

  let yTpLabel: number;
  let yEntryLabel: number = idealEntryY;
  let ySlLabel: number;

  if (isLong) {
    // LONG: TP above Entry (smaller Y), SL below Entry (larger Y)
    yTpLabel = Math.min(idealTpY, idealEntryY - STRIDE);
    ySlLabel = Math.max(idealSlY, idealEntryY + STRIDE);

    if (yTpLabel < 10) {
      const shift = 10 - yTpLabel;
      yTpLabel += shift;
      yEntryLabel += shift;
      ySlLabel += shift;
    }
    if (ySlLabel > containerH - 24) {
      const shift = ySlLabel - (containerH - 24);
      ySlLabel -= shift;
      yEntryLabel -= shift;
      yTpLabel -= shift;
    }
  } else {
    // SHORT: SL above Entry (smaller Y), TP below Entry (larger Y)
    ySlLabel = Math.min(idealSlY, idealEntryY - STRIDE);
    yTpLabel = Math.max(idealTpY, idealEntryY + STRIDE);

    if (ySlLabel < 10) {
      const shift = 10 - ySlLabel;
      ySlLabel += shift;
      yEntryLabel += shift;
      yTpLabel += shift;
    }
    if (yTpLabel > containerH - 24) {
      const shift = yTpLabel - (containerH - 24);
      yTpLabel -= shift;
      yEntryLabel -= shift;
      ySlLabel -= shift;
    }
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
      yTpLabel,
      yEntryLabel,
      ySlLabel,
    },
  ];
};

const getLabelX = (box: PositionBoxCoord) => {
  const labelWidth = 92;
  const containerW = chartContainerRef.value?.clientWidth || 800;
  if (box.width >= labelWidth + 12) {
    return Math.max(box.x + 6, Math.min(box.x + box.width - labelWidth - 6, containerW - labelWidth - 10));
  } else {
    const rightAligned = box.x + box.width + 4;
    if (rightAligned + labelWidth < containerW - 10) {
      return rightAligned;
    }
    return Math.max(6, Math.min(box.x, containerW - labelWidth - 10));
  }
};

const getClampedY = (y: number) => {
  const containerH = chartContainerRef.value?.clientHeight || 400;
  return Math.max(10, Math.min(containerH - 24, y));
};

// Center and zoom chart onto a specific trade jump
const centerOnTrade = (trade: InspectableSignal) => {
  if (!chart || !candleSeries || !trade || !trade.entry_time) return;
  if (!rawCandles.value || rawCandles.value.length === 0) return;
  try {
    const rawEntry = trade.entry_time > 2000000000 ? trade.entry_time / 1000 : trade.entry_time;
    const rawExit = trade.exit_time 
      ? (trade.exit_time > 2000000000 ? trade.exit_time / 1000 : trade.exit_time)
      : null;

    const entryIdx = findCandleIndex(rawEntry);
    if (entryIdx < 0) return;

    let exitIdx = (rawExit && !trade.isLiveActive) ? findCandleIndex(rawExit) : -1;
    if (exitIdx < 0) {
      exitIdx = trade.isLiveActive ? rawCandles.value.length - 1 : Math.min(rawCandles.value.length - 1, entryIdx + 6);
    }

    // Use setVisibleLogicalRange: directly scroll to the exact bars with comfortable padding
    const fromLogical = Math.max(0, entryIdx - 20);
    const toLogical = Math.min(rawCandles.value.length + 15, Math.max(entryIdx + 20, exitIdx + 20));

    chart.timeScale().setVisibleLogicalRange({
      from: fromLogical,
      to: toLogical,
    });
    chart.priceScale('right').applyOptions({ autoScale: true });

    requestAnimationFrame(() => {
      updateBoxCoordinates();
    });
    setTimeout(() => {
      updateBoxCoordinates();
    }, 50);
    setTimeout(() => {
      updateBoxCoordinates();
    }, 180);
    setTimeout(() => {
      updateBoxCoordinates();
    }, 350);
  } catch (err) {
    console.warn('[ChartCanvas] centerOnTrade error:', err);
  }
};

// Jump navigation methods
const prevJump = () => {
  if (selectedSignalIndex.value > 0) {
    isInspectingTrade.value = true;
    selectedSignalIndex.value--;
    centerOnTrade(allInspectableSignals.value[selectedSignalIndex.value]);
    nextTick(() => updateBoxCoordinates());
  }
};

const nextJump = () => {
  if (selectedSignalIndex.value < allInspectableSignals.value.length - 1) {
    isInspectingTrade.value = true;
    selectedSignalIndex.value++;
    centerOnTrade(allInspectableSignals.value[selectedSignalIndex.value]);
    nextTick(() => updateBoxCoordinates());
  }
};

const jumpToIndex = (idx: number) => {
  if (idx >= 0 && idx < allInspectableSignals.value.length) {
    isInspectingTrade.value = true;
    selectedSignalIndex.value = idx;
    centerOnTrade(allInspectableSignals.value[idx]);
    nextTick(() => updateBoxCoordinates());
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

const dismissInspection = () => {
  isInspectingTrade.value = false;
  positionBoxes.value = [];
  emit('dismissSignal');
};

// Global Hotkeys for Jumping [Left Arrow / '[' : Prev, Right Arrow / ']' : Next, Esc: Dismiss]
const handleKeyDown = (e: KeyboardEvent) => {
  if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
  if (e.key === 'ArrowLeft' || e.key === '[') {
    prevJump();
  } else if (e.key === 'ArrowRight' || e.key === ']') {
    nextJump();
  } else if (e.key === 'Escape') {
    dismissInspection();
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
      };

      if (indicatorCalculator) {
        const hoverTime = Number(param.time);
        const idx = timeIndexMap.get(hoverTime);
        if (idx !== undefined) {
          currentHudItems.value = indicatorCalculator.getHudItems(idx);
        }
      }
    }
  });

  // Chart click handler: clicking on or near any trade entry/exit selects and inspects that trade
  chart.subscribeClick((param) => {
    if (!param.time || allInspectableSignals.value.length === 0) return;
    const clickedTime = Number(param.time);
    const clickedIdx = timeIndexMap.get(clickedTime) ?? findCandleIndex(clickedTime);
    if (clickedIdx < 0) return;

    let bestIdx = -1;
    let minDistance = 5; // within 4 bars

    for (let i = 0; i < allInspectableSignals.value.length; i++) {
      const s = allInspectableSignals.value[i];
      const sEntry = s.entry_time > 2000000000 ? s.entry_time / 1000 : s.entry_time;
      const sEntryIdx = findCandleIndex(sEntry);
      if (sEntryIdx >= 0) {
        const dist = Math.abs(sEntryIdx - clickedIdx);
        if (dist < minDistance) {
          minDistance = dist;
          bestIdx = i;
        }
      }
      if (s.exit_time) {
        const sExit = s.exit_time > 2000000000 ? s.exit_time / 1000 : s.exit_time;
        const sExitIdx = findCandleIndex(sExit);
        if (sExitIdx >= 0) {
          const dist = Math.abs(sExitIdx - clickedIdx);
          if (dist < minDistance) {
            minDistance = dist;
            bestIdx = i;
          }
        }
      }
    }

    if (bestIdx !== -1) {
      isInspectingTrade.value = true;
      selectedSignalIndex.value = bestIdx;
      updateBoxCoordinates();
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

const applyStrategyIndicators = () => {
  if (!chart || !rawCandles.value || rawCandles.value.length === 0) return;

  const profile = getStrategyIndicatorProfile(props.selectedStrategy);
  currentProfile.value = profile;

  // 1. Remove obsolete series from chart that are not in the new profile
  const currentConfigIds = new Set(profile.seriesConfigs.map((c) => c.id));
  for (const [id, s] of activeIndicatorSeries.entries()) {
    if (!currentConfigIds.has(id)) {
      try {
        chart.removeSeries(s);
      } catch (e) {}
      activeIndicatorSeries.delete(id);
    }
  }

  // 2. Add or reconfigure series for current profile
  for (const cfg of profile.seriesConfigs) {
    if (!activeIndicatorSeries.has(cfg.id)) {
      const s = chart.addLineSeries({
        color: cfg.color,
        lineWidth: (cfg.lineWidth || 1.5) as any,
        lineStyle: (cfg.lineStyle ?? 0) as any,
        title: cfg.title,
      });
      activeIndicatorSeries.set(cfg.id, s);
    } else {
      const s = activeIndicatorSeries.get(cfg.id)!;
      s.applyOptions({
        color: cfg.color,
        lineWidth: (cfg.lineWidth || 1.5) as any,
        lineStyle: (cfg.lineStyle ?? 0) as any,
        title: cfg.title,
      });
    }
  }

  // 3. Prepare formatted candles
  const candles = rawCandles.value.map((c: any) => ({
    ...c,
    time: timeToLocal(Number(c.time)) as Time,
  }));

  // Rebuild timeIndexMap
  timeIndexMap.clear();
  candles.forEach((c: any, idx: number) => {
    timeIndexMap.set(Number(c.time), idx);
  });

  // 4. Calculate indicators
  indicatorCalculator = profile.calculate(candles);

  // 5. Populate series data
  for (const cfg of profile.seriesConfigs) {
    const s = activeIndicatorSeries.get(cfg.id);
    const data = indicatorCalculator.seriesData[cfg.id] || [];
    s?.setData(data);
  }

  // 6. Populate HUD items for latest candle
  const lastIdx = candles.length - 1;
  currentHudItems.value = indicatorCalculator.getHudItems(lastIdx);
};

const loadCandles = async (preserveViewport = false) => {
  if (!candleSeries || !chart) return;
  loadingCandles.value = true;

  try {
    const savedRange = (preserveViewport && chart) ? chart.timeScale().getVisibleLogicalRange() : null;
    const isSp = isSpStrategy.value || selectedSymbol.value.includes('SP') || selectedSymbol.value.includes('ES') || selectedSymbol.value.includes('S&P');
    const isGold = isGoldStrategy.value || selectedSymbol.value.toLowerCase().includes('xau');
    const apiSym = isSp ? 'S&P 500 (ES)' : (isGold ? 'XAUUSD' : selectedSymbol.value);
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

      // Dedicated Quantitative Indicators
      applyStrategyIndicators();

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
        };
      }

      // Apply markers if present
      if (props.tradeMarkers && props.tradeMarkers.length > 0) {
        applyMarkers(props.tradeMarkers);
      }

      if (preserveViewport && savedRange) {
        chart.timeScale().setVisibleLogicalRange(savedRange);
        redrawTradeBoxes();
        return;
      }

      // If a targeted signal is set, prioritize finding and centering on it
      let targetIdx = -1;
      if (props.targetedSignal) {
        const s = props.targetedSignal;
        const targetTime = s.time ? Number(s.time) : ((s as any).timestamp ? Math.floor((s as any).timestamp / 1000) : 0);
        targetIdx = allInspectableSignals.value.findIndex((sig) =>
          (s.id != null && String(sig.id) === String(s.id)) ||
          (targetTime && Math.abs(sig.entry_time - targetTime) < 2)
        );
      }
      if (targetIdx !== -1) {
        isInspectingTrade.value = true;
        selectedSignalIndex.value = targetIdx;
        centerOnTrade(allInspectableSignals.value[targetIdx]);
      } else if (isInspectingTrade.value && allInspectableSignals.value.length > 0) {
        const idx = Math.min(selectedSignalIndex.value, allInspectableSignals.value.length - 1);
        selectedSignalIndex.value = idx;
        centerOnTrade(allInspectableSignals.value[idx]);
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

    formatted.sort((a, b) => Number(a.time) - Number(b.time));
    candleSeries.setMarkers(formatted);
  } catch (e) {
    console.warn('[ChartCanvas] Error applying markers:', e);
  }
};

const updateLiveCandle = (candleData: { time: number; open: number; high: number; low: number; close: number; volume?: number }) => {
  if (!candleSeries || !candleData || !candleData.time || !candleData.close || candleData.close <= 0) return;
  if (!rawCandles.value || rawCandles.value.length === 0) return;

  const rawTime = Number(candleData.time);
  const open = Number(candleData.open || candleData.close);
  const high = Math.max(Number(candleData.high || candleData.close), open, Number(candleData.close));
  const low = Math.min(Number(candleData.low || candleData.close), open, Number(candleData.close));
  const close = Number(candleData.close);
  const volume = Number(candleData.volume || 10);

  const lastCandle = rawCandles.value[rawCandles.value.length - 1];
  const lastTime = Number(lastCandle.time);

  const isGold = isGoldStrategy.value || selectedSymbol.value.toLowerCase().includes('xau');
  const isSp = isSpStrategy.value || selectedSymbol.value.includes('SP') || selectedSymbol.value.includes('ES');
  const expectedStep = (isGold || isSp) ? 60 : 900;

  // If a huge gap is detected (more than 3 bars missed), schedule background full sync
  if (rawTime - lastTime > expectedStep * 3) {
    loadCandles(true);
    return;
  }

  const localTime = timeToLocal(rawTime) as Time;

  if (rawTime === lastTime) {
    // In-place update of current forming candle
    lastCandle.high = Math.max(lastCandle.high, high);
    lastCandle.low = Math.min(lastCandle.low, low);
    lastCandle.close = close;
    if (candleData.volume != null) lastCandle.volume = volume;

    candleSeries.update({
      time: localTime,
      open: lastCandle.open,
      high: lastCandle.high,
      low: lastCandle.low,
      close: lastCandle.close,
    });

    if (volumeSeries && lastCandle.volume != null) {
      volumeSeries.update({
        time: localTime,
        value: lastCandle.volume,
        color: lastCandle.close >= lastCandle.open ? 'rgba(38, 166, 154, 0.6)' : 'rgba(239, 83, 80, 0.6)',
      });
    }
  } else if (rawTime > lastTime) {
    // Brand new bar started!
    const newBar = {
      time: rawTime,
      open: open,
      high: high,
      low: low,
      close: close,
      volume: volume,
    };
    rawCandles.value.push(newBar);
    timeIndexMap.set(rawTime, rawCandles.value.length - 1);

    candleSeries.update({
      time: localTime,
      open: newBar.open,
      high: newBar.high,
      low: newBar.low,
      close: newBar.close,
    });

    if (volumeSeries) {
      volumeSeries.update({
        time: localTime,
        value: newBar.volume,
        color: newBar.close >= newBar.open ? 'rgba(38, 166, 154, 0.6)' : 'rgba(239, 83, 80, 0.6)',
      });
    }

    // Keep indicators synchronized
    applyStrategyIndicators();
  }

  // Update HUD and Legend
  legendData.value = {
    open: rawTime === lastTime ? lastCandle.open : open,
    high: rawTime === lastTime ? lastCandle.high : high,
    low: rawTime === lastTime ? lastCandle.low : low,
    close: close,
    volume: rawTime === lastTime ? lastCandle.volume : volume,
    changePct: open ? ((close - open) / open) * 100 : 0,
  };

  // Redraw trade boxes so live trades follow the new bar
  redrawTradeBoxes();
};

// Live price streams
const startLiveFeeds = () => {
  const isSp = isSpStrategy.value || selectedSymbol.value.includes('SP') || selectedSymbol.value.includes('ES') || selectedSymbol.value.includes('S&P');
  const isGold = isGoldStrategy.value || selectedSymbol.value.toLowerCase().includes('xau');

  if (isSp) {
    isWsConnected.value = true;
    const pollSp500 = async () => {
      try {
        const res = await fetch('/api/sp500/quote');
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
          const q = data.quote;
          const barBucket = Math.floor((q.timestamp || Date.now() / 1000) / 60) * 60;
          updateLiveCandle({
            time: barBucket,
            open: q.open ?? p,
            high: q.high ?? p,
            low: q.low ?? p,
            close: p,
            volume: q.volume ?? 100
          });
        }
      } catch {}
    };
    pollSp500();
    oandaTimer = setInterval(pollSp500, 2000);
  } else if (isGold) {
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
        if (data?.quote?.candle) {
          updateLiveCandle(data.quote.candle);
        } else if (data?.quote?.price) {
          const p = parseFloat(data.quote.price);
          const nowSec = data.quote.timestamp ? Number(data.quote.timestamp) : Math.floor(Date.now() / 1000);
          const barBucket = Math.floor(nowSec / 60) * 60;
          updateLiveCandle({
            time: barBucket,
            open: p,
            high: p,
            low: p,
            close: p,
            volume: 20
          });
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
          if (msg?.k) {
            const k = msg.k;
            const p = parseFloat(k.c);
            if (!isNaN(p) && p > 0) {
              if (lastLivePrice.value !== null) {
                priceFlash.value = p >= lastLivePrice.value ? 'up' : 'down';
                setTimeout(() => { priceFlash.value = null; }, 500);
              }
              lastLivePrice.value = p;
            }
            const barTimeSec = Math.floor(k.t / 1000);
            updateLiveCandle({
              time: barTimeSec,
              open: parseFloat(k.o),
              high: parseFloat(k.h),
              low: parseFloat(k.l),
              close: p,
              volume: parseFloat(k.v)
            });
          }
        } catch {}
      };
      binanceWs.onclose = () => { isWsConnected.value = false; };
    } catch {}
  }

  // Periodic non-intrusive full candle reconciliation (every 60s)
  periodicSyncTimer = setInterval(() => {
    loadCandles(true);
  }, 60000);
};

const stopLiveFeeds = () => {
  if (oandaTimer) {
    clearInterval(oandaTimer);
    oandaTimer = null;
  }
  if (periodicSyncTimer) {
    clearInterval(periodicSyncTimer);
    periodicSyncTimer = null;
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
    const s = newStrat.toLowerCase();
    const isSp = s.includes('sp') || s.includes('es') || s.includes('opening');
    const isGold = s.includes('xau') || s.includes('gold') || s.includes('goat');
    const newSymbol = isSp ? 'S&P 500 (ES)' : (isGold ? 'XAU/USD' : 'BTC/USDT');
    if (selectedSymbol.value !== newSymbol) {
      selectedSymbol.value = newSymbol;
    } else {
      // Same symbol: immediately update dedicated visual indicators on existing candles
      applyStrategyIndicators();
      nextTick(() => {
        if (props.targetedSignal) {
          applyTargetedSignal(props.targetedSignal);
        } else if (allInspectableSignals.value.length > 0) {
          jumpToLatest();
        }
      });
    }
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
  if (props.targetedSignal) {
    applyTargetedSignal(props.targetedSignal);
    return;
  }
  if (isInspectingTrade.value && allInspectableSignals.value.length > 0) {
    const idx = Math.min(selectedSignalIndex.value, allInspectableSignals.value.length - 1);
    selectedSignalIndex.value = idx;
    centerOnTrade(allInspectableSignals.value[idx]);
    nextTick(() => updateBoxCoordinates());
  }
}, { deep: true });

watch(() => selectedSignalIndex.value, (newIdx) => {
  if (isInspectingTrade.value && allInspectableSignals.value[newIdx]) {
    centerOnTrade(allInspectableSignals.value[newIdx]);
  }
  nextTick(() => {
    updateBoxCoordinates();
  });
});

watch(inspectedSignal, () => {
  nextTick(() => {
    updateBoxCoordinates();
  });
});

const applyTargetedSignal = (target: SignalData | InspectableSignal | null) => {
  if (!target) return;
  isInspectingTrade.value = true;
  const pair = (target as any).pair || '';
  const strat = (target as any).strategy || '';
  const isSp = pair.includes('SP') || pair.includes('ES') || strat.toLowerCase().includes('sp') || strat.toLowerCase().includes('opening');
  const isGold = pair.includes('XAU') || strat.toLowerCase().includes('xau') || strat.toLowerCase().includes('gold') || strat.toLowerCase().includes('goat');
  const neededSymbol = isSp ? 'S&P 500 (ES)' : (isGold ? 'XAU/USD' : 'BTC/USDT');
  if (selectedSymbol.value !== neededSymbol) {
    selectedSymbol.value = neededSymbol;
  }

  const targetTime = (target as any).time ? Number((target as any).time) : ((target as any).timestamp ? Math.floor((target as any).timestamp / 1000) : 0);
  nextTick(() => {
    const idx = allInspectableSignals.value.findIndex((s) =>
      (target.id != null && String(s.id) === String(target.id)) ||
      (targetTime && Math.abs(s.entry_time - targetTime) < 2)
    );
    if (idx !== -1) {
      selectedSignalIndex.value = idx;
      centerOnTrade(allInspectableSignals.value[idx]);
    } else if (allInspectableSignals.value.length > 0) {
      selectedSignalIndex.value = allInspectableSignals.value.length - 1;
      centerOnTrade(allInspectableSignals.value[selectedSignalIndex.value]);
    }
  });
};

watch(() => props.targetedSignal, (newTarget) => {
  if (newTarget) {
    isInspectingTrade.value = true;
    applyTargetedSignal(newTarget);
  } else {
    isInspectingTrade.value = false;
    positionBoxes.value = [];
  }
}, { deep: true, immediate: true });

watch(() => props.isActiveScreen, (active) => {
  if (active) {
    nextTick(() => {
      if (chartContainerRef.value && chart) {
        chart.applyOptions({
          width: chartContainerRef.value.clientWidth,
          height: chartContainerRef.value.clientHeight,
        });
      }
      if (isInspectingTrade.value && inspectedSignal.value) {
        centerOnTrade(inspectedSignal.value);
      }
      setTimeout(() => {
        updateBoxCoordinates();
      }, 50);
      setTimeout(() => {
        updateBoxCoordinates();
      }, 150);
      setTimeout(() => {
        updateBoxCoordinates();
      }, 300);
    });
  }
});

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
  for (const s of activeIndicatorSeries.values()) {
    try {
      chart?.removeSeries(s);
    } catch {}
  }
  activeIndicatorSeries.clear();
  if (chart) {
    chart.remove();
    chart = null;
  }
});
</script>

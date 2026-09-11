<template>
  <div class="relative w-full h-full flex flex-col font-mono select-none overflow-hidden bg-base-100">
    <!-- Top Bar: Strategy Selector (Left), Trades / Jumps Navigator (Center), Live Price (Right) -->
    <div class="h-11 bg-base-200/95 backdrop-blur-md border-b border-base-content/10 px-3 flex items-center justify-between z-20 text-xs shrink-0 gap-2">
      
      <!-- ── Left: Strategy Selector Dropdown & Symbol ── -->
      <div class="flex items-center gap-2 shrink-0">
        <!-- Strategy Selector -->
        <div class="dropdown dropdown-bottom" v-if="strategies && strategies.length > 0">
          <label tabindex="0" class="btn btn-xs btn-outline btn-primary gap-1.5 font-bold font-mono tracking-tight shadow-sm hover:scale-[1.01] transition-transform">
            <Sparkles class="w-3 h-3 text-primary shrink-0" />
            <span class="truncate max-w-[150px] sm:max-w-[220px]">{{ cleanStrategyName }}</span>
            <ChevronDown class="w-3 h-3 opacity-60 shrink-0" />
          </label>
          <ul tabindex="0" class="dropdown-content menu p-1.5 shadow-2xl bg-base-300 rounded-box w-72 max-h-80 overflow-y-auto z-50 border border-base-content/15 text-xs space-y-0.5">
            <li class="menu-title text-[10px] uppercase font-bold text-base-content/50 px-2 py-1">Active Quant Strategies</li>
            <li v-for="strat in strategies" :key="strat.name">
              <button 
                @click="emit('selectStrategy', strat.name)"
                class="flex items-center justify-between py-1.5 px-2 rounded-md hover:bg-base-200"
                :class="strat.name === selectedStrategy ? 'active font-bold bg-primary/10 text-primary' : ''"
              >
                <div class="flex items-center gap-2 truncate">
                  <span class="w-1.5 h-1.5 rounded-full" :class="strat.name.toLowerCase().includes('xau') ? 'bg-warning' : 'bg-info'" />
                  <span class="truncate font-mono">{{ strat.name.replace('.py', '') }}</span>
                </div>
                <div class="flex items-center gap-1 shrink-0">
                  <span v-if="strat.name === activeStrategy" class="badge badge-xs badge-success text-[9px] font-bold">BOT</span>
                  <span v-if="strat.name === selectedStrategy" class="text-primary font-bold ml-1">✓</span>
                </div>
              </button>
            </li>
          </ul>
        </div>

        <!-- Symbol / Asset Tag -->
        <div class="hidden sm:flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-base-300/80 border border-base-content/10 text-[11px] font-bold">
          <span>{{ isGoldStrategy ? '🟡 XAU/USD' : '🔵 BTC/USDT' }}</span>
          <span class="text-[9px] opacity-60 uppercase">{{ isGoldStrategy ? 'Spot' : 'Binance' }}</span>
        </div>
      </div>

      <!-- ── Center: Trades & Jumps Navigator ── -->
      <div class="flex items-center gap-1 shrink-0">
        <template v-if="allInspectableSignals.length > 0">
          <div class="join shadow-sm border border-base-content/15 bg-base-300/70 rounded-lg p-0.5 items-center">
            <!-- Prev Jump Button -->
            <button
              @click="prevJump"
              :disabled="selectedSignalIndex <= 0"
              class="btn btn-xs btn-ghost join-item px-2 font-bold text-[11px] disabled:opacity-20 hover:bg-base-100"
              title="Jump to Previous Trade [HotKey: Left Arrow or '[']"
            >
              ◀
            </button>

            <!-- Jump Index & Trade Dropdown Selector -->
            <div class="dropdown dropdown-bottom dropdown-center join-item">
              <label 
                tabindex="0" 
                class="btn btn-xs btn-ghost gap-1.5 px-2.5 font-mono text-[11px] hover:bg-base-100 normal-case cursor-pointer"
                title="Click to select any trade to jump directly to it on chart"
              >
                <span class="text-primary font-bold">
                  #{{ selectedSignalIndex + 1 }}<span class="opacity-50">/{{ allInspectableSignals.length }}</span>
                </span>
                
                <!-- Trade badge preview -->
                <span 
                  v-if="inspectedSignal?.isLiveActive"
                  class="badge badge-xs badge-success font-bold animate-pulse text-[9px]"
                >
                  LIVE {{ inspectedSignal.side }}
                </span>
                <span 
                  v-else-if="inspectedSignal"
                  class="badge badge-xs text-[9px] font-bold"
                  :class="(inspectedSignal.pnl_pct || 0) >= 0 ? 'badge-success text-success-content' : 'badge-error text-error-content'"
                >
                  {{ inspectedSignal.side }} {{ (inspectedSignal.pnl_pct || 0) >= 0 ? '+' : '' }}{{ (inspectedSignal.pnl_pct || 0).toFixed(2) }}%
                </span>

                <ChevronDown class="w-2.5 h-2.5 opacity-50" />
              </label>

              <!-- Dropdown List of All Trades to Jump To -->
              <ul tabindex="0" class="dropdown-content menu p-1 shadow-2xl bg-base-300 rounded-box w-72 max-h-72 overflow-y-auto z-50 border border-base-content/15 text-[11px] space-y-0.5 font-mono">
                <li class="menu-title text-[9px] uppercase font-bold text-base-content/50 px-2 py-1 flex items-center justify-between">
                  <span>Select Trade Jump</span>
                  <span class="text-primary">{{ allInspectableSignals.length }} Trades</span>
                </li>
                <li v-for="(sig, idx) in allInspectableSignals" :key="sig.id">
                  <button 
                    @click="jumpToIndex(idx)"
                    class="flex items-center justify-between py-1 px-2 rounded hover:bg-base-200"
                    :class="idx === selectedSignalIndex ? 'active font-bold bg-primary/10 text-primary' : ''"
                  >
                    <div class="flex items-center gap-1.5">
                      <span class="text-base-content/50 text-[10px]">#{{ idx + 1 }}</span>
                      <span class="badge badge-xs font-bold text-[9px]" :class="sig.side === 'BUY' || sig.side === 'LONG' ? 'badge-success' : 'badge-error'">
                        {{ sig.side }}
                      </span>
                      <span class="text-[10px]">${{ formatPrice(sig.entry_price) }}</span>
                    </div>
                    <div class="flex items-center gap-1">
                      <span 
                        class="text-[10px] font-bold font-mono"
                        :class="(sig.pnl_pct || 0) >= 0 ? 'text-success' : 'text-error'"
                      >
                        {{ (sig.pnl_pct || 0) >= 0 ? '+' : '' }}{{ (sig.pnl_pct || 0).toFixed(2) }}%
                      </span>
                      <span v-if="sig.isLiveActive" class="badge badge-xs badge-success text-[8px] font-bold">LIVE</span>
                    </div>
                  </button>
                </li>
              </ul>
            </div>

            <!-- Next Jump Button -->
            <button
              @click="nextJump"
              :disabled="selectedSignalIndex >= allInspectableSignals.length - 1"
              class="btn btn-xs btn-ghost join-item px-2 font-bold text-[11px] disabled:opacity-20 hover:bg-base-100"
              title="Jump to Next Trade [HotKey: Right Arrow or ']']"
            >
              ▶
            </button>
          </div>

          <!-- Quick Jump: Latest Trade -->
          <button
            @click="jumpToLatest"
            class="btn btn-xs btn-ghost border border-base-content/15 text-[10px] uppercase font-bold tracking-wider hover:bg-base-200 hidden md:inline-flex"
            title="Jump view to most recent trade"
          >
            Latest
          </button>

          <!-- Quick Jump: Active Live Trade (pulsing if active) -->
          <button
            v-if="hasActiveLiveTrade"
            @click="jumpToActive"
            class="btn btn-xs btn-success text-success-content font-bold text-[10px] uppercase gap-1 animate-pulse"
            title="Jump view to open live position"
          >
            <span class="w-1.5 h-1.5 rounded-full bg-base-100" />
            Active Live
          </button>
        </template>

        <div v-else class="flex items-center gap-1.5 px-3 py-1 rounded bg-base-300/60 border border-base-content/10 text-base-content/60 text-[11px]">
          <span class="w-2 h-2 rounded-full bg-info animate-ping" />
          <span>Scanning historical trades...</span>
        </div>
      </div>

      <!-- ── Right: Live Ticker & Connection ── -->
      <div class="flex items-center gap-2 shrink-0">
        <!-- Live Spot Price Readout -->
        <div 
          v-if="lastLivePrice" 
          class="badge font-bold font-mono py-2.5 px-3 transition-all duration-300 text-xs shadow-sm"
          :class="priceFlash === 'up' ? 'badge-success text-success-content' : priceFlash === 'down' ? 'badge-error text-error-content' : 'badge-neutral bg-base-300 text-base-content'"
        >
          <span>${{ lastLivePrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}</span>
        </div>

        <div class="badge badge-xs gap-1 font-bold py-1.5 px-2" :class="isWsConnected ? 'badge-success text-success-content' : 'badge-warning text-warning-content'">
          <span class="w-1.5 h-1.5 rounded-full" :class="isWsConnected ? 'bg-success-content animate-pulse' : 'bg-warning-content'" />
          <span class="hidden md:inline">{{ isWsConnected ? 'LIVE' : 'SYNC' }}</span>
        </div>
      </div>
    </div>

    <!-- ── Indicator & Trade Coordinates HUD Bar ── -->
    <div class="h-7 bg-base-200/50 backdrop-blur-xs border-b border-base-content/10 px-3 flex items-center gap-3 text-[11px] font-mono text-base-content/80 overflow-x-auto shrink-0 z-10 select-text">
      
      <!-- 1. Candlestick Coordinates (Crosshair or Latest) -->
      <div v-if="legendData.open !== undefined" class="flex items-center gap-2 shrink-0">
        <span class="text-base-content/40 font-bold uppercase text-[9px]">Candle:</span>
        <span>O: <strong class="text-base-content">{{ formatPrice(legendData.open) }}</strong></span>
        <span>H: <strong class="text-base-content">{{ formatPrice(legendData.high) }}</strong></span>
        <span>L: <strong class="text-base-content">{{ formatPrice(legendData.low) }}</strong></span>
        <span>C: <strong class="text-base-content">{{ formatPrice(legendData.close) }}</strong></span>
        <span v-if="legendData.changePct !== undefined" :class="legendData.changePct >= 0 ? 'text-success font-bold' : 'text-error font-bold'">
          {{ legendData.changePct >= 0 ? '+' : '' }}{{ legendData.changePct?.toFixed(2) }}%
        </span>
        <span class="text-base-content/60">Vol: <strong class="text-base-content">{{ legendData.volume?.toLocaleString() || '–' }}</strong></span>
      </div>

      <div class="h-3 w-[1px] bg-base-content/20 shrink-0" />

      <!-- 2. Technical Indicator Coordinates -->
      <div class="flex items-center gap-2.5 shrink-0">
        <span class="text-base-content/40 font-bold uppercase text-[9px]">Indicators:</span>
        <span v-if="legendData.ema9" class="text-sky-400">EMA9: <strong>{{ formatPrice(legendData.ema9) }}</strong></span>
        <span v-if="legendData.ema21" class="text-indigo-400">EMA21: <strong>{{ formatPrice(legendData.ema21) }}</strong></span>
        <span v-if="legendData.ema200" class="text-amber-400">EMA200: <strong>{{ formatPrice(legendData.ema200) }}</strong></span>
        <span v-if="legendData.hh15" class="text-emerald-400">HH15: <strong>{{ formatPrice(legendData.hh15) }}</strong></span>
        <span v-if="legendData.ll15" class="text-rose-400">LL15: <strong>{{ formatPrice(legendData.ll15) }}</strong></span>
        <span v-if="legendData.bbUpper" class="text-purple-400">BB: <strong>[{{ formatPrice(legendData.bbUpper) }} - {{ formatPrice(legendData.bbLower) }}]</strong></span>
        <span v-if="legendData.hurst" class="text-pink-400">Hurst: <strong>{{ legendData.hurst?.toFixed(3) }}</strong></span>
      </div>

      <!-- 3. Target Trade Coordinates (When inspecting a jump) -->
      <template v-if="inspectedSignal">
        <div class="h-3 w-[1px] bg-base-content/20 shrink-0" />
        <div class="flex items-center gap-2.5 shrink-0 bg-base-300/60 px-2 py-0.5 rounded border border-base-content/10">
          <span class="text-primary font-bold uppercase text-[9px]">Trade #{{ selectedSignalIndex + 1 }} Coordinates:</span>
          <span class="text-info font-semibold">Entry: ${{ formatPrice(inspectedSignal.entry_price) }}</span>
          <span class="text-error font-semibold">SL: ${{ formatPrice(inspectedSignal.stop_loss) }}</span>
          <span class="text-success font-semibold">TP: ${{ formatPrice(inspectedSignal.take_profit) }}</span>
          <span v-if="tradeRiskReward" class="text-warning font-semibold">R:R {{ tradeRiskReward }}</span>
          <span 
            class="font-bold font-mono"
            :class="(inspectedSignal.pnl_pct || 0) >= 0 ? 'text-success' : 'text-error'"
          >
            Result: {{ (inspectedSignal.pnl_pct || 0) >= 0 ? '+' : '' }}{{ (inspectedSignal.pnl_pct || 0).toFixed(2) }}%
          </span>
          <span v-if="inspectedSignal.exit_reason" class="badge badge-xs badge-neutral text-[9px] opacity-75">
            {{ inspectedSignal.exit_reason }}
          </span>
        </div>
      </template>
    </div>

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
import { ChevronDown, Sparkles } from 'lucide-vue-next';
import type { SignalData } from '../composables/useWebSocket';

interface TradeDetail {
  id: number;
  entry_time: number;
  entry_price: number;
  stop_loss: number;
  take_profit: number;
  exit_time?: number;
  exit_price?: number;
  exit_reason?: string;
  pnl_pct?: number;
}

interface StrategyItem {
  name: string;
  path?: string;
  size_bytes?: number;
  last_modified?: number;
  [key: string]: any;
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

// Indicator Calculation Utilities
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

function calculateBollingerBands(data: { time: Time; close: number }[], period: number = 20, mult: number = 2.0) {
  if (!data || data.length === 0) return { upper: [], middle: [], lower: [] };
  const upper: { time: Time; value: number }[] = [];
  const middle: { time: Time; value: number }[] = [];
  const lower: { time: Time; value: number }[] = [];

  for (let i = 0; i < data.length; i++) {
    const start = Math.max(0, i - period + 1);
    let sum = 0;
    const count = i - start + 1;
    for (let j = start; j <= i; j++) {
      sum += data[j].close;
    }
    const sma = sum / count;
    let sumSq = 0;
    for (let j = start; j <= i; j++) {
      const diff = data[j].close - sma;
      sumSq += diff * diff;
    }
    const std = Math.sqrt(sumSq / count);
    const up = Number((sma + mult * std).toFixed(2));
    const mid = Number(sma.toFixed(2));
    const dn = Number((sma - mult * std).toFixed(2));
    const time = data[i].time;
    upper.push({ time, value: up });
    middle.push({ time, value: mid });
    lower.push({ time, value: dn });
  }
  return { upper, middle, lower };
}

function calculateHHLL(data: { time: Time; high: number; low: number }[], period: number = 15) {
  if (!data || data.length === 0) return { hh: [], ll: [] };
  const hh: { time: Time; value: number }[] = [];
  const ll: { time: Time; value: number }[] = [];

  for (let i = 0; i < data.length; i++) {
    if (i < 1) continue;
    const start = Math.max(0, i - period);
    const end = i;
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
  if (!rawCandles.value || rawCandles.value.length === 0) return 0;
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
  try {
    const rawEntry = trade.entry_time > 2000000000 ? trade.entry_time / 1000 : trade.entry_time;
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
    const res = await fetch(`/api/candles?symbol=${encodeURIComponent(apiSym)}&count=4000&mode=live`);
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
  if (!candleSeries) return;
  try {
    const formatted = markers.map((m) => ({
      time: (typeof m.time === 'number' && m.time > 2000000000 ? timeToLocal(m.time / 1000) : timeToLocal(m.time)) as Time,
      position: m.position || (m.action === 'BUY' ? 'belowBar' : 'aboveBar'),
      color: m.color || (m.action === 'BUY' ? '#26a69a' : '#ef5350'),
      shape: m.shape || (m.action === 'BUY' ? 'arrowUp' : 'arrowDown'),
      text: m.text || m.action || 'SIGNAL',
    }));
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
  if (newMarkers) applyMarkers(newMarkers);
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

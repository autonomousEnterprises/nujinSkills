<template>
  <div class="h-7 bg-base-200/50 backdrop-blur-xs border-b border-base-content/10 px-3 flex items-center gap-3 text-[11px] font-mono text-base-content/80 overflow-x-auto shrink-0 z-10 select-text">
    <!-- 1. Candlestick Coordinates (Crosshair or Latest) -->
    <div v-if="legendData.open !== undefined" class="flex items-center gap-2 shrink-0">
      <span class="text-base-content/40 font-bold uppercase text-[9px]">Candle:</span>
      <span>O: <strong class="text-base-content">{{ formatPrice(legendData.open, isGoldStrategy || isSpStrategy) }}</strong></span>
      <span>H: <strong class="text-base-content">{{ formatPrice(legendData.high, isGoldStrategy || isSpStrategy) }}</strong></span>
      <span>L: <strong class="text-base-content">{{ formatPrice(legendData.low, isGoldStrategy || isSpStrategy) }}</strong></span>
      <span>C: <strong class="text-base-content">{{ formatPrice(legendData.close, isGoldStrategy || isSpStrategy) }}</strong></span>
      <span v-if="legendData.changePct !== undefined" :class="legendData.changePct >= 0 ? 'text-success font-bold' : 'text-error font-bold'">
        {{ legendData.changePct >= 0 ? '+' : '' }}{{ legendData.changePct?.toFixed(2) }}%
      </span>
      <span class="text-base-content/60">Vol: <strong class="text-base-content">{{ legendData.volume?.toLocaleString() || '–' }}</strong></span>
    </div>

    <div class="h-3 w-[1px] bg-base-content/20 shrink-0" />

    <!-- 2. Technical Indicator Coordinates -->
    <div class="flex items-center gap-2.5 shrink-0">
      <span class="text-base-content/40 font-bold uppercase text-[9px]">Indicators:</span>
      <span v-if="legendData.ema9" class="text-sky-400">EMA9: <strong>{{ formatPrice(legendData.ema9, isGoldStrategy || isSpStrategy) }}</strong></span>
      <span v-if="legendData.ema21" class="text-indigo-400">EMA21: <strong>{{ formatPrice(legendData.ema21, isGoldStrategy || isSpStrategy) }}</strong></span>
      <span v-if="legendData.ema200" class="text-amber-400">EMA200: <strong>{{ formatPrice(legendData.ema200, isGoldStrategy || isSpStrategy) }}</strong></span>
      <span v-if="legendData.hh15" class="text-emerald-400">HH15: <strong>{{ formatPrice(legendData.hh15, isGoldStrategy || isSpStrategy) }}</strong></span>
      <span v-if="legendData.ll15" class="text-rose-400">LL15: <strong>{{ formatPrice(legendData.ll15, isGoldStrategy || isSpStrategy) }}</strong></span>
      <span v-if="legendData.bbUpper" class="text-purple-400">BB: <strong>[{{ formatPrice(legendData.bbUpper, isGoldStrategy || isSpStrategy) }} - {{ formatPrice(legendData.bbLower, isGoldStrategy || isSpStrategy) }}]</strong></span>
      <span v-if="legendData.hurst" class="text-pink-400">Hurst: <strong>{{ legendData.hurst?.toFixed(3) }}</strong></span>
    </div>

    <!-- 3. Target Trade Coordinates (When inspecting a jump) -->
    <template v-if="inspectedSignal">
      <div class="h-3 w-[1px] bg-base-content/20 shrink-0" />
      <div class="flex items-center gap-2.5 shrink-0 bg-base-300/60 px-2 py-0.5 rounded border border-base-content/10">
        <span class="text-primary font-bold uppercase text-[9px]">Trade #{{ selectedSignalIndex + 1 }} Coordinates:</span>
        <span class="text-info font-semibold">Entry: ${{ formatPrice(inspectedSignal.entry_price, isGoldStrategy || isSpStrategy) }}</span>
        <span class="text-error font-semibold">SL: ${{ formatPrice(inspectedSignal.stop_loss, isGoldStrategy || isSpStrategy) }}</span>
        <span class="text-success font-semibold">TP: ${{ formatPrice(inspectedSignal.take_profit, isGoldStrategy || isSpStrategy) }}</span>
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
</template>

<script setup lang="ts">
import type { InspectableSignal } from '../../types';
import { formatPrice } from '../../utils/formatters';

defineProps<{
  legendData: Record<string, any>;
  inspectedSignal?: InspectableSignal | null;
  selectedSignalIndex: number;
  tradeRiskReward?: string;
  isGoldStrategy: boolean;
  isSpStrategy?: boolean;
}>();
</script>

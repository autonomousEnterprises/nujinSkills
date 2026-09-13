<template>
  <div class="h-7 bg-base-200/60 backdrop-blur-xs border-b border-base-content/10 px-3 flex items-center gap-3 text-[11px] font-mono text-base-content/80 overflow-x-auto shrink-0 z-10 select-text">
    <!-- 0. Dedicated Strategy Framework Indicator Badge -->
    <div v-if="strategyProfile" class="flex items-center gap-1.5 shrink-0" :title="strategyProfile.frameworkDescription">
      <span class="badge badge-xs font-bold font-mono text-[9px] uppercase tracking-wider py-1 px-1.5 shadow-xs" :class="strategyProfile.badgeClass">
        <span class="w-1.5 h-1.5 rounded-full bg-current animate-pulse mr-1" />
        {{ strategyProfile.frameworkBadge }}
      </span>
      <div class="h-3 w-[1px] bg-base-content/20 shrink-0" />
    </div>

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

    <!-- 2. Dedicated Strategy Technical Indicator Coordinates -->
    <div class="flex items-center gap-2.5 shrink-0">
      <span class="text-base-content/40 font-bold uppercase text-[9px]">Strategy Alpha:</span>

      <!-- Dynamic Dedicated Indicator Chips -->
      <template v-if="hudItems && hudItems.length > 0">
        <span
          v-for="item in hudItems"
          :key="item.id"
          class="flex items-center gap-1 font-mono text-[11px]"
          :style="{ color: item.color || undefined }"
          :class="item.colorClass || ''"
        >
          <span class="w-1.5 h-1.5 rounded-full shrink-0" :style="{ backgroundColor: item.color || '#38bdf8' }" />
          <span>{{ item.label }}:</span>
          <strong class="text-base-content/95">{{ item.value }}</strong>
        </span>
      </template>

      <!-- Fallback generic indicators if profile not computed yet -->
      <template v-else>
        <span v-if="legendData.ema9" class="text-sky-400">EMA9: <strong>{{ formatPrice(legendData.ema9, isGoldStrategy || isSpStrategy) }}</strong></span>
        <span v-if="legendData.ema21" class="text-indigo-400">EMA21: <strong>{{ formatPrice(legendData.ema21, isGoldStrategy || isSpStrategy) }}</strong></span>
        <span v-if="legendData.ema200" class="text-amber-400">EMA200: <strong>{{ formatPrice(legendData.ema200, isGoldStrategy || isSpStrategy) }}</strong></span>
        <span v-if="legendData.hh15" class="text-emerald-400">HH15: <strong>{{ formatPrice(legendData.hh15, isGoldStrategy || isSpStrategy) }}</strong></span>
        <span v-if="legendData.ll15" class="text-rose-400">LL15: <strong>{{ formatPrice(legendData.ll15, isGoldStrategy || isSpStrategy) }}</strong></span>
        <span v-if="legendData.bbUpper" class="text-purple-400">BB: <strong>[{{ formatPrice(legendData.bbUpper, isGoldStrategy || isSpStrategy) }} - {{ formatPrice(legendData.bbLower, isGoldStrategy || isSpStrategy) }}]</strong></span>
        <span v-if="legendData.hurst" class="text-pink-400">Hurst: <strong>{{ legendData.hurst?.toFixed(3) }}</strong></span>
      </template>
    </div>

    <!-- 3. Target Trade Coordinates (When inspecting a jump) -->
    <template v-if="inspectedSignal && isInspectingTrade">
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
        <button
          @click="emit('dismissInspection')"
          class="btn btn-ghost btn-xs h-5 min-h-0 px-1.5 text-[10px] text-base-content/60 hover:text-error hover:bg-base-200 ml-1 gap-1"
          title="Dismiss trade box and return to clean chart"
        >
          <span>✕</span>
          <span class="hidden sm:inline text-[9px]">Close Box</span>
        </button>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import type { InspectableSignal } from '../../types';
import type { IndicatorChipData, StrategyIndicatorProfile } from '../../utils/indicators';
import { formatPrice } from '../../utils/formatters';

defineProps<{
  legendData: Record<string, any>;
  inspectedSignal?: InspectableSignal | null;
  selectedSignalIndex: number;
  tradeRiskReward?: string;
  isGoldStrategy: boolean;
  isSpStrategy?: boolean;
  hudItems?: IndicatorChipData[];
  strategyProfile?: StrategyIndicatorProfile | null;
  isInspectingTrade?: boolean;
}>();

const emit = defineEmits<{
  (e: 'dismissInspection'): void;
}>();
</script>

<template>
  <div class="card bg-base-200 border border-base-content/10 p-5 space-y-4">
    <div class="flex flex-wrap items-center justify-between border-b border-base-content/10 pb-3 gap-3">
      <div class="flex items-center gap-3">
        <span class="font-bold text-sm flex items-center gap-2 text-success">
          <Zap class="w-4 h-4 fill-current" />
          CURRENT ACTIVE OPEN POSITIONS ({{ openPositions.length }} IN FLIGHT)
        </span>
        <span 
          class="badge badge-sm font-bold gap-1.5"
          :class="openPositions.length > 0 ? 'badge-success badge-outline bg-success/10 text-success' : 'badge-neutral bg-base-300 text-base-content/50'"
        >
          <span v-if="openPositions.length > 0" class="w-2 h-2 rounded-full bg-success animate-ping" />
          {{ openPositions.length > 0 ? `${openPositions.length} ACTIVE RUNNING` : 'NO OPEN POSITIONS' }}
        </span>
      </div>

      <!-- Spot Market Feeds -->
      <div class="flex items-center gap-2">
        <div class="px-2.5 py-1 rounded-box bg-base-300 border border-base-content/10 text-right">
          <div class="text-[9px] text-warning font-bold uppercase">🟡 OANDA SPOT XAU</div>
          <div class="text-xs font-bold font-mono text-warning">
            {{ liveGoldPrice ? `$${liveGoldPrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '—' }}
          </div>
        </div>
        <div class="px-2.5 py-1 rounded-box bg-base-300 border border-base-content/10 text-right">
          <div class="text-[9px] text-info font-bold uppercase">🔵 BINANCE BTC/USDT</div>
          <div class="text-xs font-bold font-mono text-info">
            {{ liveBtcPrice ? `$${liveBtcPrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '—' }}
          </div>
        </div>
      </div>
    </div>

    <!-- Position Cards Grid -->
    <div v-if="openPositions.length > 0" class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <div 
        v-for="pos in openPositions" 
        :key="pos.id"
        class="card bg-base-300/60 border border-base-content/10 p-4 space-y-3 hover:border-primary/50 transition-all"
      >
        <!-- Card Header -->
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span class="badge badge-sm font-bold" :class="(pos.pair || '').includes('XAU') ? 'badge-warning' : 'badge-info'">
              {{ pos.pair || ((pos.pair || '').includes('XAU') ? 'XAU/USD' : 'BTC/USDT') }}
            </span>
            <span class="text-xs font-bold text-secondary font-mono">{{ pos.strategy || cleanSelectedName }}</span>
          </div>
          <span class="badge badge-sm font-bold" :class="isShort(pos) ? 'badge-error' : 'badge-success'">
            {{ isShort(pos) ? '⬇ SHORT ENTRY' : '⬆ LONG ENTRY' }}
          </span>
        </div>

        <!-- Pricing Grid -->
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 bg-base-100/60 p-2.5 rounded-box border border-base-content/10 text-xs">
          <div>
            <span class="text-[9px] text-base-content/50 uppercase block">Entry</span>
            <span class="font-bold text-accent font-mono">${{ pos.price?.toLocaleString() }}</span>
          </div>
          <div>
            <span class="text-[9px] text-base-content/50 uppercase block">Stop Loss</span>
            <span class="font-bold text-error font-mono">${{ pos.stop_loss?.toLocaleString() || '—' }}</span>
          </div>
          <div>
            <span class="text-[9px] text-base-content/50 uppercase block">Take Profit</span>
            <span class="font-bold text-success font-mono">${{ pos.take_profit?.toLocaleString() || '—' }}</span>
          </div>
          <div>
            <span class="text-[9px] text-base-content/50 uppercase block">Live Spot</span>
            <span class="font-bold font-mono" :class="(pos.pair || '').includes('XAU') ? 'text-warning' : 'text-info'">
              ${{ getLiveSpot(pos) ? getLiveSpot(pos)?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '—' }}
            </span>
          </div>
        </div>

        <!-- Floating PnL & Close Button -->
        <div 
          class="flex items-center justify-between p-3 rounded-box border transition-colors"
          :class="calculateFloatingPnl(pos) >= 0 ? 'bg-success/10 border-success/30' : 'bg-error/10 border-error/30'"
        >
          <div>
            <span class="text-[10px] text-base-content/60 uppercase font-bold block">Unrealized Floating PnL</span>
            <span class="text-2xl font-bold font-mono" :class="calculateFloatingPnl(pos) >= 0 ? 'text-success' : 'text-error'">
              {{ calculateFloatingPnl(pos) >= 0 ? '+' : '' }}{{ calculateFloatingPnl(pos).toFixed(2) }}%
            </span>
          </div>
          <button
            @click="emit('closePosition', pos)"
            :disabled="actionLoading"
            class="btn btn-sm btn-error shadow font-bold text-xs"
          >
            Close Position
          </button>
        </div>

        <!-- AI Reasoning Box -->
        <div class="text-xs text-base-content/80 bg-base-100/80 p-2.5 rounded-box border border-base-content/10">
          <div class="text-[10px] font-bold text-secondary mb-1 flex items-center gap-1">
            <MessageSquare class="w-3 h-3" /> QUANT THESIS &amp; TRIGGER:
          </div>
          <p class="leading-relaxed text-[11px] opacity-90">
            {{ pos.reasoning_md || pos.annotation || 'Quantitative edge setup detected with statistical confirmation.' }}
          </p>
        </div>
      </div>
    </div>

    <!-- Empty state -->
    <div v-else class="py-8 text-center text-xs text-base-content/50 space-y-2">
      <Activity class="w-8 h-8 mx-auto text-base-content/30 animate-pulse" />
      <div class="font-bold text-base-content/80">No open positions matching current filter scope.</div>
      <div class="text-[11px]">
        Waiting for next mathematical barrier trigger or liquidity grab candle...
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Zap, MessageSquare, Activity } from 'lucide-vue-next';
import type { SignalData } from '../../types';

const props = defineProps<{
  openPositions: SignalData[];
  liveGoldPrice?: number | null;
  liveBtcPrice?: number | null;
  cleanSelectedName: string;
  actionLoading?: boolean;
}>();

const emit = defineEmits<{
  (e: 'closePosition', pos: SignalData): void;
}>();

const isShort = (pos: SignalData) => pos.action === 'SHORT' || pos.action === 'SELL';

const getLiveSpot = (pos: SignalData): number | null => {
  const isGold = (pos.pair || '').includes('XAU') || (pos.strategy || '').toLowerCase().includes('xau');
  return isGold ? props.liveGoldPrice ?? null : props.liveBtcPrice ?? null;
};

const calculateFloatingPnl = (pos: SignalData): number => {
  if (pos.pnl_pct !== undefined && pos.pnl_pct !== 0) return pos.pnl_pct;
  const spot = getLiveSpot(pos);
  if (!spot || !pos.price) return 0;
  const entry = pos.price;
  if (isShort(pos)) {
    return ((entry - spot) / entry) * 100;
  } else {
    return ((spot - entry) / entry) * 100;
  }
};
</script>

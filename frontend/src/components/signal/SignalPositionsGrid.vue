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
        <div v-if="liveSp500Price" class="px-2.5 py-1 rounded-box bg-base-300 border border-base-content/10 text-right">
          <div class="text-[9px] text-accent font-bold uppercase">📊 CME S&P 500</div>
          <div class="text-xs font-bold font-mono text-accent">
            ${{ liveSp500Price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}
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
        @click="emit('inspectPosition', pos)"
        class="card bg-base-300/60 border border-base-content/10 p-4 space-y-3 hover:border-primary/80 hover:bg-base-300/90 hover:shadow-lg active:scale-[0.99] cursor-pointer transition-all relative group"
        title="Click to view and inspect this trade setup with Entry/TP/SL boxes on chart (F1)"
      >
        <!-- Card Header -->
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span class="badge badge-sm font-bold" :class="getAssetBadgeClass(pos)">
              {{ getAssetDisplay(pos) }}
            </span>
            <span class="text-xs font-bold text-secondary font-mono">{{ pos.strategy || cleanSelectedName }}</span>
          </div>
          <div class="flex items-center gap-1.5">
            <span class="badge badge-xs badge-primary badge-outline gap-1 font-mono uppercase tracking-wider font-bold group-hover:bg-primary group-hover:text-primary-content transition-colors">
              <ExternalLink class="w-2.5 h-2.5" />
              Chart (F1)
            </span>
            <span class="badge badge-sm font-bold" :class="isShort(pos) ? 'badge-error' : 'badge-success'">
              {{ isShort(pos) ? '⬇ SHORT ENTRY' : '⬆ LONG ENTRY' }}
            </span>
          </div>
        </div>

        <!-- Pricing Grid -->
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 bg-base-100/60 p-2.5 rounded-box border border-base-content/10 text-xs">
          <div>
            <span class="text-[9px] text-base-content/50 uppercase block">Entry</span>
            <span class="font-bold text-accent font-mono">${{ pos.price?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}</span>
          </div>
          <div>
            <span class="text-[9px] text-base-content/50 uppercase block">Stop Loss</span>
            <span class="font-bold text-error font-mono">${{ pos.stop_loss ? pos.stop_loss.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '—' }}</span>
          </div>
          <div>
            <span class="text-[9px] text-base-content/50 uppercase block">Take Profit</span>
            <span class="font-bold text-success font-mono">${{ pos.take_profit ? pos.take_profit.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '—' }}</span>
          </div>
          <div>
            <span class="text-[9px] text-base-content/50 uppercase block">Live Spot</span>
            <span class="font-bold font-mono" :class="getSpotTextClass(pos)">
              {{ getLiveSpot(pos) ? `$${getLiveSpot(pos)?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '—' }}
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
            @click.stop="emit('closePosition', pos)"
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
import { Zap, MessageSquare, Activity, ExternalLink } from 'lucide-vue-next';
import type { SignalData } from '../../types';

const props = defineProps<{
  openPositions: SignalData[];
  liveGoldPrice?: number | null;
  liveBtcPrice?: number | null;
  liveSp500Price?: number | null;
  cleanSelectedName: string;
  actionLoading?: boolean;
}>();

const emit = defineEmits<{
  (e: 'closePosition', pos: SignalData): void;
  (e: 'inspectPosition', pos: SignalData): void;
}>();

const isShort = (pos: SignalData) => pos.action === 'SHORT' || pos.action === 'SELL';

const getAssetDisplay = (pos: SignalData): string => {
  if (pos.pair) return pos.pair;
  const s = (pos.strategy || '').toLowerCase();
  if (s.includes('xau') || s.includes('goat') || s.includes('gold') || s.includes('otad')) return 'XAU/USD';
  if (s.includes('sp') || s.includes('es') || s.includes('opening') || s.includes('orderflow')) return 'S&P 500 (ES)';
  return 'BTC/USDT';
};

const getAssetBadgeClass = (pos: SignalData): string => {
  const sym = getAssetDisplay(pos);
  if (sym.includes('XAU')) return 'badge-warning';
  if (sym.includes('SP') || sym.includes('ES')) return 'badge-accent';
  return 'badge-info';
};

const getSpotTextClass = (pos: SignalData): string => {
  const sym = getAssetDisplay(pos);
  if (sym.includes('XAU')) return 'text-warning';
  if (sym.includes('SP') || sym.includes('ES')) return 'text-accent';
  return 'text-info';
};

const getLiveSpot = (pos: SignalData): number | null => {
  const p = (pos.pair || '').toUpperCase();
  const s = (pos.strategy || '').toLowerCase();
  if (p.includes('XAU') || p.includes('GOLD') || s.includes('xau') || s.includes('goat') || s.includes('gold') || s.includes('otad')) {
    return props.liveGoldPrice ?? null;
  }
  if (p.includes('SP') || p.includes('ES') || s.includes('sp500') || s.includes('cme') || s.includes('opening') || s.includes('orderflow')) {
    return props.liveSp500Price ?? null;
  }
  return props.liveBtcPrice ?? props.liveGoldPrice ?? null;
};

const calculateFloatingPnl = (pos: SignalData): number => {
  if (pos.status === 'CLOSED' && pos.pnl_pct !== undefined && pos.pnl_pct !== 0) return pos.pnl_pct;
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

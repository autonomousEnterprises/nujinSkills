<template>
  <div class="h-11 bg-base-200/95 backdrop-blur-md border-b border-base-content/10 px-3 flex items-center justify-between z-20 text-xs shrink-0 gap-2 font-mono select-none">
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
            @click="emit('prevJump')"
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
                  @click="emit('jumpToIndex', idx)"
                  class="flex items-center justify-between py-1 px-2 rounded hover:bg-base-200"
                  :class="idx === selectedSignalIndex ? 'active font-bold bg-primary/10 text-primary' : ''"
                >
                  <div class="flex items-center gap-1.5">
                    <span class="text-base-content/50 text-[10px]">#{{ idx + 1 }}</span>
                    <span class="badge badge-xs font-bold text-[9px]" :class="sig.side === 'BUY' || sig.side === 'LONG' ? 'badge-success' : 'badge-error'">
                      {{ sig.side }}
                    </span>
                    <span class="text-[10px]">${{ formatPrice(sig.entry_price, isGoldStrategy) }}</span>
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
            @click="emit('nextJump')"
            :disabled="selectedSignalIndex >= allInspectableSignals.length - 1"
            class="btn btn-xs btn-ghost join-item px-2 font-bold text-[11px] disabled:opacity-20 hover:bg-base-100"
            title="Jump to Next Trade [HotKey: Right Arrow or ']']"
          >
            ▶
          </button>
        </div>

        <!-- Quick Jump: Latest Trade -->
        <button
          @click="emit('jumpToLatest')"
          class="btn btn-xs btn-ghost border border-base-content/15 text-[10px] uppercase font-bold tracking-wider hover:bg-base-200 hidden md:inline-flex"
          title="Jump view to most recent trade"
        >
          Latest
        </button>

        <!-- Quick Jump: Active Live Trade (pulsing if active) -->
        <button
          v-if="hasActiveLiveTrade"
          @click="emit('jumpToActive')"
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
</template>

<script setup lang="ts">
import { Sparkles, ChevronDown } from 'lucide-vue-next';
import type { InspectableSignal } from '../../types';
import { formatPrice } from '../../utils/formatters';

defineProps<{
  strategies: any[];
  cleanStrategyName: string;
  selectedStrategy: string;
  activeStrategy: string;
  isGoldStrategy: boolean;
  allInspectableSignals: InspectableSignal[];
  selectedSignalIndex: number;
  inspectedSignal?: InspectableSignal | null;
  hasActiveLiveTrade?: boolean;
  lastLivePrice?: number | null;
  priceFlash?: 'up' | 'down' | null;
  isWsConnected?: boolean;
}>();

const emit = defineEmits<{
  (e: 'selectStrategy', stratName: string): void;
  (e: 'prevJump'): void;
  (e: 'nextJump'): void;
  (e: 'jumpToIndex', idx: number): void;
  (e: 'jumpToLatest'): void;
  (e: 'jumpToActive'): void;
}>();
</script>

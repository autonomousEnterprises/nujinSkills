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
                <span class="w-1.5 h-1.5 rounded-full" :class="strat.name.toLowerCase().includes('sp') || strat.name.toLowerCase().includes('opening') ? 'bg-success' : (strat.name.toLowerCase().includes('xau') ? 'bg-warning' : 'bg-info')" />
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
        <span>{{ isSpStrategy ? '🟢 S&P 500' : (isGoldStrategy ? '🟡 XAU/USD' : '🔵 BTC/USDT') }}</span>
        <span class="text-[9px] opacity-60 uppercase">{{ isSpStrategy ? 'CME ES 1m' : (isGoldStrategy ? 'Spot 1m' : 'Binance 15m') }}</span>
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

            <!-- Extended Mega-Menu: Trade Jump Explorer -->
            <div 
              tabindex="0" 
              class="dropdown-content shadow-2xl bg-base-300/95 backdrop-blur-xl rounded-2xl w-[740px] max-w-[92vw] max-h-[580px] z-50 border border-base-content/20 text-xs font-mono flex flex-col mt-2 p-0 overflow-hidden shadow-primary/5"
            >
              <!-- 1. Mega-Menu Header with Aggregate KPIs -->
              <div class="px-4 py-2.5 bg-base-200/90 border-b border-base-content/10 flex items-center justify-between shrink-0">
                <div class="flex items-center gap-2">
                  <span class="font-bold text-xs uppercase tracking-wider text-base-content flex items-center gap-1.5">
                    <span class="w-2 h-2 rounded-full bg-primary animate-ping" />
                    Trade Jump Mega-Menu
                  </span>
                  <span class="badge badge-primary badge-sm font-bold text-[10px]">
                    {{ allInspectableSignals.length }} TRADES
                  </span>
                </div>

                <!-- Quick Stats Chips -->
                <div class="flex items-center gap-1.5 text-[10px]">
                  <span class="px-2 py-0.5 rounded bg-base-100/80 border border-base-content/10 text-base-content/70">
                    Win Rate: <strong class="text-success">{{ winRatePct }}%</strong>
                  </span>
                  <span class="px-2 py-0.5 rounded bg-base-100/80 border border-base-content/10 text-base-content/70">
                    Longs: <strong class="text-success">{{ longCount }}</strong> | Shorts: <strong class="text-error">{{ shortCount }}</strong>
                  </span>
                </div>
              </div>

              <!-- 2. Search and Filter Bar -->
              <div class="p-2.5 bg-base-200/50 border-b border-base-content/10 flex flex-wrap items-center justify-between gap-2 shrink-0">
                <!-- Search Input -->
                <div class="relative flex-1 min-w-[200px]">
                  <Search class="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 opacity-40 text-base-content" />
                  <input 
                    type="text"
                    v-model="searchQuery"
                    placeholder="Search by #, price, direction, reason..."
                    class="input input-xs input-bordered w-full pl-8 font-mono text-[11px] bg-base-100 focus:border-primary"
                  />
                  <button 
                    v-if="searchQuery"
                    @click="searchQuery = ''"
                    class="btn btn-ghost btn-xs absolute right-1 top-1/2 -translate-y-1/2 h-5 min-h-0 w-5 p-0 text-[10px] opacity-60"
                  >
                    ✕
                  </button>
                </div>

                <!-- Filter Pills -->
                <div class="join bg-base-100 border border-base-content/10 rounded-lg p-0.5 text-[10px]">
                  <button 
                    @click="activeFilter = 'ALL'"
                    class="btn btn-xs join-item font-mono h-6 min-h-0 px-2.5"
                    :class="activeFilter === 'ALL' ? 'btn-primary font-bold' : 'btn-ghost'"
                  >
                    All ({{ allInspectableSignals.length }})
                  </button>
                  <button 
                    @click="activeFilter = 'WIN'"
                    class="btn btn-xs join-item font-mono h-6 min-h-0 px-2.5"
                    :class="activeFilter === 'WIN' ? 'btn-success text-success-content font-bold' : 'btn-ghost text-success'"
                  >
                    Wins ({{ winCount }})
                  </button>
                  <button 
                    @click="activeFilter = 'LOSS'"
                    class="btn btn-xs join-item font-mono h-6 min-h-0 px-2.5"
                    :class="activeFilter === 'LOSS' ? 'btn-error text-error-content font-bold' : 'btn-ghost text-error'"
                  >
                    Losses ({{ lossCount }})
                  </button>
                  <button 
                    @click="activeFilter = 'LONG'"
                    class="btn btn-xs join-item font-mono h-6 min-h-0 px-2"
                    :class="activeFilter === 'LONG' ? 'btn-primary font-bold' : 'btn-ghost'"
                  >
                    Longs ({{ longCount }})
                  </button>
                  <button 
                    @click="activeFilter = 'SHORT'"
                    class="btn btn-xs join-item font-mono h-6 min-h-0 px-2"
                    :class="activeFilter === 'SHORT' ? 'btn-primary font-bold' : 'btn-ghost'"
                  >
                    Shorts ({{ shortCount }})
                  </button>
                </div>
              </div>

              <!-- 3. Multi-Column Trades Grid -->
              <div class="flex-1 overflow-y-auto p-2.5 max-h-[380px]">
                <div v-if="filteredSignals.length > 0" class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-1.5">
                  <button 
                    v-for="item in filteredSignals" 
                    :key="item.sig.id"
                    @click="selectTrade(item.idx)"
                    class="group flex flex-col gap-1 p-2 rounded-lg border transition-all text-left relative overflow-hidden"
                    :class="item.idx === selectedSignalIndex 
                      ? 'bg-primary/20 border-primary shadow-sm ring-1 ring-primary' 
                      : 'bg-base-200/70 border-base-content/10 hover:bg-base-100 hover:border-primary/50 hover:shadow'"
                  >
                    <!-- Top row: ID + Direction + Indicator -->
                    <div class="flex items-center justify-between gap-1 w-full text-[11px]">
                      <div class="flex items-center gap-1.5">
                        <span class="font-bold opacity-60 text-[10px]">#{{ item.idx + 1 }}</span>
                        <span 
                          class="badge badge-xs font-bold text-[9px] px-1.5 py-0.5" 
                          :class="item.sig.side === 'BUY' || item.sig.side === 'LONG' ? 'badge-success text-success-content' : 'badge-error text-error-content'"
                        >
                          {{ item.sig.side }}
                        </span>
                      </div>

                      <span v-if="item.sig.isLiveActive" class="badge badge-xs badge-success text-[8px] font-bold animate-pulse">
                        LIVE
                      </span>
                      <span v-else-if="item.idx === selectedSignalIndex" class="text-primary font-bold text-[9px]">
                        ● ACTIVE
                      </span>
                    </div>

                    <!-- Middle row: Entry Price + PnL -->
                    <div class="flex items-center justify-between gap-1 w-full font-mono text-[11px]">
                      <span class="text-base-content/90 font-bold">${{ formatPrice(item.sig.entry_price, isGoldStrategy || isSpStrategy) }}</span>
                      <span 
                        class="font-bold text-xs"
                        :class="(item.sig.pnl_pct || 0) >= 0 ? 'text-success' : 'text-error'"
                      >
                        {{ (item.sig.pnl_pct || 0) >= 0 ? '+' : '' }}{{ (item.sig.pnl_pct || 0).toFixed(2) }}%
                      </span>
                    </div>

                    <!-- Bottom row: Exit Details -->
                    <div v-if="item.sig.exit_reason" class="flex items-center justify-between text-[9px] opacity-40">
                      <span>{{ item.sig.exit_reason }}</span>
                      <span v-if="item.sig.exit_price">${{ formatPrice(item.sig.exit_price, isGoldStrategy || isSpStrategy) }}</span>
                    </div>
                  </button>
                </div>

                <!-- Empty Search State -->
                <div v-else class="py-12 text-center text-base-content/40 space-y-1">
                  <p class="font-bold text-xs">No trades match criteria</p>
                  <p class="text-[10px]">Try clearing your search query or selecting "All"</p>
                </div>
              </div>

              <!-- 4. Footer Bar with Quick Jump buttons -->
              <div class="px-3 py-2 bg-base-200/90 border-t border-base-content/10 flex items-center justify-between shrink-0 text-[10px] text-base-content/70">
                <div class="flex items-center gap-1.5">
                  <button 
                    @click="selectTrade(0)"
                    :disabled="selectedSignalIndex === 0"
                    class="btn btn-ghost btn-xs h-6 min-h-0 text-[10px] disabled:opacity-30"
                  >
                    ⏮ First (#1)
                  </button>
                  <button 
                    @click="selectTrade(allInspectableSignals.length - 1)"
                    :disabled="selectedSignalIndex === allInspectableSignals.length - 1"
                    class="btn btn-ghost btn-xs h-6 min-h-0 text-[10px] disabled:opacity-30"
                  >
                    ⏭ Latest (#{{ allInspectableSignals.length }})
                  </button>
                </div>

                <div class="flex items-center gap-2 font-mono">
                  <span>Hotkeys: <kbd class="kbd kbd-xs">[</kbd> Prev <kbd class="kbd kbd-xs">]</kbd> Next</span>
                </div>
              </div>
            </div>
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
import { ref, computed } from 'vue';
import { Sparkles, ChevronDown, Search } from 'lucide-vue-next';
import type { InspectableSignal } from '../../types';
import { formatPrice } from '../../utils/formatters';

const props = defineProps<{
  strategies: any[];
  cleanStrategyName: string;
  selectedStrategy: string;
  activeStrategy: string;
  isGoldStrategy: boolean;
  isSpStrategy?: boolean;
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

// ── Mega-Menu Search & Filter State ──
const searchQuery = ref('');
const activeFilter = ref<'ALL' | 'WIN' | 'LOSS' | 'LONG' | 'SHORT'>('ALL');

const winCount = computed(() => (props.allInspectableSignals || []).filter(s => (s.pnl_pct || 0) >= 0).length);
const lossCount = computed(() => (props.allInspectableSignals || []).filter(s => (s.pnl_pct || 0) < 0).length);
const longCount = computed(() => (props.allInspectableSignals || []).filter(s => s.side === 'BUY' || s.side === 'LONG').length);
const shortCount = computed(() => (props.allInspectableSignals || []).filter(s => s.side === 'SELL' || s.side === 'SHORT').length);
const winRatePct = computed(() => {
  const total = (props.allInspectableSignals || []).length;
  if (total === 0) return '0.0';
  return ((winCount.value / total) * 100).toFixed(1);
});

const filteredSignals = computed(() => {
  const list = props.allInspectableSignals || [];
  const query = searchQuery.value.trim().toLowerCase();

  return list
    .map((sig, idx) => ({ sig, idx }))
    .filter(({ sig, idx }) => {
      // Filter by classification
      if (activeFilter.value === 'WIN' && (sig.pnl_pct || 0) < 0) return false;
      if (activeFilter.value === 'LOSS' && (sig.pnl_pct || 0) >= 0) return false;
      if (activeFilter.value === 'LONG' && sig.side !== 'BUY' && sig.side !== 'LONG') return false;
      if (activeFilter.value === 'SHORT' && sig.side !== 'SELL' && sig.side !== 'SHORT') return false;

      // Filter by search query
      if (query) {
        const idMatch = `#${idx + 1}`.includes(query) || `${idx + 1}` === query;
        const sideMatch = (sig.side || '').toLowerCase().includes(query);
        const priceMatch = (sig.entry_price || 0).toString().includes(query);
        const pnlMatch = `${sig.pnl_pct || 0}%`.includes(query);
        const reasonMatch = (sig.exit_reason || '').toLowerCase().includes(query);
        return idMatch || sideMatch || priceMatch || pnlMatch || reasonMatch;
      }
      return true;
    });
});

const selectTrade = (idx: number) => {
  emit('jumpToIndex', idx);
  if (document.activeElement instanceof HTMLElement) {
    document.activeElement.blur();
  }
};
</script>

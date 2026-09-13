<template>
  <div class="card bg-base-200 border border-base-content/10 p-5 space-y-4">
    <div class="flex items-center justify-between border-b border-base-content/10 pb-3">
      <span class="font-bold text-sm flex items-center gap-2 text-secondary">
        <Clock class="w-4 h-4" />
        SIGNAL TELEMETRY &amp; AUDIT FEED
      </span>
      <span class="text-xs text-base-content/60">
        {{ allSignals.length }} Total Signals Recorded
      </span>
    </div>

    <div class="overflow-x-auto max-h-96 overflow-y-auto border border-base-content/10 rounded-box">
      <table class="table table-zebra table-sm w-full font-mono text-xs">
        <thead class="sticky top-0 bg-base-300 z-10">
          <tr>
            <th>#</th>
            <th>Time</th>
            <th>Strategy</th>
            <th>Pair</th>
            <th>Action</th>
            <th>Entry</th>
            <th>SL</th>
            <th>TP</th>
            <th>Exit Reason</th>
            <th>Net PnL</th>
            <th>Status</th>
            <th class="text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="allSignals.length === 0">
            <td colspan="12" class="p-6 text-center text-base-content/50">
              No signals recorded yet under selected filter scope.
            </td>
          </tr>
          <tr 
            v-for="(sig, idx) in allSignals" 
            :key="sig.id || idx" 
            @click="emit('inspectPosition', sig)"
            class="hover cursor-pointer hover:bg-base-100 transition-colors"
            title="Click to view and inspect this signal with Entry/TP/SL boxes on chart (F1)"
          >
            <td class="font-bold opacity-70">#{{ sig.id || idx + 1 }}</td>
            <td class="opacity-70 whitespace-nowrap">
              {{ formatDate(sig.time) }}
            </td>
            <td class="font-bold text-secondary">
              {{ (sig.strategy || cleanSelectedName).replace('Strategy', '') }}
            </td>
            <td>
              <span class="badge badge-xs font-bold" :class="(sig.pair || '').includes('XAU') ? 'badge-warning' : 'badge-info'">
                {{ sig.pair || ((sig.pair || '').includes('XAU') ? 'XAU/USD' : 'BTC/USDT') }}
              </span>
            </td>
            <td>
              <span class="badge badge-xs font-bold" :class="isLongAction(sig) ? 'badge-success' : 'badge-error'">
                {{ isLongAction(sig) ? '⬆ LONG' : '⬇ SHORT' }}
              </span>
            </td>
            <td class="font-bold text-accent">${{ sig.price ? sig.price.toLocaleString() : '—' }}</td>
            <td class="text-error">${{ sig.stop_loss ? sig.stop_loss.toLocaleString() : '—' }}</td>
            <td class="text-success">${{ sig.take_profit ? sig.take_profit.toLocaleString() : '—' }}</td>
            <td>
              <span 
                class="badge badge-xs font-bold"
                :class="sig.exit_reason === 'TAKE_PROFIT' ? 'badge-success' : sig.exit_reason === 'STOP_LOSS' ? 'badge-error' : 'badge-neutral'"
              >
                {{ sig.exit_reason || (sig.status === 'ACTIVE_IN_POSITION' ? 'IN PROGRESS' : 'CLOSED') }}
              </span>
            </td>
            <td class="font-bold">
              <span v-if="sig.status === 'ACTIVE_IN_POSITION'" class="text-info">LIVE</span>
              <span v-else :class="(sig.pnl_pct || 0) >= 0 ? 'text-success' : 'text-error'">
                {{ (sig.pnl_pct || 0) > 0 ? '+' : '' }}{{ (sig.pnl_pct || 0).toFixed(2) }}%
              </span>
            </td>
            <td>
              <span 
                class="badge badge-xs font-bold"
                :class="sig.status === 'ACTIVE_IN_POSITION' ? 'badge-success badge-outline animate-pulse' : 'badge-neutral'"
              >
                {{ sig.status || 'CLOSED' }}
              </span>
            </td>
            <td class="text-right whitespace-nowrap">
              <button
                @click.stop="emit('inspectPosition', sig)"
                class="btn btn-xs btn-ghost btn-primary font-bold mr-1"
                title="View on Chart (F1)"
              >
                Chart ↗
              </button>
              <button
                v-if="sig.status === 'ACTIVE_IN_POSITION'"
                @click.stop="emit('closePosition', sig)"
                :disabled="actionLoading"
                class="btn btn-xs btn-error btn-outline font-bold"
              >
                Close
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Clock } from 'lucide-vue-next';
import type { SignalData } from '../../types';

defineProps<{
  allSignals: SignalData[];
  cleanSelectedName: string;
  actionLoading?: boolean;
}>();

const emit = defineEmits<{
  (e: 'closePosition', sig: SignalData): void;
  (e: 'inspectPosition', sig: SignalData): void;
}>();

const isLongAction = (sig: SignalData) => sig.action === 'BUY' || sig.action === 'LONG';

const formatDate = (epoch?: number) => {
  if (!epoch) return '—';
  const t = epoch > 1e11 ? epoch : epoch * 1000;
  return new Date(t).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
};
</script>

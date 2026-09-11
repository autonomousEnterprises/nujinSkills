<template>
  <div v-if="tradesDetail.length > 0" class="card bg-base-200 border border-base-content/10 p-4 space-y-3">
    <div class="flex items-center justify-between border-b border-base-content/10 pb-2">
      <span class="font-bold text-xs flex items-center gap-2 text-primary">
        <ListFilter class="w-4 h-4" />
        SEQUENTIAL TRADE LOG ({{ tradesDetail.length }} Trades Simulated)
      </span>
      <span class="text-[10px] text-base-content/50">Zero Overlapping Executions</span>
    </div>

    <div class="overflow-x-auto max-h-48 overflow-y-auto border border-base-content/10 rounded-box">
      <table class="table table-zebra table-sm w-full font-mono text-xs">
        <thead class="sticky top-0 bg-base-300 z-10">
          <tr>
            <th>Trade #</th>
            <th>Side</th>
            <th>Entry Price</th>
            <th>Stop Loss</th>
            <th>Take Profit</th>
            <th>Exit Price</th>
            <th>Reason</th>
            <th>Net PnL</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="t in tradesDetail" :key="t.id" class="hover">
            <td class="font-bold opacity-70">#{{ t.id }}</td>
            <td>
              <span class="badge badge-xs font-bold" :class="(t.side || 'LONG') === 'LONG' ? 'badge-success' : 'badge-error'">
                {{ (t.side || 'LONG') === 'LONG' ? '⬆ LONG' : '⬇ SHORT' }}
              </span>
            </td>
            <td class="font-bold text-accent">${{ t.entry_price?.toFixed(1) }}</td>
            <td class="text-error">${{ t.stop_loss?.toFixed(1) }}</td>
            <td class="text-success">${{ t.take_profit?.toFixed(1) }}</td>
            <td>${{ t.exit_price?.toFixed(1) }}</td>
            <td>
              <span 
                class="badge badge-xs font-bold"
                :class="t.exit_reason === 'TAKE_PROFIT' ? 'badge-success' : t.exit_reason === 'STOP_LOSS' ? 'badge-error' : 'badge-neutral'"
              >
                {{ t.exit_reason }}
              </span>
            </td>
            <td class="font-bold" :class="t.pnl_pct >= 0 ? 'text-success' : 'text-error'">
              {{ t.pnl_pct > 0 ? '+' : '' }}{{ t.pnl_pct?.toFixed(2) }}%
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ListFilter } from 'lucide-vue-next';
import type { TradeDetail } from '../../types';

defineProps<{
  tradesDetail: TradeDetail[];
}>();
</script>

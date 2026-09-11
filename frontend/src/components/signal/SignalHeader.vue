<template>
  <div class="card bg-base-200 border border-base-content/10 shadow-sm p-4">
    <div class="flex flex-wrap items-center justify-between gap-4">
      <div class="flex items-center gap-3">
        <div class="p-2.5 rounded-box bg-primary/10 border border-primary/30 text-primary">
          <Send class="w-5 h-5" />
        </div>
        <div>
          <div class="flex items-center gap-2 flex-wrap">
            <span class="font-bold text-sm text-base-content">
              SIGNAL DECK — MULTI-STRATEGY TELEMETRY GATEWAY
            </span>
            <span class="badge badge-sm badge-secondary font-bold">
              {{ activeBots.length }} ACTIVE IN BOT
            </span>
            <span 
              class="badge badge-sm font-bold border"
              :class="isRunning ? 'badge-success badge-outline bg-success/10 text-success' : 'badge-neutral bg-base-300 text-base-content/60'"
            >
              {{ isRunning ? `🟢 BOT: RUNNING (${activeBots.length} Active)` : '🔴 BOT: STOPPED / IDLE' }}
            </span>
            <span 
              class="badge badge-sm font-bold border"
              :class="telegramConfigured ? 'badge-info badge-outline bg-info/10 text-info' : 'badge-neutral bg-base-300 text-base-content/50'"
            >
              {{ telegramConfigured ? '💬 TELEGRAM: CONNECTED' : '⚪ TELEGRAM: LOG ONLY' }}
            </span>
          </div>
          <div class="text-[11px] text-base-content/60 mt-0.5">
            Real-time position tracking, live R/R bounds, multi-asset spot tickers &amp; automated alert dispatch
          </div>
        </div>
      </div>

      <!-- Bot Controls (Start/Stop), Refresh & Clear -->
      <div class="flex items-center gap-2 flex-wrap">
        <button
          @click="emit('deployBot')"
          :disabled="actionLoading || isRunning"
          class="btn btn-xs sm:btn-sm btn-success gap-1 shadow font-bold"
        >
          <Play class="w-3.5 h-3.5 fill-current" />
          <span>{{ isRunning ? 'Bot Running' : 'Start Bot' }}</span>
        </button>

        <button
          @click="emit('stopBot')"
          :disabled="actionLoading || !isRunning"
          class="btn btn-xs sm:btn-sm btn-error gap-1 shadow font-bold"
        >
          <Square class="w-3 h-3 fill-current" />
          <span>Stop Bot</span>
        </button>

        <div class="divider divider-horizontal mx-1 my-1 hidden sm:flex" />

        <button
          @click="emit('fetchSignals')"
          :disabled="loading"
          class="btn btn-xs sm:btn-sm btn-ghost border border-base-content/10 gap-1"
        >
          <RefreshCw class="w-3.5 h-3.5" :class="loading ? 'animate-spin' : ''" />
          <span class="hidden sm:inline">Refresh</span>
        </button>

        <button
          @click="emit('clearSignals')"
          :disabled="actionLoading"
          class="btn btn-xs sm:btn-sm btn-ghost border border-base-content/10 text-error hover:bg-error/10 gap-1"
          title="Clear signals under current scope"
        >
          <Trash2 class="w-3.5 h-3.5" />
          <span class="hidden sm:inline">Clear</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Send, Play, Square, RefreshCw, Trash2 } from 'lucide-vue-next';

defineProps<{
  activeBots: string[];
  isRunning: boolean;
  telegramConfigured: boolean;
  actionLoading?: boolean;
  loading?: boolean;
}>();

const emit = defineEmits<{
  (e: 'deployBot'): void;
  (e: 'stopBot'): void;
  (e: 'fetchSignals'): void;
  (e: 'clearSignals'): void;
}>();
</script>

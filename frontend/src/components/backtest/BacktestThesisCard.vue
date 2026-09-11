<template>
  <div class="card bg-base-200 border border-base-content/10 p-4 space-y-3">
    <div class="flex items-center justify-between border-b border-base-content/10 pb-2 text-xs">
      <span class="font-bold flex items-center gap-2 text-primary">
        <FileCode class="w-4 h-4" />
        QUANT EDGE THESIS &amp; COUNTERPARTY MECHANICS ({{ cleanSelectedName }})
      </span>
      <ShieldCheck class="w-4 h-4 text-primary" />
    </div>

    <div v-if="thesisInfo" class="grid grid-cols-1 md:grid-cols-3 gap-3 pt-1 text-xs">
      <div class="p-3 rounded-box bg-base-300/60 border border-base-content/10 space-y-1">
        <span class="text-primary font-bold block text-[11px]">Core Hypothesis:</span>
        <span class="text-base-content/90 leading-relaxed">{{ thesisInfo.thesis }}</span>
      </div>
      <div class="p-3 rounded-box bg-base-300/60 border border-base-content/10 space-y-1">
        <span class="text-warning font-bold block text-[11px]">Counterparty Trap:</span>
        <span class="text-base-content/90 leading-relaxed">{{ thesisInfo.counterparty }}</span>
      </div>
      <div class="p-3 rounded-box bg-base-300/60 border border-base-content/10 space-y-1">
        <span class="text-error font-bold block text-[11px]">Hard Invalidation:</span>
        <span class="text-base-content/90 leading-relaxed">{{ thesisInfo.invalidation }}</span>
      </div>
    </div>
    <div v-else class="text-center py-2 text-xs text-base-content/50">
      Run a backtest to populate thesis, counterparty trap, and invalidation rules.
    </div>
  </div>
</template>

<script setup lang="ts">
import { FileCode, ShieldCheck } from 'lucide-vue-next';
import type { ThesisProps } from '../../types';

defineProps<{
  cleanSelectedName: string;
  thesisInfo?: ThesisProps | null;
}>();
</script>

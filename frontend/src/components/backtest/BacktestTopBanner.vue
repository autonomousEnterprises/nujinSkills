<template>
  <div class="card bg-base-200 border border-base-content/10 shadow-sm p-4 md:p-5">
    <div class="flex flex-wrap items-center justify-between gap-4">
      <!-- Left Info -->
      <div class="flex items-center gap-4">
        <div class="p-3 rounded-box bg-secondary/10 border border-secondary/30 text-secondary">
          <Cpu class="w-6 h-6" />
        </div>
        <div>
          <div class="flex flex-wrap items-center gap-2">
            <span class="text-[10px] uppercase font-bold text-base-content/50">SINGLE SOURCE OF TRUTH</span>
            <span class="badge badge-sm badge-secondary font-bold">INSPECTING: {{ cleanSelectedName }}</span>
            <span class="badge badge-sm badge-info font-bold">MODE: DUAL LONG &amp; SHORT</span>
            <span class="badge badge-sm badge-success font-bold">
              SYSTEM DEPLOYED: {{ activeName }} ({{ activeState?.status || 'ACTIVE_DEPLOYED' }})
            </span>
          </div>
          <h2 class="text-lg font-bold tracking-wide mt-0.5 text-base-content">{{ cleanSelectedName }}</h2>
          <p class="text-xs text-base-content/70">
            Target Profile: <span class="text-primary font-bold">{{ selectedBacktestData?.thesis_props?.target_profile || activeState?.target_profile || 'Prop Firm Challenge' }}</span>
          </p>
        </div>
      </div>

      <!-- Right KPIs -->
      <div class="flex items-center gap-4 md:gap-6 text-right">
        <div>
          <div class="text-[10px] text-base-content/50 uppercase">Expected Sharpe</div>
          <div class="text-xl font-bold font-mono" :class="getValColor(summary?.sharpe)">
            {{ summary?.sharpe != null ? summary.sharpe : '–' }}
          </div>
        </div>
        <div>
          <div class="text-[10px] text-base-content/50 uppercase">Win Rate</div>
          <div class="text-xl font-bold font-mono" :class="getValColor(summary?.win_rate)">
            {{ summary?.win_rate != null ? `${(summary.win_rate * 100).toFixed(1)}%` : '–' }}
          </div>
        </div>
        <div>
          <div class="text-[10px] text-base-content/50 uppercase">Expectancy</div>
          <div class="text-xl font-bold font-mono" :class="getValColor(summary?.expectancy_bps)">
            {{ summary?.expectancy_bps != null ? `${summary.expectancy_bps} bps` : '–' }}
          </div>
        </div>
        <div>
          <div class="text-[10px] text-base-content/50 uppercase">DSR Score</div>
          <div class="text-xl font-bold font-mono" :class="summary?.dsr != null ? (summary.dsr >= 0.95 ? 'text-success' : 'text-warning') : 'text-base-content/40'">
            {{ summary?.dsr != null ? summary.dsr : '–' }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Cpu } from 'lucide-vue-next';
import type { BacktestSummary } from '../../types';
import { getValColor } from '../../utils/formatters';

defineProps<{
  cleanSelectedName: string;
  activeName: string;
  activeState?: any;
  selectedBacktestData?: any;
  summary?: BacktestSummary | null;
}>();
</script>

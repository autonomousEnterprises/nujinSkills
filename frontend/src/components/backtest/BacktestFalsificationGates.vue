<template>
  <div class="card bg-base-200 border border-base-content/10 p-4 md:p-5 space-y-4">
    <div class="flex items-center justify-between border-b border-base-content/10 pb-2">
      <h3 class="text-xs font-bold flex items-center gap-2 text-base-content">
        <ShieldCheck class="w-4 h-4 text-primary" />
        ADVERSARIAL FALSIFICATION GATES (CYNIC AUDIT) — {{ cleanSelectedName }}
      </h3>
      <span 
        class="text-[10px] font-bold font-mono px-2 py-0.5 rounded"
        :class="passedGatesCount === 5 ? 'text-success bg-success/10' : (passedGatesCount >= 3 ? 'text-warning bg-warning/10' : 'text-error bg-error/10')"
      >
        {{ passedGatesCount === 5 ? '5/5 GATES PASSED' : `${passedGatesCount}/5 GATES PASSED (REJECTED)` }}
      </span>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
      <div class="p-3 rounded-box bg-base-300/60 border border-base-content/10 flex items-center justify-between">
        <div>
          <div class="font-bold text-base-content">Gate 1: Deflated Sharpe Ratio (DSR)</div>
          <div class="text-[10px] text-base-content/50">
            {{ gates?.gate_1_dsr?.reason || 'Overfitting & trial count penalty' }}
          </div>
        </div>
        <span 
          class="badge badge-sm font-bold"
          :class="g1Pass ? 'badge-success' : 'badge-error'"
        >
          {{ g1Pass ? `PASS (${gates?.gate_1_dsr?.dsr ?? summary?.dsr})` : (gates?.gate_1_dsr?.reason?.includes('< 30') ? 'REJECT (< 30)' : `FAIL (${gates?.gate_1_dsr?.dsr ?? 0})`) }}
        </span>
      </div>

      <div class="p-3 rounded-box bg-base-300/60 border border-base-content/10 flex items-center justify-between">
        <div>
          <div class="font-bold text-base-content">Gate 2: Parameter Surface</div>
          <div class="text-[10px] text-base-content/50">
            {{ gates?.gate_2_parameter_stability?.reason || 'Plateau verification vs cliff spike' }}
          </div>
        </div>
        <span 
          class="badge badge-sm font-bold"
          :class="g2Pass ? 'badge-success' : 'badge-error'"
        >
          {{ gates?.gate_2_parameter_stability?.plateau_status || (g2Pass ? 'STABLE PLATEAU' : 'CLIFF SPIKE') }}
        </span>
      </div>

      <div class="p-3 rounded-box bg-base-300/60 border border-base-content/10 flex items-center justify-between">
        <div>
          <div class="font-bold text-base-content">Gate 3: Monte Carlo MDD99</div>
          <div class="text-[10px] text-base-content/50">
            {{ gates?.gate_3_monte_carlo?.reason || '1,000 reshuffled price paths' }}
          </div>
        </div>
        <span 
          class="badge badge-sm font-bold"
          :class="g3Pass ? 'badge-success' : 'badge-error'"
        >
          {{ g3Pass ? `PASS (${((gates?.gate_3_monte_carlo?.mdd_99 ?? summary?.mdd_99 ?? 0) * 100).toFixed(2)}%)` : (gates?.gate_3_monte_carlo?.reason?.includes('< 10') ? 'FAIL (< 10)' : 'FAIL (> 4.5%)') }}
        </span>
      </div>

      <div class="p-3 rounded-box bg-base-300/60 border border-base-content/10 flex items-center justify-between">
        <div>
          <div class="font-bold text-base-content">Gate 4: Out-Of-Sample Walk Forward</div>
          <div class="text-[10px] text-base-content/50">
            {{ gates?.gate_4_oos_walkforward?.reason || 'Sharpe retention ratio' }}
          </div>
        </div>
        <span 
          class="badge badge-sm font-bold"
          :class="g4Pass ? 'badge-success' : 'badge-error'"
        >
          {{ g4Pass ? `PASS (${gates?.gate_4_oos_walkforward?.retention_pct ?? 78.0}%)` : `FAIL (${gates?.gate_4_oos_walkforward?.retention_pct ?? 0}%)` }}
        </span>
      </div>

      <div class="p-3 rounded-box bg-base-300/60 border border-base-content/10 flex items-center justify-between md:col-span-2">
        <div>
          <div class="font-bold text-base-content">Gate 5: Multi-Regime Survival Score</div>
          <div class="text-[10px] text-base-content/50">
            {{ gates?.gate_5_regime_survival?.reason || 'Weighted Bull/Bear/Ranging survival metric' }}
          </div>
        </div>
        <span 
          class="badge badge-sm font-bold"
          :class="g5Pass ? 'badge-success' : (gates?.gate_5_regime_survival?.status === 'WARN' ? 'badge-warning' : 'badge-error')"
        >
          {{ (gates?.gate_5_regime_survival?.status || (g5Pass ? 'PASS' : 'FAIL')) }} ({{ gates?.gate_5_regime_survival?.score ?? 0 }}/100)
        </span>
      </div>
    </div>

    <!-- Parameter Surface Heatmap Grid -->
    <div class="pt-3 border-t border-base-content/10 space-y-2">
      <div class="flex items-center justify-between text-xs font-bold text-base-content/80">
        <span>PARAMETER STABILITY SURFACE ({{ cleanSelectedName }})</span>
        <span class="text-[10px] text-base-content/50">
          X: {{ (gates?.gate_2_parameter_stability?.x_axis || ['0.9x', '1.0x', '1.1x']).join(' | ') }} &middot; Y: {{ (gates?.gate_2_parameter_stability?.y_axis || ['0.9x', '1.0x', '1.1x']).join(' | ') }}
        </span>
      </div>
      <div class="grid grid-cols-3 gap-2">
        <template v-for="(row, rIdx) in matrix" :key="rIdx">
          <div 
            v-for="(val, cIdx) in row" 
            :key="`${rIdx}-${cIdx}`"
            class="p-2.5 rounded-box border text-center flex flex-col items-center justify-center transition-all"
            :class="val < 0 ? 'bg-error/10 border-error/30' : 'bg-success/10 border-success/30'"
          >
            <span class="text-[10px] text-base-content/50">Grid [{{ rIdx + 1 }},{{ cIdx + 1 }}]</span>
            <span class="text-sm font-bold font-mono" :class="val < 0 ? 'text-error' : 'text-success'">
              {{ typeof val === 'number' ? val.toFixed(2) : val }}
            </span>
            <span class="text-[9px]" :class="val < 0 ? 'text-error' : 'text-success'">Sharpe</span>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { ShieldCheck } from 'lucide-vue-next';
import type { BacktestSummary } from '../../types';

const props = defineProps<{
  cleanSelectedName: string;
  summary?: BacktestSummary | null;
  gates?: any;
}>();

const g1Pass = computed(() => props.gates?.gate_1_dsr?.status === 'PASS');
const g2Pass = computed(() => props.gates?.gate_2_parameter_stability?.status === 'PASS');
const g3Pass = computed(() => props.gates?.gate_3_monte_carlo?.status === 'PASS');
const g4Pass = computed(() => props.gates?.gate_4_oos_walkforward?.status === 'PASS');
const g5Pass = computed(() => props.gates?.gate_5_regime_survival?.status === 'PASS');

const passedGatesCount = computed(() => {
  let count = 0;
  if (g1Pass.value) count++;
  if (g2Pass.value) count++;
  if (g3Pass.value) count++;
  if (g4Pass.value) count++;
  if (g5Pass.value) count++;
  return count;
});

const defaultMatrix = [
  [1.25, 1.40, 1.15],
  [1.32, 1.55, 1.28],
  [1.10, 1.35, 1.42],
];

const matrix = computed(() => props.gates?.gate_2_parameter_stability?.matrix || defaultMatrix);
</script>

<template>
  <header class="navbar min-h-12 h-12 bg-base-200 border-b border-base-content/10 px-3 md:px-4 flex items-center justify-between text-xs font-mono select-none z-40 transition-colors">
    <!-- Left Section: Brand, WS status, Active bot badge -->
    <div class="flex items-center gap-2 md:gap-4 overflow-hidden">
      <div class="flex items-center gap-2 font-bold tracking-wider text-base-content shrink-0">
        <Terminal class="w-4 h-4 text-primary animate-pulse" />
        <span class="hidden sm:inline">NujinSkills_CORE</span>
      </div>

      <!-- Live WS Status Badge -->
      <div class="badge badge-sm gap-1.5 py-2.5 px-2 font-semibold border-base-content/10 bg-base-300 shrink-0">
        <span class="w-2 h-2 rounded-full" :class="isConnected ? 'bg-success animate-ping' : 'bg-warning'" />
        <span :class="isConnected ? 'text-success font-bold' : 'text-warning'">
          {{ isConnected ? 'ONLINE' : 'OFFLINE' }}
        </span>
      </div>

      <!-- Active Strategies Counter Badge -->
      <div 
        class="badge badge-sm gap-1.5 py-2.5 px-2 border transition-colors cursor-pointer hidden sm:flex shrink-0"
        :class="activeCount > 0 ? 'badge-success badge-outline bg-success/10 text-success' : 'badge-neutral bg-base-300 text-base-content/60'"
        :title="activeCount > 0 ? `Active: ${effectiveActiveStrategies.join(', ')}` : 'No bot active'"
      >
        <span class="w-1.5 h-1.5 rounded-full" :class="activeCount > 0 ? 'bg-success animate-pulse' : 'bg-base-content/40'" />
        <span class="font-bold text-[10px] uppercase">Active:</span>
        <span class="font-bold font-mono">{{ activeCount }}</span>
        <span v-if="activeCount > 0 && primaryActiveStrat" class="text-[10px] opacity-80 truncate max-w-[120px] hidden lg:inline">
          ({{ primaryActiveStrat }}{{ activeCount > 1 ? ` +${activeCount - 1}` : '' }})
        </span>
      </div>

      <!-- Viewing indicator -->
      <div 
        v-if="isViewingDifferent" 
        class="badge badge-sm badge-info badge-outline bg-info/10 gap-1 py-2.5 px-2 text-[10px] hidden xl:flex shrink-0"
        :title="`Inspecting ${cleanViewingName}`"
      >
        <Eye class="w-3 h-3 text-info" />
        <span class="opacity-70 uppercase font-bold text-[9px]">Viewing:</span>
        <span class="font-bold truncate max-w-[140px]">{{ cleanViewingName }}</span>
      </div>
    </div>

    <!-- Center/Right: Navigation Tabs & Controls -->
    <div class="flex items-center gap-1.5 md:gap-2 shrink-0">
      <!-- Navigation Button Group -->
      <div class="join">
        <button
          @click="emit('update:activeScreen', 'CHART')"
          class="btn btn-xs join-item font-mono tracking-tight"
          :class="activeScreen === 'CHART' ? 'btn-primary text-primary-content font-bold shadow' : 'btn-ghost text-base-content/70'"
          title="Live Candlestick Chart (F1)"
        >
          <BarChart2 class="w-3.5 h-3.5 mr-0.5" />
          <span class="hidden md:inline">Chart</span> (F1)
        </button>

        <button
          @click="emit('update:activeScreen', 'AGENT_DECK')"
          class="btn btn-xs join-item font-mono tracking-tight"
          :class="activeScreen === 'AGENT_DECK' ? 'btn-primary text-primary-content font-bold shadow' : 'btn-ghost text-base-content/70'"
          title="Signal Deck & Bot Telemetry (F2)"
        >
          <Send class="w-3.5 h-3.5 mr-0.5" />
          <span class="hidden md:inline">Signals</span> (F2)
        </button>

        <button
          @click="emit('update:activeScreen', 'BACKTEST')"
          class="btn btn-xs join-item font-mono tracking-tight"
          :class="activeScreen === 'BACKTEST' ? 'btn-primary text-primary-content font-bold shadow' : 'btn-ghost text-base-content/70'"
          title="Backtest Analytics & Cynic Audit (F3)"
        >
          <ShieldCheck class="w-3.5 h-3.5 mr-0.5" />
          <span class="hidden md:inline">Backtest</span> (F3)
        </button>

        <button
          @click="emit('update:activeScreen', 'STRATEGY_MANAGER')"
          class="btn btn-xs join-item font-mono tracking-tight"
          :class="activeScreen === 'STRATEGY_MANAGER' ? 'btn-secondary text-secondary-content font-bold shadow' : 'btn-ghost text-base-content/70'"
          title="Strategy Lifecycle Manager & Portfolio (F4)"
        >
          <Layers class="w-3.5 h-3.5 mr-0.5" />
          <span class="hidden md:inline">Strategies</span> (F4)
        </button>
      </div>

      <!-- Divider -->
      <div class="divider divider-horizontal mx-0.5 my-2 hidden sm:flex" />

      <!-- Local Machine Clock -->
      <div 
        class="hidden lg:flex items-center gap-1.5 px-2 py-1 rounded bg-base-300 border border-base-content/10 text-[11px]"
        :title="`Local Time: ${localTimeStr}`"
      >
        <Clock class="w-3.5 h-3.5 text-accent" />
        <span class="font-bold text-success">{{ localTimeStr }}</span>
      </div>

      <!-- Audio Tone Alerts Control -->
      <div class="join border border-base-content/10 rounded-btn overflow-hidden bg-base-300">
        <button
          @click="handleToggleSound"
          class="btn btn-xs btn-ghost join-item px-2 text-[10px] font-bold uppercase"
          :class="soundEnabled ? 'text-success' : 'text-base-content/50'"
          :title="soundEnabled ? 'Audio Chimes: ON (Click to mute)' : 'Audio Chimes: MUTED (Click to unmute)'"
        >
          <Volume2 v-if="soundEnabled" class="w-3.5 h-3.5 text-success" />
          <VolumeX v-else class="w-3.5 h-3.5 text-base-content/40" />
          <span class="hidden 2xl:inline ml-1">{{ soundEnabled ? 'Tone On' : 'Muted' }}</span>
        </button>
        <button
          @click="handleTestSound"
          class="btn btn-xs btn-ghost join-item border-l border-base-content/10 px-1.5 text-[9px] text-base-content/70 hover:text-base-content uppercase font-bold"
          title="Preview Harmonic Signal Tone"
        >
          Test
        </button>
      </div>

      <!-- Theme Switcher Button -->
      <button
        @click="toggleTheme"
        class="btn btn-xs btn-circle btn-ghost border border-base-content/10"
        :title="`Switch to ${isDark ? 'Light' : 'Dark'} Mode`"
      >
        <Sun v-if="isDark" class="w-3.5 h-3.5 text-warning" />
        <Moon v-else class="w-3.5 h-3.5 text-secondary" />
      </button>
    </div>
  </header>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import {
  Terminal,
  BarChart2,
  ShieldCheck,
  Sun,
  Moon,
  Send,
  Layers,
  Eye,
  Clock,
  Volume2,
  VolumeX,
} from 'lucide-vue-next';
import { isAudioEnabled, toggleAudioEnabled, testSignalTone } from '../utils/audio';

const props = defineProps<{
  activeScreen: 'CHART' | 'AGENT_DECK' | 'BACKTEST' | 'STRATEGY_MANAGER';
  isConnected: boolean;
  theme: 'dark' | 'light';
  activeStrategy?: string;
  activeBots?: string[];
  viewingStrategy?: string;
}>();

const emit = defineEmits<{
  (e: 'update:activeScreen', screen: 'CHART' | 'AGENT_DECK' | 'BACKTEST' | 'STRATEGY_MANAGER'): void;
  (e: 'update:theme', theme: 'dark' | 'light'): void;
}>();

const isDark = computed(() => props.theme === 'dark');

// Live machine clock
const localTimeStr = ref('');
let clockTimer: any = null;

const updateClock = () => {
  const now = new Date();
  const timePart = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
  const tzPart = new Intl.DateTimeFormat('en-US', { timeZoneName: 'short' }).formatToParts(now).find((p) => p.type === 'timeZoneName')?.value || '';
  localTimeStr.value = `${timePart} ${tzPart}`;
};

// Sound notification preference
const soundEnabled = ref(isAudioEnabled());

const handleToggleSound = () => {
  soundEnabled.value = toggleAudioEnabled();
};

const handleTestSound = (e: MouseEvent) => {
  e.stopPropagation();
  testSignalTone('BUY');
};

const toggleTheme = () => {
  const next = isDark.value ? 'light' : 'dark';
  emit('update:theme', next);
  document.documentElement.setAttribute('data-theme', next);
};

// Strategy active counts & viewing state
const effectiveActiveStrategies = computed(() => {
  if (props.activeBots && props.activeBots.length > 0) {
    return props.activeBots;
  }
  return props.activeStrategy ? [props.activeStrategy] : [];
});

const activeCount = computed(() => effectiveActiveStrategies.value.length);
const primaryActiveStrat = computed(() => (activeCount.value > 0 ? effectiveActiveStrategies.value[0].replace('.py', '') : null));

const cleanViewingName = computed(() => (props.viewingStrategy ? props.viewingStrategy.replace('.py', '') : ''));
const isViewingDifferent = computed(() => {
  return Boolean(
    cleanViewingName.value &&
      (!primaryActiveStrat.value || cleanViewingName.value.toLowerCase() !== primaryActiveStrat.value.toLowerCase())
  );
});

onMounted(() => {
  updateClock();
  clockTimer = setInterval(updateClock, 1000);
});

onUnmounted(() => {
  if (clockTimer) clearInterval(clockTimer);
});
</script>

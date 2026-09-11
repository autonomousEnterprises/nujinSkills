/**
 * EdgeMiner Web Audio Tone Synthesizer
 * 
 * Generates crisp, harmonic audio chimes using the native Web Audio API.
 * - Zero external assets or network dependencies
 * - Autoplay policy unlock handling
 * - Distinct harmonic tones for BUY (ascending) vs SELL (descending)
 * - Persistent mute/unmute preferences via localStorage
 */

const STORAGE_KEY = 'edgeminer_sound_enabled';

let audioCtx: AudioContext | null = null;
let isUnlocked = false;

function getAudioContext(): AudioContext | null {
  if (typeof window === 'undefined') return null;
  if (!audioCtx) {
    const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
    if (AudioContextClass) {
      audioCtx = new AudioContextClass();
    }
  }
  return audioCtx;
}

// Automatically unlock AudioContext on the user's first gesture
export function unlockAudio() {
  if (isUnlocked) return;
  const ctx = getAudioContext();
  if (ctx && ctx.state === 'suspended') {
    ctx.resume().then(() => {
      isUnlocked = true;
    }).catch(() => {});
  } else if (ctx && ctx.state === 'running') {
    isUnlocked = true;
  }
}

if (typeof window !== 'undefined') {
  const events = ['click', 'keydown', 'touchstart', 'pointerdown'];
  const handler = () => {
    unlockAudio();
    events.forEach((ev) => window.removeEventListener(ev, handler));
  };
  events.forEach((ev) => window.addEventListener(ev, handler, { once: true, passive: true }));
}

/**
 * Checks if sound notifications are enabled (default: true).
 */
export function isAudioEnabled(): boolean {
  if (typeof window === 'undefined') return true;
  const val = localStorage.getItem(STORAGE_KEY);
  return val === null ? true : val === 'true';
}

/**
 * Sets sound notification preference and dispatches a sync event.
 */
export function setAudioEnabled(enabled: boolean) {
  if (typeof window === 'undefined') return;
  localStorage.setItem(STORAGE_KEY, enabled ? 'true' : 'false');
  window.dispatchEvent(new CustomEvent('edgeminer-sound-toggled', { detail: { enabled } }));
}

/**
 * Toggles sound enabled state and returns the new value.
 */
export function toggleAudioEnabled(): boolean {
  const next = !isAudioEnabled();
  setAudioEnabled(next);
  return next;
}

/**
 * Synthesizes a melodic trading chime based on action.
 * - BUY / LONG: Ascending two-tone chime (D5: 587Hz -> A5: 880Hz)
 * - SELL / SHORT: Descending two-tone chime (A5: 880Hz -> D5: 587Hz)
 * - DEFAULT: Dual harmonic bell chime (784Hz + 1046Hz)
 */
function synthesizeTone(action?: string) {
  const ctx = getAudioContext();
  if (!ctx) return;

  const doPlay = () => {
    try {
      const now = ctx.currentTime;
      const isBuy = action && (action.toUpperCase().includes('BUY') || action.toUpperCase().includes('LONG'));
      const isSell = action && (action.toUpperCase().includes('SELL') || action.toUpperCase().includes('SHORT'));

      const masterGain = ctx.createGain();
      masterGain.connect(ctx.destination);
      masterGain.gain.setValueAtTime(0.40, now);

      if (isBuy) {
        // Note 1: D5 (587.33 Hz)
        const osc1 = ctx.createOscillator();
        const gain1 = ctx.createGain();
        osc1.type = 'sine';
        osc1.frequency.setValueAtTime(587.33, now);
        gain1.gain.setValueAtTime(0.8, now);
        gain1.gain.exponentialRampToValueAtTime(0.001, now + 0.18);
        osc1.connect(gain1);
        gain1.connect(masterGain);
        osc1.start(now);
        osc1.stop(now + 0.18);

        // Note 2: A5 (880.00 Hz) + octave harmonic shimmer
        const osc2 = ctx.createOscillator();
        const osc2Harmonic = ctx.createOscillator();
        const gain2 = ctx.createGain();
        osc2.type = 'sine';
        osc2Harmonic.type = 'triangle';
        osc2.frequency.setValueAtTime(880.00, now + 0.10);
        osc2Harmonic.frequency.setValueAtTime(1760.00, now + 0.10);
        gain2.gain.setValueAtTime(0.001, now);
        gain2.gain.setValueAtTime(0.95, now + 0.10);
        gain2.gain.exponentialRampToValueAtTime(0.0001, now + 0.55);
        osc2.connect(gain2);
        osc2Harmonic.connect(gain2);
        gain2.connect(masterGain);
        osc2.start(now + 0.10);
        osc2Harmonic.start(now + 0.10);
        osc2.stop(now + 0.55);
        osc2Harmonic.stop(now + 0.55);

      } else if (isSell) {
        // Note 1: A5 (880.00 Hz)
        const osc1 = ctx.createOscillator();
        const gain1 = ctx.createGain();
        osc1.type = 'sine';
        osc1.frequency.setValueAtTime(880.00, now);
        gain1.gain.setValueAtTime(0.8, now);
        gain1.gain.exponentialRampToValueAtTime(0.001, now + 0.18);
        osc1.connect(gain1);
        gain1.connect(masterGain);
        osc1.start(now);
        osc1.stop(now + 0.18);

        // Note 2: D5 (587.33 Hz) + warning undertone
        const osc2 = ctx.createOscillator();
        const osc2Sub = ctx.createOscillator();
        const gain2 = ctx.createGain();
        osc2.type = 'sine';
        osc2Sub.type = 'triangle';
        osc2.frequency.setValueAtTime(587.33, now + 0.10);
        osc2Sub.frequency.setValueAtTime(293.66, now + 0.10);
        gain2.gain.setValueAtTime(0.001, now);
        gain2.gain.setValueAtTime(0.95, now + 0.10);
        gain2.gain.exponentialRampToValueAtTime(0.0001, now + 0.55);
        osc2.connect(gain2);
        osc2Sub.connect(gain2);
        gain2.connect(masterGain);
        osc2.start(now + 0.10);
        osc2Sub.start(now + 0.10);
        osc2.stop(now + 0.55);
        osc2Sub.stop(now + 0.55);

      } else {
        // General / Neutral Signal: Harmonic Chime (G5 783.99 Hz + C6 1046.50 Hz)
        const osc1 = ctx.createOscillator();
        const osc2 = ctx.createOscillator();
        const gain = ctx.createGain();
        osc1.type = 'sine';
        osc2.type = 'sine';
        osc1.frequency.setValueAtTime(783.99, now);
        osc2.frequency.setValueAtTime(1046.50, now);
        gain.gain.setValueAtTime(0.9, now);
        gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.45);
        osc1.connect(gain);
        osc2.connect(gain);
        gain.connect(masterGain);
        osc1.start(now);
        osc2.start(now);
        osc1.stop(now + 0.45);
        osc2.stop(now + 0.45);
      }
      console.log(`[Audio] Played signal tone for action: ${action || 'GENERIC'}`);
    } catch (err) {
      console.warn('[Audio] Failed inside doPlay:', err);
    }
  };

  if (ctx.state === 'suspended') {
    ctx.resume().then(() => doPlay()).catch(() => doPlay());
  } else {
    doPlay();
  }
}

/**
 * Plays the signal tone if audio is enabled.
 */
export function playSignalTone(action?: string) {
  if (!isAudioEnabled()) return;
  try {
    synthesizeTone(action);
  } catch (err) {
    console.warn('[Audio] Failed to synthesize signal tone:', err);
  }
}

/**
 * Previews / tests the signal tone regardless of mute setting.
 * Also unlocks AudioContext immediately.
 */
export function testSignalTone(action?: string) {
  try {
    unlockAudio();
    synthesizeTone(action);
  } catch (err) {
    console.warn('[Audio] Failed to test signal tone:', err);
  }
}

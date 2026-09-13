import type { Time } from 'lightweight-charts';

export interface IndicatorPoint {
  time: Time;
  value: number;
}

export interface BollingerBandsResult {
  upper: IndicatorPoint[];
  middle: IndicatorPoint[];
  lower: IndicatorPoint[];
}

export interface HHLLResult {
  hh: IndicatorPoint[];
  ll: IndicatorPoint[];
}

export interface DynamicAtrBandsResult {
  upper: IndicatorPoint[];
  lower: IndicatorPoint[];
  atr: IndicatorPoint[];
}

export interface PremarketSRResult {
  support: IndicatorPoint[];
  resistance: IndicatorPoint[];
}

export interface NecklinesResult {
  necklineLong: IndicatorPoint[];
  necklineShort: IndicatorPoint[];
}

export interface IndicatorSeriesConfig {
  id: string;
  title: string;
  color: string;
  lineWidth?: number;
  lineStyle?: number; // 0: Solid, 1: Dotted, 2: Dashed, 3: LargeDashed
}

export interface IndicatorChipData {
  id: string;
  label: string;
  colorClass?: string;
  color?: string;
  value: string;
}

export interface StrategyIndicatorProfile {
  strategyKey: string;
  strategyDisplayName: string;
  frameworkBadge: string;
  frameworkDescription: string;
  badgeClass: string;
  seriesConfigs: IndicatorSeriesConfig[];
  calculate: (candles: any[]) => {
    seriesData: Record<string, IndicatorPoint[]>;
    getHudItems: (index: number) => IndicatorChipData[];
  };
}

/**
 * Exponential Moving Average (EMA)
 */
export function calculateEMA(data: { time: Time; close: number }[], period: number): IndicatorPoint[] {
  if (!data || data.length === 0) return [];
  const k = 2 / (period + 1);
  const result: IndicatorPoint[] = [];
  let ema = data[0].close;

  for (let i = 0; i < data.length; i++) {
    const close = data[i].close;
    if (i === 0) {
      ema = close;
    } else {
      ema = close * k + ema * (1 - k);
    }
    result.push({
      time: data[i].time,
      value: Number(ema.toFixed(2)),
    });
  }
  return result;
}

/**
 * Simple Moving Average (SMA)
 */
export function calculateSMA(data: { time: Time; close: number }[], period: number): IndicatorPoint[] {
  if (!data || data.length === 0) return [];
  const result: IndicatorPoint[] = [];

  for (let i = 0; i < data.length; i++) {
    const start = Math.max(0, i - period + 1);
    let sum = 0;
    const count = i - start + 1;
    for (let j = start; j <= i; j++) {
      sum += data[j].close;
    }
    result.push({
      time: data[i].time,
      value: Number((sum / count).toFixed(2)),
    });
  }
  return result;
}

/**
 * Bollinger Bands (SMA + StdDev)
 */
export function calculateBollingerBands(
  data: { time: Time; close: number }[],
  period: number = 20,
  mult: number = 2.0
): BollingerBandsResult {
  if (!data || data.length === 0) return { upper: [], middle: [], lower: [] };
  const upper: IndicatorPoint[] = [];
  const middle: IndicatorPoint[] = [];
  const lower: IndicatorPoint[] = [];

  for (let i = 0; i < data.length; i++) {
    const start = Math.max(0, i - period + 1);
    let sum = 0;
    const count = i - start + 1;
    for (let j = start; j <= i; j++) {
      sum += data[j].close;
    }
    const sma = sum / count;
    let sumSq = 0;
    for (let j = start; j <= i; j++) {
      const diff = data[j].close - sma;
      sumSq += diff * diff;
    }
    const std = Math.sqrt(sumSq / count);
    const up = Number((sma + mult * std).toFixed(2));
    const mid = Number(sma.toFixed(2));
    const dn = Number((sma - mult * std).toFixed(2));
    const time = data[i].time;
    upper.push({ time, value: up });
    middle.push({ time, value: mid });
    lower.push({ time, value: dn });
  }
  return { upper, middle, lower };
}

/**
 * Highest High / Lowest Low (HHLL) Channel
 */
export function calculateHHLL(
  data: { time: Time; high: number; low: number }[],
  period: number = 15
): HHLLResult {
  if (!data || data.length === 0) return { hh: [], ll: [] };
  const hh: IndicatorPoint[] = [];
  const ll: IndicatorPoint[] = [];

  for (let i = 0; i < data.length; i++) {
    const start = Math.max(0, i - period);
    const end = i;
    let maxH = -Infinity;
    let minL = Infinity;
    if (end > start) {
      for (let j = start; j < end; j++) {
        if (data[j].high > maxH) maxH = data[j].high;
        if (data[j].low < minL) minL = data[j].low;
      }
    } else {
      maxH = data[i].high;
      minL = data[i].low;
    }
    hh.push({ time: data[i].time, value: Number(maxH.toFixed(2)) });
    ll.push({ time: data[i].time, value: Number(minL.toFixed(2)) });
  }
  return { hh, ll };
}

/**
 * Average True Range (ATR) & Dynamic ATR Bands
 * Bands are anchored to the previous candle close: Close[t-1] +/- (mult * ATR[t-1])
 */
export function calculateDynamicAtrBands(
  data: { time: Time; open: number; high: number; low: number; close: number }[],
  period: number = 14,
  mult: number = 3.1
): DynamicAtrBandsResult {
  if (!data || data.length === 0) return { upper: [], lower: [], atr: [] };

  const trArr: number[] = [];
  for (let i = 0; i < data.length; i++) {
    const high = data[i].high;
    const low = data[i].low;
    const prevClose = i > 0 ? data[i - 1].close : data[i].open;
    const tr = Math.max(high - low, Math.abs(high - prevClose), Math.abs(low - prevClose));
    trArr.push(tr);
  }

  const atrArr: number[] = [];
  for (let i = 0; i < data.length; i++) {
    const start = Math.max(0, i - period + 1);
    let sum = 0;
    const count = i - start + 1;
    for (let j = start; j <= i; j++) {
      sum += trArr[j];
    }
    atrArr.push(sum / count);
  }

  const upper: IndicatorPoint[] = [];
  const lower: IndicatorPoint[] = [];
  const atr: IndicatorPoint[] = [];

  for (let i = 0; i < data.length; i++) {
    const time = data[i].time;
    const prevClose = i > 0 ? data[i - 1].close : data[i].close;
    const prevAtr = i > 0 ? atrArr[i - 1] : atrArr[i];
    const up = Number((prevClose + mult * prevAtr).toFixed(2));
    const dn = Number((prevClose - mult * prevAtr).toFixed(2));

    upper.push({ time, value: up });
    lower.push({ time, value: dn });
    atr.push({ time, value: Number(atrArr[i].toFixed(2)) });
  }

  return { upper, lower, atr };
}

/**
 * Pre-Market Key Support & Resistance (Opening Flush Reversal)
 * Rolling lookback shifted by 20 bars
 */
export function calculatePremarketSR(
  data: { time: Time; high: number; low: number }[],
  lookback: number = 120,
  shift: number = 20
): PremarketSRResult {
  if (!data || data.length === 0) return { support: [], resistance: [] };
  const support: IndicatorPoint[] = [];
  const resistance: IndicatorPoint[] = [];

  for (let i = 0; i < data.length; i++) {
    const end = Math.max(0, i - shift);
    const start = Math.max(0, end - lookback);
    let minLow = Infinity;
    let maxHigh = -Infinity;

    if (end > start) {
      for (let j = start; j < end; j++) {
        if (data[j].low < minLow) minLow = data[j].low;
        if (data[j].high > maxHigh) maxHigh = data[j].high;
      }
    } else {
      minLow = data[i].low;
      maxHigh = data[i].high;
    }

    support.push({ time: data[i].time, value: Number(minLow.toFixed(2)) });
    resistance.push({ time: data[i].time, value: Number(maxHigh.toFixed(2)) });
  }

  return { support, resistance };
}

/**
 * Neckline Market Structure Levels (Local swing high/low)
 */
export function calculateNecklines(
  data: { time: Time; high: number; low: number }[],
  lookback: number = 5
): NecklinesResult {
  if (!data || data.length === 0) return { necklineLong: [], necklineShort: [] };
  const necklineLong: IndicatorPoint[] = [];
  const necklineShort: IndicatorPoint[] = [];

  for (let i = 0; i < data.length; i++) {
    const end = i;
    const start = Math.max(0, i - lookback);
    let maxHigh = -Infinity;
    let minLow = Infinity;

    if (end > start) {
      for (let j = start; j < end; j++) {
        if (data[j].high > maxHigh) maxHigh = data[j].high;
        if (data[j].low < minLow) minLow = data[j].low;
      }
    } else {
      maxHigh = data[i].high;
      minLow = data[i].low;
    }

    necklineLong.push({ time: data[i].time, value: Number(maxHigh.toFixed(2)) });
    necklineShort.push({ time: data[i].time, value: Number(minLow.toFixed(2)) });
  }

  return { necklineLong, necklineShort };
}

/**
 * Volume Z-Score (Effort vs Result)
 */
export function calculateVolumeZScore(data: { volume?: number }[], period: number = 20): number[] {
  if (!data || data.length === 0) return [];
  const zscores: number[] = [];

  for (let i = 0; i < data.length; i++) {
    const start = Math.max(0, i - period + 1);
    let sum = 0;
    const count = i - start + 1;
    for (let j = start; j <= i; j++) {
      sum += data[j].volume || 10;
    }
    const mean = sum / count;

    let sumSq = 0;
    for (let j = start; j <= i; j++) {
      const diff = (data[j].volume || 10) - mean;
      sumSq += diff * diff;
    }
    const std = Math.sqrt(sumSq / count) || 1e-6;
    const z = ((data[i].volume || 10) - mean) / std;
    zscores.push(Number(z.toFixed(2)));
  }

  return zscores;
}

/**
 * Rolling Hurst Proxy (Variance ratio of 5-bar vs 1-bar log returns)
 */
export function calculateHurstProxy(data: { close: number }[], period: number = 50): number[] {
  if (!data || data.length === 0) return [];
  const ret1: number[] = [0];
  const ret5: number[] = [0];

  for (let i = 1; i < data.length; i++) {
    ret1.push(Math.log(data[i].close / (data[i - 1].close || 1)));
    const prev5 = i >= 5 ? data[i - 5].close : data[0].close;
    ret5.push(Math.log(data[i].close / (prev5 || 1)));
  }

  const hurstArr: number[] = [];
  for (let i = 0; i < data.length; i++) {
    const start = Math.max(0, i - period + 1);
    const count = i - start + 1;
    if (count < 5) {
      hurstArr.push(0.5);
      continue;
    }

    let sum1 = 0, sum5 = 0;
    for (let j = start; j <= i; j++) {
      sum1 += ret1[j];
      sum5 += ret5[j];
    }
    const mean1 = sum1 / count;
    const mean5 = sum5 / count;

    let var1 = 0, var5 = 0;
    for (let j = start; j <= i; j++) {
      var1 += (ret1[j] - mean1) ** 2;
      var5 += (ret5[j] - mean5) ** 2;
    }
    var1 = var1 / count;
    var5 = var5 / count;

    const proxy = var5 / ((var1 || 1e-6) * 5.0);
    hurstArr.push(Number(Math.max(0.1, Math.min(0.9, proxy)).toFixed(3)));
  }

  return hurstArr;
}

// ── Strategy Indicator Profile Registry ──────────────────────────────────────

export function getStrategyIndicatorProfile(rawStratName?: string): StrategyIndicatorProfile {
  const name = (rawStratName || '').toLowerCase().replace('.py', '');

  // 1. Opening Flush Reversal Scalper (S&P 500 / ES 1m)
  if (name.includes('opening') || name.includes('reversal') || (name.includes('sp') && !name.includes('atr'))) {
    return {
      strategyKey: 'OpeningFlushReversalScalper',
      strategyDisplayName: 'S&P 500 Opening Flush Reversal Scalper',
      frameworkBadge: 'PRE-MKT S&R + ATR ENVELOPE (±1.6x) + NECKLINE',
      frameworkDescription: 'Pre-market 120m Key Liquidity Zones, Dynamic 1.6x ATR Expansion Bands & Swing Structure Necklines',
      badgeClass: 'badge-success',
      seriesConfigs: [
        { id: 'premarket_resistance', title: 'PreMkt Res', color: '#f43f5e', lineStyle: 2, lineWidth: 1.5 },
        { id: 'premarket_support', title: 'PreMkt Sup', color: '#10b981', lineStyle: 2, lineWidth: 1.5 },
        { id: 'atr_upper_band', title: 'ATR Upper (1.6x)', color: '#a855f7', lineStyle: 1, lineWidth: 1 },
        { id: 'atr_lower_band', title: 'ATR Lower (1.6x)', color: '#a855f7', lineStyle: 1, lineWidth: 1 },
        { id: 'neckline', title: 'Neckline', color: '#f59e0b', lineStyle: 0, lineWidth: 1.5 },
      ],
      calculate: (candles: any[]) => {
        const sr = calculatePremarketSR(candles, 120, 20);
        const atrBands = calculateDynamicAtrBands(candles, 14, 1.6);
        const necklines = calculateNecklines(candles, 5);

        return {
          seriesData: {
            premarket_resistance: sr.resistance,
            premarket_support: sr.support,
            atr_upper_band: atrBands.upper,
            atr_lower_band: atrBands.lower,
            neckline: necklines.necklineLong,
          },
          getHudItems: (idx: number) => {
            if (idx < 0 || idx >= candles.length) return [];
            const t = candles[idx].time;
            const date = typeof t === 'number' ? new Date(t * 1000) : new Date();
            const minOfDay = date.getUTCHours() * 60 + date.getUTCMinutes();
            const isUsReversal = minOfDay >= 825 && minOfDay <= 860;
            const isLonReversal = minOfDay >= 435 && minOfDay <= 470;
            const inWindow = isUsReversal || isLonReversal;

            return [
              { id: 'res', label: 'PreMkt Res', color: '#f43f5e', value: sr.resistance[idx]?.value ? `$${sr.resistance[idx].value.toFixed(2)}` : '–' },
              { id: 'sup', label: 'PreMkt Sup', color: '#10b981', value: sr.support[idx]?.value ? `$${sr.support[idx].value.toFixed(2)}` : '–' },
              { id: 'atr_env', label: 'ATR Env (±1.6x)', color: '#a855f7', value: `[${atrBands.lower[idx]?.value.toFixed(2)} - ${atrBands.upper[idx]?.value.toFixed(2)}]` },
              { id: 'neckline', label: 'Neckline', color: '#f59e0b', value: `$${necklines.necklineLong[idx]?.value.toFixed(2)}` },
              { id: 'atr14', label: 'ATR14', color: '#38bdf8', value: `$${atrBands.atr[idx]?.value.toFixed(2)}` },
              { id: 'window', label: 'Reversal Window', color: inWindow ? '#34d399' : '#94a3b8', value: inWindow ? 'ACTIVE' : 'STANDBY' },
            ];
          },
        };
      },
    };
  }

  // 2. Goat Funded Trader London Open OTAD Scalper
  if (name.includes('otad') || (name.includes('london') && (name.includes('goat') || name.includes('scalper')))) {
    return {
      strategyKey: 'GoatLondonOpenOtadScalper',
      strategyDisplayName: 'Goat Funded Trader London Open OTAD Scalper',
      frameworkBadge: 'LONDON OPEN VOLATILITY ABSORPTION (ATR 1.8x) + ASIAN RANGE',
      frameworkDescription: 'One-Trade-A-Day (OTAD) London Open Volatility Extension Fade & Asian Range Reversion',
      badgeClass: 'badge-warning',
      seriesConfigs: [
        { id: 'atr_upper_band', title: 'ATR Upper (1.8x)', color: '#f43f5e', lineStyle: 0, lineWidth: 1.5 },
        { id: 'atr_lower_band', title: 'ATR Lower (1.8x)', color: '#10b981', lineStyle: 0, lineWidth: 1.5 },
      ],
      calculate: (candles: any[]) => {
        const atrBands = calculateDynamicAtrBands(candles, 14, 1.8);
        const zscores = calculateVolumeZScore(candles, 20);

        return {
          seriesData: {
            atr_upper_band: atrBands.upper,
            atr_lower_band: atrBands.lower,
          },
          getHudItems: (idx: number) => {
            if (idx < 0 || idx >= candles.length) return [];
            const t = candles[idx].time;
            const date = typeof t === 'number' ? new Date(t * 1000) : new Date();
            const minOfDay = date.getUTCHours() * 60 + date.getUTCMinutes();
            const isLondon = minOfDay >= 420 && minOfDay <= 570;

            return [
              { id: 'atr_upper', label: 'ATR Band Upper', color: '#f43f5e', value: `$${atrBands.upper[idx]?.value.toFixed(2)}` },
              { id: 'atr_lower', label: 'ATR Band Lower', color: '#10b981', value: `$${atrBands.lower[idx]?.value.toFixed(2)}` },
              { id: 'session', label: 'London Window', color: isLondon ? '#34d399' : '#94a3b8', value: isLondon ? 'ACTIVE' : 'STANDBY' },
              { id: 'volz', label: 'Vol Z', color: '#38bdf8', value: `${zscores[idx] >= 0 ? '+' : ''}${zscores[idx]}` },
            ];
          },
        };
      },
    };
  }

  // 3. Gold Liquidity Sweep & ATR Rebound Scalper
  if (name.includes('liquidity') && (name.includes('sweep') || name.includes('rebound')) && (name.includes('gold') || name.includes('xau'))) {
    return {
      strategyKey: 'GoldLiquiditySweepAtrScalper',
      strategyDisplayName: 'Gold Liquidity Sweep & ATR Rebound Scalper',
      frameworkBadge: 'DYNAMIC ATR ENVELOPE (2.0x) + WICK ABSORPTION',
      frameworkDescription: 'XAUUSD 1-Minute Volatility Sweep Piercing with Passive Institutional Absorption Fading',
      badgeClass: 'badge-warning',
      seriesConfigs: [
        { id: 'atr_lower_band', title: 'ATR Lower (-2.0x)', color: '#10b981', lineStyle: 0, lineWidth: 2 },
        { id: 'atr_upper_band', title: 'ATR Upper (+1.8x)', color: '#f43f5e', lineStyle: 0, lineWidth: 2 },
      ],
      calculate: (candles: any[]) => {
        const atrBands = calculateDynamicAtrBands(candles, 14, 2.0);
        const zscores = calculateVolumeZScore(candles, 20);

        return {
          seriesData: {
            atr_lower_band: atrBands.lower,
            atr_upper_band: atrBands.upper,
          },
          getHudItems: (idx: number) => {
            if (idx < 0 || idx >= candles.length) return [];
            return [
              { id: 'atr_lower', label: 'Dip Envelope (-2.0x)', color: '#10b981', value: `$${atrBands.lower[idx]?.value.toFixed(2)}` },
              { id: 'atr_upper', label: 'Target Envelope (+1.8x)', color: '#f43f5e', value: `$${atrBands.upper[idx]?.value.toFixed(2)}` },
              { id: 'volz', label: 'Vol Z', color: '#38bdf8', value: `${zscores[idx] >= 0 ? '+' : ''}${zscores[idx]}` },
            ];
          },
        };
      },
    };
  }

  // 4. Goat Funded Trader XAUUSD Scalper (The Gold Momentum Train)
  if (name.includes('goat') || (name.includes('xau') && !name.includes('hybrid') && !name.includes('atr'))) {
    return {
      strategyKey: 'GoatFundedTraderXauusdScalper',
      strategyDisplayName: 'Goat Funded Trader XAUUSD Scalper',
      frameworkBadge: 'MOMENTUM RIBBON (EMA 9/21/200) + HH/LL 15 BREAKOUT',
      frameworkDescription: '9/21/200 Exponential Moving Average Accelerator Ribbon and 15-Bar Breakout Channel',
      badgeClass: 'badge-warning',
      seriesConfigs: [
        { id: 'ema_9', title: 'EMA 9', color: '#38bdf8', lineStyle: 0, lineWidth: 1.5 },
        { id: 'ema_21', title: 'EMA 21', color: '#818cf8', lineStyle: 0, lineWidth: 1.5 },
        { id: 'ema_200', title: 'EMA 200', color: '#f59e0b', lineStyle: 0, lineWidth: 2 },
        { id: 'hh_15', title: 'HH 15', color: '#34d399', lineStyle: 2, lineWidth: 1 },
        { id: 'll_15', title: 'LL 15', color: '#f87171', lineStyle: 2, lineWidth: 1 },
      ],
      calculate: (candles: any[]) => {
        const ema9 = calculateEMA(candles, 9);
        const ema21 = calculateEMA(candles, 21);
        const ema200 = calculateEMA(candles, Math.min(200, candles.length));
        const hhll = calculateHHLL(candles, 15);
        const zscores = calculateVolumeZScore(candles, 20);
        const atrBands = calculateDynamicAtrBands(candles, 14, 1.5);

        return {
          seriesData: {
            ema_9: ema9,
            ema_21: ema21,
            ema_200: ema200,
            hh_15: hhll.hh,
            ll_15: hhll.ll,
          },
          getHudItems: (idx: number) => {
            if (idx < 0 || idx >= candles.length) return [];
            const t = candles[idx].time;
            const date = typeof t === 'number' ? new Date(t * 1000) : new Date();
            const minOfDay = date.getUTCHours() * 60 + date.getUTCMinutes();
            const isLondon = minOfDay >= 450 && minOfDay <= 630;
            const isNy = minOfDay >= 765 && minOfDay <= 990;
            const sessionName = isLondon ? 'LONDON OPEN' : (isNy ? 'NY SESSION' : 'OFF SESSION');

            return [
              { id: 'ema9', label: 'EMA9', color: '#38bdf8', value: ema9[idx]?.value != null ? `$${ema9[idx].value.toFixed(2)}` : '–' },
              { id: 'ema21', label: 'EMA21', color: '#818cf8', value: ema21[idx]?.value != null ? `$${ema21[idx].value.toFixed(2)}` : '–' },
              { id: 'ema200', label: 'EMA200', color: '#f59e0b', value: ema200[idx]?.value != null ? `$${ema200[idx].value.toFixed(2)}` : '–' },
              { id: 'hh15', label: 'HH15', color: '#34d399', value: hhll.hh[idx]?.value != null ? `$${hhll.hh[idx].value.toFixed(2)}` : '–' },
              { id: 'll15', label: 'LL15', color: '#f87171', value: hhll.ll[idx]?.value != null ? `$${hhll.ll[idx].value.toFixed(2)}` : '–' },
              { id: 'atr14', label: 'ATR14', color: '#a855f7', value: atrBands.atr[idx]?.value != null ? `$${atrBands.atr[idx].value.toFixed(2)}` : '–' },
              { id: 'volz', label: 'Vol Z', color: '#38bdf8', value: zscores[idx] != null ? `${zscores[idx] >= 0 ? '+' : ''}${zscores[idx]}` : '–' },
              { id: 'session', label: 'Session', color: (isLondon || isNy) ? '#34d399' : '#94a3b8', value: sessionName },
            ];
          },
        };
      },
    };
  }

  // 5. Prop Firm ATR Hybrid Scalper XAUUSD (Trader MNQ on Gold 1m)
  if (name.includes('atr') && (name.includes('xau') || name.includes('gold'))) {
    return {
      strategyKey: 'PropFirmAtrHybridScalperXauusd',
      strategyDisplayName: 'Trader MNQ ATR Scalper on Gold',
      frameworkBadge: 'DYNAMIC ATR BANDS (±2.0x) + SMA 20 BASELINE',
      frameworkDescription: 'Trader MNQ Dynamic Intraday ATR Lower Envelope Limit Fill & Upper Exhaustion Reversal',
      badgeClass: 'badge-warning',
      seriesConfigs: [
        { id: 'atr_lower_band', title: 'ATR Lower (-2.0x Dip)', color: '#10b981', lineStyle: 0, lineWidth: 2 },
        { id: 'atr_upper_band', title: 'ATR Upper (+2.0x Target)', color: '#f43f5e', lineStyle: 0, lineWidth: 2 },
        { id: 'sma_20', title: 'SMA 20 Baseline', color: '#fbbf24', lineStyle: 2, lineWidth: 1 },
      ],
      calculate: (candles: any[]) => {
        const atrBands = calculateDynamicAtrBands(candles, 14, 2.0);
        const sma20 = calculateSMA(candles, 20);
        const zscores = calculateVolumeZScore(candles, 20);

        return {
          seriesData: {
            atr_lower_band: atrBands.lower,
            atr_upper_band: atrBands.upper,
            sma_20: sma20,
          },
          getHudItems: (idx: number) => {
            if (idx < 0 || idx >= candles.length) return [];
            const c = candles[idx].close;
            const prev24h = idx >= 1440 ? candles[idx - 1440].close : candles[0].close;
            const macroBull = c >= prev24h;

            return [
              { id: 'lower_band', label: 'ATR Lower (-2.0x)', color: '#10b981', value: `$${atrBands.lower[idx]?.value.toFixed(2)}` },
              { id: 'upper_band', label: 'ATR Upper (+2.0x)', color: '#f43f5e', value: `$${atrBands.upper[idx]?.value.toFixed(2)}` },
              { id: 'sma20', label: 'SMA 20', color: '#fbbf24', value: `$${sma20[idx]?.value.toFixed(2)}` },
              { id: 'atr14', label: 'ATR14', color: '#38bdf8', value: `$${atrBands.atr[idx]?.value.toFixed(2)}` },
              { id: 'volz', label: 'Vol Z', color: '#38bdf8', value: `${zscores[idx] >= 0 ? '+' : ''}${zscores[idx]}` },
              { id: 'macro', label: '24h Macro', color: macroBull ? '#34d399' : '#f87171', value: macroBull ? 'BULLISH' : 'BEARISH' },
            ];
          },
        };
      },
    };
  }

  // 4. Prop Firm ATR Hybrid Scalper (Trader MNQ on BTC/USDT 15m)
  if (name.includes('atr') || name.includes('hybrid')) {
    return {
      strategyKey: 'PropFirmAtrHybridScalper',
      strategyDisplayName: 'Prop Firm ATR Hybrid Scalper (BTC 15m)',
      frameworkBadge: 'DYNAMIC ATR BANDS (±3.1x) + SMA 20 BASELINE',
      frameworkDescription: 'Intra-bar Dynamic ATR Envelope Dip Limit Fill (Long) vs Shooting Star Exhaustion Fading (Short)',
      badgeClass: 'badge-info',
      seriesConfigs: [
        { id: 'atr_lower_band', title: 'ATR Lower (-3.1x Dip)', color: '#10b981', lineStyle: 0, lineWidth: 2 },
        { id: 'atr_upper_band', title: 'ATR Upper (+3.1x Exhaustion)', color: '#f43f5e', lineStyle: 0, lineWidth: 2 },
        { id: 'sma_20', title: 'SMA 20 Baseline', color: '#38bdf8', lineStyle: 2, lineWidth: 1 },
      ],
      calculate: (candles: any[]) => {
        const atrBands = calculateDynamicAtrBands(candles, 14, 3.1);
        const sma20 = calculateSMA(candles, 20);
        const zscores = calculateVolumeZScore(candles, 20);

        return {
          seriesData: {
            atr_lower_band: atrBands.lower,
            atr_upper_band: atrBands.upper,
            sma_20: sma20,
          },
          getHudItems: (idx: number) => {
            if (idx < 0 || idx >= candles.length) return [];
            const c = candles[idx].close;
            const prev24h = idx >= 96 ? candles[idx - 96].close : candles[0].close;
            const isBearishRegime = c < prev24h;

            return [
              { id: 'lower_band', label: 'ATR Lower (-3.1x)', color: '#10b981', value: `$${atrBands.lower[idx]?.value.toFixed(1)}` },
              { id: 'upper_band', label: 'ATR Upper (+3.1x)', color: '#f43f5e', value: `$${atrBands.upper[idx]?.value.toFixed(1)}` },
              { id: 'sma20', label: 'SMA 20', color: '#38bdf8', value: `$${sma20[idx]?.value.toFixed(1)}` },
              { id: 'atr14', label: 'ATR14', color: '#a855f7', value: `$${atrBands.atr[idx]?.value.toFixed(1)}` },
              { id: 'volz', label: 'Vol Z', color: '#38bdf8', value: `${zscores[idx] >= 0 ? '+' : ''}${zscores[idx]}` },
              { id: 'regime', label: 'Macro Regime', color: isBearishRegime ? '#f87171' : '#34d399', value: isBearishRegime ? 'BEARISH' : 'BULLISH' },
            ];
          },
        };
      },
    };
  }

  // 5. Trap Fade v1 (Fade Asian Liquidity Sweeps)
  if (name.includes('trap') || name.includes('fade')) {
    return {
      strategyKey: 'TrapFade_v1',
      strategyDisplayName: 'Fade Asian Liquidity Sweeps (Trap Fade)',
      frameworkBadge: 'BOLLINGER TRAP BANDS (±2.0σ) + HURST REGIME',
      frameworkDescription: 'Asian Liquidity Sweep Fading into Counterparty Passive Limit Traps',
      badgeClass: 'badge-accent',
      seriesConfigs: [
        { id: 'bb_upper', title: 'BB Upper (Trap)', color: '#e879f9', lineStyle: 2, lineWidth: 1.5 },
        { id: 'sma_20', title: 'SMA 20 Reversion', color: '#38bdf8', lineStyle: 0, lineWidth: 1.5 },
        { id: 'bb_lower', title: 'BB Lower (Trap)', color: '#e879f9', lineStyle: 2, lineWidth: 1.5 },
      ],
      calculate: (candles: any[]) => {
        const bb = calculateBollingerBands(candles, 20, 2.0);
        const hurst = calculateHurstProxy(candles, 50);
        const zscores = calculateVolumeZScore(candles, 20);

        return {
          seriesData: {
            bb_upper: bb.upper,
            sma_20: bb.middle,
            bb_lower: bb.lower,
          },
          getHudItems: (idx: number) => {
            if (idx < 0 || idx >= candles.length) return [];
            const h = hurst[idx];
            const isMeanRev = h < 0.5;

            return [
              { id: 'bb_up', label: 'BB Upper', color: '#e879f9', value: `$${bb.upper[idx]?.value.toFixed(1)}` },
              { id: 'sma20', label: 'SMA 20 Target', color: '#38bdf8', value: `$${bb.middle[idx]?.value.toFixed(1)}` },
              { id: 'bb_low', label: 'BB Lower', color: '#e879f9', value: `$${bb.lower[idx]?.value.toFixed(1)}` },
              { id: 'hurst', label: 'Hurst Proxy', color: isMeanRev ? '#34d399' : '#f59e0b', value: `${h} (${isMeanRev ? 'Mean-Rev' : 'Trend'})` },
              { id: 'volz', label: 'Vol Z', color: '#38bdf8', value: `${zscores[idx] >= 0 ? '+' : ''}${zscores[idx]}` },
              { id: 'wick', label: 'Wick Trap Trigger', color: '#e879f9', value: '> 38%' },
            ];
          },
        };
      },
    };
  }

  // 6. Prop Firm VSA Wick Rejection (Default for BTC 15m)
  return {
    strategyKey: 'PropFirmVsaWickRejection',
    strategyDisplayName: 'Prop Firm Challenge VSA Wick Rejection',
    frameworkBadge: 'BOLLINGER BANDS (±2.0σ) + SMA 20 EXIT + VSA Z-SCORE',
    frameworkDescription: 'Volume Spread Analysis (VSA) Wick Rejection with Bollinger Bands Mean-Reversion Target',
    badgeClass: 'badge-primary',
    seriesConfigs: [
      { id: 'bb_upper', title: 'BB Upper', color: '#c084fc', lineStyle: 2, lineWidth: 1.5 },
      { id: 'sma_20', title: 'SMA 20 (Exit)', color: '#38bdf8', lineStyle: 0, lineWidth: 1.5 },
      { id: 'bb_lower', title: 'BB Lower', color: '#c084fc', lineStyle: 2, lineWidth: 1.5 },
    ],
    calculate: (candles: any[]) => {
      const bb = calculateBollingerBands(candles, 20, 2.0);
      const hurst = calculateHurstProxy(candles, 50);
      const zscores = calculateVolumeZScore(candles, 20);

      return {
        seriesData: {
          bb_upper: bb.upper,
          sma_20: bb.middle,
          bb_lower: bb.lower,
        },
        getHudItems: (idx: number) => {
          if (idx < 0 || idx >= candles.length) return [];
          const h = hurst[idx];
          const isMeanRev = h < 0.5;

          return [
            { id: 'bb_up', label: 'BB Upper', color: '#c084fc', value: `$${bb.upper[idx]?.value.toFixed(1)}` },
            { id: 'sma20', label: 'SMA 20 (Exit)', color: '#38bdf8', value: `$${bb.middle[idx]?.value.toFixed(1)}` },
            { id: 'bb_low', label: 'BB Lower', color: '#c084fc', value: `$${bb.lower[idx]?.value.toFixed(1)}` },
            { id: 'hurst', label: 'Hurst Proxy', color: isMeanRev ? '#34d399' : '#f59e0b', value: `${h} (${isMeanRev ? 'Mean-Rev' : 'Trend'})` },
            { id: 'volz', label: 'Vol Z', color: '#38bdf8', value: `${zscores[idx] >= 0 ? '+' : ''}${zscores[idx]}` },
            { id: 'wick', label: 'Wick Rejection', color: '#c084fc', value: '> 40%' },
          ];
        },
      };
    },
  };
}

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
 * Bollinger Bands
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
    if (i < 1) continue;
    const start = Math.max(0, i - period);
    const end = i;
    let maxH = -Infinity;
    let minL = Infinity;
    for (let j = start; j < end; j++) {
      if (data[j].high > maxH) maxH = data[j].high;
      if (data[j].low < minL) minL = data[j].low;
    }
    hh.push({ time: data[i].time, value: Number(maxH.toFixed(2)) });
    ll.push({ time: data[i].time, value: Number(minL.toFixed(2)) });
  }
  return { hh, ll };
}

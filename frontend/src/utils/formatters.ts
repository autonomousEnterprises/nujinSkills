/**
 * Centralized formatting and display helpers for quant metrics, badges, and colors
 */

export const formatPrice = (p: number | undefined | null, isGold: boolean = false): string => {
  if (p == null || isNaN(p)) return '–';
  return isGold ? p.toFixed(2) : p.toFixed(1);
};

export const formatPercent = (val: number | undefined | null, decimals: number = 1): string => {
  if (val == null || isNaN(val)) return '–';
  const norm = val <= 1.0 && val >= -1.0 ? val * 100 : val;
  return `${norm.toFixed(decimals)}%`;
};

export const formatWinRate = (wr: number | undefined | null): string => {
  if (wr == null || isNaN(wr)) return '—';
  const val = wr <= 1.0 ? wr * 100 : wr;
  return `${val.toFixed(1)}%`;
};

export const formatMdd = (mdd: number | undefined | null): string => {
  if (mdd == null || isNaN(mdd)) return '—';
  const val = mdd <= 1.0 ? mdd * 100 : mdd;
  return `${val.toFixed(2)}%`;
};

export const formatSnapTime = (ts?: string): string => {
  if (!ts) return '—';
  try {
    const d = new Date(ts);
    return d.toLocaleDateString([], { month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit' });
  } catch {
    return ts.slice(5, 16);
  }
};

export const getValColor = (val?: number | null): string => {
  if (val === undefined || val === null) return 'text-base-content';
  return val < 0 ? 'text-error font-bold' : 'text-success font-bold';
};

export const getTierBadgeClass = (tier?: string): string => {
  if (!tier) return 'badge-neutral';
  if (tier.includes('S-Tier')) return 'badge-warning border-warning/40 text-warning font-bold bg-warning/10';
  if (tier.includes('A-Tier')) return 'badge-primary border-primary/40 text-primary font-bold bg-primary/10';
  if (tier.includes('B-Tier')) return 'badge-info border-info/40 text-info font-bold bg-info/10';
  return 'badge-ghost text-base-content/60';
};

export const getStatusBadgeClass = (status?: string): string => {
  if (status === 'ACTIVE_LIVE') return 'badge-success bg-success/10 text-success';
  if (status === 'CRON_BACKTEST') return 'badge-warning bg-warning/10 text-warning';
  return 'badge-neutral bg-base-300 text-base-content/50';
};

export interface ResolvedTimePeriod {
  start_time?: number;
  end_time?: number;
  start_date?: string;
  end_date?: string;
  duration_days?: number;
  period_label: string;
  short_label: string;
  candles_count?: number;
}

export const getTimePeriodInfo = (obj?: any): ResolvedTimePeriod | null => {
  if (!obj) return null;

  // 1. Direct time_period property
  const tp = obj.time_period || obj.summary?.time_period || obj.latest_backtest?.time_period;
  if (tp && (tp.period_label || tp.start_date || tp.start_time)) {
    const label = tp.period_label || `${tp.start_date || ''} → ${tp.end_date || ''} (${tp.duration_days ? tp.duration_days.toFixed(1) + 'd' : ''})`;
    const short = tp.duration_days != null ? `${tp.duration_days.toFixed(1)}d window` : label;
    return {
      start_time: tp.start_time,
      end_time: tp.end_time,
      start_date: tp.start_date,
      end_date: tp.end_date,
      duration_days: tp.duration_days,
      period_label: label,
      short_label: short,
      candles_count: tp.candles_count
    };
  }

  // 2. Summary or latest_backtest subfields
  const summary = obj.summary || obj.latest_backtest || obj;
  if (summary && summary.period_label) {
    return {
      start_time: summary.start_time,
      end_time: summary.end_time,
      start_date: summary.start_date,
      end_date: summary.end_date,
      duration_days: summary.duration_days,
      period_label: summary.period_label,
      short_label: summary.duration_days != null ? `${summary.duration_days.toFixed(1)}d window` : summary.period_label,
      candles_count: summary.candles_count
    };
  }

  // 3. Equity curve inspection
  const eq = obj.equity_curve || obj.backtest_equity_curve;
  if (Array.isArray(eq) && eq.length >= 2) {
    const t0 = Number(eq[0].time);
    const t1 = Number(eq[eq.length - 1].time);
    if (t0 > 1000000000 && t1 > 1000000000) {
      const d0 = new Date(t0 * 1000);
      const d1 = new Date(t1 * 1000);
      const days = Number(((t1 - t0) / 86400).toFixed(1));
      const s0 = d0.toISOString().slice(0, 10);
      const s1 = d1.toISOString().slice(0, 10);
      const label = `${s0} → ${s1} (${days}d)`;
      return {
        start_time: t0,
        end_time: t1,
        start_date: s0,
        end_date: s1,
        duration_days: days,
        period_label: label,
        short_label: `${days}d window`
      };
    }
  }

  // 4. Trades detail inspection
  const trades = obj.trades_detail;
  if (Array.isArray(trades) && trades.length >= 1) {
    const t0 = Number(trades[0].entry_time);
    const t1 = Number(trades[trades.length - 1].exit_time || trades[trades.length - 1].entry_time);
    if (t0 > 1000000000 && t1 > 1000000000) {
      const d0 = new Date(t0 * 1000);
      const d1 = new Date(t1 * 1000);
      const days = Number(((t1 - t0) / 86400).toFixed(1));
      const s0 = d0.toISOString().slice(0, 10);
      const s1 = d1.toISOString().slice(0, 10);
      const label = `${s0} → ${s1} (${days}d)`;
      return {
        start_time: t0,
        end_time: t1,
        start_date: s0,
        end_date: s1,
        duration_days: days,
        period_label: label,
        short_label: `${days}d window`
      };
    }
  }

  // 5. Fallback based on asset dataset
  return getDatasetFallbackPeriod(obj);
};

export const getDatasetFallbackPeriod = (identifier?: any): ResolvedTimePeriod => {
  const str = String(
    (identifier && typeof identifier === 'object' ? (identifier.name || identifier.symbol || identifier.active_strategy || '') : identifier) || ''
  ).toLowerCase();

  if (str.includes('btc') || str.includes('bitcoin')) {
    return {
      start_time: 1782864000,
      end_time: 1789625700,
      start_date: '2026-07-01 00:00 UTC',
      end_date: '2026-09-17 06:15 UTC',
      duration_days: 78.3,
      period_label: '2026-07-01 → 2026-09-17 (78.3d)',
      short_label: '78.3d window',
      candles_count: 7514
    };
  }
  if (str.includes('sp500') || str.includes('spx') || str.includes('es')) {
    return {
      start_time: 1788732000,
      end_time: 1789625220,
      start_date: '2026-09-06 22:00 UTC',
      end_date: '2026-09-17 06:07 UTC',
      duration_days: 10.3,
      period_label: '2026-09-06 → 2026-09-17 (10.3d)',
      short_label: '10.3d window',
      candles_count: 11286
    };
  }
  // Default to primary asset dataset (XAU/USD Gold)
  return {
    start_time: 1788127440,
    end_time: 1789629120,
    start_date: '2026-08-30 22:04 UTC',
    end_date: '2026-09-17 07:12 UTC',
    duration_days: 17.4,
    period_label: '2026-08-30 → 2026-09-17 (17.4d)',
    short_label: '17.4d window',
    candles_count: 16942
  };
};

export const formatTimePeriod = (obj?: any, fallback?: string): string => {
  const info = getTimePeriodInfo(obj);
  if (info && info.period_label) return info.period_label;
  if (fallback && !fallback.toLowerCase().includes('historical') && fallback !== 'N/A') return fallback;
  return getDatasetFallbackPeriod(obj).period_label;
};

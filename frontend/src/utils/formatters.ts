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

#!/usr/bin/env python3
"""
tools/send_daily_report.py
Generates and broadcasts a dynamic daily quant trading & strategy performance report to all Telegram users.
All metrics, session dates, trade PnLs, win rates, drawdowns, and strategy stats are dynamically calculated from live data.
"""

import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from server.telegram_bot import telegram_gateway


def load_json_file(path: Path):
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[Warning] Failed to load {path}: {e}")
        return None


def generate_report_text(target_date_str: str = None) -> str:
    signals_path = PROJECT_ROOT / "data" / "signals.json"
    state_path = PROJECT_ROOT / "data" / "state.json"
    strategies_path = PROJECT_ROOT / "data" / "strategies.json"

    signals = load_json_file(signals_path) or []
    state = load_json_file(state_path) or {}
    strategies = load_json_file(strategies_path) or []
    strat_lookup = {s.get("name"): s for s in strategies if isinstance(s, dict)}

    now = datetime.now().astimezone()

    # Determine session date
    if target_date_str:
        session_signals = [
            s for s in signals
            if datetime.fromtimestamp(s.get("time", 0)).astimezone().strftime("%Y-%m-%d") == target_date_str
        ]
        session_date_str = target_date_str
    else:
        today_str = now.strftime("%Y-%m-%d")
        session_signals = [
            s for s in signals
            if datetime.fromtimestamp(s.get("time", 0)).astimezone().strftime("%Y-%m-%d") == today_str
        ]
        if not session_signals and signals:
            # Fall back to most recent recorded date in signals
            latest_dt = datetime.fromtimestamp(signals[0].get("time", 0)).astimezone()
            session_date_str = latest_dt.strftime("%Y-%m-%d")
            session_signals = [
                s for s in signals
                if datetime.fromtimestamp(s.get("time", 0)).astimezone().strftime("%Y-%m-%d") == session_date_str
            ]
        else:
            session_date_str = today_str

    time_now_str = now.strftime("%H:%M:%S %Z")
    total_trades = len(session_signals)

    if total_trades == 0:
        return (
            f"📊 <b>EDGEMINER DAILY QUANT & STRATEGY REPORT</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📅 <b>Date:</b> <code>{session_date_str}</code> | ⏰ <code>{time_now_str}</code>\n"
            f"💼 <b>Portfolio Status:</b> <b>NO TRADES RECORDED TODAY</b>\n\n"
            f"ℹ️ Quantitative scanners are active and monitoring regime triggers.\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚡ <i>NujinAIs Zillions</i>"
        )

    open_trades = [s for s in session_signals if s.get("status") == "OPEN"]
    closed_trades = [s for s in session_signals if s.get("status") == "CLOSED"]

    wins = [s for s in closed_trades if float(s.get("pnl_pct", 0) or 0) > 0]
    losses = [s for s in closed_trades if float(s.get("pnl_pct", 0) or 0) < 0]
    breakeven = [s for s in closed_trades if float(s.get("pnl_pct", 0) or 0) == 0]

    gross_profit = sum(float(s.get("pnl_pct", 0) or 0) for s in wins)
    gross_loss = abs(sum(float(s.get("pnl_pct", 0) or 0) for s in losses))
    net_pnl = sum(float(s.get("pnl_pct", 0) or 0) for s in closed_trades)

    win_rate = (len(wins) / len(closed_trades) * 100) if closed_trades else 0.0
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (gross_profit if gross_profit > 0 else 1.0)
    avg_win = (gross_profit / len(wins)) if wins else 0.0
    avg_loss = (-gross_loss / len(losses)) if losses else 0.0

    pnl_values = [float(s.get("pnl_pct", 0) or 0) for s in closed_trades]
    best_trade = max(pnl_values) if pnl_values else 0.0
    worst_trade = min(pnl_values) if pnl_values else 0.0

    # Intraday cumulative equity curve and max drawdown calculation
    cum_equity = 0.0
    peak_equity = 0.0
    max_intraday_dd = 0.0
    for s in sorted(closed_trades, key=lambda x: x.get("time", 0)):
        cum_equity += float(s.get("pnl_pct", 0) or 0)
        if cum_equity > peak_equity:
            peak_equity = cum_equity
        dd = peak_equity - cum_equity
        if dd > max_intraday_dd:
            max_intraday_dd = dd

    # Traded symbols
    symbols = sorted(list({s.get("pair", "ASSET") for s in session_signals}))
    symbols_str = ", ".join(symbols) if symbols else "N/A"

    exposure_status = "FLAT (0 Open Risk)" if not open_trades else f"⚠️ {len(open_trades)} Open Trade(s)"

    # Group trades by strategy
    strat_groups = {}
    for s in session_signals:
        strat_groups.setdefault(s.get("strategy", "Autonomous Engine"), []).append(s)

    lines = [
        "📊 <b>Zillions QUANT & STRATEGY REPORT</b>",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"📅 <b>Date:</b> <code>{session_date_str}</code> | ⏰ <code>{time_now_str}</code>",
        f"🌐 <b>Market:</b> <code>{symbols_str}</code>",
        f"💼 <b>Portfolio Status:</b> <b>{exposure_status}</b>\n",
        "📈 <b>EXECUTIVE DAILY SUMMARY</b>",
        f"• <b>Net Session PnL:</b> <code>{net_pnl:+.2f}%</code>",
        f"• <b>Total Trades:</b> <code>{total_trades}</code> ({len(wins)}W / {len(losses)}L" + (f" / {len(breakeven)}BE" if breakeven else "") + f" — {win_rate:.1f}% WR)",
        f"• <b>Gross Profit / Loss:</b> <code>+{gross_profit:.2f}%</code> / <code>-{gross_loss:.2f}%</code>",
        f"• <b>Profit Factor:</b> <code>{profit_factor:.2f}</code>",
        f"• <b>Win / Loss Expectancy:</b> Avg Win <code>+{avg_win:.2f}%</code> vs Avg Loss <code>{avg_loss:.2f}%</code>",
        f"• <b>Best / Worst Trade:</b> <code>{best_trade:+.2f}%</code> / <code>{worst_trade:+.2f}%</code>",
        f"• <b>Max Intraday Drawdown:</b> <code>{max_intraday_dd:.2f}%</code>\n",
        "🤖 <b>STRATEGY MONITORING BREAKDOWN</b>",
    ]

    for idx, (s_name, s_trades) in enumerate(strat_groups.items(), 1):
        meta = strat_lookup.get(s_name, {})
        status = meta.get("status", "ACTIVE")
        audit = meta.get("audit_summary", {}) or {}
        live_meta = meta.get("live_stats", {}) or {}

        s_wins = [t for t in s_trades if float(t.get("pnl_pct", 0) or 0) > 0]
        s_losses = [t for t in s_trades if float(t.get("pnl_pct", 0) or 0) < 0]
        s_net = sum(float(t.get("pnl_pct", 0) or 0) for t in s_trades)
        s_gp = sum(float(t.get("pnl_pct", 0) or 0) for t in s_wins)
        s_gl = abs(sum(float(t.get("pnl_pct", 0) or 0) for t in s_losses))
        s_wr = (len(s_wins) / len(s_trades) * 100) if s_trades else 0.0
        s_pf = (s_gp / s_gl) if s_gl > 0 else (s_gp if s_gp > 0 else 1.0)

        sharpe_val = live_meta.get("sharpe_live")
        if sharpe_val is None:
            sharpe_val = audit.get("sharpe")

        dsr_val = audit.get("dsr") or meta.get("falsification_gates", {}).get("gate_1_dsr", {}).get("dsr")

        lines.append(f"\n{idx}️⃣ <b>{s_name}</b>")
        lines.append(f"  • <b>Status:</b> <code>{status}</code>")
        lines.append(f"  • <b>Trades Today:</b> <code>{len(s_trades)}</code> ({len(s_wins)}W / {len(s_losses)}L — {s_wr:.1f}% WR)")
        lines.append(f"  • <b>Net PnL:</b> <b><code>{s_net:+.2f}%</code></b> (Gross: +{s_gp:.2f}% / -{s_gl:.2f}%)")
        lines.append(f"  • <b>Session Profit Factor:</b> <code>{s_pf:.2f}</code>")
        if sharpe_val is not None:
            try:
                lines.append(f"  • <b>Live Sharpe:</b> <code>{float(sharpe_val):.2f}</code>")
            except (ValueError, TypeError):
                lines.append(f"  • <b>Live Sharpe:</b> <code>{sharpe_val}</code>")
        if dsr_val is not None:
            try:
                lines.append(f"  • <b>DSR Score:</b> <code>{float(dsr_val):.2f}</code>")
            except (ValueError, TypeError):
                lines.append(f"  • <b>DSR Score:</b> <code>{dsr_val}</code>")

    # Quant risk gates
    dd_pass = "PASS ✅" if max_intraday_dd <= 4.5 else "FAIL ❌"
    lines.append("\n🛡️ <b>QUANT RISK & GATE VERIFICATION</b>")
    lines.append(f"• <b>Drawdown Ceiling:</b> {dd_pass} (Max intraday: {max_intraday_dd:.2f}% vs 4.5% limit)")
    lines.append("• <b>Overnight Exposure:</b> " + ("CLEARED ✅ (100% Cash)" if not open_trades else "ACTIVE EXPOSURE ⚠️"))

    return "\n".join(lines)


def broadcast_report(target_date: str = None, dry_run: bool = False, specific_chat_id: str = None):
    report_text = generate_report_text(target_date)

    if dry_run:
        print("\n--- [DRY RUN PREVIEW] ---")
        print(report_text)
        print("-------------------------\n")
        return True

    users = [specific_chat_id] if specific_chat_id else telegram_gateway.discover_all_users()
    if not users:
        print("[Error] No Telegram chat IDs found to broadcast to.")
        return False

    token = telegram_gateway.bot_token
    if not token:
        print("[Error] TELEGRAM_BOT_TOKEN is not configured.")
        return False

    print(f"Broadcasting dynamic daily report to {len(users)} user(s): {users}")
    success = True
    for cid in users:
        ok = telegram_gateway.send_message(report_text, parse_mode="HTML", target_chat_id=cid)
        if ok:
            print(f"✅ Delivered successfully to chat {cid}")
        else:
            print(f"❌ Failed to deliver to chat {cid}")
            success = False

    return success


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send dynamic daily quant & strategy report to Telegram users.")
    parser.add_argument("--date", type=str, default=None, help="Target date YYYY-MM-DD (defaults to today / latest)")
    parser.add_argument("--dry-run", action="store_true", help="Print report to console without sending via Telegram")
    parser.add_argument("--chat-id", type=str, default=None, help="Send to a specific chat ID instead of all discovered users")
    args = parser.parse_args()

    broadcast_report(target_date=args.date, dry_run=args.dry_run, specific_chat_id=args.chat_id)

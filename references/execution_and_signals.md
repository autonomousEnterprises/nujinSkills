# Reference: Execution Bots, Code Emission & Telegram Signal Gateway

## 1. Overview: From Alpha Rules to Live Execution

Once a strategy passes all statistical validation hurdles and DSR audits, **NujinAI** transitions the strategy into production execution through three modular pathways:
1. **Production Code Emission:** Generates clean, standalone Python strategy files for standardized bot engines (Freqtrade `IStrategy` or Jesse `Strategy`) via `tools/strategy_emitter.py`.
2. **24/7 Telegram Signal Gateway:** Broadcasts real-time entry/exit alerts, stop-loss and take-profit targets, and PnL updates to user messaging channels.
3. **Bot Supervisor:** Launches and supervises paper trading (dry-run) or live execution bots via `tools/bot_control.py`.

---

## 2. Production Code Emission (`tools/strategy_emitter.py`)

Nujin compiles the mathematical rules in `.nujin/best_rules.json` into production-ready execution files:

```bash
python tools/strategy_emitter.py \
  --thesis "Prop Firm Dual VSA Wick Rejection" \
  --rules .nujin/best_rules.json \
  --framework freqtrade \
  --out strategies/PropFirmWickStrategy.py
```

### Freqtrade `IStrategy` Contract
The emitted Freqtrade strategy implements:
- `populate_indicators(dataframe, metadata)`: Calculates bar geometry (`lower_wick`, `upper_wick`), Volume Z-score, Parkinson Volatility, and Hurst proxy.
- `populate_entry_trend(dataframe, metadata)`: Evaluates boolean entry conditions for LONG and SHORT directions.
- `populate_exit_trend(dataframe, metadata)`: Enforces dynamic holding bar cutoffs and trend invalidations.
- `custom_stoploss(pair, trade, current_time, current_rate, current_profit)`: Manages ATR trailing stops and breakeven locks.

---

## 3. 24/7 Telegram Signal Gateway

Nujin connects to Telegram via the integrated Telegram Gateway in `server/telegram_bot.py`.

### A. Environment Configuration (`.env`)
```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ
TELEGRAM_CHAT_ID=-100123456789
EXCHANGE_NAME=binance
```

### B. Signal Payload Format (`SIGNAL_TRIGGERED`)
When an entry or exit signal is generated, Nujin dispatches the alert via `tools/ui_dispatcher.py`:

```bash
python tools/ui_dispatcher.py --event SIGNAL_TRIGGERED --payload '{
  "time": 1788163980,
  "action": "BUY",
  "pair": "BTC/USDT",
  "price": 64250.0,
  "stop_loss": 63400.0,
  "take_profit": 65950.0,
  "annotation": "Absorption Sweep (Hurst < 0.42, Lower Wick > 45%)",
  "reasoning_md": "**Counterparty Trap**: Aggressive market sellers absorbed at support."
}'
```

### C. Telegram Message Format
The gateway automatically formats the signal into an alert:
```
⚡ NUJIN QUANT SIGNAL: BUY BTC/USDT
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Entry Price: $64,250.00
Stop-Loss:   $63,400.00 (-1.32%)
Take-Profit: $65,950.00 (+2.65%)
Risk/Reward: 1 : 2.01

Rationale: Absorption Sweep (Hurst < 0.42, Lower Wick > 45%)
Trap: Aggressive market sellers absorbed at support.
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Time: 2026-09-11 14:15:00 UTC
```

### D. Autonomous Broadcast Tool (`tools/telegram_broadcast.py`)
Used by the AI agent whenever requested to communicate, publish reports, share market intelligence, or update subscribers:

```bash
# 1. Check Gateway & Subscriber Connectivity
python tools/telegram_broadcast.py status

# 2. Broadcast Quantitative Performance Report
python tools/telegram_broadcast.py broadcast \
  --type report \
  --title "Daily Quant Performance" \
  --message "Net PnL: +4.12% | Win Rate: 75.0% | Profit Factor: 2.84 | Max DD: 0.85%"

# 3. Broadcast Market / Macro News
python tools/telegram_broadcast.py broadcast \
  --type news \
  --title "US CPI Release Volatility" \
  --message "CPI prints higher than expected. Liquidity sweeps observed across BTC perpetuals."

# 4. Broadcast System & Strategy Lifecycle Updates
python tools/telegram_broadcast.py broadcast \
  --type update \
  --title "Strategy Deployed: BTC Volatility Fade" \
  --message "PropFirm Wick Strategy activated in live paper mode."

# 5. Broadcast Urgent Risk Alerts
python tools/telegram_broadcast.py broadcast \
  --type alert \
  --title "Volatility Spike Warning" \
  --message "Realized volatility breached 3.5 sigma. Dynamic stop-loss distances widened."

# 6. Ingest Reports from File or Piped Input
python tools/telegram_broadcast.py broadcast --type report --file reports/session_summary.md
cat reports/session_summary.md | python tools/telegram_broadcast.py broadcast --type report

# 7. Safe Dry-Run Simulation
python tools/telegram_broadcast.py broadcast --type news --title "Preview" --message "Dry-run test" --dry-run
```

---

## 4. Bot Supervisor CLI (`tools/bot_control.py`)

Controls the background execution of trading bots:

```bash
# Deploy strategy to paper trading (dry-run)
python tools/bot_control.py deploy --strategy PropFirmWickStrategy --mode dry-run

# Inspect running bot supervisor status
python tools/bot_control.py status

# Stop active bot supervisor
python tools/bot_control.py stop
```

---

## 5. Live Performance Telemetry REST API

| Endpoint | Method | Response & Description |
| --- | --- | --- |
| `/api/signals` | GET | List of all persisted signals + current open trade position. |
| `/api/signals/stats` | GET | Live performance stats since activation: win rate, profit factor, annualized Sharpe, net PnL %, max consecutive losses. |
| `/api/bot/deploy` | POST | Deploy and activate a strategy in paper trading mode. |
| `/api/bot/stop` | POST | Stop active bot execution cleanly. |

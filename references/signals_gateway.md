# Reference: 24/7 Multi-Strategy Signal Gateway & Position Telemetry

## Overview
The Signal Gateway provides real-time trade signal routing, position lifecycle management (`ACTIVE_IN_POSITION` -> `CLOSED`), multi-strategy telemetry auditing, and automated Telegram mobile alert dispatching across parallel trading bots.

---

## Multi-Strategy Signal Architecture

1. **Storage & State (`data/signals.json`):**
   Managed by thread-safe `SignalStore` in `server/state_manager.py`. All writes are file-locked.

2. **Signal Payload Schema:**
   ```json
   {
     "action": "BUY",
     "strategy": "GoatFundedTraderXauusdScalper",
     "pair": "XAU/USD",
     "price": 3584.50,
     "stop_loss": 3572.00,
     "take_profit": 3610.00,
     "status": "ACTIVE_IN_POSITION",
     "annotation": "Asian Session Liquidity Sweep",
     "reasoning_md": "Swept liquidity under Asian session low with volume absorption wick."
   }
   ```

3. **Telegram Notification Template:**
   ```
   🟢 *BUY XAU/USD* • *GoatFundedTraderXauusdScalper* — EdgeMiner Signal
   ━━━━━━━━━━━━━━━━━━━
   📈 *Entry*
   `3584.50`

   🛡️ *Stop Loss*
   `3572.00`

   🎯 *Take Profit*
   `3610.00`

   💡 _Asian Session Liquidity Sweep_
   🧠 Swept liquidity under Asian session low with volume absorption wick.
   ```

---

## Backend API Endpoints

- `GET /api/signals[?strategy=STRATEGY]`:
  Returns `signals` (filtered or all), `active_signal` (for strategy or primary), and `active_signals` (all concurrent open positions).
- `GET /api/signals/stats[?strategy=STRATEGY]`:
  Returns live Win Rate, Profit Factor, Sharpe Live, Realized PnL, plus per-strategy breakdown (`by_strategy`).
- `POST /api/signals/close`:
  Closes an active position with `{"id": 1, "exit_price": 3608.20, "exit_reason": "TAKE_PROFIT"}`.
- `POST /api/signals/clear`:
  Clears signals for a specific strategy or all with `{"strategy": "..."}`.
- `POST /api/broadcast`:
  Dispatches `SIGNAL_TRIGGERED` envelope to WebSockets and Telegram.

---

## CLI Tools

```bash
# View active positions and signal history (all or specific strategy)
python3 tools/strategy_manager.py signals
python3 tools/strategy_manager.py signals --strategy GoatFundedTraderXauusdScalper

# Inspect live performance statistics
python3 tools/state_control.py signal-stats
python3 tools/state_control.py signal-stats --strategy PropFirmVsaWickRejection

# Broadcast a new live trade signal
python3 tools/state_control.py signal-add \
  --strategy GoatFundedTraderXauusdScalper \
  --pair XAU/USD \
  --signal '{"action":"BUY","price":3584.50,"stop_loss":3572.00,"take_profit":3610.00,"annotation":"Liquidity Sweep"}'

# Close an open trade position
python3 tools/state_control.py signal-close --id 1 --exit-price 3608.20 --reason TAKE_PROFIT
```

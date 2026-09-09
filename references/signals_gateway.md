# Reference: 24/7 Telegram Signal Gateway Integration

## Overview
The Telegram Signal Gateway acts as a 24/7 mobile alert mechanism, forwarding trade signals (`SIGNAL_TRIGGERED`) and DSR audit updates emitted by the AI agent directly to Telegram chats.

---

## Gateway Architecture & Setup

1. **Environment Variables:**
   - `TELEGRAM_BOT_TOKEN`: Bot token from `@BotFather`.
   - `TELEGRAM_CHAT_ID`: Destination chat or channel ID.

2. **Event Processing:**
   When `tools/ui_dispatcher.py` sends an event to `http://localhost:8000/api/broadcast`, the server `TelegramGateway` formats the payload into rich Markdown push messages.

3. **Message Template Examples:**

   **Signal Push Alert:**
   ```
   🟢 SIGNAL TRIGGERED: BUY BTC/USDT
   ━━━━━━━━━━━━━━━━━━━
   📈 Entry Price: $64,250.00
   🛡️ Stop Loss: $63,400.00
   🎯 Take Profit: $65,950.00
   💡 Annotation: Absorption Sweep (Hurst < 0.42, Wick > 60%)
   
   🧠 Agent Rationale:
   Breakout buyers trapped by passive liquidity resistance.
   ```

   **DSR Audit Alert:**
   ```
   ✅ AGENT AUDIT UPDATE: Deflated Sharpe Ratio (DSR)
   ━━━━━━━━━━━━━━━━━━━
   📊 DSR Value: 0.964 (Status: PASS)
   ℹ️ Details: Audited across 140 trial variations
   ```

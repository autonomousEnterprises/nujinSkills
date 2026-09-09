import os
import logging
import requests
from typing import Dict, Any

logger = logging.getLogger("TelegramGateway")

class TelegramGateway:
    def __init__(self):
        self.bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
        
    @property
    def is_configured(self) -> bool:
        return bool(self.bot_token and self.chat_id)

    def send_message(self, text: str) -> bool:
        if not self.is_configured:
            logger.info(f"[Telegram Off-line / Log Only]\n{text}")
            return False
            
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        try:
            resp = requests.post(url, json=payload, timeout=5)
            return resp.status_code == 200
        except Exception as e:
            logger.error(f"Failed to dispatch Telegram message: {e}")
            return False

    def format_and_send_signal(self, payload: Dict[str, Any]):
        action = payload.get("action", "BUY")
        pair = payload.get("pair", "BTC/USDT")
        price = payload.get("price", 0.0)
        stop_loss = payload.get("stop_loss", 0.0)
        take_profit = payload.get("take_profit", 0.0)
        annotation = payload.get("annotation", "Edge Triggered")
        reasoning = payload.get("reasoning_md", "")

        icon = "🟢" if action.upper() == "BUY" else "🔴"
        text = (
            f"{icon} *SIGNAL TRIGGERED: {action} {pair}*\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"📈 *Entry Price:* ${price:,.2f}\n"
            f"🛡️ *Stop Loss:* ${stop_loss:,.2f}\n"
            f"🎯 *Take Profit:* ${take_profit:,.2f}\n"
            f"💡 *Annotation:* {annotation}\n\n"
            f"🧠 *Agent Rationale:*\n{reasoning}"
        )
        return self.send_message(text)

    def format_and_send_dsr_alert(self, payload: Dict[str, Any]):
        title = payload.get("title", "DSR Audit")
        props = payload.get("props", {})
        val = props.get("value", "N/A")
        status = props.get("status", "PASS")
        subtitle = props.get("subtitle", "")

        icon = "✅" if status == "PASS" else "❌"
        text = (
            f"{icon} *AGENT AUDIT UPDATE: {title}*\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"📊 *DSR Value:* `{val}` (Status: *{status}*)\n"
            f"ℹ️ *Details:* {subtitle}"
        )
        return self.send_message(text)

telegram_gateway = TelegramGateway()

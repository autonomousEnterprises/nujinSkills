import os
import html
import logging
import requests
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

# Load .env from project root so credentials are always available
_env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists():
    for _line in _env_path.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

logger = logging.getLogger("TelegramGateway")

class TelegramGateway:
    def __init__(self):
        self.bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
        
    @property
    def is_configured(self) -> bool:
        return bool(self.bot_token and self.chat_id)

    def send_message(self, text: str, parse_mode: Optional[str] = "HTML") -> bool:
        if not self.is_configured:
            logger.info(f"[Telegram Off-line / Log Only]\n{text}")
            return False
            
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
        }
        if parse_mode:
            payload["parse_mode"] = parse_mode

        try:
            resp = requests.post(url, json=payload, timeout=8)
            if resp.status_code == 200:
                return True
            
            logger.warning(f"[TelegramGateway] Dispatch returned {resp.status_code}: {resp.text}")
            # Resilient fallback: If entity parsing fails (e.g. 400 Bad Request), retry as unformatted plain text
            if parse_mode is not None and resp.status_code == 400:
                logger.info("[TelegramGateway] Retrying message delivery in unformatted plaintext fallback mode...")
                # Strip basic html tags for raw text fallback
                clean_text = text.replace("<b>", "").replace("</b>", "").replace("<code>", "").replace("</code>", "").replace("<i>", "").replace("</i>", "")
                fallback_payload = {"chat_id": self.chat_id, "text": clean_text}
                retry_resp = requests.post(url, json=fallback_payload, timeout=8)
                if retry_resp.status_code == 200:
                    logger.info("[TelegramGateway] Plaintext fallback delivered successfully.")
                    return True
                logger.error(f"[TelegramGateway] Plaintext retry also failed: {retry_resp.status_code} - {retry_resp.text}")
            return False
        except Exception as e:
            logger.error(f"Failed to dispatch Telegram message: {e}")
            return False

    def format_and_send_signal(self, payload: Dict[str, Any]) -> bool:
        action = payload.get("action", "BUY").upper()
        pair = html.escape(str(payload.get("pair", "BTC/USDT")))
        price = float(payload.get("price") or payload.get("entry_price") or 0.0)
        stop_loss = float(payload.get("stop_loss") or 0.0)
        take_profit = float(payload.get("take_profit") or 0.0)
        annotation = html.escape(str(payload.get("annotation", "Edge Triggered")))
        reasoning = html.escape(str(payload.get("reasoning_md", "")))
        strategy = html.escape(str(payload.get("strategy", "").replace(".py", "")))
        strat_tag = f" • <b>{strategy}</b>" if strategy else ""

        icon = "🟢" if action in ("BUY", "LONG") else "🔴"
        local_time_str = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
        # Numbers formatted on dedicated lines for 1-tap select & copy into MT4/MT5/cTrader
        text = (
            f"{icon} <b>{action} {pair}</b>{strat_tag} — EdgeMiner Signal\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"⏰ <b>Time:</b> <code>{local_time_str}</code>\n\n"
            f"📈 <b>Entry:</b>\n"
            f"<code>{price:.2f}</code>\n\n"
            f"🛡️ <b>Stop Loss:</b>\n"
            f"<code>{stop_loss:.2f}</code>\n\n"
            f"🎯 <b>Take Profit:</b>\n"
            f"<code>{take_profit:.2f}</code>\n\n"
            f"💡 <i>{annotation}</i>\n"
            f"🧠 {reasoning}"
        )
        return self.send_message(text, parse_mode="HTML")

    def format_and_send_trade_close(self, payload: Dict[str, Any]) -> bool:
        strategy = html.escape(str(payload.get("strategy", "Autonomous Bot")).replace(".py", ""))
        pair = html.escape(str(payload.get("pair", "Asset")))
        entry_p = float(payload.get("price") or payload.get("entry_price") or 0.0)
        exit_p = float(payload.get("exit_price") or 0.0)
        pnl = float(payload.get("pnl_pct") or 0.0)
        exit_reason = html.escape(str(payload.get("exit_reason", "EXIT")))
        
        icon = "🎯" if pnl >= 0 else "🛑"
        local_time_str = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
        pnl_str = f"{pnl:+.2f}%"

        text = (
            f"{icon} <b>TRADE CLOSED: {strategy}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"⏰ <b>Time:</b> <code>{local_time_str}</code>\n"
            f"📊 <b>Pair:</b> <code>{pair}</code>\n"
            f"📈 <b>Entry:</b> <code>{entry_p:.2f}</code> → <b>Exit:</b> <code>{exit_p:.2f}</code>\n"
            f"💡 <b>Exit Reason:</b> <code>{exit_reason}</code>\n"
            f"💰 <b>Realized PnL:</b> <b>{pnl_str}</b>"
        )
        return self.send_message(text, parse_mode="HTML")

    def format_and_send_dsr_alert(self, payload: Dict[str, Any]) -> bool:
        title = html.escape(str(payload.get("title", "DSR Audit")))
        props = payload.get("props", {})
        val = html.escape(str(props.get("value", "N/A")))
        status = html.escape(str(props.get("status", "PASS")))
        subtitle = html.escape(str(props.get("subtitle", "")))

        icon = "✅" if status == "PASS" else "❌"
        local_time_str = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
        text = (
            f"{icon} <b>AGENT AUDIT UPDATE: {title}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"⏰ <b>Time:</b> <code>{local_time_str}</code>\n"
            f"📊 <b>DSR Value:</b> <code>{val}</code> (Status: <b>{status}</b>)\n"
            f"ℹ️ <b>Details:</b> {subtitle}"
        )
        return self.send_message(text, parse_mode="HTML")

telegram_gateway = TelegramGateway()

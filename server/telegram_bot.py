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
        return bool(self.bot_token and (self.chat_id or os.environ.get("TELEGRAM_CHAT_ID")))

    def get_chat_ids(self) -> list[str]:
        raw = self.chat_id or os.environ.get("TELEGRAM_CHAT_ID", "")
        ids = []
        for part in raw.split(","):
            part = part.strip()
            if part and part not in ids:
                ids.append(part)
        return ids

    def discover_all_users(self) -> list[str]:
        """Discovers any active Telegram chat IDs via getUpdates and merges with configured IDs."""
        users = list(self.get_chat_ids())
        if not self.bot_token:
            return users
        try:
            resp = requests.get(f"https://api.telegram.org/bot{self.bot_token}/getUpdates", timeout=6)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("ok"):
                    for item in data.get("result", []):
                        msg = item.get("message") or item.get("channel_post") or item.get("my_chat_member", {}).get("chat")
                        cid = None
                        if msg and "chat" in msg and "id" in msg["chat"]:
                            cid = str(msg["chat"]["id"])
                        elif "chat" in item and "id" in item["chat"]:
                            cid = str(item["chat"]["id"])
                        if cid and cid not in users:
                            users.append(cid)
        except Exception as e:
            logger.warning(f"[TelegramGateway] User discovery encountered error: {e}")
        return users

    def send_message(self, text: str, parse_mode: Optional[str] = "HTML", target_chat_id: Optional[str] = None, disable_notification: bool = False) -> bool:
        if not self.bot_token:
            logger.info(f"[Telegram Off-line / Log Only]\n{text}")
            return False

        targets = [target_chat_id] if target_chat_id else self.get_chat_ids()
        if not targets:
            targets = self.discover_all_users()

        if not targets:
            logger.info(f"[Telegram Off-line / Log Only]\n{text}")
            return False

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        any_success = False

        for cid in targets:
            payload = {
                "chat_id": cid,
                "text": text,
            }
            if parse_mode:
                payload["parse_mode"] = parse_mode
            if disable_notification:
                payload["disable_notification"] = True

            try:
                resp = requests.post(url, json=payload, timeout=8)
                if resp.status_code == 200:
                    any_success = True
                    continue

                logger.warning(f"[TelegramGateway] Dispatch to {cid} returned {resp.status_code}: {resp.text}")
                # Resilient fallback: If entity parsing fails (e.g. 400 Bad Request), retry as unformatted plain text
                if parse_mode is not None and resp.status_code == 400:
                    logger.info(f"[TelegramGateway] Retrying message delivery to {cid} in unformatted plaintext fallback mode...")
                    clean_text = text.replace("<b>", "").replace("</b>", "").replace("<code>", "").replace("</code>", "").replace("<i>", "").replace("</i>", "")
                    fallback_payload = {"chat_id": cid, "text": clean_text}
                    if disable_notification:
                        fallback_payload["disable_notification"] = True
                    retry_resp = requests.post(url, json=fallback_payload, timeout=8)
                    if retry_resp.status_code == 200:
                        logger.info(f"[TelegramGateway] Plaintext fallback delivered successfully to {cid}.")
                        any_success = True
                        continue
                    logger.error(f"[TelegramGateway] Plaintext retry failed for {cid}: {retry_resp.status_code} - {retry_resp.text}")
            except Exception as e:
                logger.error(f"Failed to dispatch Telegram message to {cid}: {e}")

        return any_success

    def delete_message(self, chat_id: str | int, message_id: int) -> bool:
        """Deletes a message from Telegram (e.g. to purge sensitive credentials)."""
        if not self.bot_token or not chat_id or not message_id:
            return False
        url = f"https://api.telegram.org/bot{self.bot_token}/deleteMessage"
        try:
            resp = requests.post(url, json={"chat_id": chat_id, "message_id": message_id}, timeout=5)
            return resp.status_code == 200
        except Exception as e:
            logger.debug(f"[TelegramGateway] Failed to delete message {message_id}: {e}")
            return False

    def send_user_receipt(self, chat_id: str | int, title: str, details: Dict[str, Any], is_success: bool = True) -> bool:
        """Sends a structured execution receipt or alert directly to an individual user's chat."""
        icon = "✅" if is_success else "❌"
        time_str = datetime.now().astimezone().strftime("%H:%M:%S %Z")
        lines = [
            f"{icon} <b>{html.escape(title.upper())}</b>",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"⏰ <b>Time:</b> <code>{time_str}</code>"
        ]
        for k, v in details.items():
            lines.append(f"• <b>{html.escape(str(k))}:</b> <code>{html.escape(str(v))}</code>")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("⚡ <i>Nujin Multi-Account Execution</i>")
        return self.send_message("\n".join(lines), parse_mode="HTML", target_chat_id=str(chat_id))

    @staticmethod
    def format_broadcast_text(body: str, category: str = "general", title: str = "") -> str:
        cat = (category or "general").lower().strip()
        time_str = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
        
        if cat == "raw":
            return body

        headers = {
            "report": ("📊", "QUANTITATIVE REPORT", "Quantitative Systems"),
            "news": ("📰", "MARKET INTEL & NEWS", "FastFeed Intelligence"),
            "update": ("🚀", "SYSTEM & STRATEGY UPDATE", "Operations Core"),
            "alert": ("🚨", "RISK & VOLATILITY ALERT", "Risk Guardian"),
            "general": ("💬", "NUJIN AI BROADCAST", "EdgeMiner Engine"),
        }
        icon, default_title, tag = headers.get(cat, ("💬", "BROADCAST MESSAGE", "EdgeMiner Engine"))
        display_title = title.strip() if title else default_title

        return (
            f"{icon} <b>{display_title.upper()}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⏰ <b>Time:</b> <code>{time_str}</code>\n\n"
            f"{body.strip()}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚡ <i>NujinAI {tag}</i>"
        )

    def broadcast_custom(
        self,
        body: str,
        category: str = "general",
        title: str = "",
        parse_mode: Optional[str] = "HTML",
        target_chat_ids: Optional[list[str]] = None,
        disable_notification: bool = False
    ) -> Dict[str, Any]:
        formatted_text = self.format_broadcast_text(body, category=category, title=title)
        targets = target_chat_ids if target_chat_ids else self.get_chat_ids()
        if not targets:
            targets = self.discover_all_users()

        results = {}
        for cid in targets:
            ok = self.send_message(
                formatted_text,
                parse_mode=parse_mode,
                target_chat_id=cid,
                disable_notification=disable_notification
            )
            results[cid] = ok

        return {
            "delivered": any(results.values()) if results else False,
            "recipients": results,
            "formatted_text": formatted_text,
            "category": category,
            "title": title
        }


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
        lines = [
            f"{icon} <b>{action} {pair}</b>{strat_tag} — EdgeMiner Signal",
            "━━━━━━━━━━━━━━━━━━━",
            f"⏰ <b>Time:</b> <code>{local_time_str}</code>\n",
            "📈 <b>Entry:</b>",
            f"<code>{price:.2f}</code>\n"
        ]

        lots = float(payload.get("lots") or payload.get("lot_size") or 0.0)
        if lots > 0:
            lines.extend([
                "📦 <b>Lot Size:</b>",
                f"<code>{lots:.2f} lots</code>\n"
            ])

        if stop_loss > 0:
            lines.extend([
                "🛡️ <b>Stop Loss:</b>",
                f"<code>{stop_loss:.2f}</code>\n"
            ])

        if take_profit > 0:
            lines.extend([
                "🎯 <b>Take Profit:</b>",
                f"<code>{take_profit:.2f}</code>\n"
            ])

        # If both SL and TP are specified by the strategy, display exact Risk/Reward
        if price > 0 and stop_loss > 0 and take_profit > 0:
            risk = abs(price - stop_loss)
            reward = abs(take_profit - price)
            if risk > 0:
                rr = reward / risk
                lines.append(f"⚖️ <b>Risk/Reward:</b> <code>1 : {rr:.2f}</code>\n")

        if annotation and annotation != "Edge Triggered":
            lines.append(f"💡 <i>{annotation}</i>")
        if reasoning:
            lines.append(f"🧠 {reasoning}")

        text = "\n".join(lines)
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

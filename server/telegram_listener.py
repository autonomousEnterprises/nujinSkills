"""
server/telegram_listener.py
─────────────────────────────────────────────────────────────
Asynchronous Telegram Listener & Interactive Command Bot.

Enables multi-user, multi-broker account onboarding directly via Telegram.
Allows users to link their trading accounts (e.g. TradeLocker Pro),
adjust position sizing / risk, and pause or resume automated execution.

Maintains strict separation:
- Generic broker command interface lives here in open-source nujinSkills.
- TradeLocker credentials validation and execution live in proprietary nujinPro.
"""

from __future__ import annotations

import asyncio
import html
import logging
import os
import re
import shlex
from datetime import datetime
from typing import Dict, Any, Optional

import requests

from server.accounts_store import accounts_store
from server.brokers.registry import broker_registry
from server.telegram_bot import telegram_gateway

logger = logging.getLogger("TelegramListener")

# Conversational state machine for step-by-step onboarding
# Format: user_id -> {"step": str, "data": dict, "last_active": float}
_USER_SESSIONS: Dict[str, Dict[str, Any]] = {}


class TelegramListener:
    """
    Background worker that polls Telegram getUpdates and dispatches commands.
    """

    def __init__(self):
        self.bot_token = telegram_gateway.bot_token
        self.running = False
        self.offset = 0
        self.last_reported_date = ""

    def is_configured(self) -> bool:
        self.bot_token = telegram_gateway.bot_token or os.environ.get("TELEGRAM_BOT_TOKEN", "")
        return bool(self.bot_token)

    async def run(self) -> None:
        """Main async polling loop."""
        if not self.is_configured():
            logger.info("[TelegramListener] TELEGRAM_BOT_TOKEN not configured. Interactive polling disabled.")
            return

        self.running = True
        logger.info("[TelegramListener] 🚀 Starting Telegram Interactive Command Listener...")

        # Start 9:00 PM local computer time Daily Report Scheduler task
        asyncio.create_task(self._daily_report_scheduler())

        while self.running:
            try:
                # Use asyncio.to_thread to run the blocking getUpdates request
                updates = await asyncio.to_thread(self._fetch_updates, self.offset, 15)
                if updates:
                    for update in updates:
                        up_id = update.get("update_id", 0)
                        if up_id >= self.offset:
                            self.offset = up_id + 1
                        await self._process_update(update)
            except asyncio.CancelledError:
                logger.info("[TelegramListener] Polling task cancelled.")
                self.running = False
                break
            except Exception as e:
                logger.error(f"[TelegramListener] Polling loop error: {e}")
                await asyncio.sleep(4)

    async def _daily_report_scheduler(self) -> None:
        """Schedules automatic broadcast of daily quant report at 9:00 PM (21:00) local computer time."""
        logger.info("[TelegramListener] ⏰ Daily Report Scheduler active (Target: 9:00 PM local computer time).")
        while self.running:
            try:
                now = datetime.now().astimezone()
                today_str = now.strftime("%Y-%m-%d")
                # Trigger if local computer time hour is 21 (9:00 PM) and report hasn't been sent for today
                if now.hour == 21 and self.last_reported_date != today_str:
                    logger.info(f"[TelegramListener] 📢 9:00 PM local time reached ({now.strftime('%H:%M:%S %Z')}). Broadcasting daily report...")
                    self.last_reported_date = today_str
                    try:
                        from tools.send_daily_report import broadcast_report
                        await asyncio.to_thread(broadcast_report)
                    except Exception as e_br:
                        logger.error(f"[TelegramListener] Error in automated daily report broadcast: {e_br}")
                await asyncio.sleep(30)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[TelegramListener] Error in daily report scheduler: {e}")
                await asyncio.sleep(60)

    def _fetch_updates(self, offset: int, timeout: int = 15) -> list[dict]:
        if not self.bot_token:
            return []
        url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates"
        try:
            resp = requests.get(url, params={"offset": offset, "timeout": timeout}, timeout=timeout + 5)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("ok"):
                    return data.get("result", [])
        except Exception as e:
            logger.debug(f"[TelegramListener] getUpdates network error: {e}")
        return []

    async def _process_update(self, update: dict) -> None:
        message = update.get("message")
        if not message:
            return

        chat = message.get("chat", {})
        chat_id = chat.get("id")
        chat_type = chat.get("type", "private")
        user = message.get("from", {})
        user_id = str(user.get("id", chat_id))
        msg_id = message.get("message_id")
        text = (message.get("text") or "").strip()

        if not text or not chat_id:
            return

        # Security check: If someone attempts credentials in a group chat, warn and scrub
        if chat_type in ("group", "supergroup"):
            if text.startswith("/connect") or any(kw in text.lower() for kw in ["password", "email", "secret", "demo"]):
                telegram_gateway.delete_message(chat_id, msg_id)
                telegram_gateway.send_message(
                    "⚠️ <b>Security Alert:</b> Account configuration is strictly restricted to Private Messages.\n"
                    "Please message me privately in a 1-on-1 chat to configure broker accounts.",
                    target_chat_id=str(chat_id)
                )
                return

        # Check for active conversational session
        if user_id in _USER_SESSIONS and not text.startswith("/"):
            await self._handle_session_step(user_id, chat_id, msg_id, text)
            return

        # Handle commands
        cmd_parts = text.split()
        cmd = cmd_parts[0].lower().split("@")[0]  # Strip @botname

        if cmd in ("/start", "/help"):
            await self._cmd_help(chat_id, user_id)
        elif cmd == "/brokers":
            await self._cmd_brokers(chat_id)
        elif cmd == "/accounts":
            await self._cmd_accounts(chat_id, user_id)
        elif cmd in ("/connect", "/connect_tradelocker"):
            await self._cmd_connect(chat_id, user_id, msg_id, cmd_parts[1:])
        elif cmd == "/risk":
            await self._cmd_risk(chat_id, user_id, cmd_parts[1:])
        elif cmd == "/pause":
            await self._cmd_toggle(chat_id, user_id, cmd_parts[1:], is_active=False)
        elif cmd == "/resume":
            await self._cmd_toggle(chat_id, user_id, cmd_parts[1:], is_active=True)
        elif cmd == "/disconnect":
            await self._cmd_disconnect(chat_id, user_id, cmd_parts[1:])
        elif cmd in ("/dailyreport", "/report", "/sendreport"):
            await self._cmd_daily_report(chat_id)
        elif cmd == "/cancel":
            _USER_SESSIONS.pop(user_id, None)
            telegram_gateway.send_message("❌ Setup cancelled.", target_chat_id=str(chat_id))

    async def _cmd_help(self, chat_id: int | str, user_id: str) -> None:
        msg = (
            "🤖 <b>Welcome to NujinAI Autonomous Execution Hub</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>Your Telegram User ID:</b> <code>{user_id}</code>\n\n"
            "<b>Available Commands:</b>\n"
            "• <code>/dailyreport</code> — Generate and send dynamic daily quant & strategy report\n"
            "• <code>/brokers</code> — List installed execution brokers & pro plugins\n"
            "• <code>/connect</code> — Link a broker trading account\n"
            "• <code>/accounts</code> — View your linked trading accounts\n"
            "• <code>/risk</code> — View strategy-designed dynamic risk & lot sizing rules\n"
            "• <code>/pause &lt;acc_id&gt;</code> — Temporarily pause automated trades\n"
            "• <code>/resume &lt;acc_id&gt;</code> — Resume automated trades\n"
            "• <code>/disconnect &lt;acc_id&gt;</code> — Remove a linked account\n"
            "• <code>/cancel</code> — Abort active account setup wizard\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "⚡ <i>Trades from active strategies execute automatically across your connected accounts.</i>"
        )
        telegram_gateway.send_message(msg, target_chat_id=str(chat_id))

    async def _cmd_brokers(self, chat_id: int | str) -> None:
        brokers = broker_registry.list_available_brokers()
        lines = [
            "🔌 <b>Installed Execution Brokers:</b>",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ]
        for b in brokers:
            b_id = b.get("broker_id")
            name = b.get("name")
            is_pro = b.get("is_pro")
            active = " (Active)" if b.get("is_active") else ""
            pro_badge = " [PRO PLUGIN]" if is_pro else " [OPEN SOURCE]"
            lines.append(f"• <b>{b_id}</b>{pro_badge}{active}\n  <i>{name}</i>")

        # Check if tradelocker is registered
        has_tl = any(b.get("broker_id") == "tradelocker" for b in brokers)
        if not has_tl:
            lines.append("\n💡 <i>TradeLocker live execution is part of the <b>Nujin Pro</b> plugin.</i>")

        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━")
        telegram_gateway.send_message("\n".join(lines), target_chat_id=str(chat_id))

    async def _cmd_accounts(self, chat_id: int | str, user_id: str) -> None:
        accs = accounts_store.get_accounts_by_user(user_id, mask=True)
        if not accs:
            msg = (
                "ℹ️ <b>No accounts connected yet.</b>\n\n"
                "Use <code>/connect</code> to link your TradeLocker account."
            )
            telegram_gateway.send_message(msg, target_chat_id=str(chat_id))
            return

        lines = [
            "📋 <b>Your Connected Broker Accounts:</b>",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ]
        for i, a in enumerate(accs, 1):
            acc_id = a.get("id")
            broker_id = a.get("broker_id", "").upper()
            server = a.get("server") or "Default Server"
            login = a.get("login_masked")
            lots = a.get("default_lots", 0.10)
            status = "🟢 ACTIVE" if a.get("is_active", True) else "⏸️ PAUSED"
            lines.append(
                f"{i}. <b>{broker_id}</b> (<code>{acc_id}</code>)\n"
                f"   • Server: <code>{html.escape(server)}</code>\n"
                f"   • Login: <code>{html.escape(login)}</code>\n"
                f"   • Sizing: <code>Strategy Dynamic Smart Lotsizer</code>\n"
                f"   • Status: <b>{status}</b>"
            )
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("💡 <i>Use <code>/pause &lt;id&gt;</code> or <code>/resume &lt;id&gt;</code> to manage execution.</i>")
        telegram_gateway.send_message("\n".join(lines), target_chat_id=str(chat_id))

    async def _cmd_connect(self, chat_id: int | str, user_id: str, msg_id: int, args: list[str]) -> None:
        """Handles /connect wizard or fast one-line input."""
        # Default target broker is tradelocker
        target_broker = "tradelocker"
        if args and args[0].lower() in ("tradelocker", "paper"):
            target_broker = args[0].lower()
            args = args[1:]

        # Check if broker is registered
        available = [b.get("broker_id") for b in broker_registry.list_available_brokers()]
        if target_broker not in available:
            msg = (
                "🔒 <b>Nujin Pro Plugin Required</b>\n\n"
                f"The <b>{target_broker.upper()}</b> broker adapter requires the commercial <b>Nujin Pro</b> plugin.\n\n"
                "To unlock live multi-account execution, place your licensed <code>nujinPro</code> repository "
                "into the <code>plugins/pro/</code> directory."
            )
            telegram_gateway.send_message(msg, target_chat_id=str(chat_id))
            return

        # If full arguments provided in one line: /connect <server> <email> <password> [acc_num]
        if len(args) >= 3:
            telegram_gateway.delete_message(chat_id, msg_id)  # Delete password immediately
            server = args[0]
            email = args[1]
            password = args[2]
            acc_num = args[3] if len(args) >= 4 else ""

            await self._validate_and_save_account(
                chat_id=chat_id,
                user_id=user_id,
                broker_id=target_broker,
                server=server,
                email=email,
                password=password,
                acc_num=acc_num,
                lots=0.10
            )
            return

        # Otherwise, initiate interactive wizard
        _USER_SESSIONS[user_id] = {
            "step": "AWAIT_SERVER",
            "broker_id": target_broker,
            "data": {},
            "chat_id": chat_id
        }
        msg = (
            f"🚀 <b>Connecting {target_broker.upper()} Account</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Step 1/3: What is your <b>Broker Server</b> name?\n"
            "<i>(e.g., <code>TradeLocker Demo</code>, <code>FunderPro</code>, <code>Goat Funded Trader</code>)</i>\n\n"
            "<i>Type <code>/cancel</code> anytime to abort.</i>"
        )
        telegram_gateway.send_message(msg, target_chat_id=str(chat_id))

    async def _handle_session_step(self, user_id: str, chat_id: int | str, msg_id: int, text: str) -> None:
        session = _USER_SESSIONS.get(user_id)
        if not session:
            return

        step = session.get("step")
        data = session.setdefault("data", {})
        broker_id = session.get("broker_id", "tradelocker")

        if step == "AWAIT_SERVER":
            data["server"] = text.strip()
            session["step"] = "AWAIT_EMAIL"
            msg = (
                "Step 2/3: Enter your account <b>Email / Login</b>:\n"
                "<i>(e.g., <code>trader@gmail.com</code>)</i>"
            )
            telegram_gateway.send_message(msg, target_chat_id=str(chat_id))

        elif step == "AWAIT_EMAIL":
            data["email"] = text.strip()
            session["step"] = "AWAIT_PASSWORD"
            msg = (
                "Step 3/3: Enter your account <b>Password</b>:\n"
                "🔒 <i>Your password message will be auto-deleted from chat immediately for your security.</i>"
            )
            telegram_gateway.send_message(msg, target_chat_id=str(chat_id))

        elif step == "AWAIT_PASSWORD":
            data["password"] = text.strip()
            # Delete message containing password
            telegram_gateway.delete_message(chat_id, msg_id)

            _USER_SESSIONS.pop(user_id, None)

            await self._validate_and_save_account(
                chat_id=chat_id,
                user_id=user_id,
                broker_id=broker_id,
                server=data.get("server", ""),
                email=data.get("email", ""),
                password=data.get("password", ""),
                acc_num="",
                lots=0.10
            )

    async def _validate_and_save_account(
        self,
        chat_id: int | str,
        user_id: str,
        broker_id: str,
        server: str,
        email: str,
        password: str,
        acc_num: str,
        lots: float = 0.10
    ) -> None:
        """Validates credentials via broker adapter and writes encrypted account to disk."""
        broker = broker_registry.get_broker(broker_id)
        if not broker:
            telegram_gateway.send_message(f"❌ Broker '{broker_id}' not found.", target_chat_id=str(chat_id))
            return

        telegram_gateway.send_message("⏳ Verifying broker credentials...", target_chat_id=str(chat_id))

        is_valid, message_or_err = broker.validate_credentials({
            "server": server,
            "email": email,
            "password": password,
            "acc_num": acc_num,
            "environment": "demo" if "demo" in server.lower() else "live"
        })

        if not is_valid:
            err_msg = (
                f"❌ <b>Authentication Failed</b>\n\n"
                f"<i>Reason:</i> <code>{html.escape(message_or_err)}</code>\n\n"
                "Please check your server, login, and password, then try <code>/connect</code> again."
            )
            telegram_gateway.send_message(err_msg, target_chat_id=str(chat_id))
            return

        # Save to AccountsStore
        acc = accounts_store.add_account(
            broker_id=broker_id,
            telegram_user_id=user_id,
            telegram_chat_id=str(chat_id),
            login=email,
            password=password,
            server=server,
            acc_num=acc_num,
            default_lots=lots,
            environment="demo" if "demo" in server.lower() else "live"
        )

        success_msg = (
            f"✅ <b>Account Successfully Connected!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• <b>Account ID:</b> <code>{acc['id']}</code>\n"
            f"• <b>Broker:</b> <code>{broker_id.upper()}</code>\n"
            f"• <b>Server:</b> <code>{html.escape(server)}</code>\n"
            f"• <b>Login:</b> <code>{accounts_store.mask_login(email)}</code>\n"
            f"• <b>Sizing Engine:</b> <code>Strategy-Designed Smart Lotsizer</code>\n"
            f"• <b>Gateway Status:</b> 🟢 {html.escape(message_or_err)}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚡ <i>This account will now automatically execute all strategy signals with dynamic smart sizing in real-time.</i>"
        )
        telegram_gateway.send_message(success_msg, target_chat_id=str(chat_id))

    async def _cmd_risk(self, chat_id: int | str, user_id: str, args: list[str]) -> None:
        """Explains dynamic strategy-driven risk sizing without allowing unsafe manual overrides."""
        msg = (
            "🛡️ <b>Strategy-Designed Smart Risk & Lot Sizing</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Position lot sizing is <b>not configured by the user</b>. In accordance with quantitative "
            "risk principles and prop firm consistency rules, position sizes are calculated dynamically "
            "<b>by design from the strategy</b>:\n\n"
            "• <b>Risk Budget:</b> Fixed fractional risk per trade (e.g. 0.50% account equity)\n"
            "• <b>Structural SL Distance:</b> Dynamically scales lots inversely to stop loss width ($/point)\n"
            "• <b>Volatility Modulation:</b> Expands in high-conviction order flow absorption, contracts in extreme ATR expansion\n"
            "• <b>Account Tailoring:</b> Scaled in real-time to each connected account's live balance\n\n"
            "⚡ <i>Manual lot overrides are disabled to enforce strict drawdown preservation.</i>"
        )
        telegram_gateway.send_message(msg, target_chat_id=str(chat_id))

    async def _cmd_toggle(self, chat_id: int | str, user_id: str, args: list[str], is_active: bool) -> None:
        if not args:
            action_name = "resume" if is_active else "pause"
            telegram_gateway.send_message(f"Usage: <code>/{action_name} &lt;account_id&gt;</code>", target_chat_id=str(chat_id))
            return

        acc_id = args[0]
        ok = accounts_store.toggle_account_active(acc_id, user_id, is_active=is_active)
        if ok:
            status = "🟢 ACTIVE (Executing trades)" if is_active else "⏸️ PAUSED (No trades)"
            telegram_gateway.send_message(
                f"✅ Account <code>{acc_id}</code> status set to <b>{status}</b>.",
                target_chat_id=str(chat_id)
            )
        else:
            telegram_gateway.send_message(f"❌ Account <code>{acc_id}</code> not found.", target_chat_id=str(chat_id))

    async def _cmd_disconnect(self, chat_id: int | str, user_id: str, args: list[str]) -> None:
        if not args:
            telegram_gateway.send_message("Usage: <code>/disconnect &lt;account_id&gt;</code>", target_chat_id=str(chat_id))
            return

        acc_id = args[0]
        ok = accounts_store.delete_account(acc_id, user_id)
        if ok:
            telegram_gateway.send_message(
                f"🗑️ Account <code>{acc_id}</code> has been removed from Nujin.",
                target_chat_id=str(chat_id)
            )
        else:
            telegram_gateway.send_message(f"❌ Account <code>{acc_id}</code> not found.", target_chat_id=str(chat_id))

    async def _cmd_daily_report(self, chat_id: int | str) -> None:
        """Generates and sends the daily quant report directly to the requesting Telegram chat."""
        try:
            from tools.send_daily_report import broadcast_report
            await asyncio.to_thread(broadcast_report, specific_chat_id=str(chat_id))
        except Exception as e:
            logger.error(f"[TelegramListener] Error executing /dailyreport command: {e}")
            telegram_gateway.send_message(f"❌ Failed to generate daily report: {html.escape(str(e))}", target_chat_id=str(chat_id))

    @staticmethod
    def _is_float(val: str) -> bool:
        try:
            float(val)
            return True
        except ValueError:
            return False


telegram_listener = TelegramListener()


async def run_telegram_listener() -> None:
    """Entry point helper for server startup."""
    await telegram_listener.run()

#!/usr/bin/env python3
"""
tools/telegram_broadcast.py
Broadcast formatted messages, quantitative reports, news, strategy updates, and alerts to Telegram users.
Conforms to the Nujin Tool Authoring Standard.
"""

import os
import sys
import json
import argparse
import requests
from pathlib import Path
from typing import Optional, List, Dict, Any

# Standard prefix for AI agent log parsing
TOOL_NAME = "[TelegramBroadcast]"

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from server.telegram_bot import telegram_gateway


def check_bot_connectivity(token: str) -> Dict[str, Any]:
    if not token:
        return {"ok": False, "error": "No TELEGRAM_BOT_TOKEN provided"}
    try:
        url = f"https://api.telegram.org/bot{token}/getMe"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("ok"):
                return {"ok": True, "user": data.get("result", {})}
        return {"ok": False, "status_code": resp.status_code, "error": resp.text}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def action_status(as_json: bool = False):
    token = telegram_gateway.bot_token
    configured_ids = telegram_gateway.get_chat_ids()
    discovered_ids = telegram_gateway.discover_all_users() if token else []
    conn = check_bot_connectivity(token) if token else {"ok": False, "error": "Token missing"}

    status_data = {
        "status": "CONFIGURED" if telegram_gateway.is_configured else "UNCONFIGURED",
        "has_token": bool(token),
        "bot_token_masked": f"{token[:8]}...{token[-4:]}" if len(token) > 12 else "NONE",
        "api_connected": conn.get("ok", False),
        "bot_info": conn.get("user") if conn.get("ok") else None,
        "configured_chat_ids": configured_ids,
        "discovered_active_recipients": discovered_ids,
        "total_recipients": len(discovered_ids or configured_ids),
    }

    if as_json:
        print(json.dumps(status_data, indent=2))
        return

    print(f"\n{TOOL_NAME} TELEGRAM GATEWAY STATUS")
    print("━" * 50)
    print(f"  Configuration:    {'✅ READY' if status_data['status'] == 'CONFIGURED' else '⚠️ INCOMPLETE'}")
    print(f"  Bot Token:        {'✅ FOUND (' + status_data['bot_token_masked'] + ')' if status_data['has_token'] else '❌ MISSING'}")
    print(f"  Telegram API:     {'✅ CONNECTED' if status_data['api_connected'] else '❌ DISCONNECTED'}")
    if status_data.get("bot_info"):
        b_name = status_data['bot_info'].get('first_name', '')
        b_user = status_data['bot_info'].get('username', '')
        print(f"  Bot Identity:     {b_name} (@{b_user})")
    print(f"  Configured IDs:   {', '.join(configured_ids) if configured_ids else 'None'}")
    print(f"  Active Recipients:{', '.join(discovered_ids) if discovered_ids else 'None'}")
    print("━" * 50 + "\n")


def action_test(dry_run: bool = False, as_json: bool = False, target_chat_id: Optional[str] = None):
    test_msg = "Ping from NujinAI Agent Telegram Broadcast tool. Gateway channel operational."
    title = "GATEWAY CONNECTIVITY TEST"
    
    if dry_run:
        preview = telegram_gateway.format_broadcast_text(test_msg, category="update", title=title)
        targets = [target_chat_id] if target_chat_id else telegram_gateway.discover_all_users()
        res = {
            "status": "DRY_RUN",
            "targets": targets,
            "preview": preview
        }
        if as_json:
            print(json.dumps(res, indent=2))
        else:
            print(f"{TOOL_NAME} [DRY RUN] Would send test ping to: {targets}")
            print(preview)
        return

    targets = [target_chat_id] if target_chat_id else None
    res = telegram_gateway.broadcast_custom(
        body=test_msg,
        category="update",
        title=title,
        parse_mode="HTML",
        target_chat_ids=targets
    )
    if as_json:
        print(json.dumps(res, indent=2))
    else:
        if res.get("delivered"):
            print(f"{TOOL_NAME} ✅ Test ping delivered successfully to: {list(res.get('recipients', {}).keys())}")
        else:
            print(f"{TOOL_NAME} ❌ Test ping failed. Recipients result: {res.get('recipients')}")


def action_broadcast(
    body: str,
    category: str = "general",
    title: str = "",
    chat_id: Optional[str] = None,
    parse_mode: str = "HTML",
    silent: bool = False,
    dry_run: bool = False,
    as_json: bool = False,
):
    if not body or not body.strip():
        err = {"status": "ERROR", "message": "Message content cannot be empty."}
        if as_json:
            print(json.dumps(err, indent=2))
        else:
            print(f"{TOOL_NAME} ERROR: Message content cannot be empty.")
        sys.exit(1)

    clean_parse_mode = None if parse_mode.lower() in ("plain", "none") else parse_mode

    target_list: Optional[List[str]] = None
    if chat_id:
        target_list = [c.strip() for c in chat_id.split(",") if c.strip()]
    else:
        target_list = telegram_gateway.discover_all_users()

    formatted_text = telegram_gateway.format_broadcast_text(body, category=category, title=title)

    if dry_run:
        preview_data = {
            "status": "DRY_RUN_PREVIEW",
            "category": category,
            "title": title or "(default)",
            "silent": silent,
            "parse_mode": parse_mode,
            "target_recipients": target_list,
            "char_count": len(formatted_text),
            "preview_text": formatted_text,
        }
        if as_json:
            print(json.dumps(preview_data, indent=2))
        else:
            print(f"\n{TOOL_NAME} [DRY RUN PREVIEW]")
            print(f"Category:     {category}")
            print(f"Title:        {title or '(default)'}")
            print(f"Recipients:   {target_list}")
            print(f"Parse Mode:   {parse_mode} | Silent: {silent}")
            print("━" * 50)
            print(formatted_text)
            print("━" * 50 + "\n")
        return

    if not target_list:
        err = {"status": "ERROR", "message": "No Telegram recipients found in .env or via getUpdates."}
        if as_json:
            print(json.dumps(err, indent=2))
        else:
            print(f"{TOOL_NAME} ERROR: No Telegram recipients found.")
        sys.exit(1)

    result = telegram_gateway.broadcast_custom(
        body=body,
        category=category,
        title=title,
        parse_mode=clean_parse_mode,
        target_chat_ids=target_list,
        disable_notification=silent,
    )

    if as_json:
        print(json.dumps(result, indent=2))
    else:
        if result.get("delivered"):
            print(f"{TOOL_NAME} ✅ Successfully broadcasted '{category}' to {len(result.get('recipients', {}))} recipient(s).")
            for cid, ok in result.get("recipients", {}).items():
                status_icon = "✓" if ok else "✗"
                print(f"   [{status_icon}] Chat ID: {cid}")
        else:
            print(f"{TOOL_NAME} ❌ Broadcast delivery failed or bot offline.")
            for cid, ok in result.get("recipients", {}).items():
                print(f"   [✗] Chat ID: {cid} (Failed)")


def read_content_source(message_arg: Optional[str], file_arg: Optional[str]) -> str:
    if message_arg:
        return message_arg
    if file_arg:
        path = Path(file_arg)
        if not path.exists():
            print(f"{TOOL_NAME} ERROR: File not found: {file_arg}")
            sys.exit(1)
        return path.read_text(encoding="utf-8")
    if not sys.stdin.isatty():
        return sys.stdin.read()
    return ""


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="NujinAI Telegram Broadcast Tool — broadcast reports, market news, system updates, and alerts."
    )
    # Flat action argument conforming to Nujin Tool Standard
    parser.add_argument(
        "action",
        choices=["broadcast", "status", "test"],
        help="Action to execute: 'broadcast' message, check gateway 'status', or send 'test' ping.",
    )
    parser.add_argument("--message", "-m", default=None, help="Message text body to broadcast")
    parser.add_argument("--file", "-f", default=None, help="Path to file containing message body")
    parser.add_argument(
        "--type",
        "-t",
        choices=["general", "report", "news", "update", "alert", "raw"],
        default="general",
        help="Message preset/formatting category (default: general)",
    )
    parser.add_argument("--title", default="", help="Custom headline or title for the broadcast")
    parser.add_argument("--chat-id", default=None, help="Specific target Telegram chat ID (or comma-separated IDs)")
    parser.add_argument(
        "--parse-mode",
        choices=["HTML", "Markdown", "MarkdownV2", "plain", "none"],
        default="HTML",
        help="Telegram parse mode (default: HTML)",
    )
    parser.add_argument("--silent", action="store_true", help="Send message silently without notification sound")
    parser.add_argument("--dry-run", action="store_true", help="Preview formatted message and recipients without sending")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    args = parser.parse_args()

    if args.action == "status":
        action_status(as_json=args.json)
    elif args.action == "test":
        action_test(dry_run=args.dry_run, as_json=args.json, target_chat_id=args.chat_id)
    elif args.action == "broadcast":
        body = read_content_source(args.message, args.file)
        if not body:
            print(f"{TOOL_NAME} ERROR: No message provided. Use --message, --file, or pipe input via stdin.")
            sys.exit(1)
        action_broadcast(
            body=body,
            category=args.type,
            title=args.title,
            chat_id=args.chat_id,
            parse_mode=args.parse_mode,
            silent=args.silent,
            dry_run=args.dry_run,
            as_json=args.json,
        )

"""
server/accounts_store.py
─────────────────────────────────────────────────────────────
Secure, multi-broker account storage manager.
Persists registered broker accounts to data/broker_accounts.json
with local encryption, file locking (fcntl.flock), and thread safety.

Broker agnostic: works for TradeLocker, Binance, Bybit, etc.
"""

from __future__ import annotations

import base64
import fcntl
import hashlib
import hmac
import json
import logging
import os
import secrets
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger("AccountsStore")

_ROOT_DIR = Path(__file__).resolve().parent.parent
_DATA_DIR = _ROOT_DIR / "data"
_ACCOUNTS_FILE = _DATA_DIR / "broker_accounts.json"
_KEY_FILE = _ROOT_DIR / ".nujin" / ".secret_key"


class SecretCipher:
    """
    Symmetric encryption engine using Fernet (if cryptography is available)
    or authenticated PBKDF2-HMAC-SHA256 keystream encryption (standard library).
    """

    def __init__(self, key_path: Path = _KEY_FILE):
        self.key_path = key_path
        self._key = self._load_or_create_key()

    def _load_or_create_key(self) -> bytes:
        self.key_path.parent.mkdir(parents=True, exist_ok=True)
        if self.key_path.exists():
            try:
                raw = self.key_path.read_bytes().strip()
                if raw:
                    return raw
            except Exception as e:
                logger.warning(f"[SecretCipher] Error reading key file: {e}")

        # Generate a high-entropy 32-byte secret key
        new_key = secrets.token_bytes(32)
        try:
            self.key_path.write_bytes(new_key)
            os.chmod(self.key_path, 0o600)
        except Exception as e:
            logger.warning(f"[SecretCipher] Error persisting key file: {e}")
        return new_key

    def encrypt(self, plaintext: str) -> str:
        """Encrypts plaintext string and returns base64 encoded ciphertext with integrity tag."""
        if not plaintext:
            return ""

        # Check for cryptography library
        try:
            from cryptography.fernet import Fernet
            fernet_key = base64.urlsafe_b64encode(hashlib.sha256(self._key).digest())
            f = Fernet(fernet_key)
            return "fn:" + f.encrypt(plaintext.encode("utf-8")).decode("utf-8")
        except ImportError:
            pass

        # Standard library authenticated keystream cipher
        salt = secrets.token_bytes(16)
        iv = secrets.token_bytes(16)
        derived = hashlib.pbkdf2_hmac("sha256", self._key, salt, 100_000, dklen=64)
        enc_key = derived[:32]
        mac_key = derived[32:]

        # Keystream generation (counter mode via HMAC)
        p_bytes = plaintext.encode("utf-8")
        keystream = bytearray()
        counter = 0
        while len(keystream) < len(p_bytes):
            block = hmac.new(enc_key, iv + counter.to_bytes(4, "big"), hashlib.sha256).digest()
            keystream.extend(block)
            counter += 1

        ciphertext = bytes(a ^ b for a, b in zip(p_bytes, keystream[:len(p_bytes)]))
        tag = hmac.new(mac_key, salt + iv + ciphertext, hashlib.sha256).digest()

        payload = salt + iv + tag + ciphertext
        return "sl:" + base64.b64encode(payload).decode("utf-8")

    def decrypt(self, encoded: str) -> str:
        """Decrypts base64 encoded ciphertext string."""
        if not encoded:
            return ""

        try:
            if encoded.startswith("fn:"):
                from cryptography.fernet import Fernet
                fernet_key = base64.urlsafe_b64encode(hashlib.sha256(self._key).digest())
                f = Fernet(fernet_key)
                return f.decrypt(encoded[3:].encode("utf-8")).decode("utf-8")

            if encoded.startswith("sl:"):
                raw = base64.b64decode(encoded[3:])
                if len(raw) < 16 + 16 + 32:
                    return ""
                salt = raw[:16]
                iv = raw[16:32]
                tag = raw[32:64]
                ciphertext = raw[64:]

                derived = hashlib.pbkdf2_hmac("sha256", self._key, salt, 100_000, dklen=64)
                enc_key = derived[:32]
                mac_key = derived[32:]

                expected_tag = hmac.new(mac_key, salt + iv + ciphertext, hashlib.sha256).digest()
                if not hmac.compare_digest(tag, expected_tag):
                    logger.error("[SecretCipher] Integrity verification failed (tampered ciphertext)")
                    return ""

                keystream = bytearray()
                counter = 0
                while len(keystream) < len(ciphertext):
                    block = hmac.new(enc_key, iv + counter.to_bytes(4, "big"), hashlib.sha256).digest()
                    keystream.extend(block)
                    counter += 1

                decrypted = bytes(a ^ b for a, b in zip(ciphertext, keystream[:len(ciphertext)]))
                return decrypted.decode("utf-8")

            # Fallback unencrypted legacy representation
            return encoded
        except Exception as e:
            logger.error(f"[SecretCipher] Decryption error: {e}")
            return ""


class AccountsStore:
    """
    Thread-safe and process-safe storage for multi-broker accounts.
    """

    def __init__(self, file_path: Path = _ACCOUNTS_FILE):
        self.file_path = file_path
        self._lock = threading.RLock()
        self.cipher = SecretCipher()
        self._ensure_file()

    def _ensure_file(self) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            with self._lock:
                self._write_raw({"accounts": [], "version": 1})

    def _read_raw(self) -> Dict[str, Any]:
        try:
            if not self.file_path.exists():
                return {"accounts": [], "version": 1}
            with open(self.file_path, "r", encoding="utf-8") as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                try:
                    data = json.load(f)
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                return data if isinstance(data, dict) else {"accounts": []}
        except Exception as e:
            logger.error(f"[AccountsStore] Read error: {e}")
            return {"accounts": []}

    def _write_raw(self, data: Dict[str, Any]) -> bool:
        tmp_path = self.file_path.with_suffix(".tmp")
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    json.dump(data, f, indent=2)
                    f.flush()
                    os.fsync(f.fileno())
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            tmp_path.replace(self.file_path)
            return True
        except Exception as e:
            logger.error(f"[AccountsStore] Write error: {e}")
            if tmp_path.exists():
                try: tmp_path.unlink()
                except Exception: pass
            return False

    @staticmethod
    def mask_login(login: str) -> str:
        """Masks email or account string for safe logging and display."""
        if "@" in login:
            name, domain = login.split("@", 1)
            masked_name = name[:2] + "***" if len(name) > 2 else name + "***"
            return f"{masked_name}@{domain}"
        if len(login) > 4:
            return login[:2] + "****" + login[-2:]
        return "***"

    def add_account(
        self,
        broker_id: str,
        telegram_user_id: int | str,
        telegram_chat_id: int | str,
        login: str,
        password: str,
        server: str = "",
        acc_num: str = "",
        default_lots: float = 0.10,
        environment: str = "demo",
        label: str = "",
        extra_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Adds a new broker account to the store."""
        with self._lock:
            data = self._read_raw()
            accounts = data.get("accounts", [])

            # Generate stable unique ID
            rand_hex = secrets.token_hex(4)
            account_id = f"{broker_id[:4]}_{rand_hex}"

            # Check if this exact login on this server already exists for this user
            clean_login = login.strip()
            clean_server = server.strip()
            for acc in accounts:
                if (
                    str(acc.get("telegram_user_id")) == str(telegram_user_id)
                    and acc.get("broker_id") == broker_id
                    and acc.get("login", "").lower() == clean_login.lower()
                    and acc.get("server", "").lower() == clean_server.lower()
                ):
                    # Update existing account credentials and return
                    acc["password_encrypted"] = self.cipher.encrypt(password)
                    acc["acc_num"] = str(acc_num).strip()
                    acc["default_lots"] = max(0.01, float(default_lots))
                    acc["is_active"] = True
                    acc["updated_at"] = datetime.now(timezone.utc).isoformat()
                    self._write_raw(data)
                    logger.info(f"[AccountsStore] Updated existing account {acc['id']} for user {telegram_user_id}")
                    return acc

            new_acc = {
                "id": account_id,
                "broker_id": broker_id.lower().strip(),
                "telegram_user_id": str(telegram_user_id),
                "telegram_chat_id": str(telegram_chat_id),
                "label": label or f"{server} ({self.mask_login(clean_login)})",
                "environment": environment.lower().strip() or "demo",
                "server": clean_server,
                "login": clean_login,
                "password_encrypted": self.cipher.encrypt(password),
                "acc_num": str(acc_num).strip(),
                "default_lots": max(0.01, float(default_lots)),
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "extra": extra_config or {}
            }

            accounts.append(new_acc)
            data["accounts"] = accounts
            self._write_raw(data)
            logger.info(f"[AccountsStore] Added new account {account_id} for user {telegram_user_id}")
            return new_acc

    def get_accounts_by_user(self, telegram_user_id: int | str, mask: bool = True) -> List[Dict[str, Any]]:
        """Retrieves accounts belonging to a Telegram user."""
        with self._lock:
            data = self._read_raw()
            user_accs = [
                dict(a) for a in data.get("accounts", [])
                if str(a.get("telegram_user_id")) == str(telegram_user_id)
            ]
            if mask:
                for a in user_accs:
                    a["login_masked"] = self.mask_login(a.get("login", ""))
                    a.pop("password_encrypted", None)
            return user_accs

    def get_all_active_accounts(self, broker_id: Optional[str] = None, decrypt: bool = True) -> List[Dict[str, Any]]:
        """Retrieves all active accounts across all users for trading dispatch."""
        with self._lock:
            data = self._read_raw()
            results = []
            for a in data.get("accounts", []):
                if not a.get("is_active", True):
                    continue
                if broker_id and a.get("broker_id") != broker_id.lower().strip():
                    continue

                item = dict(a)
                if decrypt:
                    enc_pwd = item.get("password_encrypted", "")
                    item["password"] = self.cipher.decrypt(enc_pwd) if enc_pwd else ""
                results.append(item)
            return results

    def get_account_by_id(self, account_id: str, decrypt: bool = False) -> Optional[Dict[str, Any]]:
        with self._lock:
            data = self._read_raw()
            for a in data.get("accounts", []):
                if a.get("id") == account_id:
                    item = dict(a)
                    if decrypt:
                        enc_pwd = item.get("password_encrypted", "")
                        item["password"] = self.cipher.decrypt(enc_pwd) if enc_pwd else ""
                    return item
            return None

    def update_account_risk(self, account_id: str, telegram_user_id: int | str, lots: float) -> bool:
        with self._lock:
            data = self._read_raw()
            updated = False
            for a in data.get("accounts", []):
                if a.get("id") == account_id and str(a.get("telegram_user_id")) == str(telegram_user_id):
                    a["default_lots"] = max(0.01, round(float(lots), 2))
                    a["updated_at"] = datetime.now(timezone.utc).isoformat()
                    updated = True
                    break
            if updated:
                self._write_raw(data)
            return updated

    def toggle_account_active(self, account_id: str, telegram_user_id: int | str, is_active: Optional[bool] = None) -> bool:
        with self._lock:
            data = self._read_raw()
            changed = False
            for a in data.get("accounts", []):
                if a.get("id") == account_id and str(a.get("telegram_user_id")) == str(telegram_user_id):
                    curr = a.get("is_active", True)
                    a["is_active"] = not curr if is_active is None else bool(is_active)
                    a["updated_at"] = datetime.now(timezone.utc).isoformat()
                    changed = True
                    break
            if changed:
                self._write_raw(data)
            return changed

    def delete_account(self, account_id: str, telegram_user_id: int | str) -> bool:
        with self._lock:
            data = self._read_raw()
            initial_len = len(data.get("accounts", []))
            data["accounts"] = [
                a for a in data.get("accounts", [])
                if not (a.get("id") == account_id and str(a.get("telegram_user_id")) == str(telegram_user_id))
            ]
            if len(data["accounts"]) < initial_len:
                self._write_raw(data)
                return True
            return False


accounts_store = AccountsStore()

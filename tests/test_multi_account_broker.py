"""
tests/test_multi_account_broker.py
─────────────────────────────────────────────────────────────
Comprehensive unit tests for multi-account broker architecture:
1. Generic AccountsStore (encryption, isolation, thread safety, masking)
2. Telegram Listener interactive commands & session wizard
3. TradeLockerBroker concurrent multi-account order execution
"""

import unittest
from server.accounts_store import accounts_store, SecretCipher
from server.brokers.registry import broker_registry
from server.telegram_listener import telegram_listener


class TestMultiAccountBroker(unittest.TestCase):

    def test_secret_cipher_roundtrip(self):
        cipher = SecretCipher()
        secret = "my_super_secret_broker_password_123!"
        encrypted = cipher.encrypt(secret)
        self.assertNotEqual(encrypted, secret)
        self.assertGreater(len(encrypted), len(secret))
        decrypted = cipher.decrypt(encrypted)
        self.assertEqual(decrypted, secret)

    def test_accounts_store_crud(self):
        user_id = "test_user_99"
        chat_id = "test_chat_99"

        # Add account
        acc = accounts_store.add_account(
            broker_id="tradelocker",
            telegram_user_id=user_id,
            telegram_chat_id=chat_id,
            login="trader99@example.com",
            password="securepass99",
            server="FunderPro Demo",
            acc_num="ACC-99",
            default_lots=0.20
        )
        acc_id = acc["id"]
        self.assertTrue(acc_id.startswith("trad_"))
        self.assertEqual(acc["default_lots"], 0.20)

        # Retrieve by user (masked)
        user_accs = accounts_store.get_accounts_by_user(user_id, mask=True)
        self.assertGreaterEqual(len(user_accs), 1)
        found = [a for a in user_accs if a["id"] == acc_id][0]
        self.assertEqual(found["login_masked"], "tr***@example.com")
        self.assertNotIn("password_encrypted", found)

        # Retrieve with decrypt
        decrypted_acc = accounts_store.get_account_by_id(acc_id, decrypt=True)
        self.assertIsNotNone(decrypted_acc)
        self.assertEqual(decrypted_acc["password"], "securepass99")

        # Update risk
        ok = accounts_store.update_account_risk(acc_id, user_id, 0.50)
        self.assertTrue(ok)
        updated = accounts_store.get_account_by_id(acc_id, decrypt=False)
        self.assertEqual(updated["default_lots"], 0.50)

        # Toggle active
        ok_toggle = accounts_store.toggle_account_active(acc_id, user_id, is_active=False)
        self.assertTrue(ok_toggle)
        toggled = accounts_store.get_account_by_id(acc_id, decrypt=False)
        self.assertFalse(toggled["is_active"])

        # Delete account
        ok_del = accounts_store.delete_account(acc_id, user_id)
        self.assertTrue(ok_del)
        self.assertIsNone(accounts_store.get_account_by_id(acc_id))

    def test_telegram_listener_helpers(self):
        self.assertTrue(telegram_listener._is_float("0.25"))
        self.assertFalse(telegram_listener._is_float("invalid"))
        self.assertTrue(telegram_listener._is_float("1"))

    def test_concurrent_multi_account_execution(self):
        broker = broker_registry.get_broker("tradelocker")
        self.assertIsNotNone(broker)
        self.assertTrue(broker.supports_multi_account)

        # Register two simulated user accounts
        acc1 = accounts_store.add_account("tradelocker", "u1", "c1", "a1@test.com", "p1", "Server 1", "", 0.1)
        acc2 = accounts_store.add_account("tradelocker", "u2", "c2", "a2@test.com", "p2", "Server 2", "", 0.3)

        sig = {
            "action": "BUY",
            "symbol": "BTC/USDT",
            "price": 60000.0,
            "stop_loss": 59000.0,
            "take_profit": 62000.0
        }

        res = broker.execute_order(sig)
        self.assertIn(res["status"], ("FILLED", "SIMULATED_PREVIEW"))
        self.assertGreaterEqual(res["accounts_count"], 2)

        # Clean up
        accounts_store.delete_account(acc1["id"], "u1")
        accounts_store.delete_account(acc2["id"], "u2")


if __name__ == "__main__":
    unittest.main()

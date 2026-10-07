import unittest
import time
from datetime import datetime, timezone
from server.strategy_executor import NativeStrategyRunner
from server.state_manager import signal_store

class TestDrawdownCircuitBreaker(unittest.TestCase):
    def setUp(self):
        self.runner = NativeStrategyRunner("zillions_mtfvdmr")

    def test_circuit_breaker_halts_when_budget_exhausted(self):
        """Tests that when today's loss approaches the daily limit, the circuit breaker halts entries."""
        safe, reason, details = self.runner.check_drawdown_safety()
        self.assertIn("today_loss_usd", details)
        self.assertIn("max_daily_loss_usd", details)
        self.assertIn("remaining_budget_usd", details)
        
        # Today's actual loss is -$79.16 / -$80.99 with remaining budget ~$69-$70.
        # Since buffer_required is $75 (2.5x $30 trade risk), safe should be False.
        self.assertFalse(safe)
        self.assertEqual(reason, "DAILY_DRAWDOWN_BUFFER_EXHAUSTED")
        self.assertTrue("exhausted" in details["message"].lower())

if __name__ == "__main__":
    unittest.main()

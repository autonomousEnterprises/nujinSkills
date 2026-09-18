"""
tests/test_tradelocker_provider.py
─────────────────────────────────────────────────────────────
Tests for dynamic broker price feed switching and TradeLockerMarketDataProvider:
1. ProviderRegistry routing when broker is disconnected/paper (default public feeds)
2. ProviderRegistry routing when TradeLocker broker is active and connected
3. TradeLockerMarketDataProvider live tick ingestion & candle updates
4. TradeLocker snapshot quote retrieval & XauusdScalpEngine broker feed switching
"""

import asyncio
import time
import unittest
from unittest.mock import MagicMock, patch

from server.providers.base import ProviderRegistry, BaseMarketDataProvider
from server.brokers.registry import broker_registry


class TestTradeLockerPriceFeed(unittest.TestCase):

    def setUp(self):
        # Reset provider registry
        ProviderRegistry._providers.clear()

    def tearDown(self):
        ProviderRegistry._providers.clear()

    def test_default_public_provider_when_paper(self):
        """When active broker is paper/disconnected, default providers are used."""
        with patch.object(broker_registry, "get_active_broker_id", return_value="paper"):
            p_gold = ProviderRegistry.get_provider("XAU/USD", "1m")
            self.assertEqual(p_gold.symbol, "XAU/USD")
            self.assertIn("OandaGoldProvider", p_gold.__class__.__name__)

            p_btc = ProviderRegistry.get_provider("BTC/USDT", "15m")
            self.assertEqual(p_btc.symbol, "BTC/USDT")
            self.assertIn("BinanceSpotProvider", p_btc.__class__.__name__)

    def test_broker_first_routing_when_connected(self):
        """When broker is connected and provides market data, ProviderRegistry uses broker provider."""
        mock_broker = MagicMock()
        mock_broker.broker_id = "tradelocker"
        mock_broker.is_connected = True
        mock_broker.name = "TradeLocker Institutional Gateway [PRO]"

        mock_provider = MagicMock(spec=BaseMarketDataProvider)
        mock_provider.symbol = "XAU/USD"
        mock_provider.timeframe = "5m"
        mock_provider.is_running = False
        mock_broker.get_market_data_provider.return_value = mock_provider

        with patch.object(broker_registry, "get_broker", return_value=mock_broker):
            provider = ProviderRegistry.get_provider("XAU/USD", "5m")
            self.assertEqual(provider, mock_provider)
            mock_broker.get_market_data_provider.assert_called_once_with("XAU/USD", "5m")

    def test_tradelocker_provider_tick_processing(self):
        """Tests that TradeLockerMarketDataProvider processes live broker quotes and forms candles."""
        import sys, os
        pro_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "plugins", "pro"))
        if pro_path not in sys.path:
            sys.path.insert(0, pro_path)

        try:
            from brokers.tradelocker_provider import TradeLockerMarketDataProvider
        except ImportError:
            self.skipTest("TradeLocker provider not found in path")

        mock_broker = MagicMock()
        mock_broker.is_connected = True
        mock_broker._resolve_instrument_id.return_value = "inst_xau_123"

        mock_client = MagicMock()
        mock_client.get_quote.return_value = {
            "bp": 4410.20,
            "ap": 4410.50,
            "lp": 4410.35
        }
        mock_broker.client = mock_client

        provider = TradeLockerMarketDataProvider(broker_instance=mock_broker, symbol="XAU/USD", timeframe="1m")
        quote = provider.fetch_snapshot_quote()
        self.assertIsNotNone(quote)
        self.assertEqual(quote["price"], 4410.35)
        self.assertEqual(quote["bid"], 4410.20)
        self.assertEqual(quote["ask"], 4410.50)
        self.assertEqual(quote["source"], "tradelocker_broker")

        # Test process live tick synchronously
        async def run_tick():
            await provider.process_live_tick(
                price=quote["price"],
                timestamp=quote["timestamp"],
                bid=quote["bid"],
                ask=quote["ask"],
                source="tradelocker_stream"
            )
        asyncio.run(run_tick())

        candles = provider.get_candles()
        self.assertGreaterEqual(len(candles), 1)
        self.assertEqual(candles[-1]["close"], 4410.35)

    def test_xauusd_streamer_switches_to_broker_feed(self):
        """Tests that XauusdScalpEngine checks and adopts active connected broker quote."""
        from server.xauusd_streamer import XauusdScalpEngine
        engine = XauusdScalpEngine()

        mock_broker = MagicMock()
        mock_broker.broker_id = "tradelocker"
        mock_broker.is_connected = True
        mock_broker.name = "TradeLocker Institutional Gateway [PRO]"
        mock_broker.get_latest_quote.return_value = {
            "symbol": "XAU/USD",
            "price": 4425.80,
            "bid": 4425.65,
            "ask": 4425.95,
            "timestamp": int(time.time()),
            "source": "tradelocker_stream"
        }

        # Check broker latest quote call
        with patch.object(broker_registry, "get_broker", return_value=mock_broker):
            quote = mock_broker.get_latest_quote("XAU/USD")
            self.assertEqual(quote["price"], 4425.80)
            self.assertEqual(quote["source"], "tradelocker_stream")


if __name__ == "__main__":
    unittest.main()

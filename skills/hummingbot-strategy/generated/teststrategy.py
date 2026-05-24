import logging
from decimal import Decimal
from typing import Dict, Set, List
import pandas as pd
import numpy as np

from hummingbot.connector.connector_base import ConnectorBase
from hummingbot.core.data_type.common import OrderType
from hummingbot.data_feed.candles_feed.candles_factory import CandlesFactory, CandlesConfig
from hummingbot.strategy.script_strategy_base import ScriptStrategyBase


class TestStrategy(ScriptStrategyBase):
    """
    Script Strategy generated for TestStrategy.
    Implement your custom trading logic inside on_tick.
    """
    connector_name = "binance"
    trading_pair = "ETH-USDT"
    
    # Strategy parameters
    order_amount = Decimal("0.001")
    
    markets: Dict[str, Set[str]] = {
        connector_name: {trading_pair}
    }

    def __init__(self):
        super().__init__()
        # Configure candles for technical indicators
        self.candles_config = CandlesConfig(
            connector="binance",
            trading_pair=self.trading_pair,
            interval="1m",
            max_records=100
        )
        self.candles = CandlesFactory.get_candle(self.candles_config)
        self.active_order_ids: List[str] = []

    def on_start(self):
        self.candles.start()
        self.logger().info("Started candles stream for indicator calculations.")

    def on_stop(self):
        self.candles.stop()

    def on_tick(self):
        """
        Executed every clock cycle.
        """
        if not self.candles.is_ready:
            return
            
        connector: ConnectorBase = self.connectors[self.connector_name]
        mid_price = connector.get_mid_price(self.trading_pair)
        
        # Prevent order flooding: check if we have active orders
        if len(self.active_order_ids) > 0:
            return

        df = self.candles.candles_df
        
        # Calculate technical indicators
        indicators = {}
        # RSI Calculation
        close = df["close"].astype(float)
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss.replace(0, 1e-9)
        rsi = 100 - (100 / (1 + rs))
        indicators["rsi"] = float(rsi.iloc[-1])

        # SMA Calculation
        close = df["close"].astype(float)
        val = close.rolling(window=20).mean() if "sma" == "sma" else close.ewm(span=20).mean()
        indicators["sma"] = float(val.iloc[-1])

        # TODO: Implement custom alpha signal rules using indicators dict
        # Example:
        # if indicators.get("rsi") < 30:
        #     self.buy(...)
        pass

    def did_fill_order(self, event):
        if event.order_id in self.active_order_ids:
            self.active_order_ids.remove(event.order_id)

    def format_status(self) -> str:
        return f"Running TestStrategy on {self.trading_pair}"

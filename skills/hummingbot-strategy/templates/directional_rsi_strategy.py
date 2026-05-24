import logging
from decimal import Decimal
from typing import Dict, Set
import numpy as np
import pandas as pd
from hummingbot.connector.connector_base import ConnectorBase
from hummingbot.core.data_type.common import OrderType, PositionAction, PositionSide
from hummingbot.data_feed.candles_feed.candles_factory import CandlesFactory, CandlesConfig
from hummingbot.strategy.script_strategy_base import ScriptStrategyBase


class DirectionalRsiStrategy(ScriptStrategyBase):
    """
    Directional RSI Strategy.
    Buys when RSI is oversold (< 30) and sells when RSI is overbought (> 70).
    Uses CandlesFactory to fetch and stream real-time price history from Binance.
    
    Requirements:
      - pandas and numpy (pre-installed in Hummingbot environment)
    """

    connector_name = "binance_paper_trade"
    trading_pair = "BTC-USDT"
    
    # Strategy Parameters
    rsi_length = 14
    rsi_oversold = 30.0
    rsi_overbought = 70.0
    order_amount = Decimal("0.001")
    
    # Risk Management
    stop_loss_pct = Decimal("0.015")   # 1.5% stop loss
    take_profit_pct = Decimal("0.03")   # 3% take profit

    # Markets dictionary mapping for legacy compatibility
    markets: Dict[str, Set[str]] = {
        connector_name: {trading_pair}
    }

    def __init__(self):
        super().__init__()
        
        # 1. Configure the historical candles data feed
        self.candles_config = CandlesConfig(
            connector="binance",
            trading_pair=self.trading_pair,
            interval="1m",
            max_records=100
        )
        self.candles = CandlesFactory.get_candle(self.candles_config)
        
        # 2. Tracking State
        self.current_position = None  # "LONG", "SHORT", or None
        self.entry_price = Decimal("0")
        self.last_rsi = 50.0

    def on_start(self):
        """Starts the candles data feed connection."""
        self.candles.start()
        self.logger().info(f"Candles data feed started for {self.trading_pair}...")

    def on_stop(self):
        """Stops the candles data feed connection."""
        self.candles.stop()
        self.logger().info("Candles data feed stopped.")

    def calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> float:
        """
        Calculate Relative Strength Index (RSI) using standard pandas math.
        """
        close = df["close"].astype(float)
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        # Prevent division by zero
        rs = gain / loss.replace(0, 1e-9)
        rsi = 100 - (100 / (1 + rs))
        return float(rsi.iloc[-1])

    def on_tick(self):
        """
        Executes on every clock cycle.
        """
        connector: ConnectorBase = self.connectors[self.connector_name]
        
        # Ensure the candle database is fully synchronized before starting indicators
        if not self.candles.is_ready:
            return

        mid_price = connector.get_mid_price(self.trading_pair)
        if mid_price.is_nan():
            return

        # 1. Retrieve the candles DataFrame and calculate RSI
        df = self.candles.candles_df
        rsi = self.calculate_rsi(df, self.rsi_length)
        self.last_rsi = rsi

        # 2. Check risk management exits if we are currently in a trade
        if self.current_position is not None:
            self.check_risk_exits(mid_price)
            return

        # 3. Analyze entry signals (RSI crossovers)
        if rsi < self.rsi_oversold:
            self.logger().info(f"RSI is oversold ({rsi:.2f} < {self.rsi_oversold}). Opening LONG position.")
            
            # Place buy order
            self.buy(
                connector_name=self.connector_name,
                trading_pair=self.trading_pair,
                amount=self.order_amount,
                order_type=OrderType.MARKET
            )
            
            self.current_position = "LONG"
            self.entry_price = mid_price

        elif rsi > self.rsi_overbought:
            self.logger().info(f"RSI is overbought ({rsi:.2f} > {self.rsi_overbought}). Opening SHORT position.")
            
            # Place sell order
            self.sell(
                connector_name=self.connector_name,
                trading_pair=self.trading_pair,
                amount=self.order_amount,
                order_type=OrderType.MARKET
            )
            
            self.current_position = "SHORT"
            self.entry_price = mid_price

    def check_risk_exits(self, current_price: Decimal):
        """
        Exits positions dynamically if dynamic stop-loss or take-profit threshold is breached.
        """
        if self.current_position == "LONG":
            profit_loss = (current_price - self.entry_price) / self.entry_price
            
            # Stop Loss Trigger
            if profit_loss <= -self.stop_loss_pct:
                self.logger().info(f"LONG Stop Loss triggered at {current_price} ({profit_loss * 100:.2f}% P&L). Exiting.")
                self.sell(
                    connector_name=self.connector_name,
                    trading_pair=self.trading_pair,
                    amount=self.order_amount,
                    order_type=OrderType.MARKET
                )
                self.reset_state()
            
            # Take Profit Trigger
            elif profit_loss >= self.take_profit_pct:
                self.logger().info(f"LONG Take Profit triggered at {current_price} ({profit_loss * 100:.2f}% P&L). Exiting.")
                self.sell(
                    connector_name=self.connector_name,
                    trading_pair=self.trading_pair,
                    amount=self.order_amount,
                    order_type=OrderType.MARKET
                )
                self.reset_state()

        elif self.current_position == "SHORT":
            profit_loss = (self.entry_price - current_price) / self.entry_price
            
            # Stop Loss Trigger
            if profit_loss <= -self.stop_loss_pct:
                self.logger().info(f"SHORT Stop Loss triggered at {current_price} ({profit_loss * 100:.2f}% P&L). Exiting.")
                self.buy(
                    connector_name=self.connector_name,
                    trading_pair=self.trading_pair,
                    amount=self.order_amount,
                    order_type=OrderType.MARKET
                )
                self.reset_state()
            
            # Take Profit Trigger
            elif profit_loss >= self.take_profit_pct:
                self.logger().info(f"SHORT Take Profit triggered at {current_price} ({profit_loss * 100:.2f}% P&L). Exiting.")
                self.buy(
                    connector_name=self.connector_name,
                    trading_pair=self.trading_pair,
                    amount=self.order_amount,
                    order_type=OrderType.MARKET
                )
                self.reset_state()

    def reset_state(self):
        """Cleans up internal state parameters on exit."""
        self.current_position = None
        self.entry_price = Decimal("0")

    def format_status(self) -> str:
        """
        Status console printout.
        """
        connector = self.connectors[self.connector_name]
        mid_price = connector.get_mid_price(self.trading_pair)
        
        lines = []
        lines.append("══════════════════════════════════════════════════════════════════════")
        lines.append(f"  RSI Directional Bot Status — {self.trading_pair}")
        lines.append("══════════════════════════════════════════════════════════════════════")
        lines.append(f"  Current Mid Price: {mid_price:.2f}")
        lines.append(f"  Current RSI(14): {self.last_rsi:.2f}")
        lines.append(f"  Position: {self.current_position or 'NONE'}")
        if self.current_position:
            lines.append(f"    - Entry Price: {self.entry_price:.2f}")
            pnl = ((mid_price - self.entry_price) / self.entry_price if self.current_position == "LONG"
                   else (self.entry_price - mid_price) / self.entry_price)
            lines.append(f"    - Unrealized P&L: {pnl * 100:.2f}%")
        lines.append("══════════════════════════════════════════════════════════════════════")
        return "\n".join(lines)

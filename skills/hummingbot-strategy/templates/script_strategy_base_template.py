import logging
from decimal import Decimal
from typing import Dict, List, Set
from hummingbot.connector.connector_base import ConnectorBase
from hummingbot.core.data_type.common import OrderType
from hummingbot.core.event.events import OrderFilledEvent
from hummingbot.strategy.script_strategy_base import ScriptStrategyBase


class ScriptStrategyBaseTemplate(ScriptStrategyBase):
    """
    Hummingbot Legacy Script Strategy Template.
    Use this template to build custom trading logic utilizing the simple ScriptStrategyBase.
    
    WARNING: Always test in Paper Trading mode or with minimum capital first!
    """

    # 1. Define your markets configuration
    # Format: { connector_name: { trading_pair } }
    # Example: {"binance_paper_trade": {"BTC-USDT"}}
    markets: Dict[str, Set[str]] = {
        "binance_paper_trade": {"BTC-USDT"}
    }

    # 2. Strategy parameters (Use Decimal for high-precision trading metrics)
    connector_name = "binance_paper_trade"
    trading_pair = "BTC-USDT"
    base_asset = "BTC"
    quote_asset = "USDT"

    order_amount = Decimal("0.001")     # Amount of base asset to buy/sell
    price_deviation = Decimal("0.01")   # Example: Place order 1% away from mid-price
    
    # 3. State tracking (crucial to prevent order flooding)
    active_order_ids: List[str] = []
    cooldown_seconds = 60
    last_trade_timestamp = 0.0

    def on_tick(self):
        """
        Main execution loop. Called on every clock tick (usually every 1 second).
        All custom alpha logic, signals, and order placing belong here.
        """
        connector: ConnectorBase = self.connectors[self.connector_name]
        
        # Avoid placing new orders if we already have active ones in flight
        if len(self.active_order_ids) > 0:
            self.logger().info("Waiting for active orders to fill or cancel...")
            return

        # Fetch current market price
        mid_price = connector.get_mid_price(self.trading_pair)
        if mid_price.is_nan():
            self.logger().warning(f"Could not retrieve mid-price for {self.trading_pair}. Skipping tick...")
            return

        # Fetch account balances
        base_balance = connector.get_balance(self.base_asset)
        quote_balance = connector.get_balance(self.quote_asset)

        # Apply your alpha signal calculation here
        # Example signal: Check if we have sufficient quote asset to buy
        buy_price = mid_price * (Decimal("1") - self.price_deviation)
        required_quote = buy_price * self.order_amount

        if quote_balance > required_quote:
            self.logger().info(
                f"Sufficient balance. Placing BUY order for {self.order_amount} {self.base_asset} "
                f"at {buy_price} {self.quote_asset}"
            )
            
            # Place order using Decimal for price and amount
            order_id = self.buy(
                connector_name=self.connector_name,
                trading_pair=self.trading_pair,
                amount=self.order_amount,
                order_type=OrderType.LIMIT,
                price=buy_price
            )
            
            # Record order ID to track state and prevent flooding
            self.active_order_ids.append(order_id)
        else:
            self.logger().warning(
                f"Insufficient quote balance. Required: {required_quote} {self.quote_asset}, "
                f"Available: {quote_balance} {self.quote_asset}"
            )

    def did_fill_order(self, event: OrderFilledEvent):
        """
        Callback executed whenever an order is successfully filled.
        """
        self.logger().info(
            f"[{event.trading_pair}] {event.trade_type.name} order {event.order_id} filled "
            f"at {event.price} (amount: {event.amount})"
        )
        
        # Remove from active tracking
        if event.order_id in self.active_order_ids:
            self.active_order_ids.remove(event.order_id)
            
        # Update last trade timestamp for cooldown management
        self.last_trade_timestamp = self.current_timestamp

    def did_complete_buy_order(self, event):
        """Callback executed on buy order completion (filled completely)."""
        pass

    def did_complete_sell_order(self, event):
        """Callback executed on sell order completion (filled completely)."""
        pass

    def format_status(self) -> str:
        """
        Generates status message displayed in Hummingbot console upon entering 'status' command.
        Provide metrics that help verify profitability and execution state.
        """
        if not self.ready_to_trade:
            return "Strategy is not ready to trade yet..."

        connector = self.connectors[self.connector_name]
        mid_price = connector.get_mid_price(self.trading_pair)
        base_balance = connector.get_balance(self.base_asset)
        quote_balance = connector.get_balance(self.quote_asset)

        lines = []
        lines.append("══════════════════════════════════════════════════════════════════════")
        lines.append(f"  Strategy Status — {self.trading_pair}")
        lines.append("══════════════════════════════════════════════════════════════════════")
        lines.append(f"  Current Mid Price: {mid_price:.4f} {self.quote_asset}")
        lines.append(f"  Balances:")
        lines.append(f"    - {self.base_asset}: {base_balance:.6f}")
        lines.append(f"    - {self.quote_asset}: {quote_balance:.2f}")
        lines.append(f"  Active Orders: {len(self.active_order_ids)}")
        for o_id in self.active_order_ids:
            lines.append(f"    - ID: {o_id}")
        lines.append("══════════════════════════════════════════════════════════════════════")
        
        return "\n".join(lines)

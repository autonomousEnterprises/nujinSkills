from decimal import Decimal
from typing import List, Optional
from pydantic import Field

from hummingbot.strategy_v2.controllers.controller_base import ControllerBase, ControllerConfigBase
from hummingbot.strategy_v2.models.executor_actions import CreateExecutorAction, ExecutorAction, StopExecutorAction
from hummingbot.strategy_v2.models.position_executor import PositionExecutorConfig
from hummingbot.core.data_type.common import PositionMode, PriceType, OrderType


class StrategyV2ControllerTemplateConfig(ControllerConfigBase):
    """
    Configuration model for the V2 Controller Template.
    Uses Pydantic Field definitions with metadata prompts for Hummingbot CLI prompting.
    """
    controller_name: str = "strategy_v2_controller_template"
    
    connector_name: str = Field(
        default="binance_paper_trade",
        json_schema_extra={
            "prompt": "Enter the connector name (e.g., binance_paper_trade): ",
            "prompt_on_new": True
        }
    )
    trading_pair: str = Field(
        default="BTC-USDT",
        json_schema_extra={
            "prompt": "Enter the trading pair (e.g., BTC-USDT): ",
            "prompt_on_new": True
        }
    )
    order_amount: Decimal = Field(
        default=Decimal("0.001"),
        json_schema_extra={
            "prompt": "Enter the order size in base asset: ",
            "prompt_on_new": True
        }
    )
    stop_loss: Decimal = Field(
        default=Decimal("0.02"),  # 2%
        json_schema_extra={
            "prompt": "Enter the Stop Loss percentage (e.g. 0.02 for 2%): ",
            "prompt_on_new": True
        }
    )
    take_profit: Decimal = Field(
        default=Decimal("0.04"),  # 4%
        json_schema_extra={
            "prompt": "Enter the Take Profit percentage (e.g. 0.04 for 4%): ",
            "prompt_on_new": True
        }
    )
    time_limit: int = Field(
        default=3600,  # 1 hour
        json_schema_extra={
            "prompt": "Enter the position time limit in seconds (e.g., 3600): ",
            "prompt_on_new": True
        }
    )


class StrategyV2ControllerTemplate(ControllerBase):
    """
    Hummingbot Strategy V2 Controller Template.
    V2 Controllers manage the business logic (alpha signals) and delegate position lifecycle 
    execution to dedicated executors (like PositionExecutor or DCAExecutor) for safety.
    """
    config: StrategyV2ControllerTemplateConfig

    def __init__(self, config: StrategyV2ControllerTemplateConfig, *args, **kwargs):
        super().__init__(config, *args, **kwargs)
        self.config = config

    def update_processed_data(self):
        """
        Periodically executed callback to run technical analysis or fetch external signals.
        Store processed signals in `self.processed_data` (e.g., indicator calculations).
        """
        # 1. Fetch candles from Market Data Provider
        # candles = self.market_data_provider.get_candles_df(
        #     self.config.connector_name, self.config.trading_pair, "1m", limit=100
        # )
        
        # 2. Calculate indicators
        # candles["sma_fast"] = candles["close"].rolling(window=10).mean()
        
        # 3. Store in processed data dictionary
        # self.processed_data = {
        #     "signal": 1 if last_close > last_sma else -1
        # }
        self.processed_data = {"signal": 0}

    def determine_executor_actions(self) -> List[ExecutorAction]:
        """
        Evaluates the current state (signals, positions, balances) and proposes actions.
        Returns a list of ExecutorAction objects (CreateExecutorAction or StopExecutorAction).
        """
        actions = []
        signal = self.processed_data.get("signal", 0)

        # Example check: Get current active executors managed by this controller
        active_executors = self.filter_executors(
            connector_name=self.config.connector_name,
            trading_pair=self.config.trading_pair,
            active=True
        )

        # If we have no active positions and we receive a trading signal, trigger a position executor
        if len(active_executors) == 0 and signal != 0:
            side = "LONG" if signal > 0 else "SHORT"
            self.logger().info(f"Signal received: {side}. Creating position executor.")
            
            # Define Position Executor Configuration
            executor_config = PositionExecutorConfig(
                timestamp=self.market_data_provider.time(),
                connector_name=self.config.connector_name,
                trading_pair=self.config.trading_pair,
                side=side,
                entry_price=self.market_data_provider.get_price_by_type(
                    self.config.connector_name, self.config.trading_pair, PriceType.MidPrice
                ),
                amount=self.config.order_amount,
                stop_loss=self.config.stop_loss,
                take_profit=self.config.take_profit,
                time_limit=self.config.time_limit,
                type=OrderType.LIMIT
            )
            
            # Request executor orchestrator to spin up a new PositionExecutor
            actions.append(CreateExecutorAction(
                executor_config=executor_config,
                controller_id=self.config.id
            ))

        return actions

    def determine_status_text(self) -> str:
        """
        Generates status report displayed in Hummingbot console.
        """
        active_executors = self.filter_executors(active=True)
        
        lines = []
        lines.append(f"Controller: {self.config.controller_name}")
        lines.append(f"Target Pair: {self.config.trading_pair} on {self.config.connector_name}")
        lines.append(f"Active Executors: {len(active_executors)}")
        
        for executor in active_executors:
            lines.append(f"  - Executor ID: {executor.id} | Side: {executor.side} | PnL: {executor.net_pnl_pct * 100:.2f}%")
            
        return "\n".join(lines)

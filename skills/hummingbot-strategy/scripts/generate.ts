import * as fs from "fs";
import * as path from "path";

/**
 * CLI Strategy Generator for Hummingbot.
 * Generates a boilerplate Python script strategy or Strategy V2 controller.
 * 
 * Usage:
 *   npx tsx generate.ts --name MyCustomBot --type script --indicators rsi,sma --pair BTC-USDT --connector binance
 */

function parseArgs() {
  const args = process.argv.slice(2);
  const options: Record<string, string> = {
    name: "CustomStrategy",
    type: "script",
    pair: "BTC-USDT",
    connector: "binance_paper_trade",
    indicators: "",
  };

  for (let i = 0; i < args.length; i++) {
    if (args[i].startsWith("--")) {
      const key = args[i].substring(2);
      const val = args[i + 1];
      if (val && !val.startsWith("--")) {
        options[key] = val;
        i++;
      }
    }
  }

  return options;
}

const opts = parseArgs();
const className = opts.name.charAt(0).toUpperCase() + opts.name.slice(1);
const fileName = `${opts.name.toLowerCase()}.py`;
const targetDir = path.join(process.cwd(), "skills", "hummingbot-strategy", "generated");

if (!fs.existsSync(targetDir)) {
  fs.mkdirSync(targetDir, { recursive: true });
}

const targetPath = path.join(targetDir, fileName);

// Parse indicators list
const indicatorList = opts.indicators
  ? opts.indicators.split(",").map((i) => i.trim().toLowerCase())
  : [];

// Generate template based on type
let fileContent = "";

if (opts.type === "v2") {
  fileContent = `from decimal import Decimal
from typing import List, Optional
from pydantic import Field

from hummingbot.strategy_v2.controllers.controller_base import ControllerBase, ControllerConfigBase
from hummingbot.strategy_v2.models.executor_actions import CreateExecutorAction, ExecutorAction, StopExecutorAction
from hummingbot.strategy_v2.models.position_executor import PositionExecutorConfig
from hummingbot.core.data_type.common import PriceType, OrderType


class ${className}Config(ControllerConfigBase):
    """
    Configuration parameters for ${className}.
    """
    controller_name: str = "${opts.name.toLowerCase()}"
    
    connector_name: str = Field(
        default="${opts.connector}",
        json_schema_extra={"prompt": "Enter connector name: ", "prompt_on_new": True}
    )
    trading_pair: str = Field(
        default="${opts.pair}",
        json_schema_extra={"prompt": "Enter trading pair: ", "prompt_on_new": True}
    )
    order_amount: Decimal = Field(
        default=Decimal("0.001"),
        json_schema_extra={"prompt": "Enter order size: ", "prompt_on_new": True}
    )
    stop_loss: Decimal = Field(
        default=Decimal("0.02"),
        json_schema_extra={"prompt": "Enter Stop Loss (pct): ", "prompt_on_new": True}
    )
    take_profit: Decimal = Field(
        default=Decimal("0.04"),
        json_schema_extra={"prompt": "Enter Take Profit (pct): ", "prompt_on_new": True}
    )


class ${className}(ControllerBase):
    """
    Strategy V2 Controller generated for ${opts.name}.
    Implement your custom trading logic inside determine_executor_actions.
    """
    config: ${className}Config

    def __init__(self, config: ${className}Config, *args, **kwargs):
        super().__init__(config, *args, **kwargs)
        self.config = config

    def update_processed_data(self):
        """
        Calculates and refreshes technical indicators.
        Selected indicators: ${indicatorList.join(", ") || "none"}
        """
        # Fetch candles
        candles = self.market_data_provider.get_candles_df(
            self.config.connector_name, self.config.trading_pair, "1m", limit=100
        )
        
        if candles.empty or len(candles) < 30:
            self.processed_data = {"signal": 0}
            return

        # STUB: Indicator calculation code (AI agent to write detailed math)
        indicators_state = {}
${indicatorList.map((ind) => {
  if (ind === "rsi") {
    return `        # RSI Calculation
        close = candles["close"].astype(float)
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss.replace(0, 1e-9)
        rsi = 100 - (100 / (1 + rs))
        indicators_state["rsi"] = float(rsi.iloc[-1])`;
  }
  if (ind === "sma" || ind === "ema") {
    return `        # ${ind.toUpperCase()} Calculation
        close = candles["close"].astype(float)
        ${ind} = close.rolling(window=20).mean() if "${ind}" == "sma" else close.ewm(span=20).mean()
        indicators_state["${ind}"] = float(${ind}.iloc[-1])`;
  }
  return `        # Custom placeholder for indicator: ${ind}
        indicators_state["${ind}"] = 0.0`;
}).join("\n\n")}

        # Determine signal based on indicator rules
        signal = 0
        # Example signal: signal = 1 (LONG), -1 (SHORT), 0 (NONE)
        
        self.processed_data = {
            "signal": signal,
            "indicators": indicators_state
        }

    def determine_executor_actions(self) -> List[ExecutorAction]:
        """
        Decides whether to trigger position executors.
        """
        actions = []
        signal = self.processed_data.get("signal", 0)
        
        active_executors = self.filter_executors(
            connector_name=self.config.connector_name,
            trading_pair=self.config.trading_pair,
            active=True
        )

        if len(active_executors) == 0 and signal != 0:
            side = "LONG" if signal > 0 else "SHORT"
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
                type=OrderType.MARKET
            )
            
            actions.append(CreateExecutorAction(
                executor_config=executor_config,
                controller_id=self.config.id
            ))

        return actions
`;
} else {
  fileContent = `import logging
from decimal import Decimal
from typing import Dict, Set, List
import pandas as pd
import numpy as np

from hummingbot.connector.connector_base import ConnectorBase
from hummingbot.core.data_type.common import OrderType
from hummingbot.data_feed.candles_feed.candles_factory import CandlesFactory, CandlesConfig
from hummingbot.strategy.script_strategy_base import ScriptStrategyBase


class ${className}(ScriptStrategyBase):
    """
    Script Strategy generated for ${opts.name}.
    Implement your custom trading logic inside on_tick.
    """
    connector_name = "${opts.connector}"
    trading_pair = "${opts.pair}"
    
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
${indicatorList.map((ind) => {
  if (ind === "rsi") {
    return `        # RSI Calculation
        close = df["close"].astype(float)
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss.replace(0, 1e-9)
        rsi = 100 - (100 / (1 + rs))
        indicators["rsi"] = float(rsi.iloc[-1])`;
  }
  if (ind === "sma" || ind === "ema") {
    return `        # ${ind.toUpperCase()} Calculation
        close = df["close"].astype(float)
        val = close.rolling(window=20).mean() if "${ind}" == "sma" else close.ewm(span=20).mean()
        indicators["${ind}"] = float(val.iloc[-1])`;
  }
  return `        # Custom placeholder for indicator: ${ind}
        indicators["${ind}"] = 0.0`;
}).join("\n\n")}

        # TODO: Implement custom alpha signal rules using indicators dict
        # Example:
        # if indicators.get("rsi") < 30:
        #     self.buy(...)
        pass

    def did_fill_order(self, event):
        if event.order_id in self.active_order_ids:
            self.active_order_ids.remove(event.order_id)

    def format_status(self) -> str:
        return f"Running ${className} on {self.trading_pair}"
`;
}

fs.writeFileSync(targetPath, fileContent, "utf8");
console.log(`══════════════════════════════════════════════════════════════════════`);
console.log(`  🎉 Strategy generated successfully!`);
console.log(`  File: skills/hummingbot-strategy/generated/${fileName}`);
console.log(`  Type: ${opts.type.toUpperCase()}`);
console.log(`  Indicators: ${indicatorList.join(", ") || "none"}`);
console.log(`══════════════════════════════════════════════════════════════════════`);

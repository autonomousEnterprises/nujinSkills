# Hummingbot Strategy V2 Architecture

Hummingbot Strategy V2 introduces a modular architecture that decouples strategy decision-making (generating signals) from execution (placing and managing orders). This structure dramatically improves code reusability, safety, and readability.

---

## The V2 Components

```
┌─────────────────────────────────────────────────────────┐
│                   Market Data Provider                  │
│       (Aggregates candles, order book, and trades)      │
└────────────────────────────┬────────────────────────────┘
                             │ (Candles / Prices)
                             ▼
┌─────────────────────────────────────────────────────────┐
│                    Strategy Controller                  │
│  (Calculates indicators, evaluates alpha signal rules)  │
└────────────────────────────┬────────────────────────────┘
                             │ (ExecutorActions)
                             ▼
┌─────────────────────────────────────────────────────────┐
│                   Executor Orchestrator                 │
│         (Spins up / stops dedicated executors)          │
└────────────────────────────┬────────────────────────────┘
                             │
            ┌────────────────┴────────────────┐
            ▼                                 ▼
┌───────────────────────┐         ┌───────────────────────┐
│   Position Executor   │         │     DCA Executor      │
│  (Manages SL/TP/Limit)│         │ (Multi-level entries) │
└───────────────────────┘         └───────────────────────┘
```

### 1. Market Data Providers
Instead of directly listening to exchange raw websocket connections, V2 Controllers interact with the `MarketDataProvider`. This component aggregates:
- Historical and streaming candles (OHLCV) across multiple intervals.
- Market order books (depth, bids, asks).
- Trade volumes and volatility metrics.

### 2. Strategy Controllers (`ControllerBase`)
The controller acts as the "brain". It is responsible for processing market data and proposing action items.
- **Data preprocessing:** Done in `update_processed_data()`. Indicators or features should be calculated here and stored in `self.processed_data` as standard Python types.
- **Action proposal:** Done in `determine_executor_actions()`. It returns a list of `CreateExecutorAction` or `StopExecutorAction` objects.
- **Benefit:** The controller does not place buy/sell orders directly on the exchange. It only commands executors to do so. This minimizes API rate limits issues and prevents order state corruption.

### 3. Executors
Executors are independent, short-lived agents that manage the lifecycle of a specific trading position or grid level. They handle:
- Placing limit/market entry orders.
- Monitoring entry execution status.
- Enforcing risk controls: Stop Loss, Take Profit, and Time Limits.
- Execution strategies: Trail Stop, Limit Maker, or instant Market order exit.

#### Common Executors:
- **`PositionExecutor`:** Manages a single trading position (e.g. entry, TP target, SL stop, time limit).
- **`DCAExecutor`:** Executes dollar-cost averaging entries across multiple price brackets before managing the collective position.
- **`GridExecutor`:** Deploys a buying and selling grid around a target price.

---

## Defining a Controller configuration

Controllers use Pydantic configurations (`ControllerConfigBase`) to define user parameters. In Hummingbot, these configs automatically generate CLI prompts during strategy instantiation:

```python
from pydantic import Field
from hummingbot.strategy_v2.controllers.controller_base import ControllerConfigBase

class MyStrategyConfig(ControllerConfigBase):
    controller_name: str = "my_strategy"
    
    # Prompt the user for exchange connector name in CLI
    connector_name: str = Field(
        default="binance_paper_trade",
        json_schema_extra={
            "prompt": "Enter exchange connector name: ",
            "prompt_on_new": True
        }
    )
```

## Running V2 Controllers

1. **Initialize Config:**
   Run the config command to generate your controller YAML settings:
   ```bash
   create --controller-config MyStrategy
   ```
2. **Execute Bot:**
   Run the V2 controller manager script with your configuration file:
   ```bash
   start --v2 conf/controllers/my_strategy_config.yml
   ```

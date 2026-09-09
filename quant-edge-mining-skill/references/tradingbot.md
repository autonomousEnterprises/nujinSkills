**Hummingbot is generally too heavy and structurally mismatched for this specific workflow.** It is built in Cython/C++ wrappers primarily for high-frequency market making, cross-exchange arbitrage, and order-book liquidity provision. Its backtesting tooling is clunky, and orchestrating it programmatically through an LLM agent creates unnecessary friction.

For an AI agent that generates **directional, swing, or regime-based strategies from candlestick data**, there are much cleaner alternatives that support strategy injection, backtesting, paper trading, and live execution via clean CLI or Python API interfaces.

---

### Comparison of Lightweight Frameworks

| Framework | Architecture | Strengths for an AI Agent | Weaknesses |
| --- | --- | --- | --- |
| **Freqtrade** | Python / CLI / REST API | Pure CLI control; unified `IStrategy` interface; built-in dry-run (paper) & live execution on 100+ exchanges via CCXT. | Heavier installation footprint (though easy via Docker). |
| **Jesse** | Python / CLI / Clean OOP | Exceptionally clean, minimalist Python API; fast backtesting; zero look-ahead bias; native paper/live trading. | Supports fewer exchanges natively than CCXT-backed bots. |
| **Custom Micro-Runner (VBT + CCXT)** | Modular script (~150 lines) | Absolute maximum speed; zero boilerplate; exact control over agent tool contracts. | You must write the state-handling and order dispatch logic yourself. |

---

### The Best Production Choice: Freqtrade

**Freqtrade** is the most turnkey option because it separates the strategy into a single, highly standardized Python file. An agent can write the strategy file, execute CLI commands to test it, and launch it into paper trading without you having to build execution plumbing.

#### Why it fits an AI Agent tool contract:

1. **Single-File Strategy Injection:** Strategies inherit from `IStrategy`. The agent only needs to generate one Python script implementing `populate_indicators`, `populate_entry_trend`, and `populate_exit_trend`.
2. **Headless CLI Tools:** The agent can invoke native terminal commands:
```bash
# 1. Download data
freqtrade download-data --pairs BTC/USDT ETH/USDT -t 15m --timerange 20240101-

# 2. Run backtest on the generated strategy
freqtrade backtesting --strategy MyAgentGeneratedStrategy --timerange 20240101- --export trades

# 3. Launch paper trading (dry-run)
freqtrade trade --dry-run --strategy MyAgentGeneratedStrategy --config config.json

```


3. **Native Execution Engine:** Freqtrade handles order routing, trailing stop losses, take profits, emergency cancellations, and exchange connectivity across dozens of exchanges via CCXT.

---

### The Cleanest Developer Choice: Jesse

If you want a framework that feels like modern Python rather than a massive configuration-heavy application, **Jesse** is ideal.

* **Agent ergonomics:** Jesse enforces a clean, deterministic class structure:
```python
from jesse.strategies import Strategy
import jesse.indicators as ta

class AgentStrategy(Strategy):
    def should_long(self) -> bool:
        # Agent injects entry conditions
        return self.rvi > 60 and self.price > self.ema

    def should_short(self) -> bool:
        return False

    def go_long(self):
        qty = 1.0
        self.buy = qty, self.price

```


* **Execution:** Supports backtesting, visual report generation, paper trading, and live execution via a unified CLI (`jesse backtest`, `jesse live`).

---

### Recommended Agent Tooling Architecture

Instead of having the agent manage server state, expose three distinct tools to your agent:

```
┌────────────────────────────────────────────────────────┐
│                   LLM Quant Agent                      │
└───────┬──────────────────┬───────────────────┬─────────┘
        │                  │                   │
        ▼                  ▼                   ▼
┌────────────────┐ ┌────────────────┐ ┌────────────────┐
│  Tool 1:       │ │  Tool 2:       │ │  Tool 3:       │
│  write_strategy│ │  run_backtest  │ │  deploy_paper  │
└───────┬────────┘ └───────┬────────┘ └────────┬───────┘
        │                  │                   │
        ▼                  ▼                   ▼
  Generates .py      Executes CLI         Executes CLI
  into strategy      (Freqtrade /         in background
  folder             Jesse)               process

```

1. **`write_strategy_code(strategy_name: str, python_code: str)`**:
* Writes the LLM-generated code into the `./user_data/strategies/` directory.


2. **`run_backtest(strategy_name: str, timerange: str, capital: float)`**:
* Runs the CLI command, parses the returned JSON/terminal summary (Total Profit, Max Drawdown, Win Rate, Sharpe Ratio), and returns structured performance metrics back to the agent for evaluation.


3. **`launch_paper_trader(strategy_name: str, capital: float)`**:
* If the metrics pass the Deflated Sharpe and drawdown filters, launches the bot in `--dry-run` / paper mode.
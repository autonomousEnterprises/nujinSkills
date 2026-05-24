# Common Pitfalls in Hummingbot Strategy Coding

Writing trading strategies for Hummingbot requires care because the code directly controls financial capital and interacts with real-time exchange APIs. Below are the most common coding mistakes, risk issues, and how to avoid them.

---

## 1. Floating-Point Precision Errors
**The Pitfall:** Cryptocurrency exchanges require exact price tick levels and size decimals. Standard Python floats suffer from binary representation errors (e.g. `0.1 + 0.2 = 0.30000000000000004`). If you send an order size like `0.30000000000000004` to an exchange, the API will reject the order for invalid format.

**The Fix:** Always use `Decimal` for all trading pair prices, order amounts, and mathematical calculations. Wrap float conversions in strings first.

```python
# ❌ INCORRECT
price = mid_price * 1.01  # Mixing float and Decimal causes TypeError or representation bugs

#   CORRECT
from decimal import Decimal
price = mid_price * Decimal("1.01")
```

---

## 2. Order Flooding in the Event Loop
**The Pitfall:** The `on_tick(self)` method in `ScriptStrategyBase` runs every clock cycle (by default, every **1 second**). If your indicator triggers a buy signal, and you execute `self.buy()` without checking if you already have active orders, the bot will place a new buy order *every second*, creating dozens of unwanted orders.

**The Fix:** Check `self.active_order_ids` or check state trackers before initiating orders.

```python
# ❌ INCORRECT
def on_tick(self):
    if self.indicator_value < 30:
        self.buy(...)  # Will place an order every second!

#   CORRECT
def on_tick(self):
    # Only place orders if we have no active orders in flight
    if len(self.active_order_ids) > 0:
        return
        
    if self.indicator_value < 30:
        order_id = self.buy(...)
        self.active_order_ids.append(order_id)
```

---

## 3. Ignoring Market Data Readiness
**The Pitfall:** When the bot starts, the connection to exchange websocket candles, order books, and balances takes a few seconds to synchronize. If your code tries to access `self.candles.candles_df` or `self.connectors[...].get_mid_price(...)` immediately, the data may be empty, or return `NaN`, causing a Python exception that crashes the bot.

**The Fix:** Always verify market feeds are fully synchronized before running indicator mathematics or signals.

```python
#   CORRECT
def on_tick(self):
    # 1. Check if candles feed is fully initialized
    if not self.candles.is_ready:
        return
        
    # 2. Check if price data is valid
    mid_price = self.connectors[self.connector_name].get_mid_price(self.trading_pair)
    if mid_price.is_nan():
        return
```

---

## 4. API Rate Limit Bans (HTTP 429)
**The Pitfall:** Placing, modifying, or cancelling orders continuously triggers exchange rate limit guards. If your bot cancels and places orders every second, the exchange will block your API key or IP address (HTTP 429 / IP Ban).

**The Fix:** Implement cooldown periods (e.g. at least 30–60 seconds between order modifications) or use Strategy V2's Position Executors which naturally manage order rates.

```python
#   CORRECT
def on_tick(self):
    current_time = self.current_timestamp
    if current_time - self.last_trade_timestamp < self.cooldown_seconds:
        return  # Cooldown active
```

---

## 5. Unhandled Exceptions
**The Pitfall:** If your code raises an unhandled exception inside `on_tick()` (e.g. `ZeroDivisionError` when calculating volatility, or `KeyError` when querying balances), the Hummingbot script execution thread will terminate. If you have active positions open, they will be left unmanaged (no stop loss/take profit will be active).

**The Fix:** Wrap indicator math and dictionary fetches in try-except blocks. Log errors rather than letting the thread crash.

```python
#   CORRECT
try:
    df = self.candles.candles_df
    # calculate indicators safely...
except Exception as e:
    self.logger().error(f"Error calculating indicators: {str(e)}")
    return
```

# Telemetry & UI Integration Specification

This document details the standard JSON schemas used to stream live visual telemetry to the Cockpit UI (`http://localhost:3000`) and manage strategy execution states.

---

## 🛰️ 1. Cockpit Telemetry Protocol (WebSocket / IPC)

The AI agent dispatches updates to the Cockpit frontend via server API calls or IPC events using structured payloads:

```json
{
  "event": "UPSERT_WIDGET",
  "data": {
    "widget_id": "strategy_leaderboard",
    "type": "table",
    "payload": {
      "headers": ["Strategy", "Sharpe", "MaxDD", "DSR", "Status"],
      "rows": [
        ["Alpha_MeanReversion_V1", 2.14, "4.2%", 0.98, "ACTIVE"],
        ["Trend_Follower_Gen3", 1.85, "6.1%", 0.96, "TESTING"]
      ]
    }
  }
}
```

---

## 📈 2. Strategy Lifecycle Telemetry

When registering or updating a strategy in `StrategyManager`:

```json
{
  "strategy_id": "generic_quant_alpha_01",
  "name": "Adaptive Momentum Volatility Expansion",
  "timeframe": "15m",
  "symbol": "BTCUSDT",
  "metrics": {
    "sharpe": 2.15,
    "max_drawdown_pct": 3.8,
    "dsr_score": 0.97,
    "win_rate_pct": 58.4,
    "profit_factor": 1.92
  },
  "cynic_audit": {
    "friction_passed": true,
    "dsr_passed": true,
    "regimes_passed": true,
    "noise_passed": true,
    "parameters_passed": true
  },
  "status": "PROMOTED"
}
```

---

## 📱 3. Telegram & Signal Broadcast Payload

Signals broadcast to Telegram subscribers follow this unified format:

```
🚀 [NUJIN SIGNAL] BTCUSDT (15m)
Direction: LONG | Entry: $65,420.00
Stop Loss: $64,800.00 (Risk: 0.95%)
Target 1: $66,500.00 | Target 2: $67,800.00
Confidence / DSR: 0.97
Strategy: Adaptive Volatility Expansion
```

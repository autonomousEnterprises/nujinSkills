# Reference: UI Management & Dynamic Viewport Control

## Overview
The NujinSkill web terminal runs on a 100vw / 100vh layout featuring two primary screens:
1. **Screen 1 (Lightweight Chart Canvas):** TradingView Lightweight Charts displaying OHLCV candlesticks, signal markers, stop-loss lines, and take-profit lines.
2. **Screen 2 (Agent Audit Deck):** Server-Driven UI widget grid displaying live DSR scores, parameter stability heatmaps, edge thesis logs, and Telegram push history.

---

## Viewport Hotkey Control
- Press **`Ctrl + Space`** or **`Tab`** or **`F1/F2`** to instantly swap focus between Screen 1 and Screen 2.

---

## Agent UI Dispatch Commands
Equip the AI agent with tools to dynamically update the UI during mining:
- `python tools/ui_dispatcher.py --event UPSERT_WIDGET --payload '<JSON>'`
- `python tools/ui_dispatcher.py --event CHART_MARKER --payload '<JSON>'`

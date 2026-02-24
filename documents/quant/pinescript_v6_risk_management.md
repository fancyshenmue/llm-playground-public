# Pine Script® v6: Advanced Risk Management Patterns

This document provides patterns for multi-stage exits, tiered profit taking, and dynamic position sizing.

## 💰 1. Tiered Profit Taking (Partial Exits)
To exit a position in stages (e.g., 50% at TP1, 50% at TP2), use the `qty_percent` parameter in `strategy.exit`.

```pine
if strategy.position_size > 0
    // Stage 1: Close 50% of position at 5% profit
    tp1_ticks = math.round((strategy.position_avg_price * 0.05) / syminfo.mintick)
    strategy.exit("TP1", from_entry="Long", qty_percent=50, profit=tp1_ticks)

    // Stage 2: Close remaining 50% at 10% profit
    tp2_ticks = math.round((strategy.position_avg_price * 0.10) / syminfo.mintick)
    strategy.exit("TP2", from_entry="Long", qty_percent=100, profit=tp2_ticks)
```

## 📏 2. Risk-Based Position Sizing
Calculating quantity based on a fixed dollar risk per trade.

```pine
risk_per_trade = input.float(100.0, "Risk in USD per Trade")
stop_dist = ta.atr(14) * 2
// Calculate qty: risk / distance
pos_size = risk_per_trade / stop_dist
strategy.entry("RiskEntry", strategy.long, qty=pos_size)
```

## 📉 3. Dynamic Trailing based on Volatility (ATR Trail)
```pine
atrWindow = input.int(14, "ATR Window")
atrMult = input.float(3.0, "ATR Multiplier")

atrVal = ta.atr(atrWindow)
trailTicks = math.round((atrVal * atrMult) / syminfo.mintick)

if strategy.position_size > 0
    strategy.exit("ATR Trail", from_entry="Long", trail_price=close, trail_offset=trailTicks)
```

## ⚠️ Risk Execution Rules for v6:
1. **`strategy.position_avg_price`**: Always use this for calculating profit/loss distances for active trades.
2. **`strategy.close` vs `strategy.exit`**: Use `close` for signal-based exits (e.g., "Exit when RSI > 70") and `exit` for price-based exits (SL/TP/Trail).
3. **Pyramiding**: If `pyramiding` is enabled in `strategy()`, ensure `strategy.exit` IDs are unique or managed to avoid overlapping orders.

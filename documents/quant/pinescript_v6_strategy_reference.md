# Pine Script® v6: Strategy & Execution Reference (strategy.*)

This document details the strategy functions and risk management parameters for Pine Script v6.

## 🏁 1. Strategy Declaration
```pine
strategy(title, shorttitle, overlay, initial_capital, default_qty_type, default_qty_value, commission_type, commission_value, margin_long, margin_short)
```
- **`default_qty_type`**: `strategy.fixed`, `strategy.cash`, `strategy.percent_of_equity`.
- **`margin_long` / `margin_short`**: Set to `0` to disable margin calls (v5 behavior).

## 📥 2. Entering Positions
```pine
strategy.entry(id, direction, qty, limit, stop, comment)
```
- **`direction`**: **MUST** be `strategy.long` or `strategy.short`.
- **⚠️ VOID HALLUCINATION**: Do **NOT** use `long=true`, `short=true`, or `direction="long"`. These will crash.
- **`stop` / `limit`**: These are entry prices (Stop-limit or Limit orders).
- **⚠️ Note**: `loss` and `profit` parameters are REMOVED from `strategy.entry`. Use `strategy.exit` for SL/TP.

## 📤 3. Exiting Positions
### Simple Exit (SL/TP)
```pine
strategy.exit(id, from_entry, profit, loss, limit, stop)
```
- **`profit` / `loss`**: Distance from entry in **TICKS** (must divide price by `syminfo.mintick`).
- **`limit` / `stop`**: Absolute **PRICE** values.

### Trailing Stop (Mandatory Pairs)
```pine
strategy.exit(id, from_entry, trail_price, trail_points, trail_offset)
```
- **⚠️ CRITICAL RULE**: `trail_offset` **CANNOT** be used alone.
- It MUST be paired with either **`trail_price`** (absolute price) or **`trail_points`** (distance in ticks).
- **Correct Pattern**: `strategy.exit("ID", trail_price=close, trail_offset=tk)`
- **⚠️ Warning**: If you want 8% trailing stop, calculate `tk = math.round((close * 0.08) / syminfo.mintick)` and use `trail_offset = tk`.

## 🛑 4. Closing Positions
- **`strategy.close`**: Closes a specific entry by ID.
- **`strategy.close_all`**: Closes all current positions.

## 📊 5. Strategy State Variables
- **`strategy.position_size`**: Current position size (positive for long, negative for short, 0 for flat).
- **`strategy.equity`**: Current total equity.
- **`strategy.openprofit`**: Current unrealized PnL.
- **`strategy.closedtrades`**: Total number of completed trades.

## 🚫 6. Removed in v6
- **`when` parameter**: Deleted from all strategy functions. Use `if` statements.
- **`strategy.risk.max_drawdown`**: No longer supported in the same way; monitor `strategy.equity` manually if needed.

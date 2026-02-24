# Pine Script v6: The Comprehensive Reference (Bible)

This document is the **Ground Truth** for Pine Script v6 generation. It overrides any general knowledge about previous versions.

## 🏁 1. Core Syntax & Lifecycle
- **Version Flag**: Always start with `//@version=6`.
- **Boilerplate**:
  - Indicators: `indicator("Name", overlay=true)`
  - Strategies: `strategy("Name", overlay=true, margin_long=0, margin_short=0)`
- **Variables**:
  - `var`: Initialized once, persists across bars. Use for totals, entry prices, or states.
  - `varip`: Persists within the same bar across real-time updates (Intrabar).
- **Boolean Logic**:
  - `bool` are strictly `true` or `false`. No `na`.
  - Implicit casting (e.g., `if volume`) is FORBIDDEN. Use `if volume > 0`.
  - Short-circuiting: `and` / `or` are lazy-evaluated.

## 🛠️ 2. Namespaces & Functions
Nearly all built-in functions require a namespace prefix.
- **`ta.` (Technical Analysis)**: `ta.sma()`, `ta.ema()`, `ta.rsi()`, `ta.macd()`, `ta.atr()`, `ta.stoch()`, `ta.bb()`, `ta.dmi()`, `ta.barssince()`, `ta.highest()`, `ta.lowest()`, `ta.cross()`, `ta.crossover()`, `ta.all()`, `ta.any()`.
- **`math.` (Math Operations)**: `math.sum()`, `math.abs()`, `math.max()`, `math.min()`, `math.round()`.
- **`request.` (Data Requests)**: `request.security()`.
- **`strategy.` (Execution)**: `strategy.entry()`, `strategy.exit()`, `strategy.close()`, `strategy.cancel()`, `alert()`.
- **`input.` (User Inputs)**: `input.int()`, `input.float()`, `input.string()`, `input.bool()`.

## 📡 3. Multi-Timeframe (MTF) Data
- **Dynamic Security**: `request.security()` can now be called inside `if` blocks and loops.
- **Tuple Fetching**: Best practice is to fetch multiple variables in one call:
  `[dHigh, dLow, dClose] = request.security(syminfo.tickerid, "D", [high, low, close])`
- **Timeframe Format**: Always includes multiplier (e.g., `"1D"`, `"4H"`, `"60"`).

## 📉 4. Indicators & Tuples
- **MACD**: Returns `[macdLine, signalLine, histLine]`.
- **Stochastic**: Returns `[k, d]`.
- **Bollinger Bands**: Returns `[middle, upper, lower]`.
- **DMI (DMI/ADX)**: Returns `[diPlus, diMinus, adx] = ta.dmi(14, 14)`.

## 🛡️ 5. Strategy Execution Rules
- **Entry**: `strategy.entry("ID", strategy.long)`
- **Exit**: `strategy.exit("ID", from_entry="Long", profit=targetTicks, loss=stopTicks, trail_price=close, trail_offset=offsetTicks)`
- **Trailing Stop**: Must pair `trail_price` with `trail_offset`. Offset MUST be in **ticks**, not price.
- **Tick Conversion**: `ticks = math.round(price_distance / syminfo.mintick)`.
- **Timed Exits**: Use `bar_index - strategy.opentrades.entry_bar_index(0)` to count bars in trade.

## ❌ 6. Blacklist (NEVER USE)
- `ta.volume()` -> Use `volume`.
- `ta.average()` -> Use `ta.sma()`.
- `ta.percentile()` -> Use `ta.percentrank()`.
- `ta.adx()` -> Use `ta.dmi()`.
- `security()` -> Use `request.security()`.
- `request.request.security()` -> Hallucination. Use `request.security()`.
- `input()` -> Use `input.int()` or `input.float()`.
- `&&`, `||` -> Use `and`, `or`.
- `strategy.closedtrades.exit_bar()` -> Hallucination.
- Call `ta.*()` inside conditionals -> MUST pre-calculate.
- Missing `alert_message` in strategy calls -> Mandatory for automation.

## 🔔 7. Alerts & Automation
- **`alert()` Function**: Use for UI notifications and logging.
  - Usage: `alert("Message", alert.freq_once_per_bar)`
- **`alert_message` Parameter**: Essential for Webhook automation. Include in all `strategy.*` calls.
  - Format: Use JSON-like strings for compatibility.
  - Example: `strategy.entry("L", strategy.long, alert_message='{"action": "long", "ticker": "' + syminfo.ticker + '"}')`
- **Dynamic Messages**: Combine strings and variables using `str.tostring()`.
  - Example: `alert("Price hit " + str.tostring(close), alert.freq_once_per_bar)`

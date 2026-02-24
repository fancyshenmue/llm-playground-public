# Pine Script® v6: PITFALLS & BLACKLIST (ULTRA-CRITICAL)

### 🚨 GOD-TIER BLACKLIST (NEVER USE OR YOU WILL CRASH)
1.  **`ta.volume()`** -> **❌ FATAL ERROR**. It is NOT a function. Use RAW `volume`.
2.  **`ta.close()`** -> **❌ FATAL ERROR**. It is NOT a function. Use RAW `close`.
3.  **`ta.average()`** -> **❌ DOES NOT EXIST**. ALWAYS use `ta.sma()`.
4.  **`{ }` (Braces)** -> **❌ FATAL ERROR**. Use INDENTATION (4 spaces) only.
5.  **`long=true`** -> **❌ FAKE PARAMETER**. Use `strategy.long`.
6.  **`&&` and `||`** -> **❌ C-STYLE OPERATORS**. Use `and` and `or`.
7.  **`typ`** -> **❌ INVALID KEYWORD**. Use type inference or valid qualifiers: `var`, `const`, `simple`, `series`.
8.  **`security()`** -> **❌ DEPRECATED**. Use `request.security()` (v6 renamed function).
9.  **Variables starting with numbers** -> **❌ SYNTAX ERROR**. Use `h4Stoc`, `hourly4`, NOT `4HStoc`, `1hMA`.
10. **`strategy.exit(profit=price_value)`** -> **❌ WRONG TYPE**. Must convert to ticks: `math.round(price / syminfo.mintick)`.
11. **`then` and `endif`** -> **❌ NOT PINE SCRIPT**. Use indentation only: `if condition\n    code` (NO then, NO endif).
12. **`ta.macd(close, fastLength=12, ...)`** -> **❌ WRONG PARAMS**. Use positional: `ta.macd(close, 12, 26, 9)`.
13. **`ta.candlestick.engulfing()`** -> **❌ DOES NOT EXIST**. Manually code patterns: `close > open and close[1] < open[1]...`.
14. **`if volume > 2 * ta.sma(volume, 20)`** -> **❌ DON'T CALL IN CONDITIONS**. Pre-calculate: `volAvg = ta.sma(volume, 20)` then `if volume > 2 * volAvg`.
15. **`entryPrice` for R-based exits** -> Must track with: `var float entryPrice = na` then `entryPrice := strategy.position_avg_price`.
16. **`stochK, stochD = ta.stoch(...)`** -> **❌ WRONG**. `ta.stoch()` returns SINGLE value. Use: `stochK = ta.stoch(close, high, low, 14)` then `stochD = ta.sma(stochK, 3)`.
17. **`not strategy.position_size > 0`** -> **❌ AMBIGUOUS SYNTAX**. Use explicit parentheses or rewrite: `strategy.position_size == 0` or `not (strategy.position_size > 0)`.
18. **`ta.atr(close, 14)`** -> **❌ WRONG PARAMETERS**. `ta.atr()` takes ONLY the length parameter. Use: `ta.atr(14)` (it automatically uses high, low, close).
19. **`request.request.security()`** -> **❌ DOUBLE NAMESPACE**. Use only ONE `request.`: `request.security()`.
20. **`macd, signal, hist = ta.macd(...)`** -> **❌ SYNTAX ERROR**. Tuples MUST be enclosed in square brackets: `[macd, signal, hist] = ta.macd(...)`.
21. **`ta.adx(14)`** -> **❌ DOES NOT EXIST**. Use `ta.dmi()` with TWO parameters and correct order: `[diPlus, diMinus, adx] = ta.dmi(14, 14)`.
22. **`condition for 3 bars`** -> **❌ NATURAL LANGUAGE LEAK**. Pine Script uses `ta.all()`: `condMatched = ta.all(close > open, 3)`.
23. **`val != na` or `val == na`** -> **❌ SYNTAX ERROR**. You CANNOT compare with `na` directly. Use functions: `not na(val)` or `na(val)`.
24. **`strategy.closedtrades.exit_bar()`** -> **❌ FATAL HALLUCINATION**. This method does not exist. For "after X bars" exits, use: `bar_index - strategy.opentrades.entry_bar_index(0) >= 5`.
25. **`[upper, lower] = ta.bb(...)`** -> **❌ TUPLE SIZE MISMATCH**. `ta.bb()` returns THREE values: `[middle, upper, lower]`. Use: `[_, upper, lower] = ta.bb(...)`.
26. **`barssince(...)`, `highest(...)`, `sma(...)`** -> **❌ MISSING NAMESPACE**. Most technical analysis functions REQUIRE the `ta.` prefix: `ta.barssince(...)`, `ta.highest(...)`, `ta.sma(...)`.
27. **`ta.percentile(src, 10, 100)`** -> **❌ DOES NOT EXIST**. To check if a value is in the bottom 10%, use `ta.percentrank(src, 100) < 10`.
28. **`and` / `or` at end of line** -> **❌ POTENTIAL SYNTAX ERROR**. Pine Script v6 can be picky about line continuation. Avoid splitting lines at `and` / `or` unless indented exactly 4 spaces. Better: Keep logical conditions on one line.
29. **`ta.vwma()` vs `ta.vwap`** -> **❌ WRONG FUNCTION**. `ta.vwma()` is a Volume Weighted Moving Average. For standard anchored VWAP, use `ta.vwap(close)`.
30. **`ta.valuewhen(src, 1)`** -> **❌ WRONG PARAMETERS**. `ta.valuewhen` expects `(condition, source, occurrence)`. If you want "source value 1 bar ago", use `src[1]`.
31. **`.security(...)`** -> **❌ MISSING NAMESPACE**. Never start a line with `.security`. Always use `request.security(...)`.
32. **`atr`, `* atr`, `0 = ...`** -> **❌ NATURAL LANGUAGE LEAK**. This is NOT code. Always assign logic to valid variable names: `atrVal = ta.atr(14)`.
33. **`request.security(..., strategy.position_avg_price)`** -> **❌ FATAL ERROR**. Strategy-specific variables (starting with `strategy.*`) CANNOT be used inside `request.security()`. Use them directly: `entryPrice = strategy.position_avg_price`.
34. **`request.request.security(...)`** -> **❌ DOUBLE NAMESPACE**. This is a common hallucination. Always use exactly one level of namespace: `request.security(...)`.



---

## 🛑 1. VARIABLE VS FUNCTION (THE #1 AI ERROR)
The most common mistake is treating price variables as functions.
- **❌ WRONG**: `if ta.volume() > 100`, `ta.close()`, `ta.open()`
- **✅ CORRECT**: `if volume > 100`, `close`, `open`

## 🛑 2. NAMESPACE MANDATES
Nearly all logic requires `ta.`, `math.`, `strategy.`, or `input.`.
- **SUM**: Use `math.sum(volume, 20)`, **NOT** `ta.sum`.
- **INDICATORS**: Always `ta.sma()`, `ta.rsi()`, `ta.ema()`.

## 🛑 3. ASSIGNMENT SYNTAX
Pine Script v6 is strict about variable declaration.
- **INITIAL**: Use `val = close` (Level 0).
- **MUTATION**: Use `val := close` inside local blocks.
- **TYPES**: Use `float val = 0.0` or `int val = 0` for clarity.

## 🛑 4. NO CURLY BRACES
AI often generates `{ }` for `if` blocks. This is a syntax error.
- **❌ WRONG**:
```pine
if cond {
    strategy.entry("L", strategy.long)
}
```
- **✅ CORRECT**:
```pine
if cond
    strategy.entry("L", strategy.long)
```
**MANDATORY**: Blocks are defined by exactly 4 spaces or 1 tab of indentation.

## 🛑 5. STRATEGY EXITS (TRAILING STOP)
`trail_offset` REQUIRES `trail_price`.
```pine
strategy.exit("Ex", from_entry="L", trail_price=close, trail_offset=ticks)
```

## 🛑 6. ALERT PITFALLS
1.  **Missing `alert_message`**: If you use a Webhook, TradingView ONLY sends the `alert_message`. If empty, your bot gets nothing.
2.  **`alert()` vs `alertcondition()`**: `alertcondition()` is deprecated for strategies. ALWAYS use `alert()` and `alert_message`.
3.  **JSON Quotes**: Use single quotes for the Pine string to avoid escaping double quotes in JSON.
    - **✅ CORRECT**: `alert_message='{"action": "buy"}'`

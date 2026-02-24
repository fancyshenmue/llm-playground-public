# Pine Script® v6: RAG Grounding Cheat Sheet

## 🚨 CRITICAL SYNTAX RULES
- **VERSION**: Must start with `//@version=6`.
- **STRATEGY HEADER**: Must use **`strategy("Name", overlay=true)`**.
- **ENTRY**: `strategy.entry("ID", strategy.long)` or `strategy.entry("ID", strategy.short)`.
- **NO CURLY BRACES**: Use INDENTATION (4 spaces) for all blocks.
- **NO ta.volume()**: Use the variable `volume` directly.
- **NO ta.close()**: Use the variable `close` directly.
- **NO ta.average()**: Use the function `ta.sma()`.

## 📐 MANDATORY PATTERNS (COPY-PASTE)

### Trailing Stop (ALWAYS use this exact pattern):
```pine
stopPercent = input.float(8.0, "Stop %")
stopTicks = math.round((close * (stopPercent / 100)) / syminfo.mintick)
strategy.exit("Exit", from_entry="Long", trail_price=close, trail_offset=stopTicks)
```

### Profit/Loss Targets (ALWAYS convert to ticks):
```pine
// CORRECT: Convert ATR to ticks
profitTicks = math.round((1.5 * ta.atr(14)) / syminfo.mintick)
strategy.exit("TP", "Long", profit=profitTicks)

// WRONG: Never use price values directly
// strategy.exit("TP", "Long", profit=1.5 * ta.atr(14))  ❌ FATAL ERROR
```

## 📊 VOLUME ANALYSIS PATTERN
```pine
volMA = ta.sma(volume, 20)
isLowVol = volume < volMA * 0.5
```

## 🏗️ SCOPE RULES
- **LEVEL 0**: `input.*`, `ta.*` (indicator declarations), `var`.
- **LOCAL**: `strategy.entry`, `strategy.exit`, updates using `:=`.

## ❌ BLACKLIST (IMMEDIATE CRASH)
  - `ta.volume()` (Use: `volume`)
  - `ta.close()` (Use: `close`)
  - `ta.average()` (Use: `ta.sma()`)
  - `input()` (Use: `input.int()` or `input.float()`)
  - `{ }` (Curly Braces): Use indentation only.
  - `&&` and `||`: Use `and` and `or`
  - `typ`: Not a keyword. Use type inference or `var`, `const`, `simple`, `series`
  - `security()`: DEPRECATED. Use `request.security()`
  - Variable names starting with numbers: Use `h4Stoc`, NOT `4HStoc`
  - `then` and `endif`: NOT Pine Script keywords. Use indentation only.
  - Named parameters in `ta.macd()`: Use positional args: `ta.macd(close, 12, 26, 9)`
  - `ta.candlestick.*()` functions: DO NOT EXIST. Code patterns manually.
  - `not strategy.position_size > 0`: AMBIGUOUS. Use `strategy.position_size == 0` or `not (strategy.position_size > 0)`.
  - `ta.atr(close, 14)`: WRONG. Use `ta.atr(14)` - takes only length parameter.


## 📊 TECHNICAL INDICATORS (CORRECT USAGE)

### MACD (ALWAYS use positional parameters):
```pine
// ✅ CORRECT
[macdLine, signalLine, histLine] = ta.macd(close, 12, 26, 9)
isPositiveMacd = histLine > 0 and histLine > histLine[1]

// ❌ WRONG - Named parameters not supported
// macd = ta.macd(close, fastLength=12, slowLength=26, signalLength=9)
```

### Stochastic (Returns single value, NOT array):
```pine
// ✅ CORRECT - Returns K line only
stochK = ta.stoch(close, high, low, 14)
stochD = ta.sma(stochK, 3)  // D is SMA of K

// Check for oversold crossover
isOversoldCross = stochK < 20 and stochK > stochK[1]

// ❌ WRONG - Cannot destructure
// stochK, stochD = ta.stoch(high, low, close, 14, 3)
```

### ADX / DMI (Average Directional Index):
```pine
// ✅ CORRECT - Use ta.dmi() with 2 params and correct order [+DI, -DI, ADX]
[diPlus, diMinus, adxLine] = ta.dmi(14, 14) // (diLength, adxSmoothing)

// ❌ WRONG - order is [+DI, -DI, ADX], not [ADX, +DI, -DI]
// [adx, diPlus, diMinus] = ta.dmi(14, 14)
```

### Sequential Conditions (Consecutive bars):
```pine
// ✅ CORRECT - Use ta.all(condition, length)
isExhausted = ta.all(volume < volume[1], 3) // Volume lower for 3 consecutive bars

// ❌ WRONG - Natural language leak
// isExhausted = volume < volume[1] for 3 bars
```

### Correct NaN Handling:
```pine
// ✅ CORRECT - Use na() and not na()
isDefined = not na(pivotHigh)
if na(entryPrice)
    entryPrice := close

// ❌ WRONG - Direct comparison
// if val != na
// if val == na
```

### Timed Exits (Exit after X bars):
```pine
// ✅ CORRECT - Use strategy.opentrades.entry_bar_index(0)
inTrade = strategy.position_size != 0
barsInTrade = inTrade ? bar_index - strategy.opentrades.entry_bar_index(0) : 0
if barsInTrade >= 5
    strategy.close("Long", comment="Timed Exit")

// ❌ WRONG - strategy.closedtrades.exit_bar() DOES NOT EXIST
```

### Bollinger Bands (3 return values):
```pine
// ✅ CORRECT - Use 3 variables [middle, upper, lower]
[mid, upper, lower] = ta.bb(close, 20, 2.0)

// ❌ WRONG - Left side has 2 but right side has 3
// [upper, lower] = ta.bb(close, 20, 2.0)
```

### ATR (Average True Range - ONLY accepts length parameter):
```pine
// ✅ CORRECT - Only pass the period length
atrValue = ta.atr(14)  // Automatically uses high, low, close

// Use for dynamic stops
stopDistance = 2.0 * atrValue
profitTicks = math.round(stopDistance / syminfo.mintick)

// ❌ WRONG - ATR does not accept price argument
// atrValue = ta.atr(close, 14)
```

### Mandatory Namespaces:
```pine
// ✅ CORRECT - ALWAYS use ta. for tech analysis
val1 = ta.barssince(condition)
val2 = ta.highest(high, 50)
val3 = ta.sma(close, 20)

// ❌ WRONG - Pine v6 is strict
// val = barssince(condition)
```

### Percentile / Rank:
```pine
// ✅ CORRECT - Use ta.percentrank() to find relative standing
// Check if current bandwidth is in the bottom 10% of last 100 bars
bandwidthRank = ta.percentrank(bandwidth, 100)
isSqueezed = bandwidthRank < 10

// ❌ WRONG - ta.percentile() does not exist
```

### Candlestick Patterns (NO built-in functions, code manually):
```pine
// Bullish Engulfing Pattern
bullishEngulfing = close > open and close[1] < open[1] and
                   close > open[1] and open < close[1]

// Hammer Pattern
hammer = (high - low) > 3 * (close - open) and
         (close - low) / (0.001 + high - low) > 0.6 and
         (open - low) / (0.001 + high - low) > 0.6
```

### VWAP (Volume Weighted Average Price):
```pine
// ✅ CORRECT - Use ta.vwap()
vwapValue = ta.vwap(close)

// ❌ WRONG - Confusing with moving average
// vwapValue = ta.vwma(close, 14)
```

### Line Continuation:
```pine
// ✅ CORRECT - Keep logical conditions on one line for stability
longCondition = condition1 and condition2 and condition3

// ❌ RISKY - Splitting lines can trigger "end of line without line continuation"
// longCondition = condition1 and
//                 condition2
```

### History Access (Previous values):
```pine
// ✅ CORRECT - Use square brackets
prevClose = close[1]
prevHigh = high[2]

// ❌ WRONG - Confusing with ta.valuewhen
// prevClose = ta.valuewhen(close, 1)
```

### MTF Security Prefix:
```pine
// ✅ CORRECT - ALWAYS prefix with request.
dailyRsi = request.security(syminfo.tickerid, "D", ta.rsi(close, 14))

// ❌ WRONG - Missing namespace or leading dot
// dailyRsi = security(...)
// dailyRsi = .security(...)
```

### Entry Price Tracking:
```pine
// ✅ CORRECT - Use the built-in variable directly
entryPrice = strategy.position_avg_price

// ❌ FATAL ERROR - Wrapping in request.security
// entryPrice = request.security(syminfo.tickerid, "1", strategy.position_avg_price)
```

### Entry Price Tracking (Manual for R-based exits):
```pine
// Declare at top of script
var float entryPrice = na

// Update on entry
if longCondition
    strategy.entry("Long", strategy.long)
    entryPrice := close

// Use for R-based exits
if strategy.position_size > 0
    if (close - entryPrice) / entryPrice >= 0.015  // 1.5R if risk was 1%
        strategy.exit("TP", "Long", qty_percent=50)
```

### Boolean Negation (Position Checks):
```pine
// ✅ CORRECT - Clear and unambiguous
if longCondition and strategy.position_size == 0
    strategy.entry("Long", strategy.long)

// ✅ CORRECT - Using explicit parentheses
if longCondition and not (strategy.position_size > 0)
    strategy.entry("Long", strategy.long)

// ❌ WRONG - Ambiguous operator precedence
// if longCondition and not strategy.position_size > 0
```

> [!IMPORTANT]
> **Never call `ta.*()` functions inside `if` conditions!** Always pre-calculate:
> ```pine
> // ❌ WRONG
> if volume > 2 * ta.sma(volume, 20)
>
> // ✅ CORRECT
> volAvg = ta.sma(volume, 20)
> if volume > 2 * volAvg
> ```

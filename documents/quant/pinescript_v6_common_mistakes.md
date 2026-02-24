# Pine Script v6: COMMON MISTAKES TO AVOID

> [!CAUTION]
> **This document lists the MOST FREQUENT ERRORS made by AI code generators.** Every mistake listed here WILL cause your strategy to fail compilation or produce incorrect results.

---

## 🚨 CRITICAL ERROR #1: Calling `ta.*()` Functions Inside Conditionals

### ❌ WRONG - DO NOT DO THIS:
```pine
// FATAL ERROR - ta.sma() might not execute on every bar
if volume > 2 * ta.sma(volume, 20)
    strategy.entry("Long", strategy.long)

// FATAL ERROR - ta.atr() in conditional
if close > open and ta.atr(14) > 1.0
    strategy.entry("Long", strategy.long)
```

### ✅ CORRECT - ALWAYS DO THIS:
```pine
// Pre-calculate ALL ta.* functions BEFORE the if statement
volAvg = ta.sma(volume, 20)
atrValue = ta.atr(14)

// Now use the variables in conditions
if volume > 2 * volAvg
    strategy.entry("Long", strategy.long)

if close > open and atrValue > 1.0
    strategy.entry("Long", strategy.long)
```

### Why This Matters:
Pine Script's execution model requires `ta.*()` functions to execute on EVERY bar for consistency. When placed inside `if` statements, they might not execute on every bar, causing:
- Inconsistent calculations
- Compilation errors
- Unpredictable strategy behavior

### **MANDATORY RULE**:
**Calculate FIRST, Compare SECOND. Never combine them.**

---

## 🚨 CRITICAL ERROR #2: `ta.candlestick.*()` Functions DO NOT EXIST

### ❌ WRONG - THESE FUNCTIONS ARE IMAGINARY:
```pine
// DOES NOT EXIST
bullish = ta.candlestick.engulfing(close, open)

// DOES NOT EXIST
hammer = ta.candlestick.hammer(high, low, open, close)

// DOES NOT EXIST
doji = ta.candlestick.doji()
```

### ✅ CORRECT - MANUAL PATTERN IMPLEMENTATION:
```pine
// Bullish Engulfing - Must code manually
bullishEngulfing = close > open and           // Current candle bullish
                   close[1] < open[1] and     // Previous candle bearish
                   close > open[1] and        // Engulfs previous body
                   open < close[1]

// Hammer - Must code manually
bodySize = math.abs(close - open)
lowerWick = math.min(open, close) - low
upperWick = high - math.max(open, close)
hammer = lowerWick > bodySize * 2 and upperWick < bodySize
```

---

## 🚨 CRITICAL ERROR #3: MACD Array Destructuring

### ❌ WRONG:
```pine
// Missing third element
[macdLine, signalLine] = ta.macd(close, 12, 26, 9)

// Using named parameters (not supported)
macd = ta.macd(close, fastLength=12, slowLength=26, signalLength=9)
```

### ✅ CORRECT:
```pine
// MUST have ALL THREE elements
[macdLine, signalLine, histLine] = ta.macd(close, 12, 26, 9)

// Use positional parameters ONLY
isPositive = histLine > 0 and histLine > histLine[1]
```

---

## 🚨 CRITICAL ERROR #4: Stochastic Returns Single Value, Not Array

### ❌ WRONG:
```pine
// ta.stoch() does NOT return an array
stochK, stochD = ta.stoch(high, low, close, 14, 3)

// Wrong parameter order
stoch = ta.stoch(close, 14, high, low)
```

### ✅ CORRECT:
```pine
// ta.stoch() returns ONLY the K line (single value)
stochK = ta.stoch(close, high, low, 14)

// If you need D line, calculate manually as SMA of K
stochD = ta.sma(stochK, 3)

// Check crossover
isStochCross = ta.crossover(stochK, 20)
```

### Correct Syntax:
```
ta.stoch(source, high, low, length) → series float
```
- Returns: Stochastic K value ONLY
- To get D: Apply SMA to K (`ta.sma(stochK, smoothing)`)

---

## 🚨 CRITICAL ERROR #5: Profit/Loss Parameters Must Be in TICKS

### ❌ WRONG:
```pine
// Using price values directly
strategy.exit("TP", "Long", profit=1.5 * ta.atr(14))
strategy.exit("Exit", "Long", stop=close * 0.02)
```

### ✅ CORRECT:
```pine
// Convert to ticks FIRST
atr = ta.atr(14)
profitTicks = math.round((1.5 * atr) / syminfo.mintick)
stopTicks = math.round((close * 0.02) / syminfo.mintick)

strategy.exit("TP", "Long", profit=profitTicks)
strategy.exit("Exit", "Long", stop=stopTicks)
```

---

## 🚨 CRITICAL ERROR #5: Undeclared Entry Price for R-Based Exits

### ❌ WRONG:
```pine
// entryPrice is not declared anywhere
if (close - entryPrice) / entryPrice >= 0.015
    strategy.exit("TP", qty_percent=50)
```

### ✅ CORRECT:
```pine
// Declare at top of script
var float entryPrice = na

// Update on entry
if longCondition
    strategy.entry("Long", strategy.long)
    entryPrice := close

// Use for exits
if strategy.position_size > 0
    if (close - entryPrice) / entryPrice >= 0.015
        strategy.exit("TP", qty_percent=50)
```

---

## 📋 Quick Reference Checklist

Before finalizing any Pine Script strategy, verify:

- [ ] NO `ta.*()` functions inside `if` conditions (Calculate first!)
- [ ] NO `ta.candlestick.*()` functions (Code patterns manually!)
- [ ] MACD has 3 elements: `[line, signal, hist]`
- [ ] ALL `profit`, `loss`, `stop`, `trail_offset` converted to ticks
- [ ] `entryPrice` declared with `var float entryPrice = na`
- [ ] NO `then` or `endif` keywords (Use indentation only)
- [ ] NO `&&` or `||` (Use `and` and `or`)
- [ ] NO `{ }` curly braces (Use indentation only)
- [ ] NO variables starting with numbers (Use `h4MA` not `4HMA`)
- [ ] Volume as variable (NOT `ta.volume()`)

---

## 💡 Golden Rule

**When in doubt, look at the working examples in `/examples/` directory. They demonstrate CORRECT syntax for all common patterns.**

# Pine Script® v6: Standard Library & Examples (Few-Shot Reference)

This document provides high-quality, bug-free examples to be used as patterns for code generation.

## 🏆 Example 1: Robust Trend Following (EMA Cross + ATR Stop)
```pine
//@version=6
strategy("EMA Cross ATR Stop", overlay=true, initial_capital=100000)

// 1. Indicators (Global Level)
shortEma = ta.ema(close, input.int(50, "Short EMA"))
longEma  = ta.ema(close, input.int(200, "Long EMA"))
atrVal   = ta.atr(14)

// 2. Logic (State-based)
longCond = ta.crossover(shortEma, longEma)
shortCond = ta.crossunder(shortEma, longEma)

// 3. Execution
if longCond
    strategy.entry("Long", strategy.long)

if shortCond
    strategy.entry("Short", strategy.short)

// 4. Trailing Stop (Relative to current price, converted to Ticks)
// This pattern ensures 2.0x ATR trailing stop
stopTicks = math.round((atrVal * 2.0) / syminfo.mintick)
strategy.exit("Exit Long", from_entry="Long", trail_price=close, trail_offset=stopTicks)
strategy.exit("Exit Short", from_entry="Short", trail_price=close, trail_offset=stopTicks)
```

## 🏆 Example 2: RSI Pullback Strategy
```pine
//@version=6
strategy("RSI Pullback", overlay=true, margin_long=0) // 0 margin = v5 behavior

// 1. Indicators
mavg = ta.sma(close, 200)
rsiVal = ta.rsi(close, 14)

// 2. Logic
// Filter: Trading above 200 SMA
// Signal: RSI dips below 30
canLong = close > mavg
rsiLow = rsiVal < 30

if canLong and rsiLow
    strategy.entry("Entry", strategy.long)

// 3. Exit (Fixed 5% Profit, 2% Stop)
tpTicks = math.round((close * 0.05) / syminfo.mintick)
slTicks = math.round((close * 0.02) / syminfo.mintick)
strategy.exit("TP/SL", from_entry="Entry", profit=tpTicks, loss=slTicks)
```

## 🏆 Example 3: Low Volume Exhaustion (Counter-Trend)
```pine
//@version=6
strategy("Low Volume Exhaustion", overlay=true)

// 1. Indicators (Global Level / Pre-calculation)
volMA = ta.sma(volume, 20)
[plus, minus, adxVal] = ta.dmi(14, 14)
lowRef = ta.lowest(low, 50)
highRef = ta.highest(high, 50)
crossDown = ta.crossunder(adxVal, 40)

// 2. Logic (Use pre-calculated variables)
// Exhaustion: Volume is very low compared to average, ADX indicates trend is weakening
isLowVol = volume < volMA * 0.7
isExhausted = adxVal < 20 or (adxVal > 40 and crossDown)
isPriceExtreme = low < lowRef or high > highRef

if isLowVol and isExhausted and isPriceExtreme
    strategy.entry("Long", strategy.long)

// 3. Exit (8% Trailing Stop)
stopTicks = math.round((close * 0.08) / syminfo.mintick)
strategy.exit("ExitLong", from_entry="Long", trail_price=close, trail_offset=stopTicks)
```
```

## 🎯 Key Pattern Checklist:
- **NO UNDEFINED VARIABLES**: Never use `adx2` unless you have a line like `[_, _, adx2] = ta.dmi(14, 14)`.
- All indicators (`ta.*`) are defined at **Level 0**.
- All conditions use `ta.crossover` or `ta.crossunder`.
- All exits convert Price Differences to **Ticks** using `math.round(... / syminfo.mintick)`.
- Version is ALWAYS `//@version=6`.
- `when=` is NEVER used.
- `then` is NEVER used.

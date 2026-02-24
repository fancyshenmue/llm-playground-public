# Pine Script® v6: Technical Analysis Reference (ta.*)

This document provides a reference for the most commonly used technical analysis functions in Pine Script v6. Use this to grounding the AI's technical implementations.

## 📊 1. Moving Averages
- **SMA (`ta.sma`)**: `ta.sma(source, length)` - Simple Moving Average.
- **⚠️ SMA Hallucination**: NEVER use `ta.average()`. It does **NOT** exist. Always use `ta.sma()`.
- **Exponential Moving Average (`ta.ema`)**: `ta.ema(source, length)`
- **Weighted Moving Average (`ta.wma`)**: `ta.wma(source, length)`
- **Volume Weighted Moving Average (`ta.vwma`)**: `ta.vwma(source, length)`
- **Smooth Moving Average (`ta.rma`)**: `ta.rma(source, length)` - Primarily used for RSI/ATR.

## 📈 2. Oscillators & Momentum
- **Relative Strength Index (`ta.rsi`)**: `ta.rsi(source, length)`
- **MACD (`ta.macd`)**: `[macdLine, signalLine, histLine] = ta.macd(source, fastLength, slowLength, signalLength)`
- **Stochastic Oscillator (`ta.stoch`)**: `ta.stoch(source, high, low, length)`
- **Commodity Channel Index (`ta.cci`)**: `ta.cci(source, length)`
- **Momentum (`ta.mom`)**: `ta.mom(source, length)`

## 📐 3. Volatility & Trend
- **Bollinger Bands (`ta.bb`)**: `[basis, upper, lower] = ta.bb(source, length, mult)`
- **Average True Range (`ta.atr`)**: `ta.atr(length)`
- **Directional Movement Index (`ta.dmi`)**: `[plusDI, minusDI, adxVal] = ta.dmi(diLength, adxSmoothing)`
- **Supertrend (`ta.supertrend`)**: `[supertrend, direction] = ta.supertrend(factor, atrPeriod)`

## 🔍 4. Support & Signal Functions
- **Crossover (`ta.crossover`)**: `ta.crossover(source1, source2)` - Returns true if source1 crossed over source2.
- **Crossunder (`ta.crossunder`)**: `ta.crossunder(source1, source2)`
- **Bar Count (`ta.barssince`)**: `ta.barssince(condition)` - Bars since condition was true.
- **Value When (`ta.valuewhen`)**: `ta.valuewhen(condition, source, occurrence)`
- **Highest/Lowest (`ta.highest` / `ta.lowest`)**: `ta.highest(source, length)` / `ta.lowest(source, length)`
- **⚠️ Sliding Window Sum**: Use **`math.sum(source, length)`**, NOT `ta.sum`.

## ⚠️ Important Implementation Notes:
1. **Global Scope**: All `ta.*` functions MUST be called in the global scope (level 0 indentation) if they are to be consumed reliably. Do not call them inside `if` or `for` blocks if the values need to be consistent across bars.
2. **Implicit Variables**: `volume`, `close`, `open`, `high`, `low` are built-in series variables.
3. **Indices**: Use `source[1]` for the previous bar's value.

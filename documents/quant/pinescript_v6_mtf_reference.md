# Pine Script® v6: Advanced Multi-Timeframe (MTF) Analysis

This document covers how to correctly request and process data from different periods/tickers using `request.*` functions in v6.

## 📡 1. Security Request Structure
The `request.security()` function is the primary way to get data from other timeframes.

```pine
// Pattern: Always use 'simple' strings for symbols and timeframes
dailyClose = request.security(syminfo.tickerid, "D", close)
```

## 🚨 2. Avoiding "Repaint" (Lookahead)
To prevent your strategy from "cheating" by seeing future data in backtests, ALWAYS use the `barmerge.lookahead_off` and proper indexing.

```pine
// Recommended safe MTF pattern
higherTF_Close = request.security(syminfo.tickerid, "D", close[1], lookahead=barmerge.lookahead_on)
// Or the standard way:
higherTF_Close_Standard = request.security(syminfo.tickerid, "D", close)
```

## 🔄 3. Accessing Multiple Indicators via Tuples
If you need multiple values from a higher timeframe, request them in a single call to save performance.

```pine
[hEma, hRsi] = request.security(syminfo.tickerid, "240", [ta.ema(close, 20), ta.rsi(close, 14)])
```

## ⚠️ MTF Specific Pitfalls in v6:
1. **Arrays and MTF**: v6 allows passing arrays to `request.security()`, but be careful with memory limits.
2. **Boolean Data**: Remember `bool` cannot be `na` in v6. If a security request returns `na` (e.g., during gaps), use `nz()` or explicit checks for numeric types, but for booleans, ensure a fallback: `isTrending = request.security(...) ?? false`.
3. **Indicator Context**: Indicators requested via `security` should be defined inside the request or pre-calculated carefully.

## 🏆 MTF Trend Filter Pattern
```pine
//@version=6
// 1. Get Daily Trend
isDailyBullish = request.security(syminfo.tickerid, "D", close > ta.ema(close, 200))

// 2. Execution on 1H Chart
if isDailyBullish and ta.crossover(ta.ema(close, 12), ta.ema(close, 26))
    strategy.entry("MTF Long", strategy.long)
```

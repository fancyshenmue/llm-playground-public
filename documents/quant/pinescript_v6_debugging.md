# Pine Script v6: Troubleshooting "No Trades"

If your generated strategy shows no trades in the TradingView Strategy Tester, it is usually due to one of the following reasons.

---

## 1. Indicator Warm-up (Lag)
Pine Script indicators (SMA, EMA, RSI, ATR) require a certain number of bars to start calculating.
- **Example**: An `ta.sma(200)` requires at least 200 bars of data before it returns a value other than `na`.
- **The Fix**: TradingView > Chart Settings > Units > Increase the "Margin" or ensure your chart has enough historical data loaded.
- **AI Tip**: `llm-utils` now uses a default `--limit 50`, but for long-period indicators (e.g., 200 EMA), you should increase this manually using `--limit 250`.

## 2. Over-Constrained Logic
If you have too many "AND" conditions, the entry signal may never trigger in the small window of data provided.
- **Example**: `if trending and oversold and low_volatility and is_tuesday`
- **The Fix**: Simplify the logic. Start with just one or two conditions to see if trades appear, then add complexity back.

## 3. Scale & Precision (Ticks)
For `strategy.exit`, if the `profit` or `loss` parameters are too small or not converted to ticks, the order might be rejected or never hit.
- **Check**: Look for "Invalid parameters" errors in the Pine Editor console.
- **The Fix**: Always use `math.round(price_distance / syminfo.mintick)` as taught in the [Common Mistakes Guide](file://$HOME/dev/llm-playground/documents/quant/pinescript_v6_common_mistakes.md).

## 4. How to Debug (The `plot` Method)
The fastest way to see why a strategy isn't trading is to plot your conditions.

```pine
// Add this to the bottom of your script
plot(longCondition ? 1 : 0, "Long Signal", color=color.green, style=plot.style_columns)
plot(ta.sma(close, 200), "EMA 200", color=color.red)
```

- If the line for `EMA 200` doesn't appear on the chart, it's returning `na` (Warm-up issue).
- If the `Long Signal` columns never appear, your entry logic is too strict.

## 5. Multi-Timeframe (MTF) Alignment
If your strategy uses `request.security()`, ensure the higher timeframe has enough data. 1 week of data on a 1D chart is only 7 bars—not enough for a 14-period RSI.

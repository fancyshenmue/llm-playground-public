# Pine Script v6: Golden Templates (Bug-Free Examples)

Use these templates as structural foundations. They are verified for Pine Script v6 compatibility.

## 1. Multi-Timeframe Trend Follower (3 Timeframes)
```pine
//@version=6
strategy("Golden Template: MTF Trend", overlay=true)

// --- Inputs ---
shortMA_Len = input.int(20, "Short MA")
longMA_Len = input.int(50, "Long MA")

// --- 1D Context (Highest TF) ---
[dClose, dSma] = request.security(syminfo.tickerid, "1D", [close, ta.sma(close, 200)])
dailyBullish = dClose > dSma

// --- 4H Momentum (Middle TF) ---
[h4Rsi] = request.security(syminfo.tickerid, "240", [ta.rsi(close, 14)])
h4Bullish = h4Rsi > 50

// --- 1H Execution (Lowest TF) ---
maShort = ta.sma(close, shortMA_Len)
maLong = ta.sma(close, longMA_Len)
maCrossover = ta.crossover(maShort, maLong)

// --- Combined Logic ---
// Note: All indicator variables are pre-calculated outside the 'if' block.
longCondition = dailyBullish and h4Bullish and maCrossover

if longCondition
    strategy.entry("Long", strategy.long)

// --- Exit: 2% TP, 1% SL ---
targetPrice = strategy.position_avg_price * 1.02
stopPrice = strategy.position_avg_price * 0.99
strategy.exit("Exit", from_entry="Long", limit=targetPrice, stop=stopPrice)
```

## 2. Advanced Multi-Exit Trailing Stop (ATR Based)
```pine
//@version=6
strategy("Golden Template: ATR Trailing Exit", overlay=true)

// --- Indicators ---
atr = ta.atr(14)
rsi = ta.rsi(close, 14)

// --- States ---
longEntry = ta.crossover(rsi, 30)

if longEntry
    strategy.entry("L", strategy.long)

// --- Risk Management (Calculate Ticks) ---
atrTicks = math.round((atr * 2.0) / syminfo.mintick)
tp1Ticks = math.round((atr * 1.5) / syminfo.mintick)
tp2Ticks = math.round((atr * 3.0) / syminfo.mintick)

// --- Tiered Exits ---
// 50% TP, 50% with Trailing Stop
strategy.exit("TP1", from_entry="L", qty_percent=50, profit=tp1Ticks)
strategy.exit("Trail", from_entry="L", qty_percent=50, trail_price=close, trail_offset=atrTicks)
```

## 3. Bullish Divergence with Strict Logic
```pine
//@version=6
strategy("Golden Template: Divergence", overlay=true)

rsi = ta.rsi(close, 14)

// Find local lows
pivotLow = ta.pivotlow(low, 5, 5)
rsiLow = ta.pivotlow(rsi, 5, 5)

// Check for Divergence
// 1. Current Price Low is lower than previous Price Low
// 2. Current RSI Low is HIGHER than previous RSI Low
isPriceLower = low < ta.valuewhen(not na(pivotLow), pivotLow, 1)
isRsiHigher = rsi > ta.valuewhen(not na(rsiLow), rsiLow, 1)

divCondition = not na(pivotLow) and isPriceLower and isRsiHigher

if divCondition
    strategy.entry("Div", strategy.long)
```

## 4. Alert-Ready Strategy (Automation Standard)
```pine
//@version=6
strategy("Golden Template: Alerts", overlay=true)

// --- Indicators ---
smaShort = ta.sma(close, 20)
smaLong  = ta.sma(close, 50)
crossUp  = ta.crossover(smaShort, smaLong)

// --- Execution with JSON Alerts ---
if crossUp
    strategy.entry("Long", strategy.long, alert_message='{"action": "buy", "ticker": "' + syminfo.ticker + '"}')
    alert("DOGE SMA Bullish Cross at " + str.tostring(close), alert.freq_once_per_bar)

// --- Dynamic Exit Alerts ---
atr = ta.atr(14)
stopTicks = math.round(atr * 2 / syminfo.mintick)

if strategy.position_size > 0
    strategy.exit("Exit", "Long", loss=stopTicks, alert_message='{"action": "sell", "id": "stop_loss"}')
```

## 5. Ensemble Learning (Weighted Voting & MoE)
```pine
//@version=6
strategy("Golden Template: Ensemble Learning", overlay=true)

// --- 1. Weights from Meta-Analysis (Simulation) ---
// In practice, these could be inputs or adjusted based on Analyst Report
dTrendWeight = 0.50  // 50% Weight for Daily Trend
h4MomWeight  = 0.30  // 30% Weight for 4H Momentum
h1VolWeight  = 0.20  // 20% Weight for 1H Volatility/Regime

// --- 2. Multi-Timeframe Experts (RAG Pattern) ---
// Expert A: Daily Trend Specialist
[dClose, dSma200] = request.security(syminfo.tickerid, "1D", [close, ta.sma(close, 200)])
dTrendSignal = dClose > dSma200 ? 1.0 : -1.0

// Expert B: 4H Momentum Specialist
[h4Rsi] = request.security(syminfo.tickerid, "240", [ta.rsi(close, 14)])
h4MomSignal = h4Rsi > 60 ? 1.0 : (h4Rsi < 40 ? -1.0 : 0.0)

// Expert C: 1H Local Execution Specialist
maFast = ta.sma(close, 20)
maSlow = ta.sma(close, 50)
h1LocalSignal = ta.crossover(maFast, maSlow) ? 1.0 : (ta.crossunder(maFast, maSlow) ? -1.0 : 0.0)

// --- 3. Gating Logic & Ensemble Score ---
// Calculate weighted ensemble score
ensembleScore = (dTrendSignal * dTrendWeight) + (h4MomSignal * h4MomWeight) + (h1LocalSignal * h1VolWeight)

// --- 4. Dynamic Weighting (ATR-Scaled Sensitivity) ---
atr = ta.atr(14)
isHighVolatility = atr > ta.sma(atr, 50)
threshold = isHighVolatility ? 0.7 : 0.5 // Higher threshold in high vol to filter noise

longCondition = ensembleScore >= threshold
shortCondition = ensembleScore <= -threshold

// --- 5. Logic Switching (Regime Detection) ---
// Switch between Trend Following and Mean Reversion
adxLen = 14
[diPlus, diMinus, adx] = ta.dmi(adxLen, adxLen)
isTrending = adx > 25

if isTrending
    // Trend Following Logic
    if longCondition
        strategy.entry("Ensemble Trend Long", strategy.long)
else
    // Mean Reversion Logic (Simulated)
    if h4Rsi < 30 and h1LocalSignal > 0
        strategy.entry("Ensemble Revert Long", strategy.long)

// --- 6. Risk Management (ATR-Based Dynamic Stops) ---
stopMult = isHighVolatility ? 3.0 : 2.0
stopTicks = math.round((atr * stopMult) / syminfo.mintick)
profitTicks = math.round((atr * 4.0) / syminfo.mintick)

if strategy.position_size != 0
    strategy.exit("Exit", loss=stopTicks, profit=profitTicks, trail_price=close, trail_offset=stopTicks)

// --- Debugging ---
plot(ensembleScore, "Ensemble Score", color=color.new(color.blue, 50), style=plot.style_columns)
hline(0.5, "Threshold", color=color.gray)
```

## 6. Performance Best Practices (Onyx Hardening)
### A. Accelerated Trend Gating
Avoid SMAs for trend gating as they are too lagging. Use EMA or HMA.
```pine
// Level 0: Accelerated Calculation
fastEMA = ta.ema(close, 100)
slowEMA = ta.ema(close, 200)
isTrendBullish = fastEMA > slowEMA
```

### B. Adaptive Volatility Thresholds
Don't use static entry thresholds. Use Bollinger Width to adjust sensitivity.
```pine
[basis, upper, lower] = ta.bb(close, 20, 2)
bbWidth = (upper - lower) / basis
bbWidthAvg = ta.sma(bbWidth, 50)
isQuietMarket = bbWidth < bbWidthAvg
// Increase threshold in quiet markets to avoid noise
entryThreshold = isQuietMarket ? 0.8 : 0.6
```

### C. Protection against "Flash Dumps"
Use a fast ATR-based trailing stop that tightens if price moves 1 ATR in your favor.
```pine
atr = ta.atr(14)
var float trailPrice = na
if strategy.position_size > 0
    float newTrail = close - (atr * 1.5)
    trailPrice := na(trailPrice) ? newTrail : math.max(trailPrice, newTrail)
```

## 7. Regime-Based Decision Tree (Gating Architecture)
This template demonstrates how to switch between Trend-Following and Mean Reversion logic based on Market Structure (ADX).

```pine
//@version=6
strategy("Golden Template: Regime Decision Tree", overlay=true)

// --- 1. Pre-Analysis (Level 0) ---
// Structural Feature: ADX (Trend Strength)
[diPlus, diMinus, adx] = ta.dmi(14, 14)
isTrending = adx > 25

// Momentum Feature: Bias from 1D MA
ma1d = request.security(syminfo.tickerid, "1D", ta.sma(close, 20))
momentumBias = (close - ma1d) / ma1d * 100

// Volatility Feature: BB Width (Expansion/Compression)
[basis, upper, lower] = ta.bb(close, 20, 2)
bbWidth = (upper - lower) / basis
bbWidthAvg = ta.sma(bbWidth, 50)
isVolatilityExpanding = bbWidth > bbWidthAvg

// --- 2. Gating Network (Decision Tree) ---
// Setup Weight Profiles based on Regime
float aiWeight   = isTrending ? 0.70 : 0.30
float techWeight = isTrending ? 0.30 : 0.70

// Define technical signals (Level 0)
rsi = ta.rsi(close, 14)
emaFast = ta.ema(close, 20)
emaSlow = ta.ema(close, 50)
crossUp = ta.crossover(emaFast, emaSlow)

// Simulated AI Meta-Score from Analyst Report (-100 to 100)
// In practice, this value is parsed or hardcoded per generation
float aiMetaScore = 75.0

// --- 3. Weighted Logic Switching ---
float finalScore = 0.0

if isTrending
    // Trend-Following Logic: Prioritize AI Conviction + Momentum Bias
    finalScore := (aiMetaScore * aiWeight) + (ta.change(emaFast) > 0 ? 30.0 : -30.0) * techWeight
else
    // Mean Reversion Logic: Prioritize Technical Oscillators (RSI)
    float rsiSignal = rsi < 30 ? 100.0 : (rsi > 70 ? -100.0 : 0.0)
    finalScore := (aiMetaScore * aiWeight) + (rsiSignal * techWeight)

// --- 4. Adaptive Entry Confirmation ---
// Stricter threshold in ranging markets to avoid whipsaws
float entryThreshold = isTrending ? 50.0 : 65.0
longCondition = finalScore > entryThreshold

if longCondition
    strategy.entry("TreeLong", strategy.long)

// --- 5. Regime-Adaptive Risk Management ---
atr = ta.atr(14)
float stopMult = isTrending ? 3.0 : 1.5 // Wider in trends, tighter in ranges
float tpMult = isTrending ? 5.0 : 3.0

stopTicks = math.round((atr * stopMult) / syminfo.mintick)
profitTicks = math.round((atr * tpMult) / syminfo.mintick)
trailOffset = math.round((atr * 1.0) / syminfo.mintick)

if strategy.position_size > 0
    strategy.exit("ExitLong", "TreeLong", loss=stopTicks, profit=profitTicks, trail_price=close, trail_offset=trailOffset)

// --- 6. Visualization ---
plot(adx, "ADX (Structure)", color=color.new(color.blue, 50))
bgcolor(isTrending ? color.new(color.green, 95) : color.new(color.orange, 95))
```

# Pine Script v6 Code Examples

This directory contains **verified, working Pine Script v6 examples** that demonstrate correct syntax and best practices.

## 📚 Example Categories

### Basic Concepts
- **`01_basic_indicators.txt`** - Correct usage of SMA, RSI, ADX, and Volume
  - ✅ Shows proper variable assignment
  - ✅ Demonstrates `ta.*` namespace usage
  - ✅ Volume as a variable (NOT `ta.volume()`)

### Advanced Indicators
- **`02_macd_strategy.txt`** - MACD with correct v6 syntax
  - ✅ Array destructuring: `[macdLine, signalLine, histLine] = ta.macd(...)`
  - ✅ Positional parameters (NO named params)
  - ✅ Pre-calculation before conditions

### Pattern Recognition
- **`04_candlestick_patterns.txt`** - Manual candlestick pattern implementation
  - ⚠️ **CRITICAL**: `ta.candlestick.*()` functions DO NOT EXIST
  - ✅ Complete manual logic for Bullish/Bearish Engulfing
  - ✅ Hammer and Doji patterns

### Risk Management
- **`06_tiered_exits.txt`** - Multi-level profit targets
  - ✅ Entry price tracking: `var float entryPrice = na`
  - ✅ R-based calculations
  - ✅ Tick conversion for profit parameters

- **`07_trailing_stop.txt`** - ATR-based trailing stops
  - ✅ Mandatory tick conversion: `math.round(atr / syminfo.mintick)`
  - ✅ Correct `trail_price` and `trail_offset` usage

## 🎯 Usage in RAG System

These examples serve as **Few-Shot Learning** references for the LLM:
1. **Show, don't just tell**: Instead of "don't use X", we show the correct alternative
2. **Complete context**: Each example is a working strategy, not just snippets
3. **Emphasize common mistakes**: Comments highlight what NOT to do

## ⚡ Quick Reference

### Most Common Syntax Errors (FIXED in examples)
- ❌ `ta.volume()` → ✅ `volume`
- ❌ `ta.candlestick.engulfing()` → ✅ Manual pattern logic
- ❌ `ta.macd(close, fastLength=12)` → ✅ `ta.macd(close, 12, 26, 9)`
- ❌ `profit=1.5 * ta.atr(14)` → ✅ `profit=math.round((1.5 * ta.atr(14)) / syminfo.mintick)`
- ❌ `if volume > 2 * ta.sma(volume, 20)` → ✅ Pre-calculate `volAvg` first

## 📤 Uploading to Onyx

These `.txt` files are compatible with Onyx's File Connector:
1. Navigate to Onyx Admin Panel
2. Create/Update File Connector pointing to this directory
3. Trigger re-indexing
4. RAG queries will now include these examples as context

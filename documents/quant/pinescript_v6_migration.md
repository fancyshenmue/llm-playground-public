# Pine Script® v6 Migration & Syntax Guide (Optimized for RAG)

This guide provides a comprehensive knowledge base for generating high-quality Pine Script v6 code. Use this in your AnythingLLM RAG workspace.

## 🌟 1. Critical Breaking Changes (v5 ➔ v6)

### 🚫 Removal of `when` Parameter
The `when` parameter is **DELETED** from all order functions. You must use `if` blocks.
- **Functions affected**: `strategy.entry`, `strategy.exit`, `strategy.order`, `strategy.close`, `strategy.cancel`.
```pine
// ❌ WRONG (v5)
strategy.entry("Long", strategy.long, when = condition)
// ✅ CORRECT (v6)
if condition
    strategy.entry("Long", strategy.long)
```

### 🧠 Explicit Boolean Casting
Numeric values (int/float) are **NO LONGER** implicitly cast to `bool`.
- `0`, `0.0`, or `na` are NOT automatically `false`.
- **Fix**: Use `bool()` or comparison operators.
```pine
// ❌ WRONG (v6)
if bar_index
// ✅ CORRECT (v6)
if bar_index > 0
if bool(bar_index)
```

### 📉 Boolean `na` is Gone
- In v6, a `bool` MUST be `true` or `false`. It cannot be `na`.
- `na()`, `nz()`, and `fixnan()` no longer accept `bool` arguments.
- Expressions that previously returned `na` (like `bool_var[100]` on bar 1) now return `false`.

---

## 🛠️ 2. Strategy & Execution Improvements

### ⚖️ `strategy.exit()` Parameter Pairs
`strategy.exit()` now evaluates both **absolute** and **relative** parameters and uses the one that triggers **SOONEST**.
- **Absolute**: `limit`, `stop`, `trail_price`
- **Relative (Ticks)**: `profit`, `loss`, `trail_points`
- **Relative (Price)**: `trail_offset` (Tick-based offset)
- **Warning**: `trail_offset` is calculated in Price units but represents a distance. For BTC, `close * 0.08` might be 7200.0, which means 7200 ticks!

### 💰 Default Margin
- Default margin is now **100%**. Strategies will trigger margin calls if equity hits zero.
- **Fix**: Set `margin_long=0` and `margin_short=0` in `strategy()` for v5-like behavior.

---

## 🔄 3. Advanced Features

### 🚀 Dynamic `request.*()`
- You can now call `request.security()`, `request.seed()`, etc., inside `if` blocks and `for` loops.
- `dynamic_requests = true` is now the default.

### 🔁 Dynamic `for` Loops
- `for` loop boundaries are evaluated **before every iteration**.
- If `to_num` changes inside the loop (e.g., `array.size()`), the loop length changes dynamically.

### 🕒 Timeframe Format
- `timeframe.period` always includes a multiplier.
- Example: `"1D"` instead of `"D"`, `"1W"` instead of `"W"`.

---

## 🎨 4. Design & Visualization
- **Transparency**: The `transp` parameter is **REMOVED**. Use `color.new(base_color, alpha)`.
- **Color Palettes**: Some `color.*` constants have updated RGB values.
- **Labels**: Default text color for labels is now `color.white`.

---

## 📌 5. Prohibited Lexicon (FATAL ERRORS)
- **Keywords**: `then`, `end`, `do` (These are NOT Pine Script).
- **Entry Params**: `strategy.entry(..., loss=X, profit=X)` is invalid. SL/TP MUST be in `strategy.exit`.
- **History**: `[ ]` cannot be used on literal values (e.g., `10[1]`) or UDT fields directly (`obj.field[1]`). Use `(obj[1]).field` instead.
- **Division**: `5 / 2` now returns `2.5` even for constants. Use `int()` for integer division.

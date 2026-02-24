# Pine Script® v6: Core Syntax & Math Reference

This document covers essential language rules, math functions, and logical operators for Pine Script v6.

## 🧠 1. Logical Operators & Comparisons
- **`and` / `or` / `not`**: Logical operators. (Lazy evaluation in v6).
- **`==` / `!=`**: Equality check.
- **`>` / `<` / `>=` / `<=`**: Numeric comparisons.
- **`?:` (Ternary)**: `condition ? val_if_true : val_if_false`.

## ➗ 2. Math Functions (`math.*`)
- **Rounding**: `math.round(x)`, `math.floor(x)`, `math.ceil(x)`.
- **Min/Max**: `math.min(x, y)`, `math.max(x, y)`.
- **Sum**: `math.sum(source, length)`.
- **Absolute Value**: `math.abs(x)`.
- **Power/Root**: `math.pow(x, y)`, `math.sqrt(x)`.
- **⚠️ Division**: In v6, `5 / 2` is `2.5`. Use `math.floor(5 / 2)` or `int(5 / 2)` for integer results.

## 📍 3. Key Variables & Constants
- **Prices**: `open`, `high`, `low`, `close`, `hl2`, `hlc3`, `ohlc4`.
- **Information**: `bar_index`, `time`, `syminfo.mintick`, `syminfo.pointvalue`, `volume`.
- **Booleans**: `true`, `false`. (v6 does NOT allow `na` for bools).

## 🏗️ 4. Local vs Global Scope
- **Level 0 (Global)**: Declarations of indicators (e.g., `emaLine = ta.ema(...)`) and `strategy()` call must be here.
- **Level 1+ (Indented)**: Execution logic inside `if`, `for`, or `while`.
- **⚠️ Crucial**: `ta.*` functions should almost ALWAYS be at Level 0 to avoid consistency warnings or logical errors in v6.

## 📦 5. Type System
- **`int`, `float`, `bool`, `string`, `color`**: Fundamental types.
- **`series`**: Data that changes over time (most price-related variables).
- **`simple` / `const`**: Data that is set at startup.
- **Casting**: Use `bool(x)`, `int(x)`, `float(x)` for explicit conversion.

## 🚫 6. Prohibited Lexicon (Reminder)
- **NOT PINE**: `then`, `do`, `end`, `elif` (Use `else if`).
- **INVALID**: `strategy.op`, `na(bool_variable)`.
- **NO JSON**: Do NOT wrap your output in JSON objects (e.g., `{"code": "..."}`). Production pipelines expect RAW Pine Script code only.
- **NO MarkDown**: Do NOT use markdown code fences unless specifically asked.

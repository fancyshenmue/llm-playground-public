# AI Quant CLI Usage Guide

Detailed examples for using the `llm-utils quant` command suite with RAG and trade analysis support.

---

## 📥 1. Data Fetching (New!)
Automatically download multi-timeframe OHLCV data from Binance exchange.

### Basic Usage (Limited to 1000 candles per timeframe)
```bash
llm-utils quant fetch \
  --symbol BTCUSDT \
  --timeframes 1h,4h,1d \
  --limit 1000 \
  --output dataset/trading/
```

### Advanced: Pagination for Historical Data (Unlimited)
Use `--since` to automatically fetch all data from a start date, bypassing the 1000 candle limit.

```bash
llm-utils quant fetch \
  --symbol BTCUSDT \
  --timeframes 1h,1d \
  --since 2024-01-01 \
  --output dataset/trading/
```

**Example output:**
- `btcusdt_1h.csv`: ~9,000 candles (1 year of hourly data)
- `btcusdt_1d.csv`: ~380 candles (1 year of daily data)

**Supported timeframes:** `1m`, `5m`, `15m`, `30m`, `1h`, `4h`, `1d`, `1w`

**Note:** When using `--since`, the system automatically paginates through Binance API to fetch all available data.

---

## 🚀 2. Strategy Generation (Standard)
Generate a new strategy from market data.

```bash
llm-utils quant gen \
  -i dataset/trading/btc_1d.csv \
  -l "Price > EMA 200 + RSI < 45" \
  -o output/btc_strategy.pine
```

---

## 📚 3. RAG-Enhanced Generation (Strongly Recommended)
Use this to eliminate syntax errors by grounding the model in Pine Script v6 documentation.

```bash
llm-utils quant gen \
  -i dataset/trading/btc_1d.csv \
  -l "Low Volume Exhaustion Long with 8% Trailing Stop" \
  -o output/btc_rag_test.pine \
  --rag "pinescript-v6" \
  --limit 50
```

---

## 📊 4. Performance-Driven Audit
Audit your strategy using both the code and the TradingView **Trade List CSV**.

```bash
llm-utils quant audit \
  -i output/btc_strategy.pine \
  -c dataset/trading/btc_1d.csv \
  -t dataset/trading/trade_list.csv \
  -o output/performance_audit.md
```

---

## 🔄 5. Automated Refinement
Apply the analyst's performance critique to fix and optimize the code.

```bash
llm-utils quant gen \
  -i dataset/trading/btc_1d.csv \
  -l "EMA Cross with Trailing Stop" \
  --critique output/performance_audit.md \
  --rag "pinescript-v6" \
  -o output/btc_strategy_refined.pine
```

---

## 🎯 6. Advanced: Multi-Timeframe (MTF) Strategy
Generate strategies that use higher timeframe filters to improve signal quality.

```bash
llm-utils quant gen \
  -i dataset/trading/btc_1h.csv \
  -l "MTF Logic: Buy only if Daily Close > Daily EMA 200 + 1H RSI < 30" \
  --rag "pinescript-v6" \
  -o output/btc_mtf_trend.pine
```

---

## 💰 7. Advanced: Tiered Profit-Taking & ATR Stops
Professional risk management with partial exits and dynamic trailing stops.

```bash
llm-utils quant gen \
  -i dataset/trading/btc_1d.csv \
  -l "Tiered TP: 50% at 5% profit, 50% at 15% profit + ATR(14) multiplier 3.0 Trailing Stop" \
  --rag "pinescript-v6" \
  -o output/btc_pro_exit.pine
```

---

## 📐 8. Advanced: Risk-Based Position Sizing
Automatically calculate position size based on dollar risk and ATR distance.

```bash
llm-utils quant gen \
  -i dataset/trading/btc_1d.csv \
  -l "EMA Cross + Risk Management: Risk $100 per trade based on ATR(14) stop distance" \
  --rag "pinescript-v6" \
  -o output/btc_risk_sized.pine
```

---

## 💡 Configuration Tips
- **Coder Model**: Use `deepseek-coder-v2:16b` or `gpt-oss:20b` for the best balance of syntax and logic.
- **AnythingLLM**: Ensure the `pinescript-v6` workspace exists and the migration guide is "Saved and Embedded."

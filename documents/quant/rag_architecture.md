# AI Quant RAG System: Architecture & Workflow

This document explains the complete workflow and data flow of the AI Quant system with RAG (Retrieval-Augmented Generation).

## 🏗️ System Architecture Overview

```mermaid
graph TB
    User[User] -->|CLI Command| CLI[llm-utils CLI]
    CLI --> Config[config.yaml]
    CLI --> Parser[CSV Parser]

    Parser --> Market[Market Data]

    CLI -->|RAG Query| ALLM[AnythingLLM API]
    ALLM --> VDB[(Qdrant Vector DB)]
    VDB --> Docs[Pine Script v6 Docs]

    CLI -->|Generate Request| Ollama[Ollama API]
    Ollama --> Coder[qwen2.5-coder:32b]

    ALLM -->|Documentation Context| Ollama
    Market -->|Price Data Context| Ollama

    Coder -->|Raw Code| Cleaner[Code Cleaner]
    Cleaner -->|Pure Pine Script| Output[.pine File]

    Output -->|Backtest| TV[TradingView]
    TV -->|Trade List CSV| Audit[llm-utils audit]
    Audit -->|Performance Critique| CLI
```

## 🔄 Generation Workflow (Step-by-Step)

### Phase 0: Data Fetching (Optional)
```mermaid
sequenceDiagram
    participant User
    participant CLI as llm-utils
    participant Binance as Binance API
    participant FS as File System

    User->>CLI: quant fetch --symbol BTCUSDT --since 2024-01-01
    Note over CLI: Parse date to Unix timestamp
    loop Pagination (bypasses 1000 limit)
        CLI->>Binance: Request 1000 klines from startTime
        Binance->>CLI: Return batch of candles
        CLI->>CLI: Append & update startTime
    end
    CLI->>FS: Save all candles as CSV
    Note over FS: btcusdt_1h.csv (9000+ candles)
```

**Pagination Feature:**
- Without `--since`: Single API call, max 1000 candles
- With `--since`: Automatic pagination, unlimited historical data
- System tracks last candle's CloseTime and recursively fetches next batch

### Phase 1: Data Collection
```mermaid
sequenceDiagram
    participant User
    participant CLI as llm-utils
    participant Parser as CSV Parser

    User->>CLI: quant gen -i btc_1d.csv -l "EMA Cross"
    CLI->>Parser: Parse market data
    Parser->>CLI: Return OHLCV statistics
    Note over CLI: Extract: High, Low, Avg Volume
```

### Phase 2: RAG Context Retrieval
```mermaid
sequenceDiagram
    participant CLI as llm-utils
    participant ALLM as AnythingLLM
    participant VDB as Qdrant
    participant Docs as Pine Docs

    CLI->>ALLM: Query: "strategy.exit trailing stops + EMA Cross"
    ALLM->>VDB: Vector similarity search
    VDB->>Docs: Retrieve top-k chunks
    Docs->>VDB: Return doc snippets
    VDB->>ALLM: Ranked results
    ALLM->>CLI: Documentation Context (text)
    Note over CLI: Context includes:<br/>- Syntax rules<br/>- Code examples<br/>- Pitfalls
```

### Phase 3: Code Generation
```mermaid
sequenceDiagram
    participant CLI as llm-utils
    participant Ollama
    participant Coder as qwen2.5-coder

    CLI->>Ollama: Generate Request
    Note over Ollama: Prompt includes:<br/>1. Market Data<br/>2. RAG Context<br/>3. User Logic<br/>4. Mandatory Rules
    Ollama->>Coder: Execute inference
    Coder->>Ollama: Raw response (may have JSON/markdown)
    Ollama->>CLI: Return response
```

### Phase 4: Code Cleaning & Output
```mermaid
sequenceDiagram
    participant CLI as llm-utils
    participant Cleaner as Code Cleaner
    participant FS as File System

    CLI->>Cleaner: Raw LLM output
    Cleaner->>Cleaner: 1. Extract from JSON if present
    Cleaner->>Cleaner: 2. Strip preamble before //@version=6
    Cleaner->>Cleaner: 3. Remove markdown fences
    Cleaner->>CLI: Pure Pine Script code
    CLI->>FS: Write to output.pine
    Note over FS: Ready for TradingView!
```

## 🧠 RAG Knowledge Base Structure

The `documents/quant/` folder contains specialized Pine Script v6 references:

```
documents/quant/
├── pinescript_v6_migration.md      # v5 → v6 breaking changes
├── pinescript_v6_core_reference.md # Syntax, math, operators
├── pinescript_v6_ta_reference.md   # Technical indicators (ta.*)
├── pinescript_v6_strategy_reference.md # Strategy functions
├── pinescript_v6_pitfalls.md       # Common errors & anti-patterns
├── pinescript_v6_examples.md       # High-quality code templates
├── pinescript_v6_mtf_reference.md  # Multi-timeframe analysis
└── pinescript_v6_risk_management.md # Advanced exits & sizing
```

Each file is embedded into Qdrant via AnythingLLM's `Save and Embed` function.

## 🎯 Prompt Engineering Strategy

The Coder model receives a hardened prompt structure:

```
[Market Data Context]
High: $95,000 | Low: $16,000 | Avg Volume: 12.5B

[RAG Documentation Context]
<Retrieved from Vector DB based on user logic>

[Mandatory Rules]
1. ALL indicators at Level 0
2. TRAILING STOP PATTERN:
   stopTicks = math.round((close * percent) / syminfo.mintick)
   strategy.exit("ID", trail_price=close, trail_offset=stopTicks)
3. NO undefined variables (e.g., adx2)
4. USE namespaces: ta.*, strategy.*, math.*

[User Logic]
"EMA Cross with Trailing Stop"

[Output Format]
Pure Pine Script code starting with //@version=6
```

## 🔁 Audit & Refinement Loop

```mermaid
graph LR
    Gen[Generate v1] --> TV[Test in TradingView]
    TV --> Export[Export Trade List CSV]
    Export --> Audit[llm-utils audit]
    Audit --> Critique[Performance Analysis]
    Critique --> Gen2[Generate v2 with --critique]
    Gen2 --> TV

    style Critique fill:#f9f,stroke:#333
```

## 📊 Key Performance Metrics

| Component | Technology | Purpose |
|:---|:---|:---|
| **Data Fetcher** | Binance API (go-binance) | Multi-timeframe OHLCV download w/ pagination |
| **Vector DB** | Qdrant | Semantic search for docs |
| **RAG Orchestrator** | AnythingLLM | Workspace & embedding mgmt |
| **Coder Model** | Qwen2.5-Coder:32b | Code generation |
| **Analyst Model** | Custom (Plutus) | Performance critique |
| **CLI** | Go + Cobra | User interface |

## 🚀 Future Enhancements

1. **Automated Validation**: Run Pine Script linter before saving.
2. **Backtesting Integration**: Auto-submit to TradingView API for immediate results.
3. **Fine-tuning Pipeline**: Collect successful strategies to train a specialized model.
4. **Multi-Asset Support**: Extend to Forex, Stocks, and Crypto futures.

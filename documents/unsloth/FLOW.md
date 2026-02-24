# Unsloth Fine-tuning & Export Flow

This diagram illustrates the end-to-end workflow from dataset loading to model consumption in Ollama.

```mermaid
graph TB
    subgraph "1. Data Preparation"
        HF["Hugging Face (The Stack)"]
        Load["Load Parquet (Go, Python, JS, TS)"]
        Filt["Filter (max_seq_length) & Shuffle"]
        HF --> Load --> Filt
    end

    subgraph "2. Unsloth Fine-tuning"
        Base["Qwen2.5-Coder (14B/32B)"]
        QLoRA["Add QLoRA Adapters"]
        Train["SFTTrainer (Optimized Kernels)"]
        Filt --> Train
        Base --> QLoRA --> Train
    end

    subgraph "3. Export & Deployment"
        GGUF["Save GGUF (4-bit quantization)"]
        ModelF["Generate Modelfile"]
        Ollama["Ollama (ollama create)"]
        Train --> GGUF
        GGUF --> ModelF --> Ollama
    end

    subgraph "4. Consumption & Tracing"
        Proxy["Ollama Proxy (OTLP)"]
        Phoenix["Arize Phoenix (Tracing UI)"]
        MCP["local-ollama MCP Server"]
        USER["End User (VS Code / CLI)"]

        Ollama <--> Proxy
        Proxy --> Phoenix
        USER --> MCP --> Proxy
    end

    style Train fill:#f4511e,color:#fff,stroke:#333,stroke-width:2px
    style GGUF fill:#3949ab,color:#fff,stroke:#333,stroke-width:2px
    style Ollama fill:#2e7d32,color:#fff,stroke:#333,stroke-width:2px
    style Phoenix fill:#6a1b9a,color:#fff,stroke:#333,stroke-width:2px
    style HF fill:#ffca28,color:#333,stroke:#333,stroke-width:2px
```

## Flow Description

1. **Data Prep**: We pull multi-language samples from 'The Stack' dataset, filter by sequence length, and shuffle to create a balanced training set.
2. **Fine-tuning**: We use Unsloth's optimized `FastLanguageModel` and `SFTTrainer`. For 32B models, aggressive VRAM optimizations (shorter context, lower rank) are applied.
3. **Export**: The fine-tuned weights are quantized and converted to GGUF format. A `Modelfile` is generated to simplify the Ollama import.
4. **Consumption**: Requests from the MCP server pass through an `ollama-proxy` to capture traces for `Arize Phoenix` before reaching the model.

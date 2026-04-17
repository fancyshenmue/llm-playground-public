# vllm-mlx Architecture

## Overview
`vllm-mlx` introduces OpenAI and Anthropic compatible APIs backed by Apple Silicon's natively optimized MLX framework. This brings unprecedented throughput for local LLM and VLM instances on Mac hardware, especially given unified memory systems unconstrained by standard explicit VRAM limits.

## System Design and Flow

```mermaid
flowchart TD
    Client[User / Desktop Client] -->|REST API<br>/v1/chat/completions| VLLM_API[vLLM API Layer]
    
    subgraph `Hardware / Daemon Layer`
        VLLM_API --> Server
        Server[vllm-mlx Server Layer] --> MLX_VLM[MLX VLM Abstraction]
        MLX_VLM --> Apple_Silicon[Apple M2 Max<br>96GB Unified Memory]
    end
    
    subgraph `Model Storage`
        Apple_Silicon -->|Loads Gemma 4 31B 8-bit<br>~31GB allocation| Local_Cache
    end
```

## Hardware Profile
The baseline constraint mapping guarantees support up to `gemma-4-31b-8bit` relying on the host's 96GB unified memory architecture. The 8-bit quantification is chosen systematically over 4-bit configurations because 31GB memory pressure comfortably fits alongside standard host operating loads on a 96GB ceiling, optimizing for accuracy while eliminating out-of-memory overhead mapping.

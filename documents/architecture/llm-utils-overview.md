# llm-utils Architecture Overview

## Project Structure

```
llm-playground/
├── cmd/
│   ├── go/llm-utils/          # CLI tool
│   │   ├── cmd/               # Commands (Cobra)
│   │   │   ├── data_gen.go    # Image generation (data-gen)
│   │   │   ├── chat.go        # Interaction with Ollama
│   │   │   ├── tag.go         # Image tagging
│   │   │   ├── train.go       # LoRA/Fine-tune triggering
│   │   │   └── analyze.go     # Image analysis
│   │   └── config.yaml        # Configuration
│   ├── node/llm-utils-desktop # Electron Frontend
│   └── py/llm-utils           # Python utilities
├── deployments/
│   └── docker-compose/        # Docker services (Lab, Axolotl)
└── documents/                 # Documentation
```

## Core Components

### 1. llm-utils CLI (Go)
Go-based command-line interface that orchestrates:
- **Image Generation (`data-gen`)**: Uses Stable Diffusion Forge API.
- **Image Tagging (`tag`)**: Uses WD14 Tagger via Forge.
- **Training (`train`)**: Triggers external training scripts (Kohya/Axolotl).
- **Analysis (`analyze`)**: Uses Ollama Vision models.

### 2. Desktop App (Electron)
- A GUI wrapper around the CLI capabilities, providing a nicer interface for managing datasets and training configs.

### 3. External Services

#### Docker Compose Services (Containerized)
- **Ollama**: LLM for prompts and vision analysis (port 11434).
- **Onyx**: Advanced RAG engine for documentation (port 3000).
- **Axolotl**: Fine-tuning environment for LLMs (14B/32B).

#### Native WSL Services
- **Stable Diffusion Forge**: Image generation (Port 7861).
- **Kohya_ss**: LoRA training framework (managed by Pixi).

### 3. Environment
- **Platform**: WSL Ubuntu 24.04.
- **Package Management**: Pixi (conda-based) for Python/Go environments.
- **Container Orchestration**: Docker Compose.
- **GPU**: NVIDIA RTX 4090.

## Technology Stack

- **Global Manager**: Pixi (`pixi.toml` defines tools and environments).
- **Backend CLI**: Go 1.24+ (Cobra).
- **Frontend**: Node.js/Electron/React.
- **AI Models**:
  - **Analyst/Logic**: `deepseek-r1:32b` or `qwen2.5-coder:32b`.
  - **Vision**: `llama3.2-vision`.
  - **Image Gen**: SDXL / Flux models via Forge.

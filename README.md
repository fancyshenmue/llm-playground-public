# LLM Learning Lab Project

This is a lab project dedicated to the exploration, experimentation, and development of Large Language Models (LLMs).
It aims to document configuration processes, experimental designs, and the development of related toolchains throughout the learning journey.

The project covers a complete workflow ranging from model fine-tuning and inference services to desktop tool integration.

## Description

This project primarily focuses on the following core areas:
- **Model Training & Fine-tuning**: Utilizing the Axolotl framework to conduct fine-tuning experiments on open-source models (e.g., Qwen, Llama).
- **Local Inference Environment**: Building high-performance local inference services based on Ollama.
- **Tool Development**: Developing desktop applications (`llm-utils-desktop`) and backend services to assist with LLM operations.
- **Environment Standardization**: Establishing a reproducible and efficient development environment using Docker and WSL 2.

## Hardware Spec (Local Lab)

- **CPU**: Intel Core i9-13900K (24 Cores, 32 Threads)
- **GPU**: NVIDIA GeForce RTX 4090 (24GB VRAM)
- **Motherboard**: ASUS ROG MAXIMUS Z790 HERO
- **Memory**: 64GB DDR5 4800MHz (Kingston Fury, 2x32GB)
- **Storage**: Samsung 990 PRO NVMe Array
  - 1x 1TB
  - 1x 2TB (Dedicated for WSL & Docker)
  - 2x 4TB (Dedicated for LLM Datasets & Checkpoints)
- **Environment**: WSL 2 (Windows Subsystem for Linux) on Windows 11

## Tools Used

This project integrates a modern AI development toolchain:

### Core Infrastructure
- **Docker & Docker Compose**: Containerizing all services and training environments.
- **WSL 2**: Providing a high-performance Linux kernel environment to solve cross-platform development challenges.

### Generative AI & LLM
- **[Axolotl](https://github.com/OpenAccess-AI-Collective/axolotl)**: A powerful tool for efficient LLM fine-tuning.
- **[Ollama](https://github.com/ollama/ollama)**: For rapid local deployment and model inference.
- **[Hugging Face](https://huggingface.co)**: Source and management for models and datasets.
- **[Stable Diffusion Forge](https://github.com/lllyasviel/stable-diffusion-webui-forge)**: Optimized backend for fast image generation (SDXL/Flux).
- **[ComfyUI](https://github.com/comfyanonymous/ComfyUI)**: Node-based workflow engine for complex vision tasks (e.g., AnimateDiff).
- **[Kohya_ss](https://github.com/bmaltais/kohya_ss)**: Specialized scripts for training LoRA and Dreambooth models.
- **[Onyx](https://github.com/onyx-dot-app/onyx)**: Gen-AI Search & Chat, currently serving as the specific RAG (Retrieval-Augmented Generation) provider for this lab.

### Development & Applications
- **Antigravity**: Full-stack development with the Remote - WSL extension.
- **Electron / Node.js**: Used for developing the `llm-utils-desktop` application.
- **CLI Utilities**:
  - `cmd/go/llm-utils`: High-performance Go CLI.
    - **Vision & Training**: Integrates with **SD Forge** for synthetic dataset generation and **Kohya_ss** for LoRA training automation.
    - **Quant Strategy**: Backtesting, data fetching, and market analysis.
  - `cmd/py/llm-utils`: Python CLI for **Dataset Management** (Code-to-Parquet conversion, Token analysis) and **Vision/Image Generation** workflows (Forge integration, LoRA sweeping).
- **Python / PyTorch**: Training scripts and data processing.
- **Pixi**: Project dependency and environment management (where applicable).

---
> ⚠️ **Note**: This project serves as a personal learning notebook and experimental ground. Some configurations may change frequently based on experimental needs.

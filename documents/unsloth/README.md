# Unsloth Fine-tuning for Qwen2.5-Coder

This directory contains the setup for fine-tuning Qwen2.5-Coder models using [Unsloth](https://github.com/unslothai/unsloth), which provides better performance and lower memory usage compared to traditional methods like Axolotl.

## Setup

1.  **Configure environment**:
    *   Copy `.env.example` to `.env`.
    *   Update `HF_TOKEN` with your Hugging Face access token.
    *   Set `DATASET_PATH` and `OUTPUT_PATH` to your desired local directories.

2.  **Start the container**:
    ```bash
    cd deployments/docker-compose/unsloth
    docker compose up -d
    ```

## Fine-tuning

You can trigger the fine-tuning for different model sizes using the following commands from the `deployments/docker-compose/unsloth` directory:

### Qwen2.5-Coder-14B-Instruct
```bash
docker compose exec -e MODEL_NAME="Qwen/Qwen2.5-Coder-14B-Instruct" unsloth python /workspace/scripts/finetune.py
```

### Qwen2.5-Coder-32B-Instruct
```bash
docker compose exec -e MODEL_NAME="Qwen/Qwen2.5-Coder-32B-Instruct" unsloth python /workspace/scripts/finetune.py
```

## How it works

The scripts use `scripts/finetune.py`, which leverages the Unsloth library to:
*   Load the model in 4-bit quantization (QLoRA).
*   Apply optimized LoRA adapters.
*   Train on the specified dataset (default is a mixture of Go and Python from `bigcode/the-stack`).
*   **Export to Ollama**: After training, the script automatically exports the fine-tuned model to GGUF format in the output directory, ready to be used with Ollama.

## Exporting to Ollama

The GGUF files are saved to `/workspace/output/qwen-coder-gguf`. You can then create an Ollama model using a Modelfile:

```dockerfile
FROM ./qwen-coder-gguf/unsloth.Q4_K_M.gguf
# Add any specialized system prompts or parameters here
```

And run:
```bash
ollama create my-fine-tuned-qwen -f Modelfile
```

## Resource Comparison (vs Axolotl)

*   **VRAM Usage**: Unsloth typically uses 40-70% less VRAM for the same model size.
*   **Speed**: Training is often 2x-3x faster.
*   **Ease of use**: Directly exports to GGUF, eliminating the manual conversion step with `llama.cpp`.

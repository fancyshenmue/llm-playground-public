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

## 📖 Documentation
- [FINETUNING_GUIDE.md](./FINETUNING_GUIDE.md): Step-by-step workflow, memory optimizations, and continuity setup.
- [METRICS.md](./METRICS.md): Professional interpretation of Loss, Grad Norm, and other training indicators.
- [EVALUATION.md](./EVALUATION.md): Measuring model performance post-training.
- [FLOW.md](./FLOW.md): Technical architecture of the Unsloth integration.

## Fine-tuning

The fine-tuning process is now driven by a structured configuration file.

### 1. Configure parameters
Edit [deployments/docker-compose/unsloth/config.yaml](file:///home/fancyshenmue/dev/llm-playground/deployments/docker-compose/unsloth/config.yaml) to set:
*   **Model**: Name, context length.
*   **Hyperparameters**: Learning rate, LoRA rank (R), steps.
*   **Datasets**: Languages (Go, Java, Rust, etc.) and sample counts.

### 2. Execute Training
Run the training script within the container:
```bash
docker compose exec unsloth python /workspace/scripts/finetune.py
```

### 3. Quick Overrides (Optional)
You can still override any YAML value via environment variables for quick tests:
```bash
# Override learning rate and steps without changing config.yaml
docker compose exec -e LEARNING_RATE="1e-5" -e MAX_STEPS="500" unsloth python /workspace/scripts/finetune.py
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

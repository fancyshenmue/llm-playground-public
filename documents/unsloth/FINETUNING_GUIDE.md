# Unsloth Finetuning Guide

This guide covers the advanced finetuning workflow optimized for **Qwen2.5-Coder-14B** using Unsloth.

## 🚀 Key Advantages (vs Axolotl)
- **Speed**: 30x+ faster training thanks to hand-written Triton kernels.
- **Resource Efficiency**: Significantly lower VRAM usage and better memory management.
- **Stability**: Integrated fragmentation fixes and robust checkpointing.

## 🛠️ Performance & Memory Setup
To ensure stability on 24GB VRAM cards (e.g., RTX 3090/4090):
1. **CUDA Fragmentation Fix**: We force `expandable_segments:True` in both `docker-compose.yml` and the start of `finetune.py`.
2. **vLLM Standby**: Automatically disabled (`UNSLOTH_VLLM_STANDBY=0`) to prevent interference with memory optimizations.

## 📋 Configuration (`config.yaml`)
Training is driven by a structured YAML file located at `deployments/docker-compose/unsloth/config.yaml`.

### Common Parameters:
- `lora_r`: The Rank of LoRA. **64** is used for higher quality, **32** for faster iterations.
- `streaming`:
    - `true`: Consumes minimal disk space, streams data from HF.
    - `false`: Uses local cache for maximum speed.
- `resume`: Enable this to automatically pick up training from the last checkpoint.

## 🔄 Lifecycle & Continuity

### Resuming Training
If training is interrupted (OOM, system reboot), simply restart the container.
- If `resume: true` is set, the script detects existing `checkpoint-*` folders.
- It restores the optimizer state, learning rate scheduler, and random seed.

### Upgrading Architecture (e.g., Rank 32 -> 64)
> [!CAUTION]
> Checkpoints are architecture-dependent. If you change `lora_r`, you **must** clear the old checkpoints:
> `sudo rm -rf [OUTPUT_PATH]/unsloth-qwen-coder/*`

## 📦 Directory Structure
| Path | Description |
| :--- | :--- |
| `/workspace/config.yaml` | Active configuration |
| `/workspace/output/unsloth-qwen-coder` | Checkpoint archives (for resuming) |
| `/workspace/output/*-lora` | Final LoRA adapters |
| `/workspace/output/*-gguf` | Exported Ollama-ready model |

# llm-utils Documentation

## Quick Links

- [Architecture Overview](./llm-utils-overview.md) - Project structure and components
- [Current Architecture](./current-architecture.md) - WSL-only setup with Docker Compose
- [Sequence Flows](./sequence-flows.md) - Mermaid diagrams for all workflows
- [LoRA Development Lifecycle](./lifecycle.md) - Complete development cycle and iteration patterns
- [WSL Migration Guide](./wsl-migration.md) - Windows to WSL migration notes

## Command Reference

### Data Generation
```bash
# Generate training images
llm-utils data-gen --topic "street" --total 50 --output ./dataset

# With LoRA
llm-utils data-gen --prompt "city street" --lora Street_v1.safetensors --weight 0.8
```

### Image Tagging
```bash
# Tag all images in directory
llm-utils tag --path ./dataset --threshold 0.35

# With custom undesired tags
llm-utils tag --path ./dataset --undesired "watermark,text,logo"
```

### LoRA Training
```bash
# Train from config file
llm-utils train --config config.json

# Export config from Kohya GUI first
```

### Image Analysis
```bash
# Rank images by quality
llm-utils rank --dir ./output

# Deep analysis of single image
llm-utils analyze --image photo.png
```

## Configuration

Main config file: `cmd/go/llm-utils/config.yaml`

```yaml
ollama:
  base_url: "http://localhost:11434"  # Docker Compose
  model: "llama3.2:latest"

forge:
  base_url: "http://localhost:7861"  # WSL native
  model: "Juggernaut-XL_v9_RunDiffusionPhoto_v2.safetensors"

kohya:
  root_path: "$HOME/dev/kohya_ss"  # WSL native
  venv_path: "$HOME/dev/kohya_ss/.pixi/envs/default"

anything_llm:
  base_url: "http://localhost:3001/api/v1"  # Docker Compose
  workspace: "ai-image-research"
```

**Note**: All services run on WSL Ubuntu 24.04:
- Docker services managed by Docker Compose
- Forge and Kohya run natively with Pixi
- All accessible via `localhost`

## Typical Workflow

1. **Generate Training Data**
   ```bash
   llm-utils data-gen --topic "street" --total 50
   ```

2. **Tag Images**
   ```bash
   llm-utils tag --path ./dataset/50_street
   ```

3. **Train LoRA**
   ```bash
   llm-utils train --config street_config.json
   ```

4. **Test & Evaluate**
   ```bash
   llm-utils data-gen --lora Street_v1.safetensors --total 10
   llm-utils rank --dir ./test_output
   ```

5. **Analyze Best Results**
   ```bash
   llm-utils analyze --image ./test_output/best_001.png
   ```

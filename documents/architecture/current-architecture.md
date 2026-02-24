# Current Architecture (WSL-Only)

## System Layout

```
WSL Ubuntu 24.04
├── Docker Compose Services
│   ├── Ollama (LLM + Vision)
│   ├── Onyx (Advanced RAG - Port 3000)
│   ├── AnythingLLM (Knowledge Base)
│   ├── Qdrant (Vector DB)
│   └── Axolotl (Fine-tuning 14B/32B models)
│
├── Native WSL Services (Pixi Managed)
│   ├── stable-diffusion-forge (Image Gen)
│   └── kohya_ss (LoRA Training)
│
├── desktop-app (Electron/React)
│   └── cmd/node/llm-utils-desktop (Frontend UI)
│
└── llm-utils (Go CLI)
    └── cmd/go/llm-utils (Orchestration & Tools)
```

## Service Details

### Docker Compose Stacks
- **Main Lab Stack**: `deployments/docker-compose/lab/docker-compose.yml`
    - Services: Ollama, Onyx, AnythingLLM, Qdrant.
- **Training Stack**: `deployments/docker-compose/axolotl/docker-compose.yml`
    - Configurations: `deployments/docker-compose/axolotl/configs/code-training-14b.yaml`.

### llm-utils CLI
**Build (managed by Pixi):**
```bash
pixi run build-llm
```

**Quant Command Workflow:**
1. **Stage 1 (Analyst)**: Uses `deepseek-r1:32b` for market reasoning.
2. **RAG Extraction**: Queries **Onyx** for documentation.
3. **Stage 2 (Coder)**: Uses `qwen2.5-coder:32b` or `deepseek-r1:32b` for code generation.

## Network Topology

All services communicate via `localhost`:

```
llm-utils (Go)
    ↓
    ├─→ Ollama (Docker)          :11434 (Logic/Vision)
    ├─→ Onyx (Docker)            :3000  (RAG)
    ├─→ Forge (WSL Native)       :7861  (Image Gen)
    └─→ Kohya (WSL Native)       /home/.../kohya_ss
```

**Frontend (Electron)**:
- Connects to `llm-utils` (via CLI/Process) or directly to local APIs (Ollama/Forge).

## Resource Allocation

### GPU Usage
- **Forge**: 10-12 GB VRAM
- **Ollama (32B Models)**: 18-22 GB VRAM
- **Axolotl Training**: 24GB+ (Full 4090 usage, usually requires stopping others)

**Strategy**: Context switching! Don't run generation or training simultaneously.

## Development Workflow

1. **Start Services**:
   ```bash
   # Main stack
   docker-compose -f deployments/docker-compose/lab/docker-compose.yml up -d
   ```

2. **Run Tools**:
   ```bash
   # Generate Data
   pixi run llm-gen --topic "test"
   # Train Model (Axolotl)
   accelerate launch ... (inside container)
   ```

## Advantages of 32B Model Stack

✅ **Reasoning Capability**: `deepseek-r1` provides chain-of-thought analysis.
✅ **Syntax Mastery**: `qwen2.5-coder` adheres strictly to language specs.
✅ **Efficiency**: Optimized for RTX 4090 local inference.

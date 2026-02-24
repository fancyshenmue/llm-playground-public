# WSL Migration Guide

## Overview

This document covers the migration of llm-playground from Windows 11 to WSL Ubuntu 24.04.

## Key Changes

### 1. Platform Configuration

**pixi.toml**
```toml
# Changed from win-64 to linux-64
platforms = ["linux-64"]
```

### 2. Dependency Resolution

Removed `torchvision` due to conda conflict:
- `torchvision` requires `zlib < 1.3` (via ffmpeg)
- `nodejs 22.*` requires `zlib >= 1.3.1`

**Solution:** Removed torchvision from dependencies as it wasn't actively used.

### 3. Cross-Platform Python Path Detection

Updated Go code to detect Python executable location:

**Before:**
```go
pythonPath := filepath.Join(venvPath, "python.exe")  // Windows only
```

**After:**
```go
pythonPath := filepath.Join(venvPath, "python.exe")
if _, err := os.Stat(pythonPath); os.IsNotExist(err) {
    pythonPath = filepath.Join(venvPath, "bin", "python")  // Linux fallback
}
```

Files updated:
- `cmd/go/llm-utils/cmd/tag.go`
- `cmd/go/llm-utils/cmd/train.go`

### 4. Service Connectivity

**WSL → Windows Services**

Services running on Windows need special IP address:

```yaml
# config.yaml
ollama:
  base_url: "http://localhost:11434"  # Docker Desktop forwards to WSL

forge:
  base_url: "http://172.19.128.1:7861"  # Windows host IP
```

**Find Windows host IP:**
```bash
cat /etc/resolv.conf | grep nameserver | awk '{print $2}'
```

### 5. Kohya_ss Setup on WSL

**Installation:**
```bash
cd ~/dev
git clone https://github.com/bmaltais/kohya_ss.git
cd kohya_ss

# Initialize git submodules
git submodule update --init --recursive

# Create pixi.toml
cat > pixi.toml << 'EOF'
[workspace]
name = "kohya_ss"
channels = ["pytorch", "nvidia", "conda-forge"]
platforms = ["linux-64"]

[dependencies]
python = "==3.10.11"
pytorch = "==2.3.1"
torchvision = "==0.18.1"
pytorch-cuda = "==12.1"
pip = ">=23.0"
git = "*"

[tasks]
install-deps = "pip install -r requirements.txt"

[system-requirements]
cuda = "12"
EOF

# Install
pixi install
pixi run install-deps
pixi run pip install onnxruntime  # For WD14 tagger
```

**Update llm-utils config:**
```yaml
kohya:
  root_path: "$HOME/dev/kohya_ss"
  venv_path: "$HOME/dev/kohya_ss/.pixi/envs/default"
```

### 6. GPU Access

Verified CUDA access in WSL:
```bash
nvidia-smi  # Check GPU
python -c "import torch; print(torch.cuda.is_available())"  # Should return True
```

## Issues Resolved

### 1. Training Parameter Conflicts

**Problem:** Config has both `"epoch"` and `"max_train_epochs"`

**Solution:** Added `"epoch"` to skipKeys in `train.go`:
```go
skipKeys := map[string]bool{
    "epoch": true,  // GUI display field only
    // ...
}
```

### 2. Text Encoder Caching Conflict

**Problem:** Cannot cache text encoder outputs while training text encoder

**Solution:** Auto-add `--network_train_unet_only`:
```go
if hasCacheTextEncoder {
    scriptArgs = append(scriptArgs, "--network_train_unet_only")
}
```

### 3. Deprecated SDXL Parameter

**Problem:** `--sdxl_cache_text_encoder_outputs` not recognized

**Solution:** Added key mapping:
```go
keyMap := map[string]string{
    "sdxl_cache_text_encoder_outputs": "cache_text_encoder_outputs",
}
```

## Verification Checklist

- [x] GPU accessible (CUDA 12.7)
- [x] Pixi environment installs
- [x] llm-utils builds successfully
- [x] Ollama connection works
- [x] Forge connection works
- [x] Kohya_ss scripts execute
- [x] Data generation works
- [x] Image tagging works
- [x] LoRA training works
- [x] AnythingLLM integration

## Performance

WSL provides near-native Linux performance with full GPU access:
- CUDA operations: ~95% of native Linux
- File I/O: Excellent (using Linux filesystem)
- Network: Good (with proper IP configuration)

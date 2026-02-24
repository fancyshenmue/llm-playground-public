# Pixi Environment Management

This document outlines the workflow for managing the cross-platform environment using [Pixi](https://pixi.sh). Our project relies on `pixi.toml` to manage complex dependencies including Python, CUDA, Go, and Node.js.

## Environment Reset & Installation

If you encounter dependency conflicts or want a clean slate, follow these steps:

### 1. Clean Local State
Remove the local environment directory and the lock file to ensure a fresh resolution:
```bash
# Remove the environment folder
rm -rf .pixi

# Remove the lock file for a fresh dependency resolution
rm pixi.lock
```

### 2. Install Dependencies
Initialize the environment based on `pixi.toml`. This will create separate environments for the main project and the web interface:
```bash
pixi install
```

### 3. Using Pixi Shell
You can enter an interactive shell for a specific environment:
- **Main AI/ML Environment**:
  ```bash
  pixi shell -e default
  ```
- **Open WebUI Environment**:
  ```bash
  pixi shell -e webui
  ```

## GPU Verification

We use a specialized script to ensure that PyTorch is correctly linked with the NVIDIA CUDA drivers provided via Pixi.

### Run GPU Check
Execute the verification script (now in the `app/` directory) within the Pixi environment:
```bash
pixi run python app/check_gpu.py
```

### What This Checks
The `app/check_gpu.py` script validates:
- **CUDA Availability**: Whether PyTorch can see your NVIDIA GPU.
- **GPU Model**: Displays the name of the detected hardware (e.g., RTX 3080).
- **Library Versions**: Confirms the specific versions of CUDA and PyTorch being used.

> [!TIP]
> If you see a warning that only the **CPU version** is detected, ensure your NVIDIA drivers are up to date on your host machine, as Pixi's `pytorch-cuda` dependency still requires a compatible base driver.

### 4. Open WebUI
Start the Ollama Web interface (runs in an isolated environment to avoid dependency conflicts).

**Option A: Direct Run**
```bash
pixi run -e webui serve-webui
```

**Option B: Inside Pixi Shell**
If you are already inside `pixi shell -e webui`, the `open-webui` binary is in your PATH. You can run the server directly:
```bash
open-webui serve
```
*(Note: `serve-webui` is a Pixi task name, not a command itself. Tasks are run via `pixi run <task>`.)*
Then open `http://localhost:8080` in your browser.

## Project Stack (via pixi.toml)
- **Directory Structure**: 
    - `app/`: Python scripts and logic.
    - `images/`: Generated outputs and comparison targets.
    - `documents/`: Documentation and guides.
- **Runtime**: Python 3.11, Node.js 22, Go 1.24
- **AI/ML**: PyTorch (with CUDA 12.4 support), LangChain, Ollama
- **Data**: NumPy, Pandas, Pydantic, Pillow

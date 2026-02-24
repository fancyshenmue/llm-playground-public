# Full Setup Guide: Video Generation (SDXL + AnimateDiff)

This comprehensive guide covers everything from starting the service to advanced video generation.

## 0. How to Start the Service
To start the ComfyUI backend using Pixi, run the following command in your terminal:
```bash
pixi run dev
```

## 1. Initial UI Setup (Language)
If you need to switch the ComfyUI interface to Chinese (or another language):
1.  Click the **Settings** (gear icon) on the right menu.
2.  Find the **Language** dropdown.
3.  Select **Chinese** (or your preferred language).
4.  The interface will refresh automatically.

## 2. Required Custom Nodes
Install these via the **ComfyUI-Manager** (already installed in your `custom_nodes` folder):
*   **ComfyUI-AnimateDiff-Evolved**: The core engine for video.
*   **ComfyUI-VideoHelperSuite**: Essential for exporting to MP4/GIF.

## 3. Essential Models & Downloads
### A. Base Checkpoint (SDXL)
Place in: `ComfyUI/models/checkpoints/`
*   **Juggernaut-XL v9**: [Download from Civitai](https://civitai.com/models/133005/juggernaut-xl) (or your preferred SDXL model).

### B. Motion Models (AnimateDiff)
Place in: `ComfyUI/models/animatediff_models/`

#### Manual Download (CLI):
If you want to download via terminal, run these commands (the first line ensures the folder exists):
```bash
# Create the directory first
mkdir -p $HOME/dev/ComfyUI/models/animatediff_models/

# SDXL Base Motion Model
wget -O $HOME/dev/ComfyUI/models/animatediff_models/mm_sdxl_v10_beta.ckpt https://huggingface.co/guoyww/animatediff/resolve/main/mm_sdxl_v10_beta.ckpt

# Lightning (Fast) Motion Model
wget -O $HOME/dev/ComfyUI/models/animatediff_models/animatediff_lightning_4step_comfyui.safetensors https://huggingface.co/ByteDance/AnimateDiff-Lightning/resolve/main/animatediff_lightning_4step_comfyui.safetensors
```

## 4. Advanced "Gen2" Workflow
We are using the latest Gen2 node architecture for maximum stability.

### The "Gen2 Sandwich" Structure:
1.  **Load AnimateDiff Model**: Select `mm_sdxl_v10_beta.ckpt`.
2.  **Apply AnimateDiff Model (Adv.)**: Set `start_percent` to 0 and `end_percent` to 1.
3.  **Use Evolved Sampling**: **THE BRIDGE**.
    *   Connect `Checkpoint (MODEL)` ➔ `Use Evolved Sampling (model)`.
    *   Connect `Apply AD Model (M_MODELS)` ➔ `Use Evolved Sampling (m_models)`.
    *   Connect `Use Evolved Sampling (MODEL)` ➔ `KSampler (model)`.

## 5. Recommended Sampler Settings
*   **Steps**: 20 (Standard) or 6 (Lightning).
*   **CFG**: 8.0 (Standard) or 1.0 (Lightning).
*   **Sampler**: `euler`.
*   **Scheduler**: `normal`.
*   **Beta Schedule**: **`autoselect`** (Recommended to avoid validation errors).

## 6. Common Fixes
*   **"Missing input: pingpong/loop_count"**: Your `Video Combine` node is an old version. Delete it and add a new one from `Add Node -> Video Helper Suite`.
*   **"Missing input: model" in KSampler**: This happens if the Checkpoint is connected directly to AnimateDiff. It **MUST** pass through the `Use Evolved Sampling` node first.
*   **Out of Memory**: Decrease the `Empty Latent Image` resolution to 512x512 if your GPU is struggling.

---
*Last Verified: 2026-01-16*

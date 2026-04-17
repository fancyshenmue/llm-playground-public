# Phase Context: Integrate vllm-mlx with Gemma 4 (31B & 26B) as a Daemon

## Objective
The goal is to integrate `vllm-mlx` to deploy the massive **Gemma 4 31B (Dense)** and **Gemma 4 26B (MoE)** models. Given the extremely capable hardware (M2 Max 96GB Unified Memory), we can easily load these large parameter models in high precision without memory bottlenecks.

Furthermore, we will configure the model inference server to run in the background robustly, acting identically to Linux's `systemd`, by leveraging macOS's native `launchd` daemon manager.

## Proposed Architectural Changes

1. **Dependency Integration**
   - Update `pixi.toml` to add `vllm-mlx` directly via Git to ensure the latest MLX Apple Silicon patches are present.
   - Action: Add `vllm-mlx = { git = "https://github.com/waybarrios/vllm-mlx.git" }` to `[feature.main.pypi-dependencies]`.

2. **Task Configuration (High-End Models)**
   - Add two specific tasks in `pixi.toml`:
     - `serve-gemma-31b`: For `gemma-4-31b-8bit` (Requires ~31GB of unified memory out of your 96GB, leaving plenty for context and system).
     - `serve-gemma-26b`: For `gemma-4-26b-8bit` (MoE format).
   - Command implementations will point to `vllm-mlx serve mlx-community/... --port 8000`

3. **Background Daemon (Linux `systemd` Equivalent)**
   - macOS does not use `systemd`; its equivalent is **`launchd`**.
   - We will construct a native `.plist` agent file (e.g., `com.llmplayground.vllm.plist`) mapped to run your `pixi run serve-gemma-31b` command.
   - This Configuration will:
     - Keep the Server alive in the background.
     - Auto-restart if it crashes.
     - Pipe Standard Output (logs) and Error Output into a dedicated `logs/` directory.
   - We will add helper Pixi tasks (e.g., `daemon-install`, `daemon-start`, `daemon-stop`, `daemon-logs`) to give you a `systemctl`-like daily experience without needing to memorize `launchctl` commands.

## Action Plan
- Await user approval of this updated, high-spec context.
- Once approved, progress to PLAN phase to set up the Pixi config and generate the Daemon scripts/plists.

# Implementation Plan: vllm-mlx Daemonization for Gemma 4 (31B/26B)

## Checklist

- [x] 1. Update Dependencies
  - File: `pixi.toml`
  - Action: Add `vllm-mlx = { git = "https://github.com/waybarrios/vllm-mlx.git" }` under `[feature.main.pypi-dependencies]`.

- [x] 2. Update Pixi Tasks
  - File: `pixi.toml`
  - Action: Add `serve-31b = "vllm-mlx serve mlx-community/gemma-4-31b-8bit --port 8000"` to `[tasks]`.
  - Action: Add `serve-26b = "vllm-mlx serve mlx-community/gemma-4-26b-8bit --port 8000"` to `[tasks]`.
  - Action: Add `daemon-install = "bash scripts/daemon-install.sh"` to `[tasks]`.
  - Action: Add `daemon-start = "launchctl load -w ~/Library/LaunchAgents/com.llmplayground.vllm.plist"` to `[tasks]`.
  - Action: Add `daemon-stop = "launchctl unload -w ~/Library/LaunchAgents/com.llmplayground.vllm.plist"` to `[tasks]`.
  - Action: Add `daemon-logs = "tail -f ~/.llm-playground/logs/vllm.log"` to `[tasks]`.

- [x] 3. Create Daemon Setup Script
  - File: `scripts/daemon-install.sh` (Create NEW file)
  - Action: Write a bash script that dynamically generates `com.llmplayground.vllm.plist`.
  - Details: 
    - Automatically discovers the absolute path of the project.
    - Uses `which pixi` to find the absolute Pixi resolver path.
    - Sets `WorkingDirectory` to the `llm-playground` root path.
    - Sets `ProgramArguments` to execute `pixi run serve-31b`.
    - Enables `KeepAlive` for auto-restart on crashes.
    - Routes `StandardOutPath` and `StandardErrorPath` to `~/.llm-playground/logs/vllm.log`.
    - Copies the generated plist to `~/Library/LaunchAgents/`.
  - Action: Ensure script has executable permissions (`chmod +x scripts/daemon-install.sh`).

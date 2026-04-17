# vllm-mlx Operations

## Environment Handling

The environment heavily leans on Pixi to isolate python dependencies alongside `vllm-mlx` bleeding-edge GitHub pulls. Since Apple Silicon (`osx-arm64`) holds all hardware logic for MLX natively, there are no virtual environments containing CUDA constraints on this host runtime.

## Daemon Lifecycle

The `vllm-mlx` service leverages the underlying `launchd` mechanism present on macOS rather than `systemd` to sustain constant lifecycle checks.

| Lifecycle Step     | Pixi Command              | Corresponding Native execution                                                                                                                     |
| ------------------ | ------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Install Config** | `pixi run daemon-install` | Creates the native `.plist` agent representing the daemon within `~/Library/LaunchAgents` via our `scripts/daemon-install.sh`.                     |
| **Start Service**  | `pixi run daemon-start`   | Tells the macOS agent kernel to `launchctl load` the model to memory using the daemon configurations. KeepAlive ensures it is restored on crashes. |
| **Stop Service**   | `pixi run daemon-stop`    | Initiates `launchctl unload`, freeing up the unified memory mapped to the model arrays.                                                            |
| **View Logs**      | `pixi run daemon-logs`    | Binds to `tail -f ~/.llm-playground/logs/vllm.log`, piping Standard Output cleanly regardless of daemon shell context.                             |

## Serving Manual Models

If debugging the lifecycle manager, the `pixi` platform exposes raw serves that tie up the local GUI terminal foreground:

- **31B Dense Model**: `pixi run serve-gemma-31b`
- **26B MoE Model**: `pixi run serve-gemma-26b`

Both commands execute locally on port `8000`. By replacing traditional manual scripts with these configurations, you guarantee precise model targets identical to those mapped out via the background daemon.

## Zero-Day Model Workarounds (Gemma 4 Edge Case)

When deploying bleeding-edge models (e.g., Gemma 4 released days prior to engine updates), the `vllm-mlx` and `mlx_lm` parser layers might lack precise class mappings (e.g., `ModuleNotFoundError: No module named 'mlx_lm.models.gemma4'`).

To bypass this without waiting for native PyPI updates, we leverage **HuggingFace Cache Hot-Patching**:
1. Download the zero-day model via the daemon until it crashes.
2. Locate the model cache directory: `~/.cache/huggingface/hub/models--mlx-community--<model-name>/snapshots/<hash>/config.json`
3. Edit the `config.json` manually to hijack the model type:
   - Change `"model_type": "gemma4"` to `"gemma3"`
   - Change `"model_type": "gemma4_text"` to `"gemma3_text"`
   - Change `"model_type": "gemma4_vision"` to `"gemma3_vision"`
   - Change strict dataclass breaks like `"use_bidirectional_attention": "vision"` to `"use_bidirectional_attention": true`
4. Restart the daemon via `pixi run daemon-restart`. The parser will happily parse the model through its legacy but architecturally compatible parsing trees.

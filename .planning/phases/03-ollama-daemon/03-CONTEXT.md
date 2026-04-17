# Phase 03: Ollama Subsystem (Gemma 4 Native)

## Architectural Shift
During Phase 02, `vllm-mlx` experienced zero-day PyPi update lagging for Gemma 4 configuration schemas. While hot-patching strings allowed basic generation, the user requested switching back to a highly stable platform: **Ollama**.

Ollama possesses native C++/Metal day-one support for Gemma 4 (including `gemma4:31b` and `gemma4:26b`). Rather than relying on global installations (`brew install`), we inject `ollama` via Conda-Forge into the `.pixi` sandbox. This adheres to the Strict GSD rules of 100% reproducible environments.

## Services
- **Ollama Daemon**: `com.llmplayground.ollama.plist` executed via `launchd`.
- **Paths**: Models are stored discretely at `~/.llm-playground/ollama-models`.
- **Ports**: Runs strictly on `0.0.0.0:11434`.

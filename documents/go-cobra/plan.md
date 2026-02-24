# Go Cobra CLI Tool: `llm-utils`

This document details the architecture and design of the `llm-utils` Go-based CLI tool, which is integrated into the `llm-playground` polyglot project.

## 1. Project Structure

The project follows a structure that separates language-specific binaries, internal logic, and shared resources, with `pixi` as the environment manager.

```text
llm-playground/
├── cmd/
│   └── go/                    # Go executable entry points
│       └── llm-utils/         # LLM Utility CLI
│           ├── cmd/           # Cobra command definitions (chat, data-gen, etc.)
│           ├── config/        # Configuration loading & structs
│           ├── config.yaml    # Local configuration
│           └── main.go        # Entry point calling cmd.Execute()
├── internal/
│   ├── go/                    # Private Go application logic
│   │   └── api/               # API clients (Ollama, Forge, etc.)
│   ├── py/                    # Private Python logic
│   └── node/                  # Private Node.js logic
├── dataset/                   # Data artifacts and datasets
├── deployments/               # Deployment configurations (e.g., Docker, Axolotl)
├── output/                    # Generated outputs
├── go.mod                     # Go module (root)
├── go.sum
└── pixi.toml                  # Environment & task management
```

## 2. CLI Command Design

The tool is invoked as `llm-utils [command] [flags]`.

### Implemented Commands
- `llm-utils data-gen` : Generate datasets of images using Forge, with optional prompts from Ollama.
    - Flags: `--topic`, `--total`, `--lora`, `--weight`, `--prompt`, `--no-caption`, `--output`.
- `llm-utils chat [model]` : Start an interactive chat session or send a single prompt to Ollama.
    - Flags: `--prompt` (for single turn), `--verbose`.
- `llm-utils models` : List available models on the configured provider (Ollama).
- `llm-utils tag` : Auto-tag images in a directory using WD14 Tagger (via Forge).
- `llm-utils analyze` : Analyze an image using a vision model.
- `llm-utils train` : Trigger a training session (e.g., via Kohya_ss API or similar).

## 3. Pixi Integration

`pixi` manages the Go environment and provides tasks for building and running the tool.

### `pixi.toml` Tasks:
- `build-llm`: Builds the Go binary (`go build -o bin/llm-utils ./cmd/go/llm-utils`).
- `llm-help`: Runs the help command (`go run ./cmd/go/llm-utils --help`).
- `llm-test`: Runs a quick chat test.

## 4. Development Workflow

1.  **Environment Setup**:
    - Run `pixi install` to set up Go, Python, and Node.js environments.

2.  **Building**:
    - Run `pixi run build-llm` to compile the binary to `bin/llm-utils`.

3.  **Running**:
    - Use the binary: `./bin/llm-utils chat ...`
    - Or via `go run`: `go run ./cmd/go/llm-utils chat ...`

## 5. Configuration

Configuration is handled via `config.yaml` located in `cmd/go/llm-utils` (or the current execution directory). It defines endpoints for Ollama, Forge, and other settings.

## 6. Architecture Rationale

- **`cmd/go/llm-utils`**: Encapsulates the specific CLI application. `cmd` package inside holds the CLI interface logic (Cobra).
- **`internal/go`**: Contains the business logic and API clients, reusable across different Go tools in the project but not intended for external import.
- **Root `go.mod`**: Manages dependencies for all Go code in the repository.

---
*Updated on 2026-02-09*

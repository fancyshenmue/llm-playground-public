# Multi-Language Project Structure Plan: `llm-playground`

This document outlines the current directory structure and management strategy for this polyglot project (Python, Node.js, and Golang), using **Pixi** as the unified package and environment manager.

## 1. Unified Directory Layout

To ensure clarity and scalability, we follow a structure that separates language-specific binaries, internal logic, and shared resources.

```text
llm-playground/
├── .agent/                # Agent workflows and configurations
├── .pixi/                 # Pixi environment (managed automatically)
├── cmd/                   # Unified entry points for all languages
│   ├── go/                # Go executable entry points
│   │   └── llm-utils/     # Main Go CLI Utility
│   │       ├── cmd/       # Cobra command definitions
│   │       ├── config/    # Configuration handling
│   │       ├── config.yaml
│   │       └── main.go
│   ├── node/              # Node.js applications & tools
│   │   ├── llm-utils-desktop/ # Electron/Frontend Application
│   │   │   ├── src/       # Source code (React/TypeScript)
│   │   │   ├── electron.vite.config.ts
│   │   │   └── package.json
│   │   └── onyx-mcp-server/   # MCP Server Implementation
│   └── py/                # Python CLI entry points
│       └── llm-utils/     # Python CLI Utility
│           ├── commands/  # Command implementations
│           ├── config.yaml
│           └── main.py
├── dataset/               # Data artifacts and datasets
├── deployments/           # Deployment configurations
│   └── docker-compose/    # Docker Compose setups
│       └── axolotl/       # LLM Training configs (Axolotl)
├── documents/             # Project documentation
│   ├── structure/         # This structural plan
│   └── ...                # Other documentation
├── images/                # Image assets/resources
├── internal/              # Private shared logic (not for public export)
│   ├── go/                # Internal Go packages
│   │   └── api/           # API definitions/handlers
│   ├── node/              # Internal Node.js shared logic
│   │   ├── services/      # Shared services
│   │   ├── index.ts
│   │   └── types.ts
│   └── py/                # Internal Python shared logic
│       ├── utils/         # Python utility modules
│       └── __init__.py
├── output/                # Generated outputs (e.g., training results)
├── scripts/               # Standalone utility scripts
├── .gitignore             # Unified git ignore for all languages
├── go.mod                 # Go module definition (root)
├── go.sum                 # Go dependencies checksums
├── pixi.lock              # Pixi lock file
├── pixi.toml              # Unified environment & task management
└── README.md              # Project overview
```

## 2. Language Management via Pixi

Each language is managed as a feature or dependency within `pixi.toml`.

### Python
- Managed via `conda-forge` or `pypi-dependencies`.
- **CLI Tools**: `cmd/py/llm-utils/` for the main Python utility.
- **Shared Logic**: `internal/py/` for reusable modules.
- **Key Tasks**: Training, data processing scripts.

### Golang
- Managed via `conda-forge` or system Go.
- **Main App**: `cmd/go/llm-utils/` is the primary Go CLI.
- **Internal Logic**: `internal/go/` contains shared API and backend logic.
- **Tasks**: `build-llm` (builds the Go binary), regular `go build`/`go test`.

### Node.js / TypeScript
- Managed via `conda-forge` (installing `nodejs`, `npm`/`pnpm`).
- **Frontend App**: `cmd/node/llm-utils-desktop/` (Electron + React/Vite application).
- **MCP Server**: `cmd/node/onyx-mcp-server/`.
- **Shared Logic**: `internal/node/` contains shared services and types.

## 3. Communication & Integration

- **Inter-Process**: Go tools may invoke Python scripts or interact with Node.js services via local APIs or CLI arguments.
- **Shared Configuration**: Standardized config files (e.g., `config.yaml`) are present in each language's directory to maintain consistent settings.
- **Data**: Datasets and outputs reside in `dataset/` and `output/` respectively, accessible by all tools.
- **Deployments**: Docker Compose configurations in `deployments/` handle containerized environments, specifically for tasks like LLM training (Axolotl).

## 4. Key Considerations

### A. Git Ignore Strategy
A unified `.gitignore` handles noise from all languages:
- **Go**: `bin/`, `dist/`
- **Python**: `__pycache__/`, `.venv/`, `.ipynb_checkpoints/`
- **Node.js**: `node_modules/`, `out/`, `dist/`, `.vite/`
- **General**: `.env`, `.DS_Store`, `.pixi/`

### B. Shared Configuration
- Configuration files (`config.yaml`) are localized to each application instance (`cmd/go/llm-utils`, `cmd/py/llm-utils`, `cmd/node/llm-utils-desktop`) but follow similar schemas where applicable.

### C. Task Management
- use `pixi task list` to discover available commands across the project (e.g., building the Go app, running the frontend dev server, starting python scripts).

---
*Updated on 2026-02-09*

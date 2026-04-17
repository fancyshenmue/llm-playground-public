# LangGraph Enterprise Agent Operations

## Managing the PostgreSQL Infrastructure
This environment requires persistent memory mapping through `pgvector` hosted in Docker.

```bash
# Start the persistence layer (background)
make langgraph-db-up

# Stop and wipe volatility
make langgraph-db-down
```

## Running the API Layer
To prevent collision with the standard stateless lab on 8000, start the Enterprise Service strictly using its dedicated make target:

```bash
make langgraph-enterprise-api-dev
```
This serves the API at `localhost:8001`, enabling full `[Code <-> Reflect]` logging in standard output.

## Running the Real-World Agent (MCP CLI)
The project includes a robust Terminal-based agent capable of autonomous code writing via Model Context Protocol (MCP) servers.

```bash
# Optional but recommended: Open the trace observatory first
make phoenix-up

# If you forget the CLI structure, you can view the usage via:
make langgraph-agent

# Start the agent directly from the terminal
pixi run agent "build a go server in tmp/app"
```

### Configuring MCP Plugins
The agent's capabilities are loaded dynamically from `cmd/py/llm-utils/enterprise_api/mcp_servers.json`.
To add new functionalities (e.g., `chrome-devtools` or `context7`), structurally insert them under `"mcpServers"` formatted exactly as they appear in standard Claude Desktop config files.

> [!CAUTION]
> **IDE Hot-Reloading for MCP:** If you are testing your MCP servers directly inside the Gemini/Anthropic VS Code Chat window (by modifying global configurations like `~/.gemini/antigravity/mcp_config.json`), the IDE Extension Host caches the tools at session start. You **MUST** run the VS Code command `Developer: Reload Window` and open a New Chat to hot-reload dynamically added MCP tools in the chat window.

## Observability & Tracing boundaries
Both the CLI (`pixi run agent`) and the Enterprise API (`make langgraph-enterprise-api-dev`) natively inject the OpenInference `LangChainInstrumentor`. This maps all internal reasoning, tool calls, and iteration loops directly out to the Arize Phoenix Observatory under the `langgraph-mcp-agent` project.

> [!NOTE]
> - By default, Phoenix maps the UI port inside Docker (`6006`) to your local machine port `16006` to avoid conflicts. Always visit `http://localhost:16006` to view the trace graph.
> - **Trace Context Limitations:** Executing native or MCP operations directly via the VS Code AI Assistant (Chat interface) handles requests natively in the IDE and bypasses our Python `OpenInference` wrappers. Therefore, IDE-driven actions will not appear in the Phoenix dashboard.

## Example Test Prompts
Use these specialized Prompts to test the Agent's reasoning, tool-calling (MCP), and code execution abilities within the ReAct loop:

### 1. The Decorator Test
```text
Write a Python decorator called @measure_time to calculate the execution time of any function in milliseconds. Then, write a dummy function sleep_test that simulates a delay, apply the decorator to it, and call it at the very bottom of the script to print the result.
```

### 2. The Auto-Coder Filesystem Test
```text
Write a Python script that creates a text file named langgraph_magic.txt inside the /tmp/ directory, containing the text 'Hello from Gemma 4 Auto-Coder!'. After writing to the file, have the script read the file back and print its contents to the console.
```
*(After it successfully completes, you can go to your terminal and type `cat /tmp/langgraph_magic.txt` to verify that the file actually exists and MCP tool calling worked!)*

### 3. The Algorithmic State Test
```text
Please write a Python class FibonacciGenerator that contains a method to generate and print the first 15 numbers in the Fibonacci sequence. Instantiate the class and execute the method at the bottom of the script.
```

## Phase 09 Fully Autonomous Closed-Loop Coder
Phase 09 introduces a completely isolated auto-coder logic block operating completely autonomously, enforcing testing and reflection (a pure Claude Code clone context mechanism).

```bash
# View CLI usage:
make langgraph-autocoder

# Recommended: Use --dir to explicitly specify the project directory
pixi run autocoder --dir /Users/charleshsu/dev/lab/langgraph/app

# One-shot mode (non-interactive): provide the prompt as a positional argument
pixi run autocoder --dir /Users/charleshsu/dev/lab/langgraph/app "implement CRUD for Prompt entity"

# Multiple directories:
pixi run autocoder -d /path/to/project -d /path/to/shared-lib
```

> [!TIP] 
> Because this logic uses a `max_retries` counter embedded within LangGraph constraints, if the `TestNode` fails to successfully compile your code, it will automatically route back to the sub-agent and attempt to fix its own bugs until it hits its maximum retries.

### Directory Resolution Priority
The agent resolves allowed directories in this priority order:

1. **`--dir` / `-d` flag** (most reliable): Explicitly provided, `realpath`-resolved.
2. **Regex extraction** (fallback): Auto-extracted from the prompt string. Supports backtick, quote, and whitespace-delimited absolute paths.
3. **Interactive `+/path`** (REPL only): Manually added during the permission approval prompt.

> [!CAUTION]
> **Do NOT rely solely on regex extraction.** Markdown-formatted prompts with backtick-wrapped paths (`` `/path/to/dir` ``) were historically missed by the regex. Always use `--dir` for production runs.

### No-Op Detection (`test_node`)
The `test_node` includes three layers of validation before marking a run as "passed":

1. **Crash detection**: If the coder sub-agent threw an exception (`CRASH:` prefix).
2. **Give-up detection**: If the coder responded with phrases like "I cannot proceed" without writing any files.
3. **File existence check**: Expected new files (extracted from the plan via regex) are verified with `os.path.exists()`.

If any check fails, the `reflect_node` → `coder_node` retry loop is triggered (up to 3 retries).

### Tool Sanitizer Middleware (`tool_sanitizer.py`)
Local models like Gemma 4 frequently hallucinate tool argument types — passing JSON objects where MCP expects raw strings. The sanitizer intercepts these mismatches before they hit the MCP server:
- **Auto-serialization**: Fields like `content`, `newText`, `oldText` are automatically `json.dumps()`'d if the model passes them as dicts/lists.
- **Nested edit support**: Handles `edits[]` arrays in `edit_file` tool calls.

> [!CAUTION]
> **Never call `inner_tool._arun()` directly from a tool wrapper.** LangChain's private `_arun`/`_run` methods require a `config: RunnableConfig` keyword argument that is injected by the framework. If you bypass the framework by calling `_arun` directly, you will get `TypeError: missing required keyword-only argument 'config'`. Always use `inner_tool.ainvoke(args, config=config)` (the public API) instead.

## Phase 15 Enterprise AutoCoder (React Lab UI)
The Phase 15 AutoCoder integrates the Autonomous Agent directly into the frontend. To access the live streamed UI workflow, follow this operational sequence:

```bash
# 1. Bring up the PostgreSQL memory persistence layer
make langgraph-db-up

# 2. Launch the Enterprise API to host the SSE Auto-Coder endpoint
pixi run enterprise-api-dev

# 3. In a separate terminal, launch the React Frontend Lab
make autocoder-lab-dev
```

You can then navigate to `http://localhost:5173` and click the **Enterprise Auto-Coder** tab to begin visual, multi-agent automated coding.

> [!TIP]
> **Direct Project Access**: The agent operates directly on the project directories specified via `--dir`. There is no ephemeral sandbox — the MCP filesystem server receives only the project directories, keeping its tool descriptions clean and preventing local models from confusing sandbox paths with project paths.

### Configuration Model Targeting
The AutoCoder dynamically provisions model classes at runtime. First, create your local configuration from the example template:

```bash
cp cmd/py/llm-utils/config.yaml.example cmd/py/llm-utils/config.yaml
```

Then ensure the `autocoder` block in your `cmd/py/llm-utils/config.yaml` maps to the correct local Ollama models:

```yaml
# --- Enterprise AutoCoder Settings ---
autocoder:
  planner_model: "gemma4:31b"
  coder_model: "gemma4:26b"
  evaluator_model: "qwen3.5:35b-a3b"
```

# Phase 08: Real-World File System Agent (CLI)

## 1. Model Context Protocol (MCP) Integration (`mcp_client.py`)
- [x] Create `mcp_servers.json` configuration config tracking standard servers.
- [x] Create `cmd/py/llm-utils/enterprise_api/mcp_proxy.py`.
- [x] Implement MCP Client connection to spawn and hook STDIO for requested servers.
- [x] Convert MCP tools into LangChain compatible `BaseTool` objects to expose to `gemma4:26b`.

## 2. ReAct Graph Setup (`cli_agent.py`)
- [x] Create `cmd/py/llm-utils/enterprise_api/cli_agent.py`.
- [x] Wrap the Ollama `gemma4:26b` model with `bind_tools()`.
- [x] Utilize LangGraph `create_react_agent` to build the loop `[Agent -> Tool Node -> Agent]`.
- [x] Mount the `AsyncPostgresSaver` Checkpointer to persist the CLI agent's memory thread.

## 3. Typer CLI Integration (`main.py`)
- [x] Update `cmd/py/llm-utils/main.py` with a new `@app.command() def agent(task: str)`.
- [x] Implement `rich.console` and `rich.live` streaming to render an interactive CLI UX. The user should see LLM thought outputs and tool execution logs clearly (e.g. `[bold green]🛠️ Tool executing:[/bold green] mcp-server-filesystem.run_command`).
- [x] Add the `pixi` alias in `pixi.toml` -> `agent = "python cmd/py/llm-utils/main.py agent"`.

## 4. Telemetry & Observability (OpenInference)
- [x] Initialize `Phoenix` instrumentation (`MLflow` or `LangChainInstrumentor`) within the Typer command context.
- [x] Verify that MCP JSON-RPC payload inputs (e.g. file paths and shell commands) are correctly wrapped as LangChain BaseTool inputs so they natively appear in the `arizephoenix` UI timeline.

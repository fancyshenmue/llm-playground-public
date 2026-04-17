# Phase 08: Real-World File System Agent (e.g. Claude Code / Devin Clone)

## Goal
Evolve the isolated sandbox Auto-Coder from Phase 07 into a fully-fledged CLI/Workspace Agent capable of autonomous full-stack development within the host file system (e.g. creating directories, writing Go code, executing `go mod init`).

## Discussion & Architectural Choices

To achieve a true "Claude Code" level of autonomy, the LangGraph engine must shift from a rigid `Context -> Code -> Subprocess` pipeline to a highly dynamic **Tool-Calling ReAct Loop**.

### 1. The Core Paradigm Shift
Instead of forcing the LLM to output raw code strings to be caught by a generic sandbox, the Agent must be equipped with **System Actions (Tools)**:
- `TerminalTool`: Executes ad-hoc Bash commands (e.g., `mkdir -p /tmp/langgraph/app`, `go build`, `npm install`). 
- `FileWriteTool`: Writes precisely to specific file paths.
- `FileReadTool`: Analyzes existing code before making changes.

### 2. LangGraph ReAct Architecture
The graph will become a loop where `Node A` generates a ToolCall, `Node B` executes it in the OS, and it loops back until the LLM decides the overarching goal (e.g. "Build a Golang CRUD API") is complete.
`[ Agent Brain ] <--> [ OS Tools Evaluator ]`

### 3. Interface Chosen: CLI-First (Typer Integration)
**Decision**: Option A. We will integrate a new Typer command into the existing `llm-utils` CLI tool (e.g. `pixi run agent "build gin api in tmp/langgraph/app"`).
**Why**: This mirrors Claude Code/Devin perfectly, running directly within the user's terminal environment where it can natively access file paths, output rich console text (using `rich` library), and execute system commands fluidly.

## The Toolkit (Model Context Protocol - MCP)
Rather than writing hard-coded Python `@tool` decorators for file I/O, the Agent will act as an **MCP Client**. 
By loading standard MCP Servers (via `npx` or python modules depending on the configuration), the LLM can dynamically gain access to tools like:
1. `mcp-server-filesystem` (Read/Write directories safely)
2. `chrome-devtools` (Browser manipulation/scraping)
3. `context7` (Real-time Documentation querying)

**Configuration**: We will read from a standard `mcp_servers.json` (similar to Claude Desktop/Claude Code).

### Observation Service / Telemetry
Since the MCP streams JSON-RPC, we can easily pipe the requests through our existing `arize-phoenix` trace setup. Every time the Agent requests a Tool through MCP, LangChain/OpenInference will automatically log the invocation, giving you a full "Timeline View" of the agent's behavior.

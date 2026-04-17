# Phase 09 Execution Plan (Autonomous Loop)

## Objective
Implement an entirely segregated, fully autonomous agent loop that moves beyond basic ReAct tool calling into deterministic workflow control (`Context -> Plan -> Spec -> Code <-> Lint/Test -> Eval -> Commit`).

## Execution Steps

- [x] **Step 1. Sandbox Isolation & Setup**
  - Initialize `.planning/phases/09-autonomous-loop/` to document Context and Plan without disturbing existing documentation.
  - Setup a parallel backend path at `cmd/py/llm-utils/enterprise_api/autonomous` so Phase 07 (`enterprise_api/main.py`) and Phase 08 (`cli_agent.py`) remain untouched.

- [x] **Step 2. Implementation of StateGraph Constraints**
  - **`state.py`**: Create the `AgentState` schema using `TypedDict` supporting tests, memory buffers, and a retry counter.
  - **`nodes.py`**: Implement localized, strictly defined methods:
    - `plan_node`: Defines system architectures and returns precise CLI terminal test strings.
    - `coder_node`: Invokes an internal LangChain LLM equipped with `server-filesystem` MCP tools solely to write code files.
    - `test_node`: Directly executes subprocess tests (e.g. `pytest`) to gather objective test validation metrics.
    - `reflect_node`: AI-driven crash parsing returning repair logic.

- [x] **Step 3. Compile Graph Operations**
  - **`graph.py`**: Wire the node path and implement the conditional execution blocker `max_retries` (Cap at 3 loops) returning back to user to prevent LLM infinite hallucination.

- [x] **Step 4. CLI Routing & Typer Injection**
  - Build `autonomous_agent.py` to instantiate `build_autonomous_graph` using the existing Postgres DB Checkpointer.
  - Inject the command `@app.command() def autonomous(...)` into `cmd/py/llm-utils/main.py`.
  - Add macro aliases in `/Makefile` (`langgraph-autocoder`) and `pixi.toml` (`autocoder`).

- [x] **Step 5. Validation**
  - Execute `pixi run autocoder "test"` ensuring telemetry properly tracks nodes into Arize Phoenix and standard `rich` terminal output accurately prints structured graph statuses.

- [x] **Step 6. Tool Sanitizer Stabilization**
  - Fixed `SanitizedMCPTool` wrapper crashing with `TypeError: StructuredTool._arun() missing 1 required keyword-only argument: 'config'`.
  - **Root Cause**: Calling `inner_tool._arun()` (private API) bypasses LangChain's config injection layer.
  - **Fix**: Replaced with `inner_tool.ainvoke()` / `inner_tool.invoke()` (public API) which propagates `RunnableConfig` through the framework automatically.

- [ ] **Step 7. Heterogeneous Model Integration & Memory Management**
  - **Graph Node Refactor (`graph.py`)**: Bind specific `model_id` assignments to the respective StateGraph nodes (`plan_node` -> `gemma-4:31b`, `coder_node` -> `gemma-4:26b`, `eval_node` -> `qwen3.5:35b-a3b`).
  - **Memory Hook (`LLM Client`)**: Implement `keep_alive: 0` garbage collection hooks when transitioning between models to prevent Apple Silicon VRAM thrashing/RAM fallback.

- [ ] **Step 8. Lab UI Integration (Next Sub-Phase)**
  - Add `POST /api/autonomous/stream` SSE endpoint to `enterprise_api/main.py`.
  - Add "Autonomous Coder" tab to React Lab UI with structured node-event rendering.

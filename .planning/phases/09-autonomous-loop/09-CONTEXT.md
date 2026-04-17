# Phase 09: Fully Autonomous Closed-Loop Coding Agent (Claude Code Clone)

## Goal
Introduce a completely **NEW**, independent advanced coding mode. We strictly preserve the isolated sandbox Auto-Coder (Phase 07) and the standalone general ReAct Agent (Phase 08). Phase 09 introduces a separate, robust, deterministic multi-step state machine explicitly tailored for autonomous software development.

This new subsystem runs parallel to existing agents and introduces explicit LangGraph nodes for each step of a professional software development lifecycle:

`Context -> Plan -> Spec -> [ Code <-> Lint <-> Test <-> Reflect ] -> Eval -> Commit`

## Discussion & Architectural Choices

### 1. Independence from Phase 08
The Phase 08 `create_react_agent` will remain exactly as it is (invoked via `pixi run agent`). For Phase 09, we are building a new `AutonomousAgent` (invoked via `pixi run autocoder`).
By building a new custom `StateGraph`, we enforce strict guardrails for standard coding:

By moving to a custom `StateGraph`, we enforce guardrails:
1. **Forced TDD**: The agent *must* write tests (`SpecNode`) before writing implementation code (`CodeNode`).
2. **Explicit Verification**: Execution cannot proceed to `EvalCommitNode` unless internal validations (`LintTestNode` and `ReflectNode`) pass.
3. **Loop Breakers**: A strict `retry_count` prevents the local models from exhausting compute and context windows on unresolvable errors.

### 2. State Mapping
The `AgentState` (`TypedDict`) will serve as the shared memory for the nodes, replacing the simple `messages` array:
- `objective`: The initial prompt.
- `context`: Gathered file contents and semantic summaries.
- `plan`: Markdown output from the Planner.
- `tests`: Test specs created.
- `lint_output` / `test_output`: Terminal standard out/err results.
- `retry_count`: Integer tracking execution loops.
- `messages`: Standard LangChain message history.

### 3. Execution Interface
Per decision, we will execute this **CLI-first**. 
The `Typer` interface in `cmd/py/llm-utils/main.py agent` will be updated. As the graph transitions from `PlanNode` -> `CodeNode`, the Typer `rich` console will print structured event blocks (`[yellow]Linting...[/yellow]`, `[green]Tests Passed![/green]`), mimicking the aesthetics of `Claude Code` or `Devin`.

Once the CLI flow is perfected and debugged locally against our postgres checkpointer, we can port these exact state transitions to the React Lab UI (WebSockets/SSE) in a future sub-phase.

### 4. Heterogeneous Multi-Model Architecture
To maximize reasoning capabilities and prevent execution loops/hallucinations, the agent architecture employs a multi-model (Heterogeneous) setup:
1. **Plan Node (`gemma-4:31b`)**: Large, dense model designed for foundational system architecture decisions and logical reasoning. Ensures directionality is absolutely correct before execution begins.
2. **Code/Execute Node (`gemma-4:26b`)**: Mixture of Experts (MoE) configuration prioritizing high-speed API/tool calls, code generation, and rapid iterations.
3. **Evaluating Node (`qwen3.5:35b-a3b`)**: Used strictly as an impartial judge. Utilizing a different architecture family breaks "echo chambers" or blind spots that might occur if a Gemma model checks its own code.

*Note: Due to VRAM constraints, this architecture strictly requires explicit API-level memory management (`keep_alive: 0`) during node transitions to ensure only the active model occupies Apple Silicon Unified Memory.*

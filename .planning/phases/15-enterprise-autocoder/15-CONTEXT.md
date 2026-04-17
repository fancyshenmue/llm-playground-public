# Phase 15 CONTEXT: Enterprise AutoCoder

## Architectural Overview & Objectives

The goal of this phase is to elevate the "deterministic autonomous loop" (originally prototyped in Phase 09 as a Typer CLI utility) into a fully productionized, robust Enterprise LangGraph capability. This requires seamless integration with the React Lab UI, hardened state persistence, full-duplex telemetry, and secure MCP operational bounds.

## Technical Scope

Based on the existing `.planning/ROADMAP.md` and `documents/langgraph/architecture.md`, elevating the autonomous coder to production-grade involves:

1. **Lab UI Streaming Integration (SSE)**:
   - Exposing the Phase 09 `Plan -> Code -> Test -> Reflect` state graph via a new API endpoint, e.g., `POST /api/autonomous/stream`.
   - Streaming LLM reasoning, code-diff generation, and subprocess error logs directly to the Lab UI using Full-Duplex Server-Sent Events (SSE).

2. **State Persistence & Rehydration (`AsyncPostgresSaver`)**:
   - Leveraging `deployments/docker-compose/langgraph/postgres-pgvector.yml` as the foundational Memory database.
   - Ensuring the Checkpointer robustly records each transition of the multi-agent graph (Gemma_31B for Planning, 26B for Coding, Qwen_35B for Evaluation) into PostgreSQL.
   - Allowing the React frontend to seamlessly resume a session deterministically from thread checkpoints if a run halts or hits the `max_retries` guardrail constraint.

3. **Tracing & Observability**:
   - Validating that all LLM loops, tool calls, and iteration cycles pushed from the backend service to OpenTelemetry (via `SimpleSpanProcessor`) appear reliably in the Arize Phoenix locally mapping to the `langgraph-mcp-agent` project.

4. **MCP Sandbox Authorization Flow via UI**:
   - Porting the dynamic absolute path extraction mechanism from CLI arguments to handle JSON body requests from the React UI, maintaining the strict security mechanism preventing regex mutations or escalation outside the allowed sandbox.

## Alignment

Please review this context. Do we need any specific changes to the architectural flow or additional features (e.g. extending the evaluation loop, modifying the models used) before drafting the exact file-level `PLAN.md`? 

Please provide your acknowledgment or feedback to proceed.

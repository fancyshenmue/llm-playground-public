# Phase 16: Langfuse Observability Context

## Objective
Implement **Langfuse** as a 100% free, open-source, and locally hosted telemetry/observability platform for the LangGraph-based Enterprise AutoCoder (Phase 15). This replaces the LangSmith proposal, ensuring data privacy and no vendor lock-in.

## Current Architecture
- Telemetry currently uses Arize Phoenix via OpenInference instrumentation (`PhoenixInstrumentor`).
- Phase 15 runs a deterministic multi-node LangGraph (`Plan -> Code -> Test -> Reflect`) integrated via FastAPI and React.

## Technical Decisions & Conclusions (Discuss Phase)

1. **Dockerized Local Hosting (Langfuse)**
   - Unlike LangSmith, Langfuse provides a fully functional, free Docker Compose deployment.
   - We will deploy Langfuse alongside our existing Phoenix and GraphRAG databases under `deployments/docker-compose/langfuse`.
   
2. **Feature Toggle for Observability Backends**
   - **Strategy:** We will implement a **Feature Toggle** in `config.yaml` to dynamically switch or co-exist observability backends.
   - You can choose between Phoenix (for raw OTEL debugging) or Langfuse (for deep LangChain trace correlation and UI analytics).
   
3. **Config.yaml Integration**
   - Introduce an `observability` block in `cmd/py/llm-utils/config.yaml`.
   - Fields: 
     ```yaml
     observability:
       backend: "langfuse" # "langfuse", "phoenix", "both", "none"
     ```
   - Local access variables (`LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST="http://localhost:3000"`) are injected into `os.environ` at runtime from `config.yaml` (no `.env` file needed).

4. **Scope (Phase 15 First)**
   - Tracing setup will be strictly scoped to the Enterprise AutoCoder (Phase 15) code paths (i.e., `enterprise_api/main.py` and `autonomous/graph.py`).

5. **Metadata & Thread Sync**
   - We utilize `CallbackHandler` provided by Langfuse (`langfuse.langchain`) inside LangGraph.
   - **SDK v3 Breaking Change**: The `CallbackHandler` constructor no longer accepts `session_id` as a keyword argument. Instead, the React UI `thread_id` is injected via the LangChain runtime `config["metadata"]["langfuse_session_id"]` key, which Langfuse's callback automatically reads and maps to the Langfuse Session ID.
   - This enables seamless correlation between UI actions and backend LLM reasoning traces.

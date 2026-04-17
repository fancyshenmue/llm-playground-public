# Phase 16: Langfuse Observability Plan

## Overview
Deploy Langfuse via local Docker Compose to serve as a free, powerful, self-hosted observability platform. Implement a feature toggle in `config.yaml` to gracefully switch between Arize Phoenix and Langfuse telemetry across the Enterprise AutoCoder's LangGraph. Pass React UI Thread IDs into Langfuse as Session IDs via the LangChain runtime metadata pattern (SDK v3).

## Checklist

### 1. Documentation & Infrastructure
- [x] 1a. Write `documents/langfuse/architecture.md` to detail the Langfuse component structure (Web UI, DB, ClickHouse) and tracing sequence.
- [x] 1b. Write `documents/langfuse/operations.md` explaining how to start the Langfuse container, access the UI on port 3000, and generate local API keys.
- [x] 1c. Create `deployments/docker-compose/langfuse/docker-compose.yml` pulling down the official Langfuse V2 self-hosted stack.
- [x] 1d. Add `langfuse-up` and `langfuse-down` to `Makefile`.

### 2. Configuration & Dependencies
- [x] 2a. Run `pixi add langfuse` to register the Python SDK dependency.
- [x] 2b. Update `cmd/py/llm-utils/config.yaml.example` and `config.yaml` with the toggle logic:
  ```yaml
  observability:
    backend: "langfuse" # Options: langfuse, phoenix, both, none
  ```
- [x] 2c. Update `cmd/py/llm-utils/.env.example` to hint at `LANGFUSE_SECRET_KEY` and `LANGFUSE_PUBLIC_KEY` with `LANGFUSE_HOST=http://localhost:3000`.

### 3. Application Initialization & Feature Toggle
- [x] 3a. Modify `cmd/py/llm-utils/enterprise_api/main.py` to parse the new configuring toggle.
- [x] 3b. Keep the `setup_telemetry()` function, wrapping `PhoenixInstrumentor` initialization in an `if backend in ["phoenix", "both"]` block.

### 4. Metadata & Session Thread Sync (LangGraph)
- [x] 4a. Modify `cmd/py/llm-utils/enterprise_api/autonomous_agent.py` to import `from langfuse.langchain import CallbackHandler`.
- [x] 4b. In both `run` and `astream_run` methods, check the configuration toggle. If Langfuse is activated, instantiate `CallbackHandler()` (no constructor args).
- [x] 4c. Pass `{"callbacks": [langfuse_handler]}` in the standard `config` block of `app.astream(...)` alongside `{"configurable": {"thread_id": thread_id}}`.
- [x] 4d. **SDK v3 Hotfix**: Inject `thread_id` into Langfuse Session via `config.setdefault("metadata", {})["langfuse_session_id"] = thread_id` instead of the deprecated `CallbackHandler(session_id=...)` constructor parameter.

## Status
✅ All steps completed. Phase 16 is fully deployed and operational.

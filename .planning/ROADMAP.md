# Project Roadmap

## Phase 01: macOS Support & GPU Independence

- [x] Expand `pixi.toml` platforms to include `osx-arm64` and `osx-64`
- [x] Segment `cuda=12` out of main system requirements to `[target.linux-64.system-requirements]`
- [x] Isolate `pytorch-cuda` into `[feature.main.target.linux-64.dependencies]`
      STATUS: ✅ Completed

## Phase 02: vllm-mlx Integration for Gemma 4 (31B & 26B)

- [x] Configure `pixi.toml` with `vllm-mlx` Git dependencies for MLX Apple Silicon optimization
- [x] Write native `launchd` `.plist` generator script (`scripts/daemon-install.sh`)
- [x] Implement Pixi daemon alias tasks (`install`, `start`, `stop`, `logs`)
- [x] Publish `architecture.md` and `operations.md` mapped to new system
      STATUS: ✅ Completed

### Phase 03: The Ollama Pivot
- [x] Unload and scrub `vllm-mlx` infrastructure
- [x] Conda-Forge isolation of `ollama` executable within Pixi
- [x] Configure robust LaunchAgent for daemon support
- [x] Documentation alignment in `documents/ollama` for Gemma 4 (31B & 26B)
- [x] Baseline testing methodology authored in `documents/ollama/benchmark.md`
      STATUS: ✅ Completed

### Phase 04: Performance Evaluation ✅ Completed
- [x] Defined Evaluation Matrix (`benchmark.md`) integrating RAG & LangChain constraints
- [x] Wrote `py-benchmark` harness via `ollama` SDK
- [x] Ran Apple Silicon Benchmarks:
  - `gemma4:26b` (MoE) demonstrated massive speed advantages (~50+ T/s vs ~12 T/s) with identical logical adherence. Both passed RAG context lock and Strict JSON parsing tests perfectly.

### Phase 05: Professional Agent & RAG Observability ✅ Completed
- [x] Wrote `langchain_runner` test harness integrating `arize-phoenix`, `langchain`, and `langchain-ollama`.
- [x] Ran Enterprise Tool Calling & RAG Evaluation:
  - Both `gemma4:26b` and `gemma4:31b` flawlessly executed Official LangChain Tool Calling (`bind_tools`) with compliant JSON payloads.
  - Both models demonstrated perfect text-adherence without hallucinations in the Needle-In-Haystack RAG test.
  - Traces successfully shipped to local Arize Phoenix collector context.

### Phase 06: Real LangChain Test Lab ✅ Completed
- [x] **Planning & Definition**: Established `06-langchain-lab` plan emphasizing a Lab UI and advanced workflows.
- [x] **UI Implementation**: Bootstrapped `frontend/langchain-lab` with Vite/React/Tailwind using documentation-style Layout.
- [x] **FastAPI Backend**: Developed `lab_api` Python service to interface between React and LangGraph.
- [x] **Advanced Agentic Execution**: Implemented 4 distinct LangGraph workflows (ReAct, Stateful, Tools, RAG) with Gemma 4 in the Interactive UI.

### Phase 07: Enterprise Auto-Coding Agent ✅ Completed
- [x] **Infrastructure Setup**: Deploy PostgreSQL with `pgvector` via Docker Compose for enterprise State + RAG hybrid storage.
- [x] **LangGraph Refactoring**: Implement `AsyncPostgresSaver` to persist LLM memory and support Human-in-the-loop debugging.
- [x] **Auto-Coding Closed Loop**: Construct the `Context -> Plan -> Spec -> [ Code <-> Lint <-> Test <-> Reflect ] -> Eval -> Commit` cyclic graph layout.
- [x] **UI Evolution**: Refactor the frontend to support independent Thread IDs and real-time streaming (SSE/WebSockets).

### Phase 08: Real-World File System Agent (CLI) ✅ Completed
- [x] **Model Context Protocol (MCP)**: Native integration of `server-filesystem` via LangChain `BaseTool` conversion via Stdio pipes.
- [x] **ReAct Graph Loop**: Successfully bound `gemma4:26b` to MCP tools inside a stateful checkpointer (`AsyncPostgresSaver`).
- [x] **Terminal UI (Typer/Rich)**: Interactive real-time stdout streaming of the agent's LLM reasoning and file-system manipulation logs.
- [x] **Telemetry**: Fully verified OpenInference trace exports tracking every inner tool-call execution directly out to Arize Phoenix.

### Phase 09: Fully Autonomous Closed-Loop Coder (CLI) ✅ Completed
- [x] **Custom StateGraph Architecture**: Replaced generic `create_react_agent` with deterministic multi-node graph: `Plan → Code → Test → Reflect` with `max_retries=3` loop breaker.
- [x] **Sub-Agent Composition**: Phase 08 ReAct agent embedded as a worker inside the `coder_node`, isolating MCP tool-calls from the outer deterministic flow.
- [x] **Tool Sanitizer Middleware** (`tool_sanitizer.py`): Intercepts Gemma 4 type hallucinations (JSON objects where MCP expects raw strings) and auto-serializes them before they hit the MCP server. Uses `ainvoke`/`invoke` public API for proper `RunnableConfig` propagation.
- [x] **CLI Entrypoint**: `pixi run autocoder` / `make langgraph-autocoder` alongside existing Phase 08 `pixi run agent`.
- [x] **Dynamic Sandbox Paths**: Auto-extracts absolute paths from prompts and injects them as MCP `server-filesystem` allowed directories.
- [x] **Lab UI Integration**: Port Phase 09 SSE streaming to the React Lab UI via `POST /api/autonomous/stream`.

### Phase 10: E-Commerce GraphRAG Assistant ✅ Completed
- [x] Defined Graph Schema (Product, Category, Scenario, Feature, Brand).
- [x] Created `cmd/py/llm-utils/cli.py` generator for mock datasets spanning 5 domains.
- [x] Wrote FastAPI utilizing LangChain `GraphCypherQAChain` connected to Neo4j.
- [x] Implemented Next.js Web UI using the vibrant `ui-ux-pro-max` design system.
- [x] Migrated LLM inference to `gemini-flash-latest` and stabilized backend process management via `make graphrag-backend-kill`.
- [x] Scaled Graph generator to handle 100,000 Mock Products via Cypher `UNWIND` batching logic.
- [x] Implemented Dynamic Knowledge Discovery & Strict Semantic Mapping logic to prevent Text-to-Cypher zero-shot hallucinations.

### Phase 11: Enterprise Hybrid Knowledge GraphRAG Backend ✅ Completed
- [x] Extracted logic from monolith `main.py` into `core`, `schemas`, `api`, and `services` adhering to Production API Layering.
- [x] Decoupled LLM singleton instantiation isolating `gemini-flash-latest` and `nomic-embed-text`.
- [x] Developed custom `HybridRetrieverService` dynamically querying `Neo4jVector` and attaching multi-hop graph expansion Cypher queries to augment Vector Similarity.
- [x] Successfully linked React frontend UI to `/api/chat` with zero-hallucination semantic constraints. 

### Phase 12: Production-Grade Async Local Extraction Pipeline (ETL) ✅ Completed
- [x] **Fault-Tolerance**: Injected `tenacity` retries and `json-repair` to intercept `gemma4` JSON schema aberrations dynamically instead of crashing.
- [x] **Concurrency**: Swapped synchronous iteration for `asyncio.Semaphore()` and `gather()` logic to squeeze maximum batched throughput from local LLMs.
- [x] **Validation**: Run full extraction pipeline successfully into Neo4j locally using `gemma4:latest`.
- [x] **Pydantic Hardening**: Suppressed Pydantic Meta-class V1/V2 collision bugs that leaked `FieldInfo` into Neo4j instances.
- [x] **Data Diversity Injection**: Implemented deterministic local combinatorial python scripting to instantly generate 104,000 unique realistic e-commerce descriptions perfectly tuned for Knowledge Graph extractions.

### Phase 13: Operational Transaction Layer ✅ Completed (Folded into Phase 12)
- [x] **Unified Database Stack**: Merge PostgreSQL and Neo4j architectures into a single `deployments/docker-compose/graphrag-ecommerce` execution target.
- [x] **Marmelab/Data-generator-retail Integration**: Provision robust E-commerce ecosystem data (Customers, Reviews, Commands) via nodejs scripts to mimic a high-density transactional environment.
- [x] **Event-Driven Upstreaming**: Sync PostgreSQL's normalized records upstream into Neo4j graph schemas. Managed seamlessly across the multi-stage 100k Async ETL pipeline.

### Phase 14: Tailwind Interactive UI Documentation Redesign ✅ Completed
- [x] Transformed generic dashboard interfaces into a high-fidelity documentation theme mimicking Official Tailwind aesthetics (`#0B1120`).
- [x] Componentized a deep dark-mode `Sidebar.tsx` navigation tree for visual switching between Chat, Vanilla Gemma, and Vector Search models.
- [x] Rebuilt the core Interactive chat canvas (`page.tsx`) as a seamless inline debugger flowing directly against documentation backgrounds.

### Phase 15: Enterprise AutoCoder (React Lab UI) ✅ Completed
- [x] **UI Migration**: Formally ported the CLI loop to `frontend/autocoder-lab` (React/Vite).
- [x] **SSE Integration**: Upgraded `autonomous_agent.py` to stream Server-Sent Events (SSE) representing inner node transitions.
- [x] **Dynamic Configuration**: Replaced `.env` files with a centralized `config.yaml` to dynamically load heterogeneous LLMs into the graph pipeline.
- [x] **End-to-End Loop**: Executed full closed-loop Code > Test > Reflect integration safely connected via `POST /api/autonomous/stream`.

### Phase 16: Langfuse Observability Integration ✅ Completed
- [x] **Infrastructure**: Deployed localized Langfuse Docker stack (Server, Worker, Redis, MinIO, PostgreSQL, Clickhouse) using `docker-compose`. Mapped Postgres to `5433` to prevent database collision. Added named persistent volumes across all stateful services.
- [x] **Feature Toggling & Parity**: Implemented `observability.backend` switch in `config.yaml` to robustly toggle between Arize Phoenix and Langfuse.
- [x] **SDK V3 Update**: Modernized API parameter injection for `CallbackHandler` using `os.environ` fallback logic, averting runtime deprecation and key assertion failures for `secret_key`.
- [x] **SDK V3 Session Hotfix**: Removed deprecated `CallbackHandler(session_id=...)` constructor parameter. Migrated to `config["metadata"]["langfuse_session_id"]` injection pattern per official Langfuse v3 documentation.
- [x] **Trace Reliability**: Hardened `autonomous_agent.py` to prevent cascading failures if telemetry endpoints fall offline or become unrouteable. Mapped UI `thread_id` to Langfuse `Session ID` via LangChain runtime metadata.

### Phase 17: E-Commerce GraphRAG Langfuse Observability ✅ Completed
- [x] **API Endpoint Tracing**: Instrumented the FastAPI `/api/chat` route using Langfuse `@observe` and injected `CallbackHandler` deep into the LLM synthesis pipelines.
- [x] **Retriever Tracing**: Passed runnable configuration dynamically into `HybridRetrieverService` guaranteeing accurate tracking of Neo4j Vector and BM25 index fetches.
- [x] **ETL Batch Tracing**: Applied Langfuse monitoring to the local Gemini 2.5 Flash context extraction scripts to strictly monitor runtime and latency per document batch.
- [x] **UI/Pipeline Deduplication Resiliency**: Upgraded Neo4j Vector search candidate generation depth (`k=1000`) and tightened LLM prompt synthesis rules to overcome the structural synthetic data redundancy (150 identical products) preventing UI starvation.

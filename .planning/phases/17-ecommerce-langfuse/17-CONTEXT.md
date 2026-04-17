# Phase 17: E-Commerce GraphRAG Langfuse Observability

## Context & Objectives
Following the successful deployment of the Langfuse observability stack in Phase 16, the goal of Phase 17 is to instrument the E-Commerce GraphRAG system (built in Phases 10-13) with full LangChain tracing. This will provide complete visibility into the hybrid vector/graph retrieval process, CJK translation overhead, and final LLM synthesis latency.

## Architecture Integration Strategy

1. **Environment Setup**: 
   - Add `LANGFUSE_SECRET_KEY`, `LANGFUSE_PUBLIC_KEY`, and `LANGFUSE_HOST` to the e-commerce backend environment scope (adjusting `.env.example`).
   - Ensure the frontend `thread_id` (session ID) is captured from the UI and passed sequentially through the backend for continuous session monitoring.

2. **API Endpoint Tracing (`api/routes/chat.py`)**:
   - Utilize `@observe(name="ecommerce_graphrag_chat")` on `chat_endpoint` to capture the overall request lifecycle.
   - Instantiate `langfuse.langchain.CallbackHandler` mapped to the API request's `thread_id` (via `config["metadata"]["langfuse_session_id"]` per SDK v3 standards).
   - Inject the callback handler into the execution configurations (`config={"callbacks": [...]}`) for:
     - The `translate_chain` (Query Optimizer)
     - The `retriever` (Hybrid Neo4j Search)
     - The `synthesis_chain` (Final Generation)

3. **Retriever Service Propagation**:
   - Refactor `retrieve_with_translation` inside the closure to accept and propagate the `RunnableConfig`, guaranteeing that Neo4j's exact retrieval latency is independently metered inside the parent trace.

## Discussion Questions
1. **Scope of Telemetry**: Do we want to implement tracing *strictly* for the real-time query side (`chat.py`), or should we also add Langfuse tracking to the asynchronous ETL pipeline (`async_fetch.py`) to measure Gemini 2.5 Flash extraction times?
2. **Feature Toggle**: In Phase 16, we built a `config.yaml` toggle (`observability.backend`). Should we port this explicit toggle logic to the E-Commerce backend, or just enable Langfuse silently if the environment variables (`LANGFUSE_HOST` etc.) are present?

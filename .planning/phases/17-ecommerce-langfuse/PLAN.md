# Phase 17 Implementation Plan: E-Commerce GraphRAG Langfuse Observability

## Task Definition
Instrument the E-Commerce GraphRAG system with Langfuse telemetry. Ensure both real-time query flows (`chat.py`) and background ETL pipelines (`async_fetch.py`) are fully traceable.

## Execution Checklist

- [x] **1. Environment Configuration**
  - [x] **1a.** Modify `backend/ecommerce-graphrag/.env.example` to include `LANGFUSE_SECRET_KEY`, `LANGFUSE_PUBLIC_KEY`, and `LANGFUSE_HOST`.
  - [x] **1b.** Ensure `langfuse` is listed in `backend/ecommerce-graphrag/requirements.txt` to maintain parity with `pixi.toml` dependencies.

- [x] **2. Real-Time API Tracing (`backend/ecommerce-graphrag/api/routes/chat.py`)**
  - [x] **2a.** Import `langfuse` (`observe`, `CallbackHandler`, `langfuse_context`).
  - [x] **2b.** Decorate `chat_endpoint` with `@observe(name="ecommerce_graphrag_chat")` and define standard properties.
  - [x] **2c.** Inside `chat_endpoint`, instantiate `CallbackHandler(session_id=request.thread_id)`.
  - [x] **2d.** Inject `config={"callbacks": [langfuse_handler]}` into `translate_chain.ainvoke`, `retriever.ainvoke`, and `synthesis_chain.ainvoke`.
  
- [x] **3. Retriever Deep-Tracing (`backend/ecommerce-graphrag/services/retriever_service.py`)**
  - [x] **3a.** Refactor `retrieve_with_translation` inside `HybridRetrieverService` to accept `config: RunnableConfig` and pass `config` downwards to Neo4jVector queries to capture latent database latency.

- [x] **4. ETL Pipeline Tracing (`backend/ecommerce-graphrag/ingestion/async_fetch.py`)**
  - [x] **4a.** Import `langfuse.decorators.observe`.
  - [x] **4b.** Decorate `extract_knowledge_async` with `@observe(name="ecommerce_etl_extract", as_type="generation")` to log latency per document extraction step.
  - [x] **4c.** Add `langfuse_context.update_current_observation` to attach `kwargs` like `url` and the raw completion texts to the trace span.

- [x] **5. Verification**
  - [x] **5a.** Verify API traces appear in Langfuse (http://localhost:3000).
  - [x] **5b.** Verify ETL traces capture the LLM latency.

## Notes
* As requested, this uses silent-enable: if `LANGFUSE_HOST` is missing, standard fallback prevents crashing (Langfuse implicitly disables itself if keys are missing in SDK v3).
* We assume the Langfuse Docker container on port 3000 is still active from Phase 16.

# GraphRAG E-Commerce Architecture

This document describes the production-grade Hybrid GraphRAG E-Commerce system. It covers the dual-database infrastructure, asynchronous ETL pipeline, real-time query mechanics, and graph ontology.

> [!NOTE]
> For the higher-level Enterprise system overview (covering Phase 12 & 13), see [enterprise-graphrag/architecture.md](../enterprise-graphrag/architecture.md).
> For Neo4j operational commands and backup procedures, see [neo4j/operations.md](../neo4j/operations.md).

---

## 1. System Topology & Data Flow

The system operates across two layers linked by an asynchronous ETL ingestion pipeline:

- **Primary Transactional Layer (ACID)**: PostgreSQL (`pgvector`) — Source of Truth for products, categories, customers, orders, and reviews.
- **Knowledge Retrieval Layer (Graph & Vector)**: Neo4j — Semantic Retrieval Engine for vector searches, BM25 keyword matches, and multi-hop Cypher traversals.
- **Observability Layer (Telemetry)**: Langfuse — Distributed tracing capturing LLM latency, chunk retrieval, token usage, and session management.

```mermaid
graph TD
    classDef system fill:#0f172a,stroke:#3b82f6,stroke-width:2px,color:#fff;
    classDef llm fill:#4c1d95,stroke:#a855f7,stroke-width:2px,color:#fff;
    classDef db fill:#064e3b,stroke:#10b981,stroke-width:2px,color:#fff;
    classDef obs fill:#9d174d,stroke:#f43f5e,stroke-width:2px,color:#fff;

    LF("Langfuse Tracking :3000"):::obs

    subgraph "Data Generation & Ingestion"
        DG("hybrid_amazon_generator.py"):::system
        PG[(PostgreSQL 5432)]:::db
        ETL("async_fetch.py"):::system

        DG -->|"Fetch Open Datasets + Synthesize CRM"| PG
        PG -->|"SELECT Products & Relations"| ETL
        ETL <-->|"Prompt / JSON"| GF("Cloud Gemini 2.5 Flash"):::llm
        ETL -.->|"ETL Execution Trace"| LF
        ETL -->|"Self-Healing Retry"| ETL
        ETL -->|"MERGE Nodes & Edges"| DB[(Neo4j 7687)]:::db
    end

    subgraph "Real-Time RAG Pipeline"
        UI["Next.js Frontend :3000"]:::system -->|"POST /api/chat"| API("FastAPI Router :8000"):::system
        API --> RS("HybridRetrieverService"):::system

        RS -->|"Embed Query"| EMB("nomic-embed-text<br>(Ollama)"):::llm
        EMB -.->|"1. Vector KNN<br>2. BM25 Keyword"| DB

        DB -->|"RRF + 1-Hop Expansion"| RS
        RS -->|"Context Subgraph"| QA("Gemma4:latest<br>(Local Synthesis)"):::llm
        QA -->|"Response"| API
        API -.->|"Session & Latency Traces"| LF
    end
```

---

## 2. Infrastructure

All data stores are managed via a single Docker Compose file:

- **Compose File**: `deployments/docker-compose/graphrag-ecommerce/docker-compose.yml`
- **Start**: `make graphrag-db-up`
- **Stop**: `make graphrag-db-down`

### Databases

| Service               | Container           | Port        | Volume                     | Purpose                   |
| --------------------- | ------------------- | ----------- | -------------------------- | ------------------------- |
| PostgreSQL (pgvector) | `graphrag-postgres` | 5432        | `pg-data`                  | ACID Source of Truth      |
| Neo4j + APOC          | `graphrag-neo4j`    | 7474 / 7687 | `neo4j-data`, `neo4j-logs` | Semantic Retrieval Engine |

### Local AI Models (Ollama)

| Model                    | Role                     | Invocation                                   |
| ------------------------ | ------------------------ | -------------------------------------------- |
| `gemma4:latest`          | LLM Synthesis (QA chain) | `ChatOllama(model="gemma4:latest")`          |
| `nomic-embed-text`       | Vector Embeddings (768d) | `OllamaEmbeddings(model="nomic-embed-text")` |
| Gemini 2.5 Flash (Cloud) | ETL Knowledge Extraction | `genai.GenerativeModel("gemini-2.5-flash")`  |

### Observability Stack (External)

| Service               | Container           | Port        | Purpose                   |
| --------------------- | ------------------- | ----------- | ------------------------- |
| Langfuse Server       | `langfuse-server`   | 3000        | Telemetry Dashboard UI    |

> **Note**: The Langfuse stack is managed independently under `deployments/docker-compose/langfuse/docker-compose.yml`. E-Commerce services integrate with it via environment variables if available.

---

## 3. Graph Ontology

### Node Labels

| Label      | Source              | Examples                      |
| ---------- | ------------------- | ----------------------------- |
| `Product`  | PostgreSQL (direct) | Camping Tent, Sunscreen SPF50 |
| `Category` | PostgreSQL (direct) | Outdoor Gear, Health & Beauty |
| `Customer` | PostgreSQL (direct) | Synthetic CRM entities        |
| `Order`    | PostgreSQL (direct) | Purchase transactions         |
| `Review`   | PostgreSQL (direct) | Customer ratings & comments   |
| `Brand`    | LLM Extraction      | Arc'teryx, CeraVe             |
| `Feature`  | LLM Extraction      | Waterproof, Organic           |
| `Benefit`  | LLM Extraction      | UV Protection, Pain Relief    |
| `Scenario` | LLM Extraction      | Climbing, Daily Skincare      |

### Relationship Types

| Relationship       | Source → Target    | Origin                      |
| ------------------ | ------------------ | --------------------------- |
| `BELONGS_TO`       | Product → Category | PostgreSQL (direct mapping) |
| `PRODUCED_BY`      | Product → Brand    | LLM Extraction              |
| `HAS_FEATURE`      | Product → Feature  | LLM Extraction              |
| `PROVIDES_BENEFIT` | Product → Benefit  | LLM Extraction              |
| `SUITABLE_FOR`     | Product → Scenario | LLM Extraction              |
| `PLACED`           | Customer → Order   | PostgreSQL (direct mapping) |
| `CONTAINS`         | Order → Product    | PostgreSQL (direct mapping) |
| `WROTE`            | Customer → Review  | PostgreSQL (direct mapping) |
| `ABOUT`            | Review → Product   | PostgreSQL (direct mapping) |

### Schema Visualization

```mermaid
graph TD
    P["Product"]
    C["Category"]
    Cu["Customer"]
    O["Order"]
    R["Review"]
    B["Brand"]
    F["Feature"]
    Bn["Benefit"]
    S["Scenario"]

    P -- BELONGS_TO --> C
    P -- PRODUCED_BY --> B
    P -- HAS_FEATURE --> F
    P -- PROVIDES_BENEFIT --> Bn
    P -- SUITABLE_FOR --> S

    Cu -- PLACED --> O
    O -- CONTAINS --> P
    Cu -- WROTE --> R
    R -- ABOUT --> P
```

---

## 4. Real-Time Query Sequence

When a user submits a natural language question, the system executes the following pipeline:

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Frontend as Next.js Web UI
    participant Router as FastAPI Router (chat.py)
    participant Svc as HybridRetrieverService
    participant Neo4j as Neo4j (Vector + Graph)
    participant Gemma as Local Gemma4
    participant LF as Langfuse

    User->>Frontend: "我需要防曬的有機護膚品"
    Frontend->>Router: POST /api/chat {thread_id}
    Router->>LF: Init trace(session_id=thread_id)

    %% CJK Translation Phase
    Router->>Gemma: translate_chain("我需要...")
    Note over Gemma: Detects non-ASCII input >20%<br>Translates to English keywords
    Gemma-->>Router: "organic sunscreen skincare UV"

    %% Hybrid Retrieval Phase
    Router->>Svc: retrieve_with_translation(query)
    Svc->>Gemma: nomic-embed-text("organic sunscreen...")
    Gemma-->>Svc: [0.12, -0.45, 0.88, ...] (768d)

    Svc->>Neo4j: HybridQuery(Vector KNN + BM25)
    Note over Neo4j: 1. Vector Cosine Search<br>2. BM25 Full-Text Search<br>3. Reciprocal Rank Fusion (RRF)
    Note over Neo4j: 4. 1-Hop OPTIONAL MATCH<br>(Product)-[r]->(neighbor)<br>(Product)<-[:ABOUT]-(Review)<-[:WROTE]-(Customer)
    Neo4j-->>Svc: Top-3 Subgraphs + Metadata

    %% LLM Synthesis Phase
    Svc-->>Router: docs[] (page_content + metadata)
    Router->>Gemma: synthesis_chain(context + original question)
    Note over Gemma: Answers in Traditional Chinese<br>Using strict product card format
    Gemma-->>Router: Synthesized Response

    %% Response Assembly
    Router->>Router: _extract_product_context(docs)
    Router->>LF: Finalize Trace (latency, tokens)
    Router-->>Frontend: ChatResponse(reply, context[])
    Frontend-->>User: Chat panel + Product inspector panel
```

### Key Design Decisions

- **CJK Translation Routing**: `nomic-embed-text` is English-only. Non-ASCII queries (>20% non-ASCII characters) are first translated to English keywords via `Gemma4`, then used for retrieval. English queries bypass translation entirely (~500ms latency savings).
- **Hybrid Search (RRF)**: Combines Vector KNN (semantic similarity) and BM25 (keyword matching) via Reciprocal Rank Fusion for better recall than either method alone. The candidate retrieval depth is intentionally elevated (`k=1000`) to overcome heavy topological redundancy in the synthetic dataset, guaranteeing that the LLM receives diverse, distinct base products for deduplicated UI rendering.
- **1-Hop Graph Expansion**: After finding anchor Product nodes, the retriever expands 1 hop to pull associated Features, Benefits, Reviews, and Customer sentiments into the context window.
- **Structured Response**: The LLM is constrained to output in a strict `Key: Value` product card format with Markdown image syntax, enabling the frontend to render a split-screen layout (chat panel + product inspector panel).

---

## 5. ETL Pipeline

### Self-Healing Mechanisms

| Mechanism           | Library                                    | Purpose                                                      |
| ------------------- | ------------------------------------------ | ------------------------------------------------------------ |
| Concurrency Control | `asyncio.Semaphore(3)`                     | Prevent API rate limit exhaustion                            |
| Retry with Backoff  | `tenacity` (3 attempts, exponential 4–30s) | Survive transient network failures                           |
| JSON Auto-Repair    | `json_repair`                              | Salvage malformed LLM JSON output before Pydantic validation |
| Cost Protection     | `EXTRACT_LIMIT` env var                    | Cap LLM API calls during development                         |
| Resumption Safety   | Neo4j edge query                           | Skip products already extracted on restart                   |
| Batch Chunking      | 50-doc chunks with `asyncio.gather`        | Prevent coroutine explosion on 100K+ records                 |

### ETL Sequence

```mermaid
sequenceDiagram
    autonumber
    actor Admin
    participant PY as hybrid_amazon_generator.py
    participant HF as Open Dataset API
    participant PG as PostgreSQL
    participant Script as async_fetch.py
    participant LLM as Gemini 2.5 Flash (Cloud)
    participant DB as Neo4j

    Admin->>PY: make graphrag-generate-data
    PY->>HF: Fetch real Products & Reviews
    HF-->>PY: JSON Payload
    PY->>PY: Synthesize Customers & Orders (Faker)
    PY-->>Admin: JSONL files saved

    Admin->>Script: make graphrag-seed-postgres
    Script->>PG: Bulk COPY INTO tables
    PG-->>Script: Transaction Committed

    Admin->>Script: EXTRACT_LIMIT=10000 make graphrag-etl

    Note over Script: PART A: Direct Relational Mapping
    Script->>PG: SELECT products, categories, customers, reviews, orders
    PG-->>Script: SQL Rows
    Script->>DB: MERGE Products, Categories (10K batches)
    Script->>DB: MERGE Customers, Reviews, Orders + Edges (10K batches)

    Note over Script: PART B: LLM Semantic Extraction
    Script->>DB: Query already-processed product IDs (resumption check)
    DB-->>Script: processed_ids set

    loop Concurrent Extraction (Semaphore=3, Chunks=50)
        Script->>LLM: generate_content_async(EXTRACTION_PROMPT)
        LLM-->>Script: Raw JSON (Entities & Relationships)
        Script->>Script: json-repair + Pydantic validate
        Script->>DB: add_graph_documents(GraphDocument[])
    end

    Note over Script: PART C: Vector Index Regeneration
    Script->>DB: Neo4jVector.from_existing_graph(HYBRID)
    Note over DB: Generates nomic-embed-text vectors<br>Bootstraps BM25 Keyword Index
    DB-->>Script: Index Created

    Script-->>Admin: ETL Complete
```

---

## 6. Backend Module Map

```
backend/ecommerce-graphrag/
├── main.py                          # FastAPI app (port 8000)
├── api/routes/chat.py               # POST /api/chat endpoint
├── core/
│   ├── config.py                    # Settings (YAML parsing, env injection)
│   ├── database.py                  # Neo4j + PostgreSQL connections
│   └── llm.py                       # Gemma4 (synthesis) + nomic-embed-text (embeddings)
├── services/
│   └── retriever_service.py         # HybridRetrieverService (Vector + BM25 + Graph)
├── schemas/
│   └── chat_schema.py               # ChatRequest / ChatResponse (Pydantic)
└── ingestion/
    ├── async_fetch.py               # Main ETL pipeline (Part A/B/C)
    ├── ontology.py                  # Ontology definitions
    └── seed_mock_graph.py           # Legacy mock seeder
```

---

## 7. Makefile Quick Reference

| Command                        | Description                                        |
| ------------------------------ | -------------------------------------------------- |
| `make graphrag-db-up`          | Start PostgreSQL + Neo4j containers                |
| `make graphrag-db-down`        | Stop containers                                    |
| `make graphrag-generate-data`  | Generate 100K retail product JSONL                 |
| `make graphrag-seed-postgres`  | Bulk load JSONL → PostgreSQL                       |
| `make graphrag-etl`            | Run ETL: PG → Neo4j (EXTRACT_LIMIT controls scope) |
| `make graphrag-rebuild`        | Clean Neo4j → full ETL                             |
| `make graphrag-backend-dev`    | Start FastAPI on port 8000                         |
| `make graphrag-frontend-dev`   | Start Next.js on port 3000                         |
| `make graphrag-neo4j-clean`    | Wipe all Neo4j data                                |
| `make graphrag-postgres-clean` | Wipe all PostgreSQL tables                         |
| `make graphrag-clean-all`      | Full wipe (Neo4j + PG + JSONL)                     |
| `make graphrag-verify`         | Run end-to-end topology health check               |

---

## 8. Implementation Notes

- The **Next.js frontend** renders a split-screen layout: left panel for chat, right panel for structured product cards with images and prices.
- The **FastAPI backend** extracts structured product data from retriever documents (`_extract_product_context`) and returns it alongside the LLM's conversational reply.
- The **synthesis LLM** (Gemma4) is constrained via system prompt to answer in **Traditional Chinese (繁體中文)**, using a strict product card format that the frontend can reliably parse.
- The **embedding model** (nomic-embed-text) runs locally via Ollama, eliminating dependency on cloud embedding APIs.
- The **ETL pipeline** supports both **cloud** (Gemini 2.5 Flash) and **local** (Gemma4 via Ollama) LLM providers, controlled by the `ETL_LLM_PROVIDER` setting in `config.yaml`.
- **Configuration Management**: The system utilizes a structured `config.yaml` instead of legacy `.env` files. `core/config.py` acts as a translation layer, loading YAML boundaries (server, db, observability) and dynamically populating `os.environ` to satisfy standard Python SDKs seamlessly.
- **Observability Integration (v4 SDK)**: Tracing is powered by the Langfuse Python SDK v4 (`from langfuse import observe, get_client`). Decorators capture execution context, and ETL operations log custom I/O via `get_client().update_current_generation()`.

# Enterprise Hybrid Knowledge GraphRAG Architecture

This document describes the Phase 12 & 13 production-grade Hybrid GraphRAG system. It outlines how a primary relational database (PostgreSQL) interacts via asynchronous event-driven pipelines (ETL) to feed a deeply connected Graph and Vector database (Neo4j) for Semantic RAG reasoning.

## 1. Unified System Architecture Diagram

The system operates across a **Primary Transactional Layer (ACID)** and a **Knowledge Retrieval Layer (Graph & Vector)**, linked by an **Asynchronous ETL Ingestion Pipeline**.

```mermaid
graph TD
    classDef system fill:#0f172a,stroke:#3b82f6,stroke-width:2px,color:#fff;
    classDef llm fill:#4c1d95,stroke:#a855f7,stroke-width:2px,color:#fff;
    classDef db fill:#064e3b,stroke:#10b981,stroke-width:2px,color:#fff;
    classDef auth fill:#7f1d1d,stroke:#ef4444,stroke-width:2px,color:#fff;

    %% Unified Dual-Database & ETL Subsystem
    subgraph "Phase 13: Amazon Hybrid Data & Infrastructure"
        DG("Python Hybrid Amazon Generator<br>(hybrid_amazon_generator.py)"):::system
        PG[(PostgreSQL 5432<br>Primary DB)]:::db
        ETL("Python ETL Pipeline<br>(async_fetch.py)"):::system
        
        DG -->|Fetch Real Open-Dataset + Synthesize Customers| PG
        PG -->|SELECT Products & CRM Data| ETL
        ETL <-->|Prompt / JSON| GF("Cloud Gemini 2.5 Flash<br>(Google GenAI)"):::llm
        ETL -->|Self-Healing / Retry| ETL
        ETL -->|Direct Props and LLM Concepts via MERGE| DB[(Neo4j 7687<br>Graph Database)]:::db
    end

    %% Enterprise RAG Subsystem
    subgraph "Phase 11: Real-Time RAG Pipeline"
        UI[Next.js Frontend]:::system -->|POST /api/chat| API("FastAPI Router"):::system
        API --> RS("Hybrid Retriever Service"):::system
        
        RS -->|Embed Query| V("Nomic Embeddings<br>(nomic-embed-text)"):::llm
        V -.->|1. Vector Search<br>2. BM25 Keyword Search| DB
        
        DB -->|Reciprocal Rank Fusion + 1-Hop Expansion| RS
        RS -->|"Context Subgraph (with Images/Prices)"| QA("Gemma4:26b Synthesis<br>(QA Chain)"):::llm
        QA -->|Response| API
    end
```

## 2. Infrastructure Deployment (Phase 12)

To ensure cohesive local mirroring of a production setup, all data stores are unified into a single Docker Compose execution target:

- **Directory**: `deployments/docker-compose/graphrag-ecommerce/docker-compose.yml`
- **Execution Target**: `make graphrag-db-up`

### Databases:
- **PostgreSQL (`pgvector`)**: Handles user carts, CRM data, raw product schemas, structured pricing, customer reviews, and orders acting as the ACID Source of Truth.
- **Neo4j (`7474/7687`)**: Acts as the highly-optimized read-replica Semantic Retrieval Engine for Vector searches and multi-hop Cypher traversals.

## 3. Real-Time Query Sequence Flow

The following sequence illustrates the traversal mechanics when a user submits a natural language question.

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Frontend as Next.js Web UI
    participant Router as API Router (chat.py)
    participant Svc as Retriever Service
    participant Neo4j as Neo4j (Vector + Graph)
    participant Gemma as Local Gemma4:26b

    User->>Frontend: "I need an organic supplement to protect my skin"
    Frontend->>Router: POST /api/chat
    Router->>Svc: invoke_chain(query)
    
    %% Semantic Search Phase
    Svc->>Gemma: nomic-embed-text("organic supplement...")
    Gemma-->>Svc: [0.12, -0.45, 0.88, ...] (Vector 768d)
    
    %% Graph Traversal Phase (Hybrid)
    Svc->>Neo4j: HybridQuery(Vector, BM25, Cypher Expanse)
    Note over Neo4j: 1. Vector KNN Search (Cosine)<br/>2. Full-Text Search (BM25)<br/>3. Reciprocal Rank Fusion (RRF)
    Note over Neo4j: 4. Cypher Traversal Expand<br/>(Product)<-[:ABOUT]-(Review)<-[:WROTE]-(Customer)
    Neo4j-->>Svc: Context: {Matched Subgraph Arrays + ImageURLs}
    
    %% LLM Synthesis Phase
    Svc->>Gemma: QA_PROMPT(Context + User Question)
    Gemma-->>Svc: Synthesized Response
    
    Svc-->>Router: ChatResponse Payload
    Router-->>Frontend: JSON Response
    Frontend-->>User: "為您推薦以下有機護膚補充品..."
```

## 4. Extraction Ontology & Self-Healing ETL

To combat LLM hallucinations or network faults during extraction:
- **Concurrency**: `asyncio.Semaphore(15)` manages cloud API limits by bounding batched generations.
- **Resiliency**: The `tenacity` library injects exponential backoff retries to guarantee JSON delivery.
- **Auto-Correction**: `json-repair` dynamically intervenes before `Pydantic` schema verification to salvage misformatted JSON responses from the LLM.
- **Cost Protection**: The `EXTRACT_LIMIT` environment variable enforces a configurable threshold to prevent accidental API quota consumption during development rebuilds.

## 5. Async ETL & Data Generation Sequence Flow (Phase 12)

This sequence illustrates the end-to-end data generation and ingestion pipeline, moving from synthetic Node.js generation into PostgreSQL (ACID), and finally extracting the ontology into Neo4j via LLM.

```mermaid
sequenceDiagram
    autonumber
    actor Admin
    participant PY as hybrid_amazon_generator.py
    participant HF as Open Dataset API (HF/FakeStore)
    participant PG as PostgreSQL (Primary DB)
    participant Script as async_fetch.py (Python)
    participant LLM as Gemini 2.5 Flash (Cloud)
    participant DB as Neo4j Database

    %% Data Generation & Seeding
    Admin->>PY: make graphrag-generate-data
    PY->>HF: Fetch real Products & Reviews
    HF-->>PY: JSON Payload
    PY->>PY: Synthesize Relational Customers & Orders (Faker)
    PY-->>Admin: "JSONL files generated successfully."

    Admin->>Script: make graphrag-seed-postgres
    Script->>PG: Bulk COPY INTO products, categories...
    PG-->>Script: Transaction Committed
    Script-->>Admin: "Database Seeded successfully."

    %% Concept Extraction Pipeline
    Admin->>Script: EXTRACT_LIMIT=104000 make graphrag-etl
    Script->>PG: SELECT * FROM products p JOIN categories c ...
    PG-->>Script: Products Payload (SQL Rows)
    
    loop Concurrent LLM Extraction (Semaphore limits cloud bursts)
        Script->>LLM: generate_content_async(EXTRACTION_PROMPT + Product Desc)
        Note left of LLM: Deep Zero-Shot Extraction<br/>into target JSON Schema
        LLM-->>Script: Raw String Output (Entities)
        Script->>Script: Validate & json-repair
    end
    
    %% Graph Mapping & Injection
    Script->>DB: Cypher: MERGE Nodes (Product, Category, Feature...)
    Script->>DB: Cypher: SET p.price, p.stock (From PG Data directly)
    Script->>DB: Cypher: MERGE Edges (LLM Extracted Concepts)
    
    %% Relational Direct Mapping (No LLM required)
    Script->>PG: SELECT * FROM orders, reviews, customers...
    PG-->>Script: Relational Foreign Key Data
    Script->>DB: Cypher: MERGE (Customer)-[:PLACED]->(Order)-[:CONTAINS]->(Product)
    Script->>DB: Cypher: MERGE (Customer)-[:REVIEWED]->(Product)
    
    %% Vector Embeddings & Hybrid Indexing
    Script->>DB: Neo4jVector.from_existing_graph(search_type=HYBRID)
    Note over DB: Generates nomic-embed-text vectors<br/>and bootstraps BM25 Keyword Index
    
    DB-->>Script: Transaction Success
    Script-->>Admin: "ETL Pipeline completed successfully! Neo4j deeply populated."
```

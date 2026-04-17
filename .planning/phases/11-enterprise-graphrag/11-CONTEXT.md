# Phase 11 CONTEXT: Enterprise Hybrid Knowledge GraphRAG

## Architectural North Star & Executive Summary

The primary objective of Phase 11 is to transcend traditional, single-dimensional Vector RAG (Retrieval-Augmented Generation) by implementing a **Production-Grade Hybrid Vector-Graph Architecture**. 

Traditional RAG suffers from severe hallucination and context-scattering when dealing with highly connected, nuanced enterprise datasets (like E-Commerce catalogs with subtle attributes spanning multiple brands and categories). By fusing Neo4j's explicit Cypher relationship traversals with the fuzzy semantic matching of High-Dimensional Vector Search (KNN), we create a **Zero-Hallucination Retrieval Pipeline** capable of answering complex, multi-hop user intents natively.

This entire architecture is built atop local Apple Silicon unified memory constraints, leveraging independent local models (`gemma4:latest` for extraction/synthesis and `nomic-embed-text` for vectorization).

---

## 1. Automated Ontology Knowledge Extraction (The ETL Subsystem)

The foundation of the Knowledge Graph requires extracting organic, unstructured payload data (e.g., from DummyJSON) and mapping it into rigid Neo4j nodes and edges.

### Design Principles:
- **Strict Ontology Mapping**: Instead of allowing the LLM to hallucinate graph schemas, we clamp the extraction using predefined arrays (`ALLOWED_NODES`, `ALLOWED_RELATIONSHIPS`). The LLM is restricted to populating only these valid entities.
- **Fault-Tolerance via Auto-Healing**: Pydantic validation errors and raw JSON schema hallucinations from the 9B parameter model are intercepted. We incorporate `tenacity` exponential backoff retries and the `json-repair` library to dynamically heal malformed JSON outputs on the fly, preventing catastrophic pipeline crashes during bulk ingestion.
- **Asynchronous Bottleneck Control**: To prevent Unified Memory (RAM/Swap) explosion on macOS, the ingestion script is wrapped in `asyncio.Semaphore`. This creates a deterministic, highly-controlled processing throttle, ensuring the local Ollama instance does not queue and choke.

---

## 2. Multi-Dimensional Semantic Indexing

Once the nodes and relationships reside in Neo4j, they must be made semantically searchable.

### Pipeline:
1. **Embedding Generation**: We utilize `nomic-embed-text` to generate mathematically dense 768-dimensional coordinates representing the semantic meaning of `title`, `description`, and `category` text properties.
2. **Neo4jVector Bindings**: We leverage `Neo4jVector.from_existing_graph()` to index these embeddings directly within the Graph Database engine. This allows Neo4j to serve dual roles: Vector Database (for semantic proximity) and Graph Engine (for structural traversal).

---

## 3. The Retrieval Orchestration (Hybrid Cypher + KNN)

This is the core intellectual property of Phase 11. When a user asks a vague intent question (e.g., *"I need something refreshing for my face for the summer"*):

1. **Semantic Anchor (Vector Phase)**: The query is vectorized, and `Neo4jVector` performs a KNN search to find the closest `Product` nodes.
2. **Graph Expansion (Cypher Phase)**: Instead of immediately returning these products to the LLM, a custom Cypher query (`retrieval_query`) is triggered. It anchors on the retrieved `Product` nodes and dynamically traverses outward across edges (e.g., `-[HAS_FEATURE]->(Feature)`, `-[BELONGS_TO]->(Category)`).
3. **Synthesis**: The LLM is fed a highly enriched subgraph (not just isolated text chunks) that inherently contains structural truth, drastically reducing logical hallucination.

---

## 4. Decoupled Production API Layering

To prevent monolithic spaghetti code, the FastAPI backend is rigorously refactored into a scalable Enterprise micro-framework:

- **`core/`**: Centralized configurations, environment settings, and singleton instance managers (`Neo4jGraph`, `ChatOllama`).
- **`schemas/`**: Pydantic validations defining exact HTTP Request/Response contracts (`ChatRequest`, `ChatResponse`).
- **`api/routes/`**: Clean, lightweight router functions exposed to the frontend.
- **`services/`**: The heavy-lifting business logic layer containing `retriever_service.py` to decouple LangChain graph manipulation away from HTTP handlers.

By compartmentalizing these domains, the backend acts as a highly disciplined, event-ready microservice capable of seamless integration with Next.js frontend interfaces natively.

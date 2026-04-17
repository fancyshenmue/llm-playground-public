# Phase 13 Implementation Plan: Real Amazon Data & Edge Integration

This plan implements full data transition from synthetic text to real-world Amazon models, injecting genuine GraphRAG review structures into the Enterprise ETL. All steps are strictly sequenced to maintain PostgreSQL DDL compatibility while unlocking multi-hop semantic querying over Customer-Review-Product interaction matrices.

## User Review Required

> [!WARNING]
> Environment Data Target Strategy: Pulling 100,000 real Product records plus 500,000 linked Reviews from a full HuggingFace dataset format requires ~1-2GB of transient memory and network download time during PyArrow initialization. To optimize development velocity, I recommend downloading a curated small slice (e.g., 500 real Products mapped to 2000 reviews) via an HTTP API, and utilizing deterministic programmatic replication (Combinatorics) to safely spin this slice up to 100,000 unique semantic records. Please confirm if this subset-multiplication architecture is acceptable.

## Detailed Task Checklist

### Phase 13.A: Python Hybrid Data Generator Scaffold
- [x] 1. **Initialize Engine Foundation:** Create `scripts/ecommerce-graphrag/hybrid_amazon_generator.py`
  - Implement `import requests, json, faker, os, random` imports. Establish strict absolute pathway hooks pointing outputs to `scripts/ecommerce-graphrag/data/*.jsonl`.
- [x] 2. **Network Scaffolding (Products):** Implement `fetch_real_products(batch_size)` parsing REST API streams or local parquet.
  - Map external API keys: `id -> pg_id integer`, `title -> reference`, `description -> description`, `image -> original URI`.
  - Sanitize all descriptions (remove HTML tags, handle JSON string escapes) to prevent `psycopg` COPY failures during `seed_postgres.py`.
- [x] 3. **Review Ingestion Logic:** Implement `fetch_real_reviews()`.
  - Extract exact human sentiments. Bind correctly normalized `rating` (1-5) and `comment` (raw string).

### Phase 13.B: Foreign Key & Relationship Synthesis
- [x] 4. **Reverse-Synthesize Customers:** Implement `synthesize_customers(total_unique_users)` using `@faker-js/faker` equivalent in Python (e.g., `Faker` library).
  - Seed state: `Faker.seed(42)` for determinism.
  - Generate 100% compliant Postgres tuples: `id, first_name, last_name, email, address, city, zipcode, avatar, birthday`.
- [x] 5. **Temporal Synthesis (Orders/Invoices):** Implement `synthesize_transaction_history()`.
  - Back-propagate `Order` nodes matching the `Review` timestamps. An order date must strictly precede the review date.
  - Bind nested `basket` logic containing the `product_id` and `price` sum to accurately reflect `total_spent` in `Customer` tables.

### Phase 13.C: Infrastructure & Operations Routing
- [x] 6. **Deprecate Node Legacy Script:** Modify `Makefile` target `graphrag-generate-data`.
  - REMOVE: `pixi run npm run generate --prefix scripts/ecommerce-graphrag`.
  - ADD: `pixi run python scripts/ecommerce-graphrag/hybrid_amazon_generator.py`.
  - REMOVE: Execution of `diversify_data.py` (since the new script natively handles combinatorial diversity injection).
- [x] 7. **Garbage Collection:** Remove `diversify_data.py` from repository tracking to clean the codebase.

### Phase 13.D: High-Fidelity GraphRAG ETL Upgrade
- [x] 8. **Modify `async_fetch.py` (Neo4j Constraints Schema):** 
  - Add specific constraint creation for Customer and Review bounds:
    ```cypher
    CREATE CONSTRAINT customer_id IF NOT EXISTS FOR (c:Customer) REQUIRE c.id IS UNIQUE
    CREATE CONSTRAINT review_id IF NOT EXISTS FOR (r:Review) REQUIRE r.id IS UNIQUE
    ```
- [x] 9. **Modify `async_fetch.py` (Relational Ingestion):** In `map_postgres_to_neo4j()`, append direct cypher SQL bindings.
  - Execute batch `MERGE` statements translating PostgreSQL `customers`, `orders`, and `reviews` into exact Neo4j Nodes.
  - Bind Deep Edges: `(Customer)-[:PLACED]->(Order)-[:CONTAINS]->(Product)`, `(Customer)-[:WROTE]->(Review)-[:ABOUT]->(Product)`.
- [x] 10. **Vector Embedding Scope Expansion:** In `Neo4jVector.from_existing_graph(...)`, ensure the LLM continues to extract context strictly against `Product` nodes but inherently relies on the surrounding relational edges mapped in Task 9.

### Phase 13.E: Semantic Retriever Upgrade
- [x] 11. **Modify `retriever_service.py` (Cypher Logic Expanse):** Update `retrieval_query` string payload under `_initialize_vector_store()`.
  - **Before:** `OPTIONAL MATCH (node)-[r]->(neighbor)` (1-hop blind fetch).
  - **After:** Multi-hop traversal parsing `Review` texts directly into the context payload:
    ```cypher
    OPTIONAL MATCH (node)<-[:ABOUT]-(r:Review)<-[:WROTE]-(c:Customer)
    WITH node, score, collect({review: r.comment, rating: r.rating, customer: c.city}) as verified_sentiments
    ```
  - Append `verified_sentiments` dynamically to the final `context` string passed into `QA_PROMPT`.

### Phase 13.F: Local LLM Provider Switch
- [x] 12. **Environment Separation**: Modify `backend/ecommerce-graphrag/.env` to include `ETL_LLM_PROVIDER` and `ETL_OLLAMA_MODEL`.
- [x] 13. **Local Routing**: Modify `async_fetch.py` to route async generate calls dynamically between Google API `generate_content_async` and Langchain `ChatOllama.ainvoke` based on the `.env` configuration.

## Structural Verifications Post-Execution
- **Data Integrity Validation**: Execute `make graphrag-seed-postgres`. Validate that exactly zero FK exceptions arise representing flawless topological constraint satisfaction between synthetic orders and real product endpoints.
- **GraphRAG Vector Expansion Check**: Log output metrics confirming Neo4j mapped >> 2.0x Edges relative to baseline due to intensive semantic mapping.

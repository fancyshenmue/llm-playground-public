# Phase 12 CONTEXT: Retail Data Infrastructure & Dual-Database ETL

## Executive Summary

Phase 12 consolidates the entire Enterprise GraphRAG E-Commerce stack into a production-grade, dual-database architecture. It replaces the fragile DummyJSON external dependency with a self-contained, locally-generated dataset of **100,000 products** via the Marmelab `data-generator-retail` npm package. All six retail entity types (Customers, Categories, Products, Orders, Invoices, Reviews) are written to **both PostgreSQL (ACID transactional layer)** and **Neo4j (semantic retrieval layer)**, establishing the first true unified data backbone for the system.

---

## 1. Data Source: `data-generator-retail`

The Marmelab `data-generator-retail` package generates a complete, interconnected retail ecosystem in a single `generateData()` call:

| Entity     | Key Fields                                                        | Relationships                       |
| ---------- | ----------------------------------------------------------------- | ----------------------------------- |
| Categories | `id`, `name`                                                      | —                                   |
| Products   | `id`, `category_id`, `reference`, `price`, `stock`, `description` | Product → Category                  |
| Customers  | `id`, `first_name`, `last_name`, `email`, `address`               | —                                   |
| Orders     | `id`, `date`, `customer_id`, `basket[]`, `total`, `status`        | Order → Customer, Order → Product   |
| Invoices   | `id`, `date`, `order_id`, `customer_id`, `total`                  | Invoice → Order, Invoice → Customer |
| Reviews    | `id`, `date`, `customer_id`, `product_id`, `rating`, `comment`    | Review → Customer, Review → Product |

The default output is ~900 products. To achieve 100,000+, the generator script will be called in a loop with unique seed offsets, then concatenated and de-duplicated.

### Script Location

`scripts/ecommerce-graphrag/generate-retail-data.js`

---

## 2. Infrastructure: Unified Docker Compose

A single `docker-compose.yml` at `deployments/docker-compose/graphrag-ecommerce/docker-compose.yml` will bootstrap both databases:

- **PostgreSQL (pgvector:pg16)** on port `5432` — ACID-compliant transactional store.
- **Neo4j (latest)** on ports `7474/7687` — Graph + Vector semantic retrieval engine.

This replaces the current standalone `deployments/docker-compose/neo4j/docker-compose.yml` for GraphRAG purposes.

### Makefile Targets

- `make graphrag-db-up` — Start both PostgreSQL and Neo4j.
- `make graphrag-db-down` — Stop both.
- `make graphrag-generate-data` — Run the Node.js generator script, output JSON to `scripts/ecommerce-graphrag/data/`.
- `make graphrag-seed-postgres` — Load generated JSON into PostgreSQL tables.
- `make graphrag-etl` — Run LLM entity extraction from PostgreSQL → Neo4j (existing async pipeline, adapted).
- `make graphrag-neo4j-clean` — Wipe Neo4j (existing).

---

## 3. PostgreSQL Schema Design

```sql
CREATE TABLE categories (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE products (
    id          SERIAL PRIMARY KEY,
    category_id INTEGER REFERENCES categories(id),
    reference   VARCHAR(255),
    price       DECIMAL(10,2),
    stock       INTEGER DEFAULT 0,
    width       DECIMAL(6,2),
    height      DECIMAL(6,2),
    description TEXT,
    image       TEXT,
    thumbnail   TEXT
);

CREATE TABLE customers (
    id          SERIAL PRIMARY KEY,
    first_name  VARCHAR(255),
    last_name   VARCHAR(255),
    email       VARCHAR(255) UNIQUE,
    address     TEXT,
    city        VARCHAR(255),
    zipcode     VARCHAR(20),
    avatar      TEXT,
    birthday    DATE,
    nb_orders   INTEGER DEFAULT 0,
    total_spent DECIMAL(12,2) DEFAULT 0
);

CREATE TABLE orders (
    id          SERIAL PRIMARY KEY,
    date        TIMESTAMP,
    customer_id INTEGER REFERENCES customers(id),
    total       DECIMAL(12,2),
    status      VARCHAR(50),
    returned    BOOLEAN DEFAULT FALSE
);

CREATE TABLE order_items (
    id          SERIAL PRIMARY KEY,
    order_id    INTEGER REFERENCES orders(id),
    product_id  INTEGER REFERENCES products(id),
    quantity    INTEGER
);

CREATE TABLE invoices (
    id          SERIAL PRIMARY KEY,
    date        TIMESTAMP,
    order_id    INTEGER REFERENCES orders(id),
    customer_id INTEGER REFERENCES customers(id),
    total       DECIMAL(12,2)
);

CREATE TABLE reviews (
    id          SERIAL PRIMARY KEY,
    date        TIMESTAMP,
    customer_id INTEGER REFERENCES customers(id),
    product_id  INTEGER REFERENCES products(id),
    rating      INTEGER CHECK (rating BETWEEN 1 AND 5),
    comment     TEXT,
    status      VARCHAR(50)
);
```

---

## 4. Neo4j Graph Ontology

The Knowledge Graph extends the Phase 11 ontology to incorporate the full retail ecosystem:

```
(:Product) -[:BELONGS_TO]-> (:Category)
(:Customer) -[:PLACED]-> (:Order)
(:Order) -[:CONTAINS]-> (:Product)
(:Customer) -[:REVIEWED]-> (:Product)
(:Review) -[:ABOUT]-> (:Product)
(:Review) -[:BY]-> (:Customer)
(:Invoice) -[:FOR]-> (:Order)
```

This enables multi-hop queries like:

- _"Which customers who bought kitchen products also left 5-star reviews?"_
- _"Find products frequently co-purchased with laptops."_

---

## 5. ETL Pipeline Adaptation

The existing `async_fetch.py` will be forked/adapted to read from **PostgreSQL** instead of DummyJSON:

1. **Source**: `SELECT` from PostgreSQL tables (products joined with categories).
2. **LLM Extraction**: Cloud API `Gemini 2.5 Flash` ontology extraction logic paired with `tenacity` retry logic to ensure JSON validation compliance without blocking.
3. **Direct Property Mapping**: Alongside LLM-extracted entities, directly `MERGE` structured properties (`price`, `stock`, `category`, `description`) onto Product nodes.
4. **Relationship Construction**: Deterministically create edges (e.g., `BELONGS_TO`, `CONTAINS`) from PostgreSQL foreign keys — no LLM needed for structured relationships.
5. **Embedding Generation & Hybrid Indexing**: `Neo4jVector.from_existing_graph(search_type=SearchType.HYBRID)` generates enriched text embeddings via Nomic while simultaneously bootstrapping a native Neo4j Full-Text Index. This ensures subsequent retrievals combine vector cosine similarity with BM25 keyword matching via Reciprocal Rank Fusion (RRF).
6. **Data Realism Engine**: A pre-flight combinatorial script (`diversify_data.py`) ensures the baseline data is augmented with highly specific e-commerce properties (e.g. Leather, Ergonomics, Daily Commute) rather than narrow art gallery ontology, creating true 100k+ semantic uniqueness.

---

## 6. Architecture Alignment

This phase implements the combined "Phase 12 + Phase 13" blocks from the existing Unified System Architecture Diagram in `architecture.md`:

```
PostgreSQL (Source of Truth) → ETL Pipeline → Neo4j (Semantic Retrieval)
                                    ↕
               Cloud Gemini 2.5 Flash (Entity Extraction)
                 Local Nomic Embed (Vector Injection)
```

The Phase 11 Real-Time RAG Pipeline remains untouched — it continues to serve the Next.js frontend via the same FastAPI `/api/chat` endpoint, but now queries a far richer, structurally-connected Knowledge Graph.

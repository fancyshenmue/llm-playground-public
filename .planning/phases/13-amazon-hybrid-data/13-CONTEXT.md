# Phase 13 Architectural Context: Real-World Amazon Data & Hybrid Graph Injection

## 1. Executive Summary
Currently, the E-commerce GraphRAG system utilizes `data-generator-retail` to synthesize a dataset of 104,000 products. However, this dataset consists entirely of duplicated abstract poster metadata (e.g., "Cat Nose" images) accompanied by statistically uniform *Lorem Ipsum* descriptions. Our semantic enricher (`diversify_data.py`) partially masks this by combinatorially injecting adjectives, but the core entity associations lack real-world depth and semantic variability.

To establish a true Enterprise GraphRAG demonstration, we must migrate to authentic Big Data e-commerce topologies. Phase 13 completely deprecates the Node.js dummy generator in favor of a Python-native Hybrid Synthesis engine (`hybrid_amazon_generator.py`). This engine will ingest a slice of a verified open dataset (e.g., HuggingFace Amazon Reviews 2023 or FakeStore REST API) while synthetically scaffolding the relational Customer/Order CRM constraints required for PostgreSQL ACID validation. In addition, the Neo4j ETL pipeline will be upgraded to graph these extended semantic relationships (`Review`, `Customer`), unlocking advanced multi-hop queries.

## 2. Technical Weaknesses in the Current State

1. **Semantic Dead-Ends**: Context chunks embedded into Nomic currently contain random combinations like `"Carbon Fiber Edition Cat Nose"`. When testing Vector Search, the LLM hallucinates because the intrinsic properties of a "Cat Nose" conflict with "Carbon Fiber". Real GraphRAG evaluation requires genuine product specs (e.g., "120Hz OLED Screen").
2. **Missing Network Dynamics**: The current Neo4j pipeline (`async_fetch.py`) ONLY maps `Product` and `Category`. Real-world GraphRAG architectures integrate user engagement to perform logic such as Collaborative Filtering across the semantic space (`[Customer]->[WROTE]->[Review]->[ABOUT]->[Product]`).
3. **Mismatched Image URIs**: The UI renders Marmelab's static `.jpeg` poster templates, degrading the visual fidelity of the Next.js storefront.

## 3. Structural Directives for the New Hybrid Data Engine

The `hybrid_amazon_generator.py` must fulfill exact deterministic guarantees to maintain zero backward breakage with the `seed_postgres.py` DDL schemas.

### 3.1 Relational Blueprint & Schema Preservation
The output MUST yield six interconnected NDJSON (JSONL) artifacts:

*   **`categories.jsonl`**: Fetched dynamically based on real product categorical mapping.
    *   *Schema*: `{"id": int, "name": str}`
*   **`products.jsonl`**: Sourced directly from Real-World APIs. Image URLs must point to real CDNs.
    *   *Schema*: `{"id": int, "category_id": int, "reference": str (real product title), "price": float, "stock": int, "width": float, "height": float, "description": str (real human text), "image": url, "thumbnail": url}`
*   **`customers.jsonl`**: Reverse-synthesized via Python Faker matching geographic and demographic distributions.
    *   *Schema*: `{"id": int, "first_name": str, "last_name": str, "email": str, "address": str, "city": str, "zipcode": str, "avatar": str, "birthday": ISO-Date, "nb_commands": int, "total_spent": float}`
*   **`reviews.jsonl`**: Mapped directly from the real-world dataset. The text MUST be the actual written review, accurately tied to a legitimate `Customer ID` and `Product ID`.
    *   *Schema*: `{"id": int, "date": ISO-Date, "customer_id": int, "product_id": int, "rating": int, "comment": str, "status": str}`
*   **`orders.jsonl`** & **`invoices.jsonl`**: Synthesized probabilistically based on review timestamps to ensure temporal validity (a review cannot precede an order).
    *   *Schema*: Strictly bound foreign keys `customer_id` and nested `basket` arrays reflecting valid `product_id` prices.

### 3.2 Volume & Memory Scaling Limits
*   **Memory Ceiling**: The Python script must process data as an asynchronous stream or via chunked generators to prevent RAM exhaustion when handling the target goal of `100,000` synthesized entities.
*   **Reproducibility**: Use pseudo-random seed initialization (`random.seed(42)` and `Faker.seed(42)`) so subsequent runs deterministically output identical graphs to aid testing.

## 4. Neo4j ETL Architectural Upgrades

To fully leverage the Data Engine upgrade, `async_fetch.py` will be modified in **Phase 13**:

```cypher
// 1. Ingestion of Customer Nodes
MERGE (c:Customer {id: row.customer_id})
SET c.city = row.city, c.total_spent = row.total_spent

// 2. Ingestion of Review Nodes
MERGE (r:Review {id: row.review_id})
SET r.comment = row.comment, r.rating = row.rating, r.date = row.date

// 3. Mapping the Deep Edges
MERGE (c)-[:WROTE]->(r)
MERGE (r)-[:ABOUT]->(p:Product {id: row.product_id})
```

By completing this topology, the Vector-First GraphRAG can jump from a semantically-matched Product Node outward to retrieve exact Customer sentiments and reviews, injecting profound contextual understanding into the final LLM prompt.

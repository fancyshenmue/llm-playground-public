---
name: graphrag-verify
description: Verify Phase 13 Enterprise GraphRAG pipeline health — checks PostgreSQL, Neo4j, ETL completeness, Hybrid Search indexes, and cross-references against architecture documents.
---

# GraphRAG Pipeline Verification Skill

This skill validates the end-to-end health of the Enterprise GraphRAG Dual-Database system after an ETL run, incorporating Phase 13 Hybrid Synthesis checks.

## When To Use

- After running `make graphrag-etl` or `make graphrag-rebuild`
- After running `make graphrag-seed-postgres`
- When diagnosing search quality issues
- Before running production-scale `EXTRACT_LIMIT=0` ETL

## Verification Steps

### Step 1: Run the Verification Script

Execute the comprehensive check script:

```bash
export PATH="$HOME/.pixi/bin:$PATH" && pixi run python .agent/skills/graphrag-verify/scripts/verify_pipeline.py
```

### Step 2: Cross-Reference Against Architecture Specs

After the script runs, manually compare results against these reference documents:

| Document                                                 | Expected Validation                                                                                                                                                            |
| -------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `.planning/phases/12-retail-data-infra/12-CONTEXT.md` §4 | Neo4j ontology: Product→Category (BELONGS_TO), Product→Brand (PRODUCED_BY), Product→Feature (HAS_FEATURE), Product→Benefit (PROVIDES_BENEFIT), Product→Scenario (SUITABLE_FOR) |
| `.planning/phases/12-retail-data-infra/PLAN.md`          | Execution checklist items 12a–12m should be `[x]`. Items 12n (E2E test) and 12o (Hybrid+Image) reflect current WIP status                                                      |
| `documents/enterprise-graphrag/architecture.md` §1       | Dual-database flow: PG → ETL → Neo4j with Cloud Gemini extraction + Local Nomic embeddings                                                                                     |

### Step 3: Interpret Results

The verification script checks **9 categories**:

1. **PostgreSQL Row Counts** — All 7 tables should be populated according to `DATA_SCALE` boundaries.
2. **FK Integrity** — 100% of products must have valid `category_id` foreign keys.
3. **Diversity Injection** — Product references should contain Brand + Adjective + Material patterns, NOT plain `faker.lorem` text.
4. **Neo4j Node Counts** — Categories, Features, Brands, Benefits, Scenarios, Customers, Orders, and Reviews nodes should exist. Product count should closely mirror `DATA_SCALE`.
5. **Neo4j Relationship Types** — Structural edges: `BELONGS_TO`, `PLACED`, `CONTAINS`, `WROTE`, `ABOUT`. LLM extracted edges: `HAS_FEATURE`, `PROVIDES_BENEFIT`, `SUITABLE_FOR`, `PRODUCED_BY`.
6. **Schema Constraints** — `product_id`, `category_id`, `customer_id`, `review_id` UNIQUE constraints MUST exist.
7. **Hybrid Search Indexes** — `product_hybrid_index` (VECTOR) and `product_keyword_index` (FULLTEXT) must be ONLINE.
8. **Embedding Coverage** — Percentage of Product nodes with non-null `embedding` property.
9. **Semantic Extraction Coverage** — Count of products with LLM-extracted edges (beyond BELONGS_TO).

### Expected Healthy Output

```
=== PostgreSQL Health ===
  categories:    11          ✅
  customers:     ~20,000     ✅
  products:      ~100,000    ✅
  orders:        ~60,000     ✅
  order_items:   ~120,000    ✅
  invoices:      ~60,000     ✅
  reviews:       ~60,000     ✅
  FK Integrity:  100%        ✅

=== Neo4j Health ===
  Product nodes: ~100,000    ✅
  Category nodes: 11         ✅
  Constraints: product_id + category_id + customer_id + review_id  ✅
  Vector Index: ONLINE       ✅
  Keyword Index: ONLINE      ✅
  Embedding Coverage: >99%   ✅
  Semantic Products: depends on EXTRACT_LIMIT
```

### Common Failure Modes

| Symptom                       | Root Cause                                   | Fix                                                                                     |
| ----------------------------- | -------------------------------------------- | --------------------------------------------------------------------------------------- |
| Products = 0 in Neo4j         | ETL Part A didn't run                        | `make graphrag-etl`                                                                     |
| Embeddings = 0                | Part C failed or timed out                   | Re-run `make graphrag-etl` (idempotent)                                                 |
| No constraints                | Skipped or Neo4j restarted                   | Re-run ETL (constraints created at start)                                               |
| FK Integrity < 100%           | Data gen offset bug                          | `make graphrag-clean-all && make graphrag-generate-data && make graphrag-seed-postgres` |
| Semantic Products = 0         | `EXTRACT_LIMIT=0` not set or API key invalid | Check `GOOGLE_API_KEY` in `.env`                                                        |
| Semantic Products = 10 (stuck) | API 429 TooManyRequests (Rate Limit exceeded) | `async_fetch.py` concurrency too high. Ensure Semaphore is 3 and delays are added.      |
| Products ~130 instead of 104k | Title collision (MERGE on title)             | Verify `async_fetch.py` uses `pg_id` not `title`                                        |

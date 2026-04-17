# Phase 10: E-Commerce GraphRAG Implementation Context

## Goal
Implement a GraphRAG (Retrieval-Augmented Generation mapped over a Graph Database) assistant tailored for an e-commerce platform. The system should allow users to input natural language queries (e.g., "mountain gear that is waterproof") and receive highly relevant product recommendations by leveraging graph traversals across interconnected entities.

## Architectural Choices
- **Graph Database**: Neo4j (deployed via Docker Compose). Chosen over FalkorDB for the initial PoC due to its mature ecosystem, robust LangChain support, and visual exploration tool (Neo4j Browser).
- **Core Orchestration**: Python with FastAPI and LangChain. We utilize `GraphCypherQAChain` to execute a Text-to-Cypher translation via an LLM.
- **LLM Agent**: Gemini 1.5 Flash via Google AI Studio Free Tier (configured securely via environment variables), ensuring swift translation of intent into Cypher queries.
- **Frontend Stack**: Next.js with React and Tailwind CSS. The design adheres strictly to the `ui-ux-pro-max` workflow guidelines ("Vibrant & Block-based" style using primary green `#059669` and secondary orange).

## Data Ontology
A mock dataset generator was implemented across 5 primary domains (Mountain Climbing, Supplements, Electronics, Skincare, Pet Care) using the following schema:
- **Nodes**: `Product`, `Category`, `Scenario`, `Feature`, `Brand`
- **Edges**: `BELONGS_TO`, `SUITABLE_FOR`, `HAS_FEATURE`, `PRODUCED_BY`

## Verification Requirements
- E2E application components must be fully runnable via central CLI patterns.
- Neo4j must persist graph relationships and expose them via bolt port `7687`.

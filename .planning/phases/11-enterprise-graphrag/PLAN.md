# Phase 11 Execution PLAN: Enterprise Hybrid Knowledge GraphRAG

This checklist represents the exact, code-file-level sequence of steps required to build the production-grade hybrid retrieval architecture. Every item specifies the technical class, method, or file to touch.

## 1. ETL Ingestion Pipeline (Entity Extraction)

- [x] **1a:** Create `backend/ecommerce-graphrag/ingestion_ontology.py` to hold constant arrays for:
  - `ALLOWED_NODES = ["Product", "Brand", "Category", "Feature", "Material", "Benefit"]`
  - `ALLOWED_RELATIONSHIPS = ["PRODUCED_BY", "BELONGS_TO", "HAS_FEATURE", "MADE_OF", "PROVIDES_BENEFIT"]`
- [x] **1b:** Create `backend/ecommerce-graphrag/ingest.py`. Import `requests` to fetch data from `https://dummyjson.com/products?limit=100`.
- [x] **1c:** In `ingest.py`, map the JSON payload into LangChain `Document` objects containing `page_content=product['description']` and `metadata={"id": product['id'], "title": product['title'], "brand": product['brand']}`.
- [x] **1d:** Instantiate `ChatGoogleGenerativeAI(model="gemini-flash-latest")` and wrap it in `LLMGraphTransformer` using the strict `ALLOWED_NODES` ontology to extract organic entities natively.
- [x] **1e:** Use `Neo4jGraph.add_graph_documents()` to securely write the extracted GraphDocuments into Neo4j. Execute this script to populate the Database.

## 2. Vector Indexing Mechanism

- [x] **2a:** Ensure `nomic-embed-text` is registered. Inside `ingest.py` (after entity extraction), invoke LangChain's `Neo4jVector.from_existing_graph()`.
- [x] **2b:** Configure the vector index parameters:
  - `embedding=OllamaEmbeddings(model="nomic-embed-text")`
  - `node_label="Product"` (Or Target Concept Nodes)
  - `text_node_properties=["title", "description"]`
  - `embedding_node_property="embedding"`
  - `index_name="product_description_vector"`
- [x] **2c:** Verify Neo4j indices are created by querying `SHOW VECTOR INDEXES` computationally or via the UI.

## 3. Real-World Backend Architecture (Layered Design)

- [x] **3a:** Re-architect the `backend/ecommerce-graphrag/` directory to mimic a production FastAPI application. Instead of everything in `main.py`, create the following layout:
  - `core/config.py`: Environment variable validation and loading.
  - `core/database.py`: Neo4j driver singleton initialization.
  - `core/llm.py`: Initialization of `ChatGoogleGenerativeAI` and `OllamaEmbeddings`.
  - `schemas/chat.py`: Pydantic models (`ChatRequest`, `ChatResponse`).
  - `api/routes/chat.py`: The FastAPI router grouping endpoint logic.
  - `services/retriever_service.py`: Decoupled LangChain RAG mechanics (Neo4jVector initialization and chain building).
- [x] **3b:** Inside `services/retriever_service.py`, instantiate `Neo4jVector.from_existing_index` mapping to `"product_description_vector"`.
- [x] **3c:** Define the `retrieval_query` Cypher template to perform the **Multi-Hop Expansion**. e.g. `MATCH (node)-[:HAS_FEATURE]->(f:Feature) RETURN node.title, node.description, f.name`.
- [x] **3d:** Configure the retriever block: `vector_store.as_retriever(search_kwargs={'k': 5})`.

## 4. FastAPI Assembly & LLM Generation Integration

- [x] **4a:** Rewrite `main.py` completely to act solely as the Application Entrypoint (registering CORS and importing `api/routes/chat.py`).
- [x] **4b:** Construct a standard LangChain `create_stuff_documents_chain` using `QA_GENERATION_PROMPT` for the Gemini synthesis phase.
- [x] **4c:** Stitch the custom Neo4j Hybrid Retriever and QA Generation chain together inside `services/retriever_service.py`.
- [x] **4d:** Expose this chain through the router, maintaining the payload format for the Next.js UI (`reply`, `context`, etc.).

## 5. End-to-End System Validation

- [ ] **5a:** Clear the old database completely (`MATCH (n) DETACH DELETE n`).
- [ ] **5b:** Run `python ingest.py` and actively monitor LLM costs/latency as it organically extracts the 100 products.
- [ ] **5c:** Run `make graphrag-backend-dev`, boot up the Next.js UI.
- [ ] **5d:** Perform Stress Test 1 (Vague Intent): Ask `"I need something to apply to my face that feels refreshing"`. Verify the Hybrid Vector hits the skincare descriptions and returns organic features _without_ exact string matching failing.
- [ ] **5e:** Document final architecture into `.planning/ROADMAP.md` completely verifying Phase 11.

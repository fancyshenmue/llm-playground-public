import os
import json
import asyncio
import time

# Set sys path so we can import core
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from core.database import get_neo4j_graph, get_postgres_pool
from langchain_core.documents import Document
import google.generativeai as genai
from langchain_neo4j.graphs.graph_document import GraphDocument, Node, Relationship
from langchain_neo4j import Neo4jGraph
from langchain_neo4j import Neo4jVector
from langchain_neo4j.vectorstores.neo4j_vector import SearchType
from langchain_ollama import OllamaEmbeddings
from pydantic.v1 import BaseModel, Field
from typing import List, Optional
from json_repair import repair_json
from tenacity import retry, stop_after_attempt, wait_exponential


from langfuse import observe, get_client
# ==========================================
# 1. Ontology Definition
# ==========================================
ALLOWED_NODES = ["Product", "Brand", "Category", "Feature", "Benefit", "Scenario"]
ALLOWED_RELATIONSHIPS = ["PRODUCED_BY", "BELONGS_TO", "HAS_FEATURE", "PROVIDES_BENEFIT", "SUITABLE_FOR"]

class Entity(BaseModel):
    id: str = Field(..., description="Unique identifier or name of the entity.")
    type: str = Field(..., description=f"Must be one of {ALLOWED_NODES}")

class ObjectRelationship(BaseModel):
    source_id: str = Field(..., description="ID of the source Entity.")
    target_id: str = Field(..., description="ID of the target Entity.")
    type: str = Field(..., description=f"Must be one of {ALLOWED_RELATIONSHIPS}")

class KnowledgeGraph(BaseModel):
    entities: List[Entity] = Field(..., description="List of recognized entities.")
    relationships: List[ObjectRelationship] = Field(..., description="List of recognized relationships.")

PROVIDER = os.getenv("ETL_LLM_PROVIDER", "gemini").lower()

if PROVIDER == "ollama":
    from langchain_ollama import ChatOllama
    OLLAMA_MODEL = os.getenv("ETL_OLLAMA_MODEL", "gemma4:latest")
    print(f"🔧 Starting LLM Provider: LOCAL OLLAMA ({OLLAMA_MODEL})")
    llm = ChatOllama(model=OLLAMA_MODEL, temperature=0.0)
else:
    print("☁️ Starting LLM Provider: CLOUD GEMINI (gemini-2.5-flash)")
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    llm = genai.GenerativeModel('gemini-2.5-flash', generation_config={"temperature": 0.0})

EXTRACTION_PROMPT = """You are a highly structured data extractor.
Your task is to read the text below and extract a Knowledge Graph strictly adhering to the schema.
Only output a raw JSON object (without markdown wrappers like ```json).

You MUST output exactly in this JSON format:
{{
  "entities": [
    {{"id": "entity name", "type": "ALLOWED_NODE_TYPE"}}
  ],
  "relationships": [
    {{"source_id": "entity name", "target_id": "entity name", "type": "ALLOWED_RELATIONSHIP_TYPE"}}
  ]
}}

# ALLOWED_NODES:
{allowed_nodes}

# ALLOWED_RELATIONSHIPS:
{allowed_relationships}

# Text:
{text}
"""

@observe(name="ecommerce_etl_extract", as_type="generation")
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=4, max=30))
async def extract_knowledge_async(doc: Document, semaphore: asyncio.Semaphore) -> Optional[GraphDocument]:
    async with semaphore:
        prompt = EXTRACTION_PROMPT.format(
            allowed_nodes=", ".join(ALLOWED_NODES),
            allowed_relationships=", ".join(ALLOWED_RELATIONSHIPS),
            text=doc.page_content
        )

        print(f"   => [Extraction Started]: {doc.metadata['title']} ...")
        
        # Log to Langfuse
        get_client().update_current_generation(
            input=doc.page_content,
            model=OLLAMA_MODEL if PROVIDER == "ollama" else "gemini-2.5-flash",
            metadata={"title": doc.metadata['title'], "pg_id": doc.metadata['pg_id']}
        )

        start_time = time.time()
        
        if PROVIDER == "ollama":
            from langchain_core.messages import HumanMessage
            res = await llm.ainvoke([HumanMessage(content=prompt)])
            raw_res = res.content.strip()
        else:
            res = await llm.generate_content_async(prompt)
            raw_res = res.text.strip()
            
        elapsed = time.time() - start_time

        print(f"   => [LLM Responded] in {elapsed:.2f}s for '{doc.metadata['title']}'...")
        
        # Log raw response to Langfuse
        get_client().update_current_generation(output=raw_res)

        if raw_res.startswith("```json"): raw_res = raw_res[7:]
        if raw_res.endswith("```"): raw_res = raw_res[:-3]

        try:
            fixed_json_str = repair_json(raw_res)
            json_obj = json.loads(fixed_json_str)
            kg = KnowledgeGraph.parse_obj(json_obj)
            kg_dict = kg.dict()

            root_id = str(doc.metadata['pg_id'])
            root_title = str(doc.metadata['title'])
            
            nodes = [Node(id=root_id, type="Product", properties={"title": root_title})]
            valid_node_types = {root_title: "Product", root_id: "Product"}
            
            for ent in kg_dict["entities"]:
                ent_id = str(ent["id"])
                if ent["type"] in ALLOWED_NODES and ent_id != root_title:
                    nodes.append(Node(id=ent_id, type=str(ent["type"]), properties={}))
                    valid_node_types[ent_id] = str(ent["type"])

            relationships = []
            for rel in kg_dict["relationships"]:
                s_id = str(rel["source_id"])
                t_id = str(rel["target_id"])
                
                # Auto-resolve LLM hallucinating names back to integer pg_id
                if s_id == root_title: s_id = root_id
                if t_id == root_title: t_id = root_id

                if (rel["type"] in ALLOWED_RELATIONSHIPS and s_id in valid_node_types and t_id in valid_node_types):
                    relationships.append(Relationship(
                        source=Node(id=s_id, type=valid_node_types[s_id], properties={}),
                        target=Node(id=t_id, type=valid_node_types[t_id], properties={}),
                        type=str(rel["type"]),
                        properties={}
                    ))

            graph_doc = GraphDocument(nodes=nodes, relationships=relationships, source=doc)
            print(f"   => [SUCCESS]: {doc.metadata['title']} ({len(nodes)} nodes, {len(relationships)} edges)")
            return graph_doc

        except Exception as e:
            print(f"   => [FAILED] {doc.metadata['title']}: {str(e)}")
            raise ValueError(f"Extraction failed: {e}")

# ==========================================
# 3. Direct Neo4j Mapping Functions (No LLM)
# ==========================================
def map_postgres_to_neo4j(graph: Neo4jGraph):
    pool = get_postgres_pool()
    with pool.connection() as conn:
        with conn.cursor() as cur:
            print("0. Initializing Neo4j Schema Constraints (Critical for Performance)...")
            try:
                graph.query("CREATE CONSTRAINT product_id IF NOT EXISTS FOR (p:Product) REQUIRE p.id IS UNIQUE")
                graph.query("CREATE CONSTRAINT category_id IF NOT EXISTS FOR (c:Category) REQUIRE c.id IS UNIQUE")
                graph.query("CREATE CONSTRAINT customer_id IF NOT EXISTS FOR (c:Customer) REQUIRE c.id IS UNIQUE")
                graph.query("CREATE CONSTRAINT review_id IF NOT EXISTS FOR (r:Review) REQUIRE r.id IS UNIQUE")
            except Exception as e:
                print(f"Constraint creation notice: {e}")
            
            print("1. Syncing Categories...")
            cur.execute("SELECT id, name FROM categories")
            categories = [{"id": row[0], "name": row[1]} for row in cur.fetchall()]
            graph.query("""
                UNWIND $batch AS row
                MERGE (c:Category {id: row.name})
            """, params={"batch": categories})

            print("2. Syncing Products (All 104K in batches)...")
            cur.execute("""
                SELECT p.id, p.reference, p.price, p.description, p.image, c.name
                FROM products p JOIN categories c ON p.category_id = c.id
            """)

            total_products = []
            batch_size = 10000

            while True:
                rows = cur.fetchmany(batch_size)
                if not rows:
                    break

                products_batch = []
                for row in rows:
                    products_batch.append({
                        "pg_id": row[0],
                        "title": row[1],
                        "price": float(row[2]) if row[2] else 0.0,
                        "description": row[3],
                        "image": row[4],
                        "category": row[5]
                    })

                graph.query("""
                    UNWIND $batch AS row
                    MERGE (p:Product {id: row.pg_id})
                    SET p.title = row.title, p.description = row.description, p.price = row.price, p.image = row.image, p.category = row.category
                    MERGE (c:Category {id: row.category})
                    MERGE (p)-[:BELONGS_TO]->(c)
                """, params={"batch": products_batch})

                total_products.extend(products_batch)
                print(f"   ... Pushed batch of {len(products_batch)} products. Total so far: {len(total_products)}")

            print(f"   Finished syncing {len(total_products)} products and edges to Neo4j.")
            
            print("3. Syncing Customers...")
            cur.execute("SELECT id, city, total_spent FROM customers")
            customers = [{"id": row[0], "city": row[1], "spent": float(row[2])} for row in cur.fetchall()]
            graph.query("""
                UNWIND $batch AS row
                MERGE (c:Customer {id: row.id})
                SET c.city = row.city, c.total_spent = row.spent
            """, params={"batch": customers})
            
            print("4. Syncing Reviews and Deep Edges...")
            cur.execute("""
                SELECT r.id, r.product_id, r.customer_id, r.rating, r.comment, r.date, o.id as order_id
                FROM reviews r 
                LEFT JOIN orders o ON r.id = o.id 
            """)
            # Since generating 60k reviews, chunk them just in case memory triggers limits on Neo4j
            reviews = []
            for row in cur.fetchall():
                reviews.append({
                    "id": row[0], "pid": row[1], "cid": row[2], 
                    "rating": row[3], "comment": row[4], "date": str(row[5]), "oid": row[6]
                })
            
            chunk_size = 10000
            for i in range(0, len(reviews), chunk_size):
                batch = reviews[i:i+chunk_size]
                graph.query("""
                    UNWIND $batch AS row
                    // Create Review Node
                    MERGE (r:Review {id: row.id})
                    SET r.rating = row.rating, r.comment = row.comment, r.date = row.date
                    
                    // Create Order Node
                    MERGE (o:Order {id: row.oid})
                    
                    // Edge Mapping
                    WITH row, r, o
                    MATCH (c:Customer {id: row.cid})
                    MATCH (p:Product {id: row.pid})
                    
                    MERGE (c)-[:PLACED]->(o)-[:CONTAINS]->(p)
                    MERGE (c)-[:WROTE]->(r)-[:ABOUT]->(p)
                """, params={"batch": batch})
                print(f"   ... Pushed batch of {len(batch)} reviews & relational edges.")
                
            return total_products

# ==========================================
# 4. Pipeline Orchestration
# ==========================================
async def async_etl_pipeline():
    graph = get_neo4j_graph()

    print("=== PART A: Direct Relational Mapping (PostgreSQL -> Neo4j) ===")
    products = map_postgres_to_neo4j(graph)

    print("\n=== PART B: LLM Semantic Knowledge Extraction ===")
    # [Resumption Safety] Query Neo4j to find products that already have semantic edges
    processed_req = graph.query("MATCH (p:Product)-[r]->() WHERE type(r) <> 'BELONGS_TO' RETURN DISTINCT p.id as id")
    processed_ids = {str(rec['id']) for rec in processed_req}
    
    documents = []
    for p in products:
        if str(p['pg_id']) in processed_ids:
            continue
            
        content = (
            f"Product Name: {p['title']}\n"
            f"Category: {p['category']}\n"
            f"Description: {p['description']}\n"
        )
        documents.append(Document(page_content=content, metadata={"title": p['title'], "pg_id": p['pg_id']}))
        
    print(f"   => Found {len(processed_ids)} previously processed products.")
    
    # ========================================================
    # SECURITY & COST LIMIT: Prevent accidental massive token burn
    # ========================================================
    # To run all 100,000 products, run: EXTRACT_LIMIT=0 make graphrag-rebuild
    try:
        data_scale = int(os.getenv("DATA_SCALE", "100000"))
        # If running a small test scale, extract them all natively. If massive scale, default to safety 25.
        default_limit = data_scale if data_scale <= 2500 else 25
        sample_limit = int(os.getenv("EXTRACT_LIMIT", str(default_limit)))
    except ValueError:
        sample_limit = 25

    if sample_limit > 0 and len(documents) > sample_limit:
        print(f"   ⚠️ [SAFETY LIMIT ACTIVATED] Limiting LLM Semantic Extraction to first {sample_limit} products.")
        print(f"   (To extract all {len(documents)} records, run with EXTRACT_LIMIT=0. Est cost: ~$5, Time: ~45m)")
        documents = documents[:sample_limit]
    else:
        print(f"   🔥 [FULL PRODUCTION MODE] Proceeding to extract ALL {len(documents)} products via Gemini API...")
    
    if len(documents) == 0:
        print("   => All products are extracted! Skipping Part B.")
    
    # Process in chunks to prevent creating 104k simultaneous coroutines
    semaphore = asyncio.Semaphore(3) # 3 concurrent calls (free-tier: ~10-15 RPM)
    chunk_size = 50
    
    valid_graph_docs = []
    for i in range(0, len(documents), chunk_size):
        chunk = documents[i:i+chunk_size]
        print(f"   => Processing LLM extraction chunk {i//chunk_size + 1}/{(len(documents)+chunk_size-1)//chunk_size}...")
        tasks = [extract_knowledge_async(doc, semaphore) for doc in chunk]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        chunk_valid = []
        chunk_failed = 0
        for idx, res in enumerate(results):
            if isinstance(res, GraphDocument):
                chunk_valid.append(res)
            elif isinstance(res, Exception):
                chunk_failed += 1
                doc_title = chunk[idx].metadata.get('title', 'unknown')
                print(f"   => [ERROR SWALLOWED] {doc_title}: {type(res).__name__}: {str(res)[:200]}")
        
        valid_graph_docs.extend(chunk_valid)
        print(f"   => Chunk result: {len(chunk_valid)} success, {chunk_failed} failed out of {len(chunk)}")
        
        # Merge subgraphs per chunk to stream to Neo4j
        if chunk_valid:
            graph.add_graph_documents(chunk_valid)
            
    print(f"   => Extracted {len(valid_graph_docs)} subgraphs from {len(products)} products. All merged into Neo4j!")

    print("\n=== PART C: Regenerating Vector Index ===")
    print(f"Running Neo4jVector.from_existing_graph (nomic-embed-text) on ALL {len(products)} Product nodes...")

    embeddings = OllamaEmbeddings(model='nomic-embed-text')
    Neo4jVector.from_existing_graph(
        embedding=embeddings,
        url=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        username=os.getenv("NEO4J_USERNAME", "neo4j"),
        password=os.getenv("NEO4J_PASSWORD", "password"),
        index_name='product_hybrid_index',
        keyword_index_name='product_keyword_index',
        node_label='Product',
        text_node_properties=['title', 'description', 'category'],
        embedding_node_property='embedding',
        search_type=SearchType.HYBRID,
    )
    print("   => Vector and BM25 index regenerated successfully. All Neo4j product entities are now mapped for Hybrid Search.")

    total_nodes = graph.query("MATCH (n) RETURN COUNT(n) AS count")[0]["count"]
    total_edges = graph.query("MATCH ()-[r]->() RETURN COUNT(r) AS count")[0]["count"]
    print("\n=======================================================")
    print(f"ETL Pipeline Complete! Neo4j currently holds:")
    print(f"  - Total Nodes: {total_nodes}")
    print(f"  - Total Relationships: {total_edges}")
    print("=======================================================")

if __name__ == "__main__":
    asyncio.run(async_etl_pipeline())


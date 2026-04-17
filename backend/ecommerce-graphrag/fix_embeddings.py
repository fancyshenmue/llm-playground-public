"""
fix_embeddings.py
=================
One-shot script to force-generate missing vector embeddings for ALL Product nodes
in Neo4j using nomic-embed-text via Ollama.

Run this ONCE after ETL ingestion to ensure the vector index is fully populated:
    pixi run python backend/ecommerce-graphrag/fix_embeddings.py
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from langchain_neo4j import Neo4jVector
from core.config import settings
from core.llm import get_embeddings

def rebuild_product_embeddings():
    print("=" * 60)
    print("GraphRAG Embedding Repair Tool")
    print("=" * 60)
    print(f"Target Index : product_hybrid_index")
    print(f"Node Label   : Product")
    print(f"Model        : {settings.OLLAMA_EMBEDDING_MODEL}")
    print(f"Neo4j URI    : {settings.NEO4J_URI}")
    print()
    print("Connecting to Neo4j and rebuilding embeddings...")
    print("This may take several minutes for large catalogs.\n")

    embeddings = get_embeddings()

    # from_existing_graph will upsert embeddings for every matching node,
    # regardless of whether the embedding field already exists. 
    # This is safe to run multiple times (idempotent).
    vector_store = Neo4jVector.from_existing_graph(
        embedding=embeddings,
        url=settings.NEO4J_URI,
        username=settings.NEO4J_USERNAME,
        password=settings.NEO4J_PASSWORD,
        index_name="product_hybrid_index",
        node_label="Product",
        text_node_properties=["id", "description", "category"],
        embedding_node_property="embedding",
    )

    print("\n✅ Embedding repair complete!")
    print("   All Product nodes now have vector coordinates in Neo4j.")
    print("   You can now restart the backend and run semantic search queries.")
    return vector_store

if __name__ == "__main__":
    rebuild_product_embeddings()

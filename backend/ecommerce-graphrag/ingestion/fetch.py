import os
import requests
import time

from langchain_core.documents import Document
from langchain_ollama import ChatOllama
from langchain_neo4j.graphs.graph_document import GraphDocument, Node, Relationship
from langchain_neo4j import Neo4jGraph
from pydantic.v1 import BaseModel, Field
from typing import List

from ontology import ALLOWED_NODES, ALLOWED_RELATIONSHIPS



# --- Custom Pydantic Graph Extractor ---
class ExtractedNode(BaseModel):
    id: str = Field(description="Unique identifier for the node (e.g. 'Apple', 'Laptop', 'Waterproof')")
    type: str = Field(description=f"Node type. MUST be one of: {ALLOWED_NODES}")

class ExtractedEdge(BaseModel):
    source_id: str = Field(description="The ID of the source node")
    target_id: str = Field(description="The ID of the target node")
    type: str = Field(description=f"Relationship type. MUST be one of: {ALLOWED_RELATIONSHIPS}")

class KnowledgeGraph(BaseModel):
    entities: List[ExtractedNode] = Field(description="List of extracted nodes")
    relationships: List[ExtractedEdge] = Field(description="List of extracted edges between nodes")

def extract_and_load_knowledge_graph():
    print("1. Fetching raw product data from dummyjson...")
    response = requests.get("https://dummyjson.com/products?limit=10") # Limit to 10 for quick testing
    if response.status_code != 200:
        raise Exception(f"Failed to fetch data: {response.status_code}")
    
    products = response.json().get('products', [])
    print(f"Fetched {len(products)} products.")

    print("2. Mapping JSON payload into LangChain Document objects...")
    documents = []
    for p in products:
        content = f"Product Title: {p.get('title', '')}\nCategory: {p.get('category', '')}\nDescription: {p.get('description', '')}"
        
        doc = Document(
            page_content=content,
            metadata={
                "id": str(p.get('id')),
                "title": str(p.get('title')),
                "brand": str(p.get('brand', 'Unknown')),
                "category": str(p.get('category', 'Unknown'))
            }
        )
        documents.append(doc)

    print("3. Initializing Local Gemma 26B Graph Extractor...")
    llm = ChatOllama(
        model="gemma4:26b",
        temperature=0.0, 
    )

    print("4. Extracting Graph Ontology via LLM...")
    graph_documents = []
    for doc in documents:
        print(f"   => Processing: {doc.metadata['title']}...")
        prompt = f"""
        Extract the knowledge graph from the following product documentation.
        You must strictly use these Node Categories: {ALLOWED_NODES}
        You must strictly use these Edge Relationships: {ALLOWED_RELATIONSHIPS}
        
        CRITICAL: Output ONLY a valid JSON payload matching this exact schema:
        {KnowledgeGraph.schema_json()}
        Do NOT wrap the response in ```json. Just raw parsable JSON string.
        
        Text:
        {doc.page_content}
        """
        try:
            # We enforce JSON mode natively via Ollama for stricter parsing
            res_str = llm.invoke(prompt, format="json").content.strip()
            
            # Clean up markdown if model disobeys
            if res_str.startswith("```json"):
                res_str = res_str[7:]
            if res_str.startswith("```"):
                res_str = res_str[3:]
            if res_str.endswith("```"):
                res_str = res_str[:-3]
            res_str = res_str.strip()
            
            res = KnowledgeGraph.parse_raw(res_str)
            
            # Convert Pydantic output to LangChain Neo4j GraphDocument objects
            lc_nodes = {}
            for n in res.entities:
                if n.type in ALLOWED_NODES:
                    lc_nodes[n.id] = Node(id=n.id, type=n.type)
            
            lc_edges = []
            for e in res.relationships:
                if e.type in ALLOWED_RELATIONSHIPS and e.source_id in lc_nodes and e.target_id in lc_nodes:
                    lc_edges.append(Relationship(
                        source=lc_nodes[e.source_id],
                        target=lc_nodes[e.target_id],
                        type=e.type
                    ))
            
            # Central anchor node for the document itself
            doc_node = Node(id=doc.metadata['title'], type="Product", properties=doc.metadata)
            
            # Connect the extracted graph to the root document node implicitly if needed
            graph_doc = GraphDocument(
                nodes=list(lc_nodes.values()) + [doc_node],
                relationships=lc_edges,
                source=doc
            )
            graph_documents.append(graph_doc)
        except Exception as e:
            print(f"   [!] Failed extracting {doc.metadata['title']}: {e}")

    print(f"\nSuccessfully extracted {len(graph_documents)} graph documents!")

    print("5. Connecting to Neo4j and writing knowledge graph...")
    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

    try:
        graph = Neo4jGraph(
            url=NEO4J_URI,
            username=NEO4J_USERNAME,
            password=NEO4J_PASSWORD,
        )
        
        graph.add_graph_documents(
            graph_documents,
            baseEntityLabel=True,
            include_source=True
        )
        print("ETL Pipeline completed successfully! True Knowledge Graph has been born.")
    except Exception as e:
        print(f"Failed to connect or write to Neo4j: {e}")

if __name__ == "__main__":
    extract_and_load_knowledge_graph()

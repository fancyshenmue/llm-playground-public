import os
from langchain_neo4j import Neo4jGraph
from langchain_neo4j import Neo4jVector
from langchain_ollama import OllamaEmbeddings


def seed_graph_database():
    print("1. Connecting to Neo4j...")
    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

    graph = Neo4jGraph(url=NEO4J_URI, username=NEO4J_USERNAME, password=NEO4J_PASSWORD)
    
    print("2. Clearing old graph...")
    graph.query("MATCH (n) DETACH DELETE n;")

    print("3. Seeding rich interconnected Graph Knowledge (Mock Data)...")
    seed_cypher = """
    // Create Categories
    CREATE (c1:Category {name: '戶外裝備'})
    CREATE (c2:Category {name: '機能服飾'})

    // Create Features & Benefits
    CREATE (f1:Feature {name: 'Gore-Tex 防水'})
    CREATE (f2:Feature {name: 'Vibram 黃金大底'})
    CREATE (b1:Benefit {name: '防風避雨'})
    CREATE (b2:Benefit {name: '抗滑抓地'})
    CREATE (b3:Benefit {name: '輕量化'})

    // Create Scenarios
    CREATE (s1:Scenario {name: '百岳縱走'})
    CREATE (s2:Scenario {name: '海外滑雪'})

    // Create Products & Relationships
    CREATE (p1:Product {id: 'P001', title: 'Arcteryx 始祖鳥 Alpha SV 頂級防水外套', category: '機能服飾', description: '針對海外極端天候設計的頂尖衝鋒衣，使用最耐磨的Gore-Tex Pro材質。', price: 24500})
    CREATE (p1)-[:BELONGS_TO]->(c2)
    CREATE (p1)-[:HAS_FEATURE]->(f1)
    CREATE (p1)-[:PROVIDES_BENEFIT]->(b1)
    CREATE (p1)-[:SUITABLE_FOR]->(s1)
    CREATE (p1)-[:SUITABLE_FOR]->(s2)

    CREATE (p2:Product {id: 'P002', title: 'Lowa Renegade GTX 中筒登山鞋', category: '戶外裝備', description: '德國國民神鞋，兼具防水防滑與舒適度，適合各種中低海拔山區。', price: 7900})
    CREATE (p2)-[:BELONGS_TO]->(c1)
    CREATE (p2)-[:HAS_FEATURE]->(f1)
    CREATE (p2)-[:HAS_FEATURE]->(f2)
    CREATE (p2)-[:PROVIDES_BENEFIT]->(b2)
    CREATE (p2)-[:SUITABLE_FOR]->(s1)

    CREATE (p3:Product {id: 'P003', title: 'Hilleberg Niak 單雙人輕量帳篷', category: '戶外裝備', description: '黃標輕量化設計，極致抗風，適合熱愛縱走且重視裝備重量的進階玩家。', price: 31000})
    CREATE (p3)-[:BELONGS_TO]->(c1)
    CREATE (p3)-[:PROVIDES_BENEFIT]->(b3)
    CREATE (p3)-[:PROVIDES_BENEFIT]->(b1)
    CREATE (p3)-[:SUITABLE_FOR]->(s1)
    """
    graph.query(seed_cypher)
    print("Graph properly seeded with 3 interconnected products! 🎉")

    print("4. Building Vector Store Index with nomic-embed-text...")
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    
    Neo4jVector.from_existing_graph(
        embedding=embeddings,
        url=NEO4J_URI,
        username=NEO4J_USERNAME,
        password=NEO4J_PASSWORD,
        index_name="product_hybrid_index",
        node_label="Product",
        text_node_properties=["title", "description", "category"],
        embedding_node_property="embedding",
    )
    print("Vector Index built successfully! Backend is 100% READY.")

if __name__ == "__main__":
    seed_graph_database()

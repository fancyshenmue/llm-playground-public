from langchain_neo4j import Neo4jGraph
from psycopg_pool import ConnectionPool
from .config import settings

def get_neo4j_graph():
    try:
        graph = Neo4jGraph(
            url=settings.NEO4J_URI,
            username=settings.NEO4J_USERNAME,
            password=settings.NEO4J_PASSWORD,
        )
        return graph
    except Exception as e:
        print(f"Warning: Could not connect to Neo4j. Error: {e}")
        return None

_pg_pool = None

def get_postgres_pool():
    global _pg_pool
    if _pg_pool is None:
        conninfo = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
        try:
            _pg_pool = ConnectionPool(conninfo, min_size=1, max_size=10)
        except Exception as e:
            print(f"Warning: Could not connect to PostgreSQL. Error: {e}")
    return _pg_pool

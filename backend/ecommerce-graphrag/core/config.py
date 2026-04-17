import os
import yaml
from pathlib import Path

# Load config.yaml
config_path = Path(__file__).parent.parent / "config.yaml"
_config = {}
if config_path.exists():
    with open(config_path, "r", encoding="utf-8") as file:
        _config = yaml.safe_load(file) or {}

class Settings:
    # Server configs
    HOST = _config.get("server", {}).get("host", "0.0.0.0")
    PORT = _config.get("server", {}).get("port", 8000)

    # Neo4j Graph Database configurations
    NEO4J_URI = _config.get("neo4j", {}).get("uri", "bolt://localhost:7687")
    NEO4J_USERNAME = _config.get("neo4j", {}).get("username", "neo4j")
    NEO4J_PASSWORD = _config.get("neo4j", {}).get("password", "password")
    
    # Postgres configs
    POSTGRES_DB = _config.get("postgres", {}).get("db", "ecommerce")
    POSTGRES_USER = _config.get("postgres", {}).get("user", "postgres")
    POSTGRES_PASSWORD = _config.get("postgres", {}).get("password", "password")
    POSTGRES_HOST = _config.get("postgres", {}).get("host", "localhost")
    POSTGRES_PORT = _config.get("postgres", {}).get("port", "5432")
    
    # We use Google's LLM for Synthesizing the response
    GOOGLE_API_KEY = _config.get("llm", {}).get("google_api_key", os.getenv("GOOGLE_API_KEY"))
    LLM_MODEL = _config.get("llm", {}).get("model", "gemini-flash-latest")
    
    # We use local Ollama Nomic Embeddings for vector search
    # As Google Embeddings often throw PermissionDenied 403 on standard keys
    OLLAMA_EMBEDDING_MODEL = "nomic-embed-text"

    # ETL configuration
    ETL_LLM_PROVIDER = _config.get("etl", {}).get("provider", "ollama")
    ETL_OLLAMA_MODEL = _config.get("etl", {}).get("model", "gemma4:latest")

    # Langfuse configuration
    LANGFUSE_SECRET_KEY = _config.get("langfuse", {}).get("secret_key", os.getenv("LANGFUSE_SECRET_KEY"))
    LANGFUSE_PUBLIC_KEY = _config.get("langfuse", {}).get("public_key", os.getenv("LANGFUSE_PUBLIC_KEY"))
    LANGFUSE_HOST = _config.get("langfuse", {}).get("host", "http://localhost:3000")

# Inject critical keys into OS environ for LangChain/Langfuse SDKs to pick up automatically
if _config.get("langfuse", {}).get("secret_key"):
    os.environ["LANGFUSE_SECRET_KEY"] = _config["langfuse"]["secret_key"]
if _config.get("langfuse", {}).get("public_key"):
    os.environ["LANGFUSE_PUBLIC_KEY"] = _config["langfuse"]["public_key"]
if _config.get("langfuse", {}).get("host"):
    os.environ["LANGFUSE_HOST"] = _config["langfuse"]["host"]
if _config.get("llm", {}).get("google_api_key"):
    os.environ["GOOGLE_API_KEY"] = str(_config["llm"]["google_api_key"])
if _config.get("neo4j", {}).get("uri"):
    os.environ["NEO4J_URI"] = str(_config["neo4j"]["uri"])
if _config.get("neo4j", {}).get("username"):
    os.environ["NEO4J_USERNAME"] = str(_config["neo4j"]["username"])
if _config.get("neo4j", {}).get("password"):
    os.environ["NEO4J_PASSWORD"] = str(_config["neo4j"]["password"])

settings = Settings()

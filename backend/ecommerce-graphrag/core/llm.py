from langchain_ollama import ChatOllama
from langchain_ollama import OllamaEmbeddings
from .config import settings

def get_llm():
    # Force use Local Gemma4 to prevent Google API 404 blocking
    return ChatOllama(
        model="gemma4:latest",
        temperature=0.0
    )

def get_embeddings():
    # We use local Ollama embeddings built from nomic-embed-text for vector search
    # It removes reliance on Google API limits
    return OllamaEmbeddings(
        model=settings.OLLAMA_EMBEDDING_MODEL
    )

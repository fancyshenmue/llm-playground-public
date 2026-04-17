from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import chat

# Initialize FastAPI
app = FastAPI(
    title="Enterprise Hybrid GraphRAG Backend",
    description="Vector Semantic Similarity + Neo4j Graph Expansion",
    version="2.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(chat.router, prefix="/api", tags=["Chat"])

@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "architecture": "Hybrid Vector + Multi-Hop Graph Traversal",
        "llm_synthesizer": "gemini-flash-latest",
        "vector_embedding": "nomic-embed-text (Ollama)"
    }

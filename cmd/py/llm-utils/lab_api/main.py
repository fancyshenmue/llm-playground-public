from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .agent import run_agent

app = FastAPI(title="LangChain Lab API", version="0.1.0")

# Enable CORS for React frontend (port 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Wildcard for local testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    mode: str = "ReAct Architecture"

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    # Run the appropriate LangGraph agent based on mode
    result = run_agent(request.message, request.mode)
    return {"response": result}

import os
import re
from contextlib import asynccontextmanager
os.environ["PHOENIX_PROJECT_NAME"] = "langgraph-mcp-agent"

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from phoenix.otel import register
from openinference.instrumentation.langchain import LangChainInstrumentor

from .graph import invoke_coding_agent, stream_coding_agent
from .autonomous_agent import AutonomousAgent

import yaml

config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yaml")
if not os.path.exists(config_path):
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yaml.example")

try:
    with open(config_path, "r") as f:
        _cfg = yaml.safe_load(f) or {}
    _obs = _cfg.get("observability") or {}
    OBS_BACKEND = _obs.get("backend", "none") if isinstance(_obs, dict) else "none"
except Exception:
    OBS_BACKEND = "none"

# Initialize observability
def setup_telemetry():
    if OBS_BACKEND in ["phoenix", "both"]:
        try:
            register(endpoint="http://127.0.0.1:16006/v1/traces")
            LangChainInstrumentor().instrument()
            print("🔭 Phoenix Telemetry activated: Tracing MCP calls.")
        except Exception as e:
            print(f"⚠️ Phoenix Telemetry initialization failed: {e}")

setup_telemetry()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # AutonomousAgent instances are request-scoped (created per /api/autonomous/stream call)
    # with dynamic sandbox directories. No global pre-initialization needed.
    yield

app = FastAPI(title="Enterprise Auto-Coding Agent API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class CodeRequest(BaseModel):
    task: str
    thread_id: str = "auto_coder_session_01"

@app.get("/health")
def health_check():
    return {"status": "Enterprise API Operational"}

@app.post("/api/encode")
async def execute_coding_task(request: CodeRequest):
    result = await invoke_coding_agent(request.task, request.thread_id)
    return {
        "message": "Cycles completed",
        "iterations": result.get("iterations", 0),
        "code_passed": result.get("lint_errors") == "PASS",
        "final_code": result.get("code")
    }

@app.post("/api/encode/stream")
async def execute_coding_task_stream(request: CodeRequest):
    """Event Source endpoint for streaming LangGraph node executions."""
    return StreamingResponse(
        stream_coding_agent(request.task, request.thread_id), 
        media_type="text/event-stream"
    )

@app.post("/api/autonomous/stream")
async def execute_autonomous_stream(request: CodeRequest):
    """Event Source endpoint for Phase 15 Autonomous Coder."""
    
    # 2c: Parse prompt string to extract absolute directory paths so MCP doesn't crash on permissions
    # Supports paths preceded by whitespace, backticks, or quotes
    global_extracted = set()
    for match in re.findall(r'(?:^|[\s`\'"])(/[^\s\)\(`\'"]+)', request.task):
        candidate = match.rstrip("/")
        raw_candidate = os.path.expanduser(candidate)
        real_candidate = os.path.realpath(raw_candidate)
        for c in [raw_candidate, real_candidate]:
            if "." in os.path.basename(c):
                c = os.path.dirname(c)
            if c and c != "/":
                global_extracted.add(c)

    valid_dirs = [d for d in global_extracted if os.path.exists(d)]
    
    # 2d: Establish Thread-Isolated Sandbox Scratchpad
    # We create the dir but DO NOT append it to valid_dirs because pointing local models
    # to an empty directory can trick them into hallucinating an empty project structure.
    short_id = request.thread_id[:8]
    isolated_sandbox = f"/tmp/autocoder_{short_id}"
    os.makedirs(isolated_sandbox, exist_ok=True)
    
    async def event_generator():
        # Instantiate a request-scoped agent initialized with dynamic paths
        mcp_path = os.path.join(os.path.dirname(__file__), "mcp_servers.json")
        agent = AutonomousAgent(mcp_path, extra_allowed_dirs=valid_dirs)
        await agent.mcp_manager.initialize() # Skip model flush for latency, just init proxy
        
        try:
            async for event in agent.astream_run(request.thread_id, request.task):
                yield event
        finally:
            await agent.cleanup()
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")

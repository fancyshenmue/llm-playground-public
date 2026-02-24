import os
import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse
import httpx
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource

# Configuration
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")
PHOENIX_COLLECTOR_URL = os.getenv("PHOENIX_COLLECTOR_URL", "http://phoenix:4317")
SERVICE_NAME = os.getenv("SERVICE_NAME", "ollama-proxy")

# Setup Telemetry
resource = Resource(attributes={
    "service.name": SERVICE_NAME
})

trace.set_tracer_provider(TracerProvider(resource=resource))
tracer = trace.get_tracer(__name__)

# Configure OTLP Exporter (sending to Phoenix)
otlp_exporter = OTLPSpanExporter(endpoint=PHOENIX_COLLECTOR_URL, insecure=True)
trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(otlp_exporter))

app = FastAPI()
client = httpx.AsyncClient(timeout=600.0)

@app.middleware("http")
async def trace_middleware(request: Request, call_next):
    # Only trace API calls
    if not request.url.path.startswith("/api/"):
        return await call_next(request)

    path = request.url.path
    method = request.method

    # Start a span for the request
    with tracer.start_as_current_span(f"{method} {path}") as span:
        span.set_attribute("http.method", method)
        span.set_attribute("http.url", str(request.url))

        # Capture body for model and prompt info (if feasible)
        # Note: Consuming body in middleware can be tricky, doing it in route handler is safer for large payloads
        # But for simplicity, we'll try to peek if possible or just rely on the route handler below.

        response = await call_next(request)

        span.set_attribute("http.status_code", response.status_code)
        return response

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy(path: str, request: Request):
    target_url = f"{OLLAMA_URL}/{path}"

    # Extract model and prompt info for tracing
    body_bytes = b""
    model_name = "unknown"
    prompt_snippet = ""

    if request.method == "POST":
        try:
            body_bytes = await request.body()
            import json
            body_json = json.loads(body_bytes)
            model_name = body_json.get("model", "unknown")
            prompt_snippet = body_json.get("prompt", "") or str(body_json.get("messages", ""))
        except Exception:
            pass

    # Enrich current span with LLM attributes if available
    span = trace.get_current_span()
    if span.is_recording():
        span.set_attribute("llm.model", model_name)
        span.set_attribute("llm.input", prompt_snippet[:1000]) # Cap length
        span.set_attribute("llm.system", "ollama")

    # Forward request
    # Use streaming to support streaming responses from Ollama
    async def forward_request():
        # Re-create request with same headers/body
        headers = dict(request.headers)
        headers.pop("host", None)
        headers.pop("content-length", None) # Let httpx handle this

        req = client.build_request(
            request.method,
            target_url,
            headers=headers,
            content=body_bytes
        )

        r = await client.send(req, stream=True)
        return r

    upstream_response = await forward_request()

    # Stream response back
    return StreamingResponse(
        upstream_response.aiter_bytes(),
        status_code=upstream_response.status_code,
        headers=upstream_response.headers,
        background=None
    )

if __name__ == "__main__":
    print(f"Starting Proxy forwarding to {OLLAMA_URL}, tracing to {PHOENIX_COLLECTOR_URL}")
    uvicorn.run(app, host="0.0.0.0", port=11435)

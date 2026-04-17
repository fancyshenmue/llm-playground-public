# Ollama Operations

## Start/Stop the Engine

```bash
pixi run ollama-daemon-install  # Generates LaunchAgent Plist
pixi run ollama-daemon-start    # Loads the daemon into Memory
pixi run ollama-daemon-stop     # Kills the process fully
```

## Model Management

```bash
pixi run ollama-daemon-logs     # Tails the output of the server
pixi run ollama-list            # Lists locally downloaded Ollama models
pixi run ollama-run-31b         # Pulls (if needed) and bootstraps Gemma 4 31B Dense
pixi run ollama-run-26b         # Pulls (if needed) and bootstraps Gemma 4 26B MoE A4B
```

## Performance Evaluation
We support three tiers of performance & intelligence evaluation:

**1. Raw Speed & Protocol Compliance (TTFT / TPS / JSON)**
```bash
pixi run py-benchmark           # Console UI measuring latency, token throughput, and rigid formatting
```

**2. Academic Logic Testing (EleutherAI lm-eval)**
```bash
pixi run ollama-academic-eval   # Automatically downloads HuggingFace GSM8K datasets and scores locally
```

**3. Enterprise RAG/Agent Observability (Arize Phoenix)**
```bash
# Tests JSON router strictness and RAG hallucination resistance via Python Runner
pixi run py-eval --models "gemma4:26b,gemma4:31b" -f documents/evaluation/eval_rag_agent.json
```

**4. LangChain Official Integration & Agent Evaluation**
```bash
# Tests official LangChain Tool Calling (bind_tools) and Needle-in-Haystack RAG via Ollama endpoint
pixi run python cmd/py/llm-utils/main.py eval-langchain --model gemma4:26b
```
*Note: The LangChain script spins up a temporary inline Phoenix server at `http://localhost:16006` for tracing. For permanent tracking in Phase 06, run `docker compose up -d` in `deployments/docker-compose/arizephoenix`.*

## Phase 06: Interactive LangChain Web Lab

The interactive test laboratory consists of a Python FastAPI backend connecting to the React (Vite+Tailwind v4) frontend. **Note**: The Ollama Daemon must be running.

**1. Start the API Backend**
```bash
# Runs Uvicorn on localhost:8000, serving LangGraph Agent operations
pixi run api-dev
```

**2. Start the React Frontend**
```bash
# Runs Vite dev server on localhost:5173 
pixi run lab-dev
```
Once both are running, open your browser to [http://localhost:5173](http://localhost:5173) to interact with Gemma 4 through the React Chat container!

## Expected Success State

When `ollama-daemon-logs` is running and an API call triggers the loading of a model (e.g. `gemma4:31b`), you should see output confirming **Apple Metal GPU** mapping:

```log
time=... level=INFO source=device.go msg="compute graph" device=Metal size="8.6 GiB"
time=... level=INFO source=server.go msg="llama runner started"
```

And `pixi run ollama-list` should explicitly show the loaded local models:

```
NAME          ID              SIZE     MODIFIED
gemma4:26b    ...             17 GB    ...
gemma4:31b    ...             19 GB    ...
```

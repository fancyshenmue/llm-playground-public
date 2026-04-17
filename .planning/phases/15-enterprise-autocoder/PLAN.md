# Phase 15 PLAN: Enterprise AutoCoder (Production UI Integration)

This checklist tracks the implementation steps for moving the Phase 09 Autonomous Coder logic out of the pure CLI environment into the Lab UI, using Postgres/pgvector as persistent state management via SSE.

## 0. Phase Standardization & Renaming

- [x] **0a:** Rename `frontend/langchain-lab` to `frontend/autocoder-lab` via terminal (`mv`).
- [x] **0b:** Update `pixi.toml` `lab-install` and `lab-dev` tasks to point to `--prefix frontend/autocoder-lab` instead of `langchain-lab`.
- [x] **0c:** Update references in `Makefile` (if any exist beyond `pixi run`) to use the new name.

## 1. Dynamic Model Configuration & Agent Backend

- [x] **1a:** Refactor `cmd/py/llm-utils/enterprise_api/autonomous_agent.py` to remove hardcoded model names (`gemma4:31b`, `gemma4:26b`, `qwen3.5:35b-a3b`). Load nested `autocoder` keys dynamically from `cmd/py/llm-utils/config.yaml`, abandoning `.env` files for architectural unity.
- [ ] **1b:** Add an `astream_run(self, thread_id: str, prompt: str)` method specifically built to `yield` Server-Sent Events (SSE) stringified JSON strings (e.g., `yield f"data: {{...}}\n\n"`), closely matching the logic of the `App.tsx` parsing requirements (status, node_update, finished). This replaces the Typer `Console()` print statements.
- [ ] **1c:** Inside `astream_run`, ensure the `AsyncPostgresSaver` handles the DB connection similarly to the CLI `run()` method, effectively fetching checkpoints dynamically from `deployments/docker-compose/langgraph/postgres-pgvector.yml`.
- [ ] **1d:** Ensure proper JSON payload formatting during `yield` (e.g., handling iteration counts, the Plan node output, the Code node AST/status, and Reflection outputs).

## 2. Exposing the API Endpoint (FastAPI)

- [x] **2a:** Modify `cmd/py/llm-utils/enterprise_api/main.py`. Import the `AutonomousAgent` from `autonomous_agent.py`.
- [x] **2b:** Initialize a global (or dependency-injected) instance of `AutonomousAgent(mcp_config_path="cmd/py/llm-utils/enterprise_api/mcp_servers.json")`. Add a startup hook to run its `await agent.initialize()` logic, flushing models and starting the MCP Proxy.
- [x] **2c:** Create `POST /api/autonomous/stream`. The endpoint will parse the prompt string, invoke the `agent.mcp_manager` to extract any absolute directory paths (`['/Users/...']`) into `allowed_dirs` (so the UI doesn't crash on permissions), and return a `StreamingResponse` wrapping `astream_run`.

## 3. React UI Lab Integration (Frontend)

- [x] **3a:** Edit `frontend/autocoder-lab/src/App.tsx`. In the `sendMessage` function block specifically checking `if (activeTab === 'Enterprise Auto-Coder')`, change the `fetch` endpoint from `http://localhost:8001/api/encode/stream` to `http://localhost:8001/api/autonomous/stream`.
- [x] **3b:** Extend the SSE parser (`if (data.type === ... )`) in `App.tsx` to handle the specific events the `AutonomousAgent` yields, such as rendering the architectural Plan in Markdown, the lint/test results, and the reflections.
- [x] **3c:** Expand the `App.tsx` styling for the Auto-Coder tab if necessary to visually distinguish between planning (Gemma-31B), coding (Gemma-26B), and testing/reflecting (Qwen-35B).

## 4. Verification Check

- [x] **4a:** Run `make langgraph-db-up` to ensure the pgvector image is live.
- [x] **4b:** Run `make langgraph-enterprise-api-dev` and `make autocoder-lab-dev` (renamed from langchain-lab-dev).
- [x] **4c:** Go to `localhost:5173`, navigate to `Enterprise Auto-Coder`, test a sandbox command like `"Write a Python calculator class in /tmp/test_project"`. Verify that the models stream back over SSE and that Phoenix tracks the traces correctly.
- [x] **4d:** Check-off Phase 15 completion in `.planning/ROADMAP.md` and `.planning/STATE.md`.

## 5. Security: Dynamic Thread-Isolated Sandboxing
- [x] **5a:** Remove universal `/tmp` hardcoded arg from `mcp_servers.json`.
- [x] **5b:** Refactor `main.py` stream API to dynamically allocate `os.makedirs(f"/tmp/autocoder_{request.thread_id}", exist_ok=True)` and inject it into the MCP filesystem arguments.
- [x] **5c:** Document dynamic UUID-based isolation in `architecture.md` and `operations.md`.

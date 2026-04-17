# Phase 15 Enhancement PLAN: SSE Observability & UI Polish

This checklist tracks all 6 post-audit improvements to Phase 15. No architectural changes — strictly data enrichment, cleanup, and documentation.

---

## 1. Enrich `astream_run` Plan Node SSE Payload

- [x] **1a:** In `cmd/py/llm-utils/enterprise_api/autonomous_agent.py`, modify the `plan_node` branch inside `astream_run()` (line ~128). Replace the hardcoded status message with a `node_update` event carrying `state.get("plan")` and `state.get("test_specs")` as payload fields.
- [x] **1b:** In `frontend/autocoder-lab/src/App.tsx`, extend the `node_update` handler (around line 76) to detect `data.node === 'plan_node'` and render the plan markdown content using `ReactMarkdown`.

## 2. Enrich `astream_run` Reflect Node SSE Payload

- [x] **2a:** In `autonomous_agent.py`, modify the `reflect_node` branch inside `astream_run()` (line ~134). Replace the generic status string with a `node_update` event carrying `state.get("reflection_strategy")` as a payload field.
- [x] **2b:** In `App.tsx`, extend the `node_update` handler to detect `data.node === 'reflect_node'` and render the reflection strategy in markdown.

## 3. Enrich `astream_run` Test Node SSE Payload

- [x] **3a:** In `autonomous_agent.py`, add `validation_status` field to the `test_node` SSE payload (line ~131-133).
- [x] **3b:** In `App.tsx`, replace the hardcoded 150-char truncation (`data.lint_errors.substring(0, 150)`) with a collapsible or scrollable full-text render. Use `data.validation_status` for styling logic instead of string comparison.

## 4. Clean Up `global_agent` Lifespan

- [x] **4a:** In `cmd/py/llm-utils/enterprise_api/main.py`, verify whether the legacy `/api/encode/stream` endpoint (line 66-72) depends on `global_agent`. If it uses `stream_coding_agent` from `graph.py` (not the agent), then the global_agent is orphaned.
- [x] **4b:** If confirmed orphaned: remove the `global_agent` variable, simplify the `lifespan` hook, and remove the unnecessary VRAM flush + MCP init at startup. If legacy endpoint needs it: add a clear comment explaining its purpose.

## 5. Fix `config.yaml` Documentation Gap

- [x] **5a:** In `documents/langgraph/operations.md`, add a prerequisite step in the "Configuration Model Targeting" section (line ~114) instructing users to `cp config.yaml.example config.yaml` before editing.

## 6. Update Frontend Branding

- [x] **6a:** In `frontend/autocoder-lab/src/App.tsx`, change header text `LangChain Test Lab` (line 142) to `AutoCoder Lab`.
- [x] **6b:** Change `Phase 06 Interactive Test Lab` (line 189) to `Enterprise AutoCoder Lab`.
- [x] **6c:** Update `Phase 06 Lab` nav link text (line 147) to `AutoCoder Lab` or similar.

## 7. Architectural Pivot: Direct Project Access

- [x] **7a:** Update `operations.md` to replace "Ephemeral Isolation Sandbox" with "Direct Project Access", outlining priority resolution and `no-op` detection features.
- [x] **7b:** Refactor CLI `main.py` path regex extraction to `r'(?:^|[\s`\'"])(/[^\s\)\(`\'"]+)'` and utilize `os.path.realpath`.
- [x] **7c:** Stop injecting `/tmp/autocoder_{uuid}` into isolated `extra_allowed_dirs` in `main.py` (CLI) so model tool descriptions stay cleanly mapped to the project, preventing infinite loops.
- [x] **7d:** Apply the same realpath resolution and `/tmp` exclusion modifications to `enterprise_api/main.py`.
- [x] **7e:** Update `architecture.md` to reflect the removal of forceful scratch-volume injection.

---

## Verification

- [x] **V1:** Run `pixi run lab-dev` — confirm the React frontend compiles without errors.
- [x] **V2:** Visually confirm header and branding text changes in browser.
- [x] **V3:** Review the SSE payload structure in `autonomous_agent.py` to confirm all node branches yield complete data.

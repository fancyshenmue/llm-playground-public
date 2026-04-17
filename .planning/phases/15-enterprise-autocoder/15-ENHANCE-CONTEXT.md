# Phase 15 Enhancement CONTEXT: SSE Observability & UI Polish

## Background

Phase 15 was verified as fully implemented and marked ✅ in ROADMAP. However, a post-completion code audit identified 6 enhancement opportunities, primarily around **SSE data density** and **UI consistency**.

## Technical Conclusions

### High-Impact (Observability)

1. **Plan Content Missing from SSE**: `astream_run()` yields a hardcoded placeholder `📋 Plan: Default Implementation` instead of forwarding the actual `state.get("plan")` markdown from the 31B Planner. The CLI `run()` method correctly renders this content. This is a data-payload gap, not an architectural issue.

2. **Reflection Strategy Missing from SSE**: Similarly, `reflect_node` in `astream_run()` yields a generic status string but discards `state.get("reflection_strategy")`. Users cannot observe the Qwen-35B evaluator's actual fix strategy in the UI.

### Medium-Impact (Data Precision)

3. **Test Node Payload Incomplete**: The `test_node` SSE event doesn't include the `validation_status` enum. The frontend relies on string comparison (`lint_errors !== 'PASS'`), which is fragile. The error output is also hard-truncated at 150 chars in the frontend.

### Low-Impact (Housekeeping)

4. **`global_agent` Lifespan Waste**: The FastAPI lifespan hook initializes a `global_agent` (including VRAM flush + MCP Proxy), but the `/api/autonomous/stream` endpoint never uses it. Need to clarify its purpose or remove it.

5. **`config.yaml` Documentation Gap**: `operations.md` instructs users to "ensure your config.yaml file contains..." but only `config.yaml.example` exists. The fallback code works, but the doc omits the copy step.

6. **Frontend Branding Stale**: `App.tsx` header still reads "LangChain Test Lab" and "Phase 06 Interactive Test Lab" after the Phase 0a rename to `autocoder-lab`.

## Architectural Pivot: Direct Project Access

Initially, Phase 15 introduced a "Thread-Isolated Sandbox Security" design, which actively injected an empty `/tmp/autocoder_{uuid}` directory into the MCP `extra_allowed_dirs`. However, real-world usage identified a fatal flaw: local models would frequently confuse this empty sandbox with the actual project root, causing infinite useless loops. 

As a result, an architectural pivot was initiated to enforce **Direct Project Access**:
- The agent relies directly on project paths specified via `--dir` or extracted from the prompt.
- The ephemeral sandbox `/tmp/autocoder_{id}` is still created for scratch usage but is **deliberately excluded** from the MCP filesystem allowed directories. 
- The path extraction regex has been enhanced to support paths in backticks, quotes, and whitespace (`r'(?:^|[\s`\'"])(/[^\s\)\(`\'"]+)'`), resolving symlinks via `os.path.realpath`.

## Scope

All 6 items (plus the Direct Project Access pivot) are approved for implementation. These updates ensure cleaner tool descriptions for local models and improve overall reliability.

# Phase 07: Enterprise Auto-Coding Agent Architecture

## Goal
Implement a closed-loop Agentic Auto-coding system utilizing LangGraph and PostgreSQL (`pgvector`), capable of cyclic autonomous programming mirroring Devin/Sweep.dev workflows.

## Workflow Layout
The LangGraph architecture will strictly follow this state machine loop:
`Context -> Plan -> Spec -> [ Code <-> Lint <-> Test <-> Reflect ] -> Eval -> Commit`

## Core Technologies
1. **State Persistence & RAG**: PostgreSQL + `pgvector` container.
2. **Framework**: `langgraph` via the new `enterprise_api` service.
3. **Model Infrastructure**: Local Ollama running `gemma4:31b` (Planning/Reflection) and `gemma4:26b` (Fast Coding).

## Sandbox Constraints
In order to validate the "Test" cycle accurately without executing unsafe code directly on the host, a Python Subprocess or native Linter sandbox must be provisioned for real-world simulation within the `[ Code <-> Lint <-> Test <-> Reflect ]` cycle.

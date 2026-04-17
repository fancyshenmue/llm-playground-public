# Phase 05: Professional Agent & RAG Observability (✅ Completed)

## Objective
Following hardware benchmarking, Phase 05 will deploy an uncompromising, dual-track evaluation suite against the locally running `gemma4:26b` and `gemma4:31b` models. Based on explicit user directives, we will test **"All"** dimensions: Academic generalized intelligence via EleutherAI's harness, and Enterprise workflow resilience via our local Arize Phoenix trace suite.

## Track A: Academic Baseline Intelligence (lm-evaluation-harness)
We will integrate EleutherAI's `lm-eval` suite directly into the `pixi` sandbox.
- **Goal:** Emulate the "Leaderboard" run using canonical datasets. 
- **Target Datasets:**
  - `gsm8k`: High-school logic and math.
  - `arc_challenge`: Complex science questioning.
- **Mapping:** `lm-eval` will hook directly into our local daemon via Ollama's OpenAI compatibility layer `http://localhost:11434/v1`.

## Track B: Enterprise RAG & Agent Stability (Arize Phoenix)
Academic tests do not measure if a model will break your software routing logic. We will leverage the built-in `runner.py` system.
- **Goal:** Measure obedience and context-blindness constraints.
- **Testing Scope:**
  1. **LangChain Tool Calling Accuracy**: Output exact JSON, failing if even one markdown tick exists.
  2. **Needle-In-Haystack RAG Vulnerability**: Test for contextual hallucinations inside massive context bounds.
- **Observability:** Logs will pipe into the local Arize telemetry URL (`http://localhost:16006`).

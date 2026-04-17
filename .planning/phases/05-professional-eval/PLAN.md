# Phase 05: Professional Dual-Track Evaluation Plan

## Track A: Academic Evaluation (EleutherAI)
- [x] 1. Inject `lm-eval` into Pixi Python ecosystem.
  - Modify `pixi.toml` dependencies to include `lm-eval`.
- [x] 2. Establish `lm-eval` shell task in `pixi.toml`
  - Register task `ollama-academic-eval` pointing to the `lm_eval` CLI interacting strictly over `--model local-chat-completions` targeting Ollama's API.
- [ ] 3. Run localized Academic Benchmarks
  - Perform a sample test on `gsm8k` against the unified memory matrix.

## Track B: RAG & Agent Robustness (Arize Phoenix & JSON Constraints)
- [x] 4. Define Agent Test JSON Ledger
  - Create mapping file: `documents/evaluation/eval_rag_agent.json` containing extreme JSON and Haystack tasks.
- [x] 5. Wire the Evaluator Harness
  - Execute `pixi run py-eval` using the new ledger file. Ensure `runner.py` properly triggers scoring.
- [x] 6. Complete Metric Publishing
  - Output Academic scores and Workflow survival rates to `documents/ollama/benchmark.md`.

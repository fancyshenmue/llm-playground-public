# Phase 04: Performance Evaluation Execution Plan

- [x] 1. Create `cmd/py/llm-utils/commands/eval/benchmark.py` testing harness
  - Integrate `ollama` python client to query running models.
  - Implement concurrent or sequential testing for `gemma4:31b` and `gemma4:26b`.
  - Capture precise `eval_duration`, `eval_count` (Tokens/s), and `load_duration` metrics directly from the Ollama API response object.
- [x] 2. Implement the specialized prompt test suite
  - Add RAG Context test prompt (Needle in Haystack context extraction).
  - Add LangChain Agent test prompt (Strict JSON output validation).
  - Add Logic/Coding constraint prompt.
- [x] 3. Present Results using `rich`
  - Wire output to display side-by-side split panels or cleanly formatted tables detailing pure Speed Data alongside generated texts for visual evaluation.
- [x] 4. Wire up to `pixi.toml`
  - Register task: `py-benchmark = "python cmd/py/llm-utils/main.py benchmark"`
- [ ] 5. Run the evaluation and declare the ultimate test results.

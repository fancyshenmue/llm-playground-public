# Phase 04: Performance Evaluation (31B vs 26B)

## Objective
The primary goal of this phase is to establish a clear, empirical framework to test and compare the capabilities of **Gemma 4 31B (Dense)** against **Gemma 4 26B (Mixture of Experts - MoE)** running locally on Apple Silicon (M2 Max) via the Ollama endpoint (`0.0.0.0:11434`).

## Background Context
Since we fully decoupled from `vllm-mlx` and moved to `ollama`, we now have both models loaded natively. The user needs to verify the tradeoff between a traditional dense model (31B) where every parameter is active per token, versus an MoE model (26B) which only activates ~9B parameters per token.

### Hypothesis
- **31B Dense**: Will consume significantly more active memory bandwidth and thus may result in lower Tokens-Per-Second (TPS). However, it might exhibit slightly more robust generalized logic.
- **26B MoE**: Should generate text faster per token and run cooler.

## Evaluation Strategy
To measure this without needing heavy datasets like MMLU or HumanEval, we will construct a bespoke Python testing harness.

1. **Quantitative Matrix (Speed)**
   - Measure **Tokens Per Second (TPS)**.
   - Measure **Time-to-First-Token (TTFT)**.

2. **Qualitative Matrix (Logic, RAG & LangChain Readiness)**
   Since the target downstream application involves LangChain and RAGFlow, the qualitative tests must push the models exactly where agents break:
   - **Needle in a Haystack (RAG Readiness)**: Inject a large block of dense text containing a single hidden, contradictory fact, and ask the model to synthesize an answer strictly based on the provided context (testing context adherence vs learned bias).
   - **Strict Formatting (LangChain/Agent Readiness)**: Demand the output strictly in a deeply nested JSON schema representing a function call or entity extraction with absolutely no markdown wrapping ````json... ```` (testing format compliance).
   - **Algorithmic Logic**: A hard coding boundaries test to see if 31B's density outperforms 26B's MoE routing.

## Implementation Architecture
We will write a new CLI command to the existing `cmd/py/llm-utils/main.py` Python suite leveraging the official Python `ollama` SDK (which Pixi already provides).
- Task: `pixi run py-benchmark`
- Invokes: `main.py benchmark --models "gemma4:31b,gemma4:26b"`
- Render: A `rich` terminal output table displaying latency, TPS, and accuracy logs metrics cleanly.

# Objective Evaluation Guide

To properly assess your fine-tuned model's quality, you should move beyond "vibes" and use measurable metrics. Here are the three industry-standard ways to evaluate a Coder model.

## 1. Unit Test Pass Rate (Pass@k)
The gold standard for coding models. It involves asking the model to solve a problem and then **actually running** unit tests against the output.

*   **Primary Tool**: [HumanEval](https://github.com/openai/human-eval) or [MultiPL-E](https://github.com/nuprl/MultiPL-E) (for multi-language support like Go/TS).
*   **Metric**: `Pass@1` (Does it get it right on the first try?).
*   **How to do it**:
    - Use the `bigcode-evaluation-harness`.
    - It will prompt your model with 160+ coding problems and run them in a sandboxed environment.

## 2. LLM-as-a-Judge (using Arize Phoenix)
Since you already have Phoenix set up, this is the most integrated way. You use a "Teacher" model (like GPT-4o or Claude 3.5) to grade your "Student" model (Qwen-14B-ft).

*   **Workflow**:
    1.  Run a set of 50-100 test prompts via your `local-ollama` MCP.
    2.  In **Arize Phoenix**, use the **Evaluators** feature.
    3.  Define a "Code Correctness" or "Code Style" evaluator.
    4.  The Teacher model will look at the Student's output and give it a score from 1-5 or a Pass/Fail.
*   **Benefit**: You get a nice dashboard in Phoenix showing exactly where the 14B model fails compared to the 32B or the base model.

## 3. Loss & Perplexity (Intrinsic)
You already see the `loss` during Unsloth training.
*   **Validation Loss**: The most critical metric during training. If the training loss goes down but validation loss starts going up, you are **overfitting**.
*   **Perplexity**: A measure of how "surprised" the model is by the test data. Lower is better.

## 4. Practical "Sanity Test" Suite
Create a local `eval_set.json` containing 10-20 complex tasks relevant to your work:
- 5 Go concurrency tasks.
- 5 Gin-gonic API tasks.
- 5 TypeScript React/Node tasks.
- 5 Python Data processing tasks.

**Execution Flow**:
1.  Run the suite against the **Base Model**.
2.  Run the suite against **14b-ft-v1**.
3.  Compare results. If the v1 model starts hallucinating imports or missing `sync.Mutex` where the base model didn't, the fine-tuning needs adjustment.

## Recommended Tooling
- **[BigCode Evaluation Harness](https://github.com/bigcode-project/bigcode-evaluation-harness)**: The most comprehensive tool for evaluating code LLMs across multiple languages.
- **[Arize Phoenix Evals](https://docs.arize.com/phoenix/evaluation/llm-evals)**: Best for non-execution based qualitative scoring.

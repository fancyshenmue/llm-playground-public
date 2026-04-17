# Evaluation Output Strategy for Unsloth Fine-Tuned Models

This document outlines the objective evaluation framework for the fine-tuned Ollama models within this project. The goal is to ensure high-quality code generation and prevent regression.

## 1. Hybrid Evaluation Architecture

To ensure the highest reliability, our project adopts a **Hybrid Evaluation Strategy**. Instead of relying on a single metric, we triangulate model quality using three independent pillars:

| Pillar | Method | Base on | Role | Weight |
| :--- | :--- | :--- | :--- | :--- |
| **Objective** | **Keyword Heuristics** | `eval_set.json` rules | Syntax/dependency check. | 20% |
| **Subjective** | **LLM-as-a-Judge** | Judge Model Logic | Evaluating style and intent. | 40% |
| **Functional** | **Functional Pass** | Runtime Execution | Hard verification of logic. | 40% |

### 1.1 Technical Implementation
The system utilizes a language-specific execution engine inside `runner.py`:
1.  **Isolation**: Code is written to a `tempfile` with the correct extension (`.py`, `.go`).
2.  **Augmentation**: The `verification_script` defined in `eval_set.json` is appended to the model output.
3.  **Validation**: A subprocess runs the `verification_cmd`. A return code of `0` indicates a Functional Pass.

### 1.2 Scoring Formula
$Quality Score = (KW \times 0.2) + (Judge \times 0.4) + (Pass \times 0.4)$
*Note: If no verification script is provided, weights are redistributed to Keywords and Judge scores.*

## 2. Advanced Evaluation Features

### 2.1 A/B Comparison
The system supports simultaneous evaluation of multiple models. This allows for direct side-by-side comparison between the base model and fine-tuned versions within Arize Phoenix.

### 2.2 Automated Scoring
Responses are automatically evaluated for keyword consistency (objective) and can be graded by a judge model (subjective) in a single run.

## 3. Usage Guide

The evaluation system is integrated into `pixi`.

### 3.1 Standard Evaluation
Runs the default fine-tuned model against the expanded test set:
```bash
pixi run py-eval
```

### 3.2 A/B Testing (Side-by-Side)
Specify multiple models to compare:
```bash
pixi run py-eval --models "llama3.2, qwen2.5-coder-14b-ft:latest"
```

### 3.3 LLM-as-a-Judge
Enable qualitative scoring by specifying a judge model:
```bash
pixi run py-eval -m qwen2.5-coder-14b-ft:latest --judge qwen2.5-coder:32b
```

### 3.4 Arize Phoenix Telemetry (Agent & RAG Tracing)
During Track B professional evaluation, or when building standalone RAG / LangChain Agent scripts, you can hook into the local Arize Phoenix visualizer to intercept internal logic:
1. **Instrument Codebase**: Insert this trace layer at the head of your LangChain script:
   ```python
   from phoenix.trace.langchain import LangChainInstrumentor
   LangChainInstrumentor().instrument()
   ```
2. **Visualize DAG**: Open `http://localhost:16006` to dissect reasoning chains.
3. **Engine Port Note**: When testing natively via `runner.py` without the heavy Phoenix API proxy activated, ensure `OLLAMA_PROXY_URL` is set to `http://localhost:11434`.

## 4. Domain-Specific "Sanity Tests"

We maintain a curated `eval_set.json` (15+ tasks) focusing on our stack's critical areas:
*   **Go**: Concurrency (`sync.WaitGroup`), Error handling (`errors.Is`), Context.
*   **Gin**: Middleware, Authentication, Binding, Streaming.
*   **TypeScript**: React Hooks, Generics, Union Types, Context API.
*   **Python**: Decorators, Regex, Pandas manipulations.

## 5. Workflow Architecture

```mermaid
graph LR
## 6. Hyperparameter Tuning

The Unsloth finetuning environment is now primarily driven by a structured YAML configuration located at `deployments/docker-compose/unsloth/config.yaml`.

### 6.1 Configuration Hierarchy
Settings follow a tiered approach to balance stability and flexibility:
1.  **Environment Variables (Primary Override)**: If a variable like `LEARNING_RATE` is set in the `.env` or system, it overrides everything else. Useful for quick one-off experiments.
2.  **config.yaml (Default source)**: The main source of truth for structured parameters.
3.  **Code Defaults**: Hardcoded safe defaults within `finetune.py`.

### 6.2 Key Parameters in config.yaml

| Category | Parameter | Description |
| :--- | :--- | :--- |
| **Model** | `name` | HuggingFace path (e.g., `Qwen/Qwen2.5-Coder-14B-Instruct`) |
| **Training** | `learning_rate`| Steps size for the optimizer (Default: `2e-4`) |
| **Training** | `lora_r` | Rank of the LoRA adapters (Higher = more specific, more VRAM) |
| **Training** | `max_steps` | Total training iterations to perform. |
| **Dataset** | `languages` | List of target languages (Go, Python, etc.). |
| **Dataset** | `samples_per_lang`| Diversity per language (Default: `10000`) |

### 6.3 Optimization Strategy
To close the gap between the 14B-FT and 32B models, use the `config.yaml` to:
1.  **Iterate on `max_steps`**: Increase to `5000+` for deeper pattern recognition.
2.  **Fine-tune `learning_rate`**: Drop to `1e-4` or `5e-5` to avoid overshooting local minima.
3.  **LoRA Rank**: Experiment with `r: 64` or `r: 128` if GPU memory allows.

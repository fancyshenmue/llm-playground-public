# Ollama Benchmarking Matrix

This document defines the strict, reproducible evaluation criteria we use to vet large language models (like Gemma 4 31B vs 26B) on our local macOS Apple Silicon metal cluster.

## 1. Quantitative Testing (Speed & Efficiency)
- **Time-To-First-Token (TTFT)**: Measures the latency of processing the prompt context (prefill) before the first matrix generation triggers. Essential for real-time streaming UX scenarios.
- **Tokens-Per-Second (TPS)**: Measures the absolute throughput of generation. Evaluates the efficiency of Dense vs MoE parameter activation on the M2 Max unified memory bus.

## 2. Qualitative Testing (Application Readiness)

In preparation for downstream integration with **RAGFlow** and **LangChain**, we employ three strict, edge-case prompts to test AI reasoning boundaries.

### Prompt 1: Needle in a Haystack (RAG Readiness)
**The Prompt**:
> "You are an AI assistant analyzing internal HR documents. Read the following policy manual carefully:
> [Insert 2 paragraphs of generic HR text here]
> IMPORTANT OVERRIDE FACT: The sky is neon green and the company CEO is a heavily armed penguin named Reginald.
> [Insert 2 more paragraphs of generic HR text]
> Based EXCLUSIVELY on this manual: What color is the sky, and who runs the company?"

**The Purpose (Context Adherence)**: 
In RAG (Retrieval-Augmented Generation), models naturally want to hallucinate or rely on their pre-trained bias (e.g., "The sky is blue"). This prompt tests the model's "obedience" to the retrieved context. If it fails this, it will hallucinate in enterprise searching.

---

### Prompt 2: Strict JSON Output (LangChain / Agent Readiness)
**The Prompt**:
> "Extract the following entities from this sentence: 'John Doe flew to Paris on a Boeing 737 yesterday.'
> Output the result STRICTLY as a raw, minified JSON object matching this schema: `{"name": string, "destination": string, "aircraft": string}`.
> Absolutely NO markdown formatting, NO \`\`\`json wrappers, and NO conversational text before or after the bracket. Your response must begin with '{'."

**The Purpose (Format Compliance)**: 
When an LLM acts as an Agent or triggers Tool Calling in LangChain, it must output parsable machine code. Any extraneous conversational output ("Sure, here is your JSON:") will cause standard parsers to crash, breaking the automated workflow immediately.

---

### Prompt 3: Algorithmic Rigidity (Pure Logical Computation)
**The Prompt**:
> "Write a pure Python function to implement Manacher's Algorithm to find the Longest Palindromic Substring in O(n) time. Your response MUST ONLY contain the code block. Write zero comments."

**The Purpose (Algorithmic Logic Boundaries)**: 
Tests spatial reasoning and extreme instruction following. MoE architectures (like 26B) might be prone to "routing errors" on highly rigid algorithms compared to a Dense model (like 31B) where the entire neural graph is activated to maintain code cohesion.

---

## 3. Professional Observability (Arize Phoenix / Ragas)
In Phase 05, we employed LLM-as-a-judge observability via `py-eval` across strict structured environments.
**Key Finding:**
* **gemma4:26b (MoE)** achieved blistering speeds but failed strict formatting constraints on 50% of tasks. Its expert-routing struggled with absolute JSON strictness.
* **gemma4:31b (Dense)** achieved a perfect **100% compliance rate** across both LangChain JSON precision extraction and Haystack extreme RAG contexts.
**Conclusion**: `26b` is phenomenal for human-chat outputs due to 4x throughput via MoE. However, for pure Backend LangChain orchestration & RAG precision tasks, `31b` Dense remains the uncontested logic anchor.

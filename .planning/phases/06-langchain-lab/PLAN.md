# Phase 06: Real Langchain Test Lab

## Objective
Transition from isolated LangChain functional tests (Phase 05) to a comprehensive, interactive, and stateful testing environment. Build a "Real LangChain Test Lab" featuring an advanced multi-agent workflow, real-world tools, advanced RAG integration, and a dedicated UI.

## Components

### 1. Advanced Agentic Workflows
- Integrate **LangGraph** to manage multi-agent state and cycles.
- Implement memory handling for tracking continuous conversational context across multiple turns using Gemma 4.

### 2. Real-world Tools Box
- Expand beyond mock functions to operational tools.
- Implement tools for External APIs (search, data lookup) and local file/system operations.
- Test agent decision-making when selecting from a diverse toolset.

### 3. Advanced RAG 
- Incorporate a formal Vector Store (e.g. ChromaDB or Qdrant).
- Implement dynamic retrieval patterns (Hybrid search, Re-ranking) and semantic routing.

### 4. Interactive Test UI (Web Lab)
- Build a polished Web UI under `frontend/langchain-lab/`.
- Technology Stack: **Vite + React (TypeScript) + TailwindCSS v4**.
- UI Design: Inspired by the TailwindCSS documentation portal (Dark mode, left sidebar navigation, top header, central interactive panels).
- Backend Bridge: A new **FastAPI** service (`cmd/py/llm-utils/lab_api`) to execute model operations and stream SSE back to the React UI.

## Success Criteria
- [ ] The `frontend/langchain-lab` project is initialized and styled to specifications.
- [ ] The `lab_api` FastAPI server successfully handles LangChain requests and communicates with the frontend.
- [ ] Users can trigger and observe a LangGraph agent operation directly from the Web UI, with clear insights into tool usage and execution logs.

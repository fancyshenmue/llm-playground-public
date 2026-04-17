# Ollama Architecture
## Ecosystem Isolation
We implement Ollama using the pure Conda-forge binary mapped strictly into our `.pixi` sandbox, completely avoiding `brew` system pollution.

## Component Network
```mermaid
graph TD
    A[Ollama Daemon<br>Port: 11434] --> B[.pixi/envs/default/bin/ollama]
    A --> C[~/.llm-playground/ollama-models]
    A --> D[~/.llm-playground/logs/ollama.log]
```

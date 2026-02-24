# Ollama Deployment and Model Management Guide

This guide provides instructions on how to use the modularized Ollama service, manage Modelfiles, and transform fine-tuned models into Ollama format.

## 1. Modular Deployment Overview

The Ollama service is isolated into its own Docker Compose environment to allow independent management and better resource allocation.

**Directory:** `deployments/docker-compose/ollama/`

### Running the Service
To start the Ollama service:
```bash
cd deployments/docker-compose/ollama
docker compose up -d
```

## 2. Modelfile Management

Modelfiles are version-controlled within the project to ensure reproducible model deployments.

**Directory:** `deployments/docker-compose/ollama/modelfiles/`
**Container Mount Point:** `/modelfiles/` (Read-Only)

### Creating a New Model
When you have a merged model in `/models` (mapped from your local output directory), use the following command to create the Ollama model:

```bash
docker compose exec ollama ollama create <model_name> -f /modelfiles/<your_modelfile>.modelfile
```

Example for Qwen 1.5B:
```bash
docker compose exec ollama ollama create qwen-1.5b-merged -f /modelfiles/qwen-1.5b-merged.modelfile
```

## 3. Transforming Models (Merged -> Ollama)

After fine-tuning and merging your model using Axolotl, follow these steps to use it in Ollama:

1.  **Merge weights**: Use the `code-merge-14b.yaml` (or equivalent) config to produce a full-precision merged model.
2.  **Verify path**: Ensure the merged model is in the output directory linked to the Ollama container (default: `/models`).
3.  **Prepare Modelfile**: Check `deployments/docker-compose/ollama/modelfiles/` and update the `FROM` path to point correctly inside the container (e.g., `FROM /models/qwen-14b-merged`).
4.  **Run `ollama create`**: Execute the command mentioned in Section 2.

## 4. Usage in Other Services

Services in the `lab` environment (Open WebUI, AnythingLLM) are configured to connect to this standalone Ollama instance via the shared `llm-network`.

- **Internal URL:** `http://ollama:11434`
- **External URL:** `http://localhost:11434`

## 5. Exporting Models

For detailed instructions on how to package and move these models to another machine, please refer to the [Model Export and Porting Guide](./model-export-and-porting.md).

## 6. Containerized GGUF Conversion (via llama.cpp)

If you need to convert your merged Safetensors model into a single **GGUF** file (for macOS or distribution), we have included a `llama-cpp` service.

### How to Convert
1.  **Start the conversion container**:
    ```bash
    docker compose up -d llama-cpp
    ```
2.  **Run the conversion script**:
    ```bash
    docker compose exec llama-cpp python3 /app/convert_hf_to_gguf.py /models/qwen-1.5b-merged/merged --outfile /models/qwen-1.5b-merged.gguf
    ```
    *   `/models/qwen-1.5b-merged/merged` is the actual model path containing `config.json`.
    *   The output `.gguf` will be created in your shared `/models` directory.

### Why use this?
- **No local dependencies**: You don't need to install Python, llama.cpp, or complex libraries on your host machine.
- **Consistent environment**: The version of conversion scripts is pinned to the official llama.cpp image.

---

## 7. Complete Export Example (GGUF for Mac/Other PC)

Here is the end-to-end workflow to export your fine-tuned model:

1.  **Convert to GGUF**:
    ```bash
    docker compose exec llama-cpp python3 /app/convert_hf_to_gguf.py /models/qwen-1.5b-merged/merged --outfile /models/qwen-1.5b-merged.gguf
    ```
2.  **Copy to Target PC**:
    - The file will be at `F:/Docker/Mount/llm-playground/output/qwen-1.5b-merged.gguf`.
    - Copy this single file to your Mac.
3.  **Deploy on Mac (Native Ollama)**:
    - Create a file named `qwen.modelfile` on your Mac:
      ```dockerfile
      FROM ./qwen-1.5b-merged.gguf
      ```
    - Run: `ollama create my-qwen -f qwen.modelfile`

---

## 8. Troubleshooting: Qwen Tokenizer Errors

If you see an error like `AttributeError: 'list' object has no attribute 'keys'` when converting Qwen models, it is often caused by a formatting conflict in `tokenizer_config.json` regarding special tokens.

**Fix:**
Temporarily remove the `extra_special_tokens` key from `tokenizer_config.json` before converting:

```bash
docker compose exec llama-cpp python3 -c 'import json; p="/models/your-model/merged/tokenizer_config.json"; d=json.load(open(p)); d.pop("extra_special_tokens", None); json.dump(d, open(p, "w"), indent=2)'
```

After removing this key, run the conversion command again. The script will use the base vocabulary correctly, and the model will export successfully.

---

## 9. Importing GGUF Models into Ollama

Once you have a `.gguf` file, you can import it into Ollama using a Modelfile.

### 1. Create a Modelfile
Create a file (e.g., `my-model.modelfile`) and point it to your GGUF path:
```dockerfile
FROM /path/to/your-model.gguf
```

### 2. Register the Model
Run the `ollama create` command:
```bash
docker compose exec ollama ollama create my-model-name -f /modelfiles/my-model.modelfile
```

### 3. Run and Test
```bash
docker compose exec ollama ollama run my-model-name
```

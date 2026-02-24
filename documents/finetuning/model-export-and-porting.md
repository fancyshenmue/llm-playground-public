# Model Export and Porting Guide

This guide explains how to export your fine-tuned models from this environment and import them into Ollama on other machines.

## 1. Organizing Your Modelfiles

We have moved the Modelfiles to a dedicated directory within the project to keep them organized and version-controlled.

**Directory:** `deployments/docker-compose/ollama/modelfiles/`

When you create a new model in Ollama, you should reference the merged model path.

## 2. Exporting the Model to Other PCs

To move your model to another machine, follow these steps:

### Option A: Transferring the Merged Weights (Safetensors)

If the target machine is also running Ollama or a similar environment and you want to use the Modelfile approach:

1.  **Locate the Merged Model**: Find the directory containing your merged model (e.g., `/workspace/output/qwen-1.5b-merged`).
2.  **Compress the Directory**: Use `tar` or `zip` to package the entire folder.
    ```bash
    tar -czvf qwen-1.5b-merged.tar.gz /path/to/your/merged/model
    ```
3.  **Transfer the File**: Move the compressed file to the target PC using a USB drive, cloud storage, or `scp`.
4.  **Extract and Create**:
    - On the target PC, extract the file.
    - Create a Modelfile that points to the extracted path.
    - Run `ollama create <model_name> -f Modelfile`.

### Method B: Moving the Dir (Modelfile Approach)
This is what you are doing now: directly copy the `merged` folder. Point a Modelfile to it. It's simple and preserves precision.

---

### Method C: Exporting as a Single GGUF File (Optimized for Ollama)

If you want a more portable, single-file format:

1.  **Preparation (Mandatory for Qwen)**:
    Axolotl-merged Qwen models have a formatting bug in `tokenizer_config.json`. Run this fix inside your `ollama` deployment folder:
    ```bash
    docker compose exec llama-cpp python3 -c 'import json; p="/models/your-model/merged/tokenizer_config.json"; d=json.load(open(p)); d.pop("extra_special_tokens", None); json.dump(d, open(p, "w"), indent=2)'
    ```
2.  **Run the conversion script**:
    ```bash
    docker compose exec llama-cpp python3 /app/convert_hf_to_gguf.py /models/qwen-1.5b-merged/merged --outfile /models/qwen-1.5b-merged.gguf
    ```
    *   `/models/qwen-1.5b-merged/merged` is the actual model path containing `config.json`.
    *   The output `.gguf` will be created in your shared `/models` directory.

> [!IMPORTANT]
> **Qwen Compatibility**: You must run the `extra_special_tokens` removal script (see Section 8) before converting any Qwen model merged by Axolotl.

### 3. Importing your Model into Ollama

Once the `.gguf` file is on your target machine, follow these steps to import it:

1.  **Create a Modelfile**: In the same directory as your `.gguf` file, create a file named `Modelfile`:
    ```dockerfile
    # Modelfile
    FROM ./your-model.gguf
    ```
2.  **Run the Create Command**:
    ```bash
    ollama create my-custom-model -f Modelfile
    ```
3.  **Verify**: Run `ollama run my-custom-model` to start chatting!

## 3. Special Case: macOS (Apple Silicon M1/M2/M3)

If your "other PC" is a Mac, pay close attention to these two points:

### Docker on macOS Limitation
> [!WARNING]
> **Docker on macOS cannot access the GPU (Metal)** for LLM acceleration.
> If you run Ollama inside Docker on a Mac, it will run on the **CPU only**, which is extremely slow.

### The Solution: Native Execution + GGUF
To get GPU speed on a Mac, you should:
1.  **Run Ollama Natively**: Download the macOS version of Ollama from [ollama.com](https://ollama.com). It uses Apple's Metal API for incredible speed.
2.  **Use GGUF**: While native Ollama can use the Modelfile approach, **GGUF** is the native language of the Apple Silicon inference engines.
3.  **Why you need llama.cpp**: This is why you need `llama.cpp` on your current (Linux/Windows) PC—to convert your merged Safetensors into a single `.gguf` file before sending it to the Mac.

## 4. Summary: Which one should I choose?

| Target System | Recommended Method | Why? |
| :--- | :--- | :--- |
| **High-end Linux/Win PC** | **Method B (Safetensors)** | Simple, full precision, GPU works in Docker. |
| **Mac (Apple Silicon)** | **GGUF (via llama.cpp)** | Native Ollama + Metal acceleration requires GGUF for best performance. |
| **Edge Devices / Low RAM** | **GGUF (Quantized)** | GGUF allows "Quantization" (compression) to fit models into small RAM. |

## 5. Recommended Project Structure

We recommend keeping your Ollama deployment separate from other services (like Open WebUI or AnythingLLM) to make it easier to manage model updates and exports.

- `deployments/docker-compose/ollama`: Dedicated Ollama deployment.
- `deployments/docker-compose/ollama/modelfiles`: All your custom Modelfiles.
- `documents/finetuning/model-export-and-porting.md`: This guide.

## 4. Summary of Improvements

- **Modularity**: Ollama is now a standalone service.
- **Organization**: Modelfiles are tracked in the project repository.
- **Portability**: You have a clear path for moving models between environments.

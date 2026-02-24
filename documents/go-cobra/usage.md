# llm-utils Usage Guide

This guide describes how to use the `llm-utils` CLI for LLM and image generation tasks.

## 1. Installation & Environment

The project is managed by Pixi. To ensure all Go dependencies and environments are set up correctly:

```bash
pixi install
```

### Building the CLI
To build the binary into `bin/llm-utils`:
```bash
pixi run build-llm
# or for a static build to ~/bin/llm-utils:
pixi run build-llm-utils
```

---

## 2. Command Reference: `data-gen`

The `data-gen` command (aliased as `llm-gen` in Pixi) is used to generate datasets of images and optional captions using Ollama (for prompt expansion) and Forge (for image generation).

### Basic Command
```bash
# Using the binary directly
./bin/llm-utils data-gen --topic "beauty girl" --total 3

# Or via Pixi task
pixi run llm-gen --topic "beauty girl" --total 3
```

### Flags

| Flag           | Shorthand | Default         | Description                                      |
| :------------- | :-------- | :-------------- | :----------------------------------------------- |
| `--topic`      | `-T`      | `"beauty girl"` | The main subject for generation.                 |
| `--total`      | `-n`      | `30`            | Number of images to generate.                    |
| `--lora`       | `-L`      | `""`            | Specify a LoRA model (supports autocomplete).    |
| `--weight`     | `-W`      | `1.0`           | Set the strength of the LoRA model (0.1 to 1.0). |
| `--prompt`     | `-p`      | `""`            | Manual base prompt (skips Ollama extension).     |
| `--trigger`    | `-g`      | `""`            | Override the default LoRA trigger word.          |
| `--timestamp`  | none      | `false`         | Include Unix timestamp in filenames.             |
| `--no-caption` | `-C`      | `false`         | Skip generating accompanying `.txt` files.       |
| `--output`     | `-o`      | `./dataset/...` | Destination directory for results.               |

### Use Case Examples

#### Case A: Generating a Training Dataset (with Captions)
When generating data for training (like WD14), you want both images and captions:
```bash
./bin/llm-utils data-gen --topic "cyberpunk city" --total 20
```

#### Case B: Batch Generation with Trained Model (No Captions)
When using a specific LoRA version (v9) to generate subjects without needing caption files:
```bash
./bin/llm-utils data-gen --lora FancyStyle_v1-000009.safetensors --weight 0.8 --no-caption --total 5
```

#### Case C: Custom Output Directory
Organize your research by specifying a custom output path:
```bash
./bin/llm-utils data-gen --topic "vintage car" --output "./dataset/research/2026_cars" --total 10
```

#### Case D: Testing LoRA Weights
Quickly test how different weights affect the style (requires running commands sequentially):
```bash
./bin/llm-utils data-gen --lora FancyStyle_v1-000009.safetensors --weight 0.5 --total 1 --output ./output/test_w05
./bin/llm-utils data-gen --lora FancyStyle_v1-000009.safetensors --weight 0.8 --total 1 --output ./output/test_w08
./bin/llm-utils data-gen --lora FancyStyle_v1-000009.safetensors --weight 1.0 --total 1 --output ./output/test_w10
```

#### Case E: Manual Prompt (Skip Ollama)
If you want to use a specific prompt and bypass the Ollama AI expansion:
```bash
./bin/llm-utils data-gen --prompt "A hyper-realistic futuristic car on Mars" --lora FancyStyle_v1-000009.safetensors --total 1
```

### Dynamic Trigger Words
The tool automatically detects the correct trigger word based on your LoRA filename:
- **BeautyGirlStyle**: prepends `BeautyGirlStyle` to the prompt.
- **FancyStyle** (or any other): prepends `FancyStyle` to the prompt.

---

## 3. Other Utility Commands

### Chat with Ollama
Verify your connection and model performance:
```bash
./bin/llm-utils chat --model llama3.2-vision
# Or via Pixi
pixi run llm-chat --model llama3.2-vision
```
*(Inside the chat, you can type your prompt to see the model's response)*

### List Available Models
Check which models are currently served by Ollama:
```bash
./bin/llm-utils models
```

### Batch Tagging (WD14 Tagger)
Automatically generate .txt tags for a directory of images using the Forge Tagger API:
```bash
./bin/llm-utils tag --path ./dataset/your_folder --threshold 0.4
```

### Analyze an Image
Use a vision model to describe an existing image:
```bash
./bin/llm-utils analyze --image ./dataset/beauty_girl_001.png
# Or via Pixi
pixi run llm-analyze --image ./dataset/beauty_girl_001.png
```

### Start Training (Kohya_ss)
Trigger a training session using a JSON configuration file (Gradio export):
```bash
./bin/llm-utils train --config ./deployments/training_configs/my_lora.json
```

---

## 4. Best Practice: The Model Self-Evolution Loop

This is the recommended workflow to train a high-quality LoRA by iteratively refining your data.

### Step 1: Initial Generation (Base Data)
Generate your first batch of training data.
```bash
# Generate 30 images with a basic topic
./bin/llm-utils data-gen --topic "beauty girl" --total 30 --output ./dataset/v1_base
```

### Step 2: Automated Tagging (WD14)
Prepare the `.txt` labels for training.
```bash
./bin/llm-utils tag --path ./dataset/v1_base --threshold 0.35
```

### Step 3: Training & Feedback (The Loop)
1. **Train your LoRA (v1)** using the Go CLI:
   ```bash
   ./bin/llm-utils train --config ./deployments/training_configs/my_lora.json
   ```
2. Use the new LoRA to generate a test sample:
   ```bash
   ./bin/llm-utils data-gen --lora your_lora_v1.safetensors --total 1 --output ./output/test_v1
   ```
3. **Crucial Step**: Analyze the output to find optimized prompt tokens:
   ```bash
   ./bin/llm-utils analyze --image ./output/test_v1/beauty_girl_001.png
   ```

### Step 4: Evolution (Refined Data)
Use the keywords found in the analysis (e.g., "red boxing gloves", "ponytail") to generate an even better dataset for v2:
```bash
./bin/llm-utils data-gen --prompt "BeautyGirlStyle, <lora:v1:1>, optimized keywords from analysis..." --total 30 --output ./dataset/v2_refined --no-caption
./bin/llm-utils tag --path ./dataset/v2_refined
```
*Repeat until your LoRA reaches perfection.*

---

## 5. Advanced: Multiple Configurations
If you have different setups for different projects, you can point to a specific YAML file:
```bash
./bin/llm-utils --config ./config_experimental.yaml data-gen --topic "test"
```

---

## 3. Configuration (`config.yaml`)

The tool looks for `config.yaml` in the directory it's executed from, or typically inside `cmd/go/llm-utils` during dev.

### Model Setup
Ensure your Ollama model supports vision (e.g. `llama3.2-vision`) if you plan to use Analyze/Chat features heavily.

### LoRA Autocomplete
The `--lora` flag pulls its autocomplete suggestions from the `loras` list in `config.yaml` or dynamically from Forge if configured.

---

## 4. Shell Integration (Autocomplete)

To enable Tab-completion for flags (like picking a LoRA from the list):

1. Generate the script:
   ```bash
   ./bin/llm-utils completion bash > llm-utils.bash
   ```
2. Source it:
   ```bash
   source ./llm-utils.bash
   ```

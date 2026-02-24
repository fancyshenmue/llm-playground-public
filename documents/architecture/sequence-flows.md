# llm-utils Sequence Flows

> **See also**: [LoRA Development Lifecycle](./lifecycle.md) - Complete development lifecycle, iteration patterns, and state machines

## Table of Contents

1. [Data Generation Flow](#1-data-generation-flow)
2. [Image Tagging Flow](#2-image-tagging-flow)
3. [LoRA Training Flow](#3-lora-training-flow)
4. [Image Ranking Flow](#4-image-ranking-flow)
5. [Image Analysis Flow](#5-image-analysis-flow)
6. [Complete Workflow](#6-complete-workflow-end-to-end)

## 1. Data Generation Flow

### Diagram

```mermaid
sequenceDiagram
    participant User
    participant llm-utils
    participant Ollama
    participant Forge

    User->>llm-utils: data-gen --topic "street" --total 50

    loop For each image (1 to 50)
        llm-utils->>Ollama: Generate prompt for "street"
        Ollama-->>llm-utils: Return detailed prompt + caption
        llm-utils->>Forge: txt2img API call
        Forge-->>llm-utils: Return generated image
        llm-utils->>llm-utils: Save image.png + caption.txt
    end

    llm-utils-->>User: ✅ 50 images generated
```

### Process Explanation

**Step 1: User Initiates Generation**
- User executes `llm-utils data-gen` with topic and count
- Optional: Can specify LoRA model, weight, manual prompt

**Step 2-5: Generation Loop (for each image)**

1. **Prompt Generation (Ollama)**
   - llm-utils sends topic to Ollama LLM
   - Ollama generates unique, detailed SDXL prompt
   - Returns both prompt (for image generation) and caption (for training)
   - Ensures diversity by tracking iteration number

2. **Image Generation (Forge)**
   - llm-utils calls Stable Diffusion Forge API
   - Passes the generated prompt
   - Forge renders image using base model + optional LoRA
   - Returns PNG image data

3. **File Saving**
   - Saves image as `{timestamp}_{number}.png`
   - Saves caption as `{timestamp}_{number}.txt`
   - Stores in specified output directory

**Step 6: Completion**
- Reports total images generated
- Ready for tagging or training

---

## 2. Image Tagging Flow

### Diagram

```mermaid
sequenceDiagram
    participant User
    participant llm-utils
    participant Kohya
    participant WD14Model

    User->>llm-utils: tag --path ./dataset
    llm-utils->>llm-utils: Find Python executable
    llm-utils->>Kohya: Execute tag_images_by_wd14_tagger.py

    loop For each image
        Kohya->>WD14Model: Analyze image
        WD14Model-->>Kohya: Return tags with confidence
        Kohya->>Kohya: Filter by threshold
        Kohya->>Kohya: Save tags to .txt file
    end

    Kohya-->>llm-utils: Tagging complete
    llm-utils-->>User: ✅ All images tagged
```

### Process Explanation

**Step 1: User Initiates Tagging**
- Specifies directory containing images
- Optionally sets thresholds and undesired tags

**Step 2: Python Path Detection**
- llm-utils locates correct Python executable
- Checks for `python.exe` (Windows) first
- Falls back to `bin/python` (Linux)

**Step 3: Execute Kohya Tagger**
- Runs `tag_images_by_wd14_tagger.py` script
- Passes directory path and parameters
- Script initializes WD14 vision model

**Step 4-7: Tagging Loop (for each image)**

1. **Image Analysis**
   - Kohya loads image and preprocesses
   - Sends to WD14 ConvNeXt model
   - Model analyzes visual content

2. **Tag Extraction**
   - WD14 returns tags with confidence scores
   - E.g., `{"1girl": 0.95, "street": 0.87, "outdoors": 0.78}`

3. **Filtering**
   - Removes tags below threshold (default 0.35)
   - Removes undesired tags (watermark, text, etc.)
   - Separates character tags vs general tags

4. **Save to File**
   - Appends or overwrites `.txt` caption file
   - Format: `tag1, tag2, tag3` (comma-separated)

**Step 8-9: Completion**
- Reports tagging statistics
- Shows tag frequency if requested

---

## 3. LoRA Training Flow

### Diagram

```mermaid
sequenceDiagram
    participant User
    participant llm-utils
    participant Kohya
    participant GPU

    User->>llm-utils: train --config config.json
    llm-utils->>llm-utils: Read JSON config
    llm-utils->>llm-utils: Parse & validate parameters
    llm-utils->>llm-utils: Auto-fix conflicts (cache + unet)
    llm-utils->>llm-utils: Build command line args

    llm-utils->>Kohya: Execute sdxl_train_network.py
    Kohya->>Kohya: Load base model
    Kohya->>Kohya: Prepare dataset (bucketing)

    loop Training steps (1600)
        Kohya->>GPU: Forward pass
        GPU-->>Kohya: Loss value
        Kohya->>GPU: Backward pass (gradients)
        Kohya->>Kohya: Update LoRA weights
    end

    Kohya->>Kohya: Save LoRA model (.safetensors)
    Kohya-->>llm-utils: Training complete
    llm-utils-->>User: ✅ LoRA saved to output_dir
```

### Process Explanation

**Step 1: User Initiates Training**
- Provides JSON config file (exported from Kohya GUI or hand-written)
- Config contains all training parameters (learning rate, network dim, etc.)

**Step 2-5: Config Processing**

1. **Read JSON Config**
   - Parse JSON file into map structure
   - Validate required fields

2. **Validate Parameters**
   - Check for conflicting settings
   - Verify paths exist

3. **Auto-fix Conflicts**
   - If `cache_text_encoder_outputs`, add `--network_train_unet_only`
   - Map deprecated parameters (e.g., `sdxl_cache_text_encoder_outputs` → `cache_text_encoder_outputs`)
   - Skip GUI-only fields (`epoch`, `model_list`, etc.)

4. **Build Command**
   - Convert JSON to command-line arguments
   - Separate Accelerate args from training script args

**Step 6-10: Training Execution**

1. **Execute Training Script**
   - Runs `sdxl_train_network.py` via Accelerate
   - Loads base SDXL model into GPU memory

2. **Dataset Preparation**
   - Scans training directory for images
   - Creates buckets by resolution (e.g., 1024x1024)
   - Preprocesses and caches latents to disk
   - Calculates total steps based on images and repeats

3. **Training Loop**
   - For each step (1-1600):
     - Forward pass: generate predictions
     - Calculate loss (L2, Huber, etc.)
     - Backward pass: compute gradients
     - Update LoRA weights using optimizer (Prodigy, AdamW, etc.)
   - Gradient accumulation every N steps

4. **Save Model**
   - Saves LoRA weights as `.safetensors` file
   - Includes metadata (network dim, alpha, training params)

**Step 11-12: Completion**
- Reports training complete
- LoRA ready for use in Stable Diffusion

---

## 4. Image Ranking Flow

### Diagram

```mermaid
sequenceDiagram
    participant User
    participant llm-utils
    participant Ollama

    User->>llm-utils: rank --dir ./output
    llm-utils->>llm-utils: List all images in directory

    loop For each image
        llm-utils->>Ollama: Send image for vision analysis
        Ollama->>Ollama: Analyze composition, lighting, style
        Ollama-->>llm-utils: Return score (1-10) + feedback
        llm-utils->>User: 🖼️ image.png: 9 - Excellent composition
    end

    llm-utils-->>User: ✅ Ranking complete
```

### Process Explanation

**Step 1: User Initiates Ranking**
- Specifies directory containing generated images
- Can optionally filter by file pattern

**Step 2: List Images**
- Scans directory for image files (PNG, JPG, etc.)
- Sorts by filename for consistent ordering

**Step 3-6: Ranking Loop (for each image)**

1. **Send to Vision Model**
   - Encodes image as base64
   - Sends to Ollama with llama3.2-vision model
   - Includes ranking criteria in prompt

2. **AI Analysis**
   - Ollama analyzes:
     - Composition (rule of thirds, balance, focal point)
     - Lighting (natural/dramatic, shadows, highlights)
     - Visual appeal (colors, clarity, detail)
     - Style consistency (matches intended aesthetic)

3. **Return Score**
   - Score from 1-10
   - Brief explanation of score
   - Specific feedback on strengths/weaknesses

4. **Display to User**
   - Shows each image's score in real-time
   - Helps identify best images for selection

**Step 7: Completion**
- All images ranked
- User can manually review high-scoring images

**Use Cases:**
- Filter training data (keep only 8+ scores)
- Compare different LoRA weights
- Evaluate prompt variations

---

## 5. Image Analysis Flow

### Diagram

```mermaid
sequenceDiagram
    participant User
    participant llm-utils
    participant Ollama
    participant AnythingLLM

    User->>llm-utils: analyze --image photo.png
    llm-utils->>Ollama: Send image + analysis prompt
    Ollama->>Ollama: Deep analysis (composition, lighting, style)
    Ollama-->>llm-utils: Detailed analysis report

    llm-utils->>User: Display analysis
    llm-utils->>AnythingLLM: Store analysis in knowledge base
    AnythingLLM-->>llm-utils: Stored successfully

    llm-utils-->>User: ✅ Analysis saved to AnythingLLM
```

### Process Explanation

**Step 1: User Initiates Analysis**
- Specifies single image for deep analysis
- Can be used on generated images or reference images

**Step 2-3: Deep Analysis**

1. **Send to Vision LLM**
   - Encodes image as base64
   - Sends with comprehensive analysis prompt
   - Requests detailed breakdown

2. **AI Analysis**
   - Much more detailed than ranking
   - Analyzes:
     - **Composition**: Layout, perspective, focal points, leading lines
     - **Lighting**: Type, direction, mood, quality
     - **Style**: Aesthetic, genre, FancyStyle characteristics
     - **Technical Quality**: Sharpness, artifacts, color accuracy
     - **Suggestions**: Specific improvements for next iteration

**Step 4: Display Results**
- Shows full analysis report to user
- Formatted as markdown for readability

**Step 5-6: Knowledge Base Storage**

1. **Store in AnythingLLM**
   - Sends analysis text to AnythingLLM API
   - Links to image filename
   - Stores in specified workspace

2. **Confirmation**
   - Reports successful storage
   - Analysis now searchable in AnythingLLM

**Step 7: Completion**
- User has detailed understanding of image
- Knowledge accumulated for future reference

**Use Cases:**
- Understand why certain images work better
- Learn from successful generations
- Build searchable knowledge base of techniques
- Query: "What lighting techniques worked best in street scenes?"

---

## 6. Complete Workflow (End-to-End)

### Diagram

```mermaid
sequenceDiagram
    participant User
    participant llm-utils
    participant Services

    User->>llm-utils: 1. data-gen (Generate training data)
    llm-utils->>Services: Ollama + Forge
    Services-->>llm-utils: 50 images + captions

    User->>llm-utils: 2. tag (Add WD14 tags)
    llm-utils->>Services: Kohya WD14 Tagger
    Services-->>llm-utils: Tagged all images

    User->>llm-utils: 3. train (Train LoRA)
    llm-utils->>Services: Kohya training scripts
    Services-->>llm-utils: LoRA model created

    User->>llm-utils: 4. Test LoRA
    User->>llm-utils: data-gen --lora Street_v1.safetensors
    llm-utils->>Services: Generate test images
    Services-->>llm-utils: Test images

    User->>llm-utils: 5. rank (Evaluate quality)
    llm-utils->>Services: Ollama vision
    Services-->>llm-utils: Quality scores

    User->>llm-utils: 6. analyze (Deep analysis)
    llm-utils->>Services: Ollama + AnythingLLM
    Services-->>llm-utils: Stored in knowledge base
```

### Complete Workflow Explanation

This is the typical end-to-end workflow for creating and refining a custom LoRA model.

**Phase 1: Data Generation (Steps 1-2)**
1. Generate initial training dataset
   - 50+ images with captions
   - Diverse prompts from Ollama
2. Add detailed tags
   - WD14 model provides accurate tags
   - Improves training quality

**Phase 2: Training (Step 3)**
3. Train LoRA model
   - Uses tagged dataset
   - Runs for 1600 steps
   - Produces `Street_v1.safetensors`

**Phase 3: Testing & Iteration (Steps 4-6)**
4. Generate test images
   - Use newly trained LoRA
   - Verify it learned the concept

5. Evaluate quality
   - Rank test images (1-10 scores)
   - Find best results

6. Deep analysis
   - Analyze top-scoring images
   - Understand what works
   - Store insights in knowledge base

**Iteration Loop:**
If results aren't satisfactory:
- Adjust training parameters
- Generate more/better training data
- Retrain and test again

**Typical Timeline:**
- Data generation: 1-2 hours (50 images)
- Tagging: 5-10 minutes
- Training: 2-4 hours (1600 steps on RTX 4090)
- Testing & evaluation: 30-60 minutes
- **Total: 4-8 hours per LoRA iteration**

**Automation Benefits:**
All steps are automatable via llm-utils:
```bash
# Complete workflow in one script
llm-utils data-gen --topic "street" --total 50
llm-utils tag --path ./dataset/street
llm-utils train --config street_config.json
llm-utils data-gen --lora Street_v1.safetensors --total 10
llm-utils rank --dir ./test_output
llm-utils analyze --image ./test_output/best_001.png
```

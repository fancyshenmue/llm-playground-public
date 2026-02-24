# Fine-tuning Performance Analysis & Workflow Recommendations: 14B vs 32B

This document records performance observations, underlying principles, and best practice workflows for fine-tuning Qwen-14B and 32B models in an RTX 4090 (24GB VRAM) environment.

## 1. Core Reasons for Performance Differences

The 14B model is significantly faster than the 32B during fine-tuning due to three main factors:

### VRAM Usage & CPU Offloading
- **14B (4-bit)**: Weights occupy ~**7.5GB**. Including Activations and KV Cache for a 4096 context length, total usage is ~12-15GB. The GPU has enough headroom, requiring **no system RAM**.
- **32B (4-bit)**: Weights alone take **16GB**. With a 4096 context, usage easily approaches the 24GB limit. When VRAM is full, CPU Offloading moves computations to system RAM over the low-bandwidth PCIe bus, causing a massive speed drop.

### Gradient Accumulation Settings
One "Step" on the progress bar represents one weight update.
- **14B**: Set to 16, meaning it updates after processing 16 samples.
- **32B**: Set to 48, meaning it updates after processing 48 samples.
Even if the per-sample computation speed were identical, 32B would appear 3x slower visually.

### Computational Complexity (FLOPs)
The 32B model has ~2.3x the parameters of the 14B. With more layers and higher hidden dimensions, the raw physical computation (FLOPs) per forward/backward pass is naturally more than double.

---

## 2. Key Terminology

### Step vs. Epoch
- **Step (Iteration)**: One increment on the progress bar, representing one weight update.
- **Epoch**: One complete pass through the entire dataset. One Epoch usually contains thousands of Steps.

### Effective Batch Size
`Effective Batch Size = micro_batch_size × gradient_accumulation_steps`
- **14B (Step=16)**: Learns after seeing 16 samples.
- **32B (Step=48)**: Learns after seeing 48 samples. Larger models require larger batch sizes for training stability.

---

## 3. Iterative Fine-tuning Workflow (Train -> Merge -> Re-Train)

To teach a model different sets of knowledge in stages, use this "Checkpoint Progression" flow:

1. **Stage 1 (LoRA Training)**: `Base Model + Dataset A = LoRA Adapter A`
2. **Stage 2 (Merge Weights)**: `Base Model + Adapter A = New Model V2`
3. **Stage 3 (Next Iteration)**: Use `New Model V2` as the **Base Model** and train with `Dataset B`.

### Best Practices
- **Catastrophic Forgetting**: During later stages, include 10-20% of data from previous stages (replay mechanism) to prevent the model from forgetting old knowledge.
- **Learning Rate**: Use a **lower** `learning_rate` for subsequent stages (e.g., dropping from 2e-4 to 5e-5).
- **Specialization**: A fine-tuned 14B specialized in a specific domain (e.g., internal APIs, specific formats) often outperforms a base 32B in that domain.

---

## 4. Dataset Loading & OOM Mitigation

### Why does Streaming still cause OOM?
Even with `streaming: true`, RAM usage can spike due to:
- **Shuffle Buffer**: Memory used to pre-read and randomize samples.
- **File Indexing**: Metadata generated when scanning large numbers of files (e.g., using wildcard `*`).

### Best Solution: Manual Sharding
If loading a full dataset causes a crash, specify files manually:
- **Approach**: `data_files: "data/go/train-00000-of-*.parquet"`
- **Continuation**: After finishing `00000`, change to `00001` and use **`resume_from_checkpoint`** pointing to the folder of the most recent save.

> [!NOTE]
> **What does the number in `checkpoint-500` mean?**
> The number (e.g., 500) represents the **Training Step** at which the model was saved. It is NOT a fixed value. You can find your specific numbers by checking your `output_dir`. For example, if you set `saves_per_epoch: 4` and your total steps are 2000, you will see folders like `checkpoint-500`, `checkpoint-1000`, etc.

---

## 5. Performance Optimization (RTX 4090)

- **Micro Batch Size**: Since 14B runs smoothly, try increasing `micro_batch_size` from 1 to 2 or 4. As long as VRAM doesn't overflow, this significantly improves throughput.
- **Flash Attention**: Ensure `flash_attention: true` is enabled to save VRAM on 4096+ sequence lengths.

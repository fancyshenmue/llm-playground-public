# GPU Resource & Scaling Guide

This document explains how GPU resources (VRAM) are utilized during Unsloth fine-tuning and why increasing the dataset size is safe.

## VRAM vs. Training Time

The most important distinction to understand is that **dataset size affects training time, not VRAM usage.**

| Factor | Affects VRAM? | Affects Time? | Notes |
| :--- | :---: | :---: | :--- |
| **Model Size** (14B vs 32B) | ✅ Yes | ✅ Yes | Larger models require more baseline VRAM. |
| **Max Sequence Length** | ✅ Yes | ✅ Yes | Memory usage grows geometrically with context length. |
| **Batch Size** | ✅ Yes | ✅ Yes | Higher batch size increases peak VRAM. |
| **Dataset Size** (Samples) | ❌ No | ✅ Yes | More samples just mean more iterations. |

## Why is Scaling Dataset Size Safe?

During training, the GPU processes data in "chunks" defined by your `batch_size`.
- With `per_device_train_batch_size = 1`, the GPU only ever holds **one sample** in its active memory for computation at any given millisecond.
- Once that sample is processed and gradients are updated, the memory used for the sample's activations is cleared.
- Increasing from 1,000 to 20,000 samples simply means the GPU performs this loop 20 times more often. **Peak VRAM remains constant.**

## Factors that DO Increase VRAM Risk

1.  **Increased `max_seq_length`**:
    - The attention mechanism's memory requirement is quadratic relative to the sequence length.
    - Reducing this (e.g., to 128 for 32B models) is the most effective way to fit large models in 24GB.
2.  **Memory Fragmentation**:
    - Over time, allocating and deallocating memory can leave "holes".
    - We use `PYTORCH_ALLOC_CONF=expandable_segments:True` to mitigate this.
3.  **LoRA Rank (`r`)**:
    - Higher rank means more trainable parameters. While small, it adds up for 32B+ models on the edge of 24GB.

## Other Resource Impacts

- **System RAM**: High sample counts (50k+) might increase RAM usage during the initial loading and shuffling phase, but 20k samples of code text usually only take ~500MB-1GB.
- **Disk Space**: The Hugging Face cache will grow as you download more Parquet files from 'The Stack'.

## Summary for 24GB (RTX 4090)

- **14B Model**: Can comfortably handle `max_seq_length = 1024` with `r = 32`.
- **32B Model**: Requires `max_seq_length = 128-256` and `r = 4-8` to avoid OOM during loss calculation.

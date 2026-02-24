
## 🛠️ Optimization Guide: Training 32B Models on Consumer Hardware

Running a 32B parameter model (like Qwen2.5-Coder-32B) on a consumer PC (64GB RAM, 24GB VRAM) pushes the hardware to its absolute limit. This section documents the critical optimizations required to make this possible.

### 1. The RAM Bottleneck (64GB is not enough)
*   **Problem**: Loading a 32B model in BF16 precision requires ~60GB+ of RAM just for weights. During training initialization, memory usage spikes well beyond 64GB due to overhead, optimizer states, and dataset buffers.
*   **Solution: Massive Striped Pagefile**:
    *   We utilized Windows **Pagefile** (Swap) to extend virtual memory to ~120GB.
    *   **Crucial Trick**: We distributed the Pagefile across **4 separate NVMe SSDs** (Striping). This creates a "RAID 0"-like effect for swap memory, allowing Windows to move data in and out of RAM at much higher speeds (3-4GB/s) than a single drive could handle, preventing the system from freezing during model loading.

### 2. The I/O Bottleneck (Dataset Processing)
*   **Problem**: The `bigcode/the-stack` dataset is massive. Standard Axolotl processing involves:
    1.  Downloading parquet files.
    2.  Tokenizing everything into a huge Arrow table in RAM/Disk.
    3.  **Sample Packing**: Sorting all sequences by length to pack them efficiently (requires fully materialized dataset).
    *   On Windows/WSL2, the I/O overhead of memory-mapping these huge cache files caused persistent `RuntimeError: One of the subprocesses has abruptly died` due to I/O timeouts or driver-level constraints.
*   **Solution: True Streaming Mode**:
    *   We enabled `streaming: true` AND disabled `sample_packing: false`.
    *   **Why**: Streaming bypasses the disk cache entirely. Data flows from Network -> CPU RAM -> GPU VRAM on-the-fly.
    *   **Trade-off**: Slightly less efficient training (more padding since we can't bin-pack), but it **eliminates** the crash-prone dataset preparation step.

### 3. The VRAM Bottleneck (24GB is not enough)
*   **Problem**: A 32B model in 4-bit quantization (QLoRA) takes up ~18GB VRAM. However, activation memory (processing the context) and optimizer states quickly push this beyond the 24GB limit of an RTX 4090, causing OOM (Out of Memory) errors during initialization.
*   **Solution: CPU Offload**:
    *   We configured `llm_int8_enable_fp32_cpu_offload: true` (inside `bnb_config_kwargs`).
    *   This tells the `bitsandbytes` library: "If the model doesn't fit in VRAM, put the extra layers in System RAM."
    *   This allows the training to start, utilizing the massive CPU RAM (backed by the NVMe Pagefile) as an overflow buffer for the GPU.

### 4. The IPC Bottleneck (Docker Shared Memory)
*   **Problem**: PyTorch `DataLoader` uses shared memory (`/dev/shm`) to transfer data between worker processes. Docker defaults to 64MB, which is instantly exhausted, causing processes to crash with `Bus error`.
*   **Solution**:
    *   Set `shm_size: 16g` in `docker-compose.yml`.
    *   This gives PyTorch plenty of room to move batch data without crashing.

### Summary Configuration
To reproduce this stability, your config should look like this:

```yaml
# code-training.yaml
base_model: Qwen/Qwen2.5-Coder-32B-Instruct
load_in_4bit: true
bnb_config_kwargs:
  llm_int8_enable_fp32_cpu_offload: true  # Allow VRAM overflow to RAM

datasets:
  - path: bigcode/the-stack
    streaming: true        # Bypass Disk I/O
    type: completion       # Standard Causal LM training

sequence_len: 4096         # Maximize context within 24GB VRAM
sample_packing: false      # Disable packing to allow True Streaming
pad_to_sequence_len: true
dataset_processes: 1       # Minimize RAM overhead
gpu_memory_limit: 20GiB    # Reserve buffer for activations
```

## 📊 Expected Resource Patterns

When training starts, you will see a distinct "Burst -> Silence" pattern in your resource monitor. This is normal and indicates a healthy configuration.

### Phase 1: The "Swap Burst" (Initialization)
*   **Duration**: 1-3 minutes.
*   **Disk Activity**: **100% Usage across ALL Pagefile Drives (Striping)**.
    *   **Reason**: The OS is frantically moving "Cold Memory" (e.g., your Browser, Discord, OS background tasks) from RAM to the NVMe Pagefile to free up ~60GB of physical RAM for the model weights.
    *   **RAM**: Shoots up to 95-99% usage.
*   **Result**: If your disk I/O graph looks like a solid brick wall across multiple drives, it means the striping strategy is working perfectly to keep the system responsive.

### Phase 2: The "Compute Steady State" (Training Loop)
*   **Duration**: Hours/Days.
*   **Disk Activity**: **Near Zero**.
    *   **Reason**: Once the model is loaded into RAM/VRAM, it stays there ("Hot Memory"). The training data being streamed in is relatively small (a few MBs per second), which modern NVMe drives handle effortlessly.
*   **GPU**: Usage stabilizes (e.g., 90-100% depending on CPU bottleneck).
*   **RAM**: Usage remains high but stable. Windows has successfully segregated the active model (in RAM) from the inactive apps (in Pagefile).

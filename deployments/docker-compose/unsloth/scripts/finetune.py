import os

# Allow Unsloth to install llama.cpp dependencies into the system environment
os.environ["UV_SYSTEM_PYTHON"] = "1"

# Disable WandB to prevent interactive login prompts
import torch
from unsloth import FastLanguageModel
from datasets import load_dataset
from trl import SFTTrainer
from transformers import TrainingArguments
from unsloth import is_bfloat16_supported

# Configuration
model_name = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-Coder-14B-Instruct")
load_in_4bit = True

# Disable memory fragmentation
os.environ["PYTORCH_ALLOC_CONF"] = "expandable_segments:True"

# Dynamic optimization based on model size
is_32b = "32B" in model_name

if is_32b:
    max_seq_length = 128       # Extreme minimum to fit 32B in 24GB
    gpu_memory_fraction = 0.90  # Leave room for loss kernels (approx 21.6GB)
    lora_r = 4                 # Minimal rank to save every MB
    use_packing = False
else:
    max_seq_length = 1014
    gpu_memory_fraction = 0.83
    lora_r = 32
    use_packing = False

print(f">>> Target Model: {model_name}")
print(f">>> Setting max_seq_length to {max_seq_length}")
print(f">>> Limiting VRAM to {gpu_memory_fraction * 24:.2f} GB")

torch.cuda.set_per_process_memory_fraction(gpu_memory_fraction, 0)

# 1. Load Model & Tokenizer
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = model_name,
    max_seq_length = max_seq_length,
    load_in_4bit = load_in_4bit,
)

# 2. Add LoRA Adapters
model = FastLanguageModel.get_peft_model(
    model,
    r = lora_r,
    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj",
                      "gate_proj", "up_proj", "down_proj",],
    lora_alpha = lora_r * 2,
    lora_dropout = 0,
    bias = "none",
    use_gradient_checkpointing = "unsloth",
    random_state = 3407,
    use_rslora = False,
    loftq_config = None,
)

# 3. Load Datasets for multiple languages
languages = ["go", "python", "javascript", "typescript"]
datasets = []

print(f">>> Loading datasets for: {', '.join(languages)}")
for lang in languages:
    try:
        lang_ds = load_dataset("bigcode/the-stack",
                               data_files = {"train": [f"data/{lang}/train-*.parquet"]},
                               split = "train[:10000]", # Recommended: 10k per language for high diversity
                               streaming = False)
        print(f"--- Loaded {len(lang_ds)} samples for {lang}")
        datasets.append(lang_ds)
    except Exception as e:
        print(f"--- Warning: Could not load dataset for {lang}: {e}")

if not datasets:
    raise RuntimeError("No datasets were loaded. Check your internet connection or dataset names.")

from datasets import concatenate_datasets
dataset = concatenate_datasets(datasets)
dataset = dataset.shuffle(seed = 3407)

# Filter dataset to avoid truncation errors in Unsloth's fused loss
print(f">>> Total samples before filtering: {len(dataset)}")
print(">>> Filtering dataset for sequence length...")
dataset = dataset.filter(
    lambda x: len(tokenizer.encode(x["content"])) <= max_seq_length,
    num_proc = 4
)
print(f">>> Dataset size after filtering: {len(dataset)}")

# Formatting function for SFT
def formatting_prompts_func(examples):
    # Ensure we return a list of strings
    return [str(content) for content in examples["content"]]

# 4. Initialize Trainer
trainer = SFTTrainer(
    model = model,
    tokenizer = tokenizer,
    train_dataset = dataset,
    formatting_func = formatting_prompts_func,
    max_seq_length = max_seq_length,
    packing = use_packing, # Dynamically set based on model size
    args = TrainingArguments(
        per_device_train_batch_size = 1,
        gradient_accumulation_steps = 8,
        warmup_steps = 10,
        max_steps = 2500, # Recommended: 2500 steps covers approx 1 Epoch for 40k samples (at batch 8)
        learning_rate = 2e-4,
        fp16 = not is_bfloat16_supported(),
        bf16 = is_bfloat16_supported(),
        logging_steps = 1,
        optim = "adamw_8bit",
        weight_decay = 0.01,
        lr_scheduler_type = "linear",
        seed = 3407,
        output_dir = "/workspace/output/unsloth-qwen-coder",
        report_to = "none", # Disable logging to WandB, etc.
    ),
)

# 5. Train
trainer_stats = trainer.train()

# 6. Save LoRA
model.save_pretrained(f"/workspace/output/{model_name.split('/')[-1]}-lora")
tokenizer.save_pretrained(f"/workspace/output/{model_name.split('/')[-1]}-lora")

# 7. Export to GGUF (Ollama)
print("--- Exporting to GGUF ---")
model.save_pretrained_gguf(
    f"/workspace/output/{model_name.split('/')[-1]}-gguf",
    tokenizer,
    quantization_method = "q4_k_m",
)

import os

# Avoid CUDA fragmentation (Must be set BEFORE torch is imported)
os.environ["PYTORCH_ALLOC_CONF"] = "expandable_segments:True"
# Disable Unsloth's vLLM standby to prevent it from overriding expandable_segments
os.environ["UNSLOTH_VLLM_STANDBY"] = "0"
# Allow Unsloth to install llama.cpp dependencies into the system environment
os.environ["UV_SYSTEM_PYTHON"] = "1"

# Disable WandB to prevent interactive login prompts
import torch
from unsloth import FastLanguageModel
from datasets import load_dataset
from trl import SFTTrainer
from transformers import TrainingArguments
from unsloth import is_bfloat16_supported

import yaml

# Load Configuration from YAML
config_path = "/workspace/config.yaml"
if not os.path.exists(config_path):
    # Fallback to local if running outside container for testing
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")

with open(config_path, "r") as f:
    config = yaml.safe_load(f)

# Helper to get config with env override
def get_config(keys, default=None):
    # Try ENV first for flat overrides (useful for quick CI/CD changes)
    env_key = keys[-1].upper()
    env_val = os.getenv(env_key)
    if env_val is not None:
        return env_val

    # Traverse YAML dict
    val = config
    for k in keys:
        if isinstance(val, dict) and k in val:
            val = val[k]
        else:
            return default
    return val

# 1. Mode & Model Configuration
mode = get_config(["training", "mode"], "instruct")
model_name = get_config(["model", "name"], "Qwen/Qwen2.5-Coder-14B-Instruct")
load_in_4bit = get_config(["model", "load_in_4bit"], True)
max_seq_override = os.getenv("MAX_SEQ_LENGTH")

# 2. Hyperparameters (Mode-specific)
learning_rate = float(get_config(["training", mode, "learning_rate"], 2e-5 if mode == "instruct" else 1e-4))
max_steps = int(get_config(["training", mode, "max_steps"], 2000 if mode == "instruct" else 5000))

# Shared Training Config
batch_size = int(get_config(["training", "batch_size"], 1))
grad_accum = int(get_config(["training", "gradient_accumulation_steps"], 8))
warmup_steps = int(get_config(["training", "warmup_steps"], 10))
weight_decay = float(get_config(["training", "weight_decay"], 0.01))
optim = get_config(["training", "optim"], "adamw_8bit")
seed = int(get_config(["training", "seed"], 3407))
quantization_method = get_config(["export", "quantization_method"], "q4_k_m")
resume_from_checkpoint = get_config(["training", "resume"], False)

# 3. Dataset Configuration
languages = get_config(["dataset", "languages"], ["go", "python", "javascript", "typescript"])
samples_per_lang = int(get_config(["dataset", "samples_per_lang"], 10000))
use_streaming = get_config(["dataset", "streaming"], False)

# Dynamic defaults based on model size if not overridden
is_32b = "32B" in model_name

if is_32b:
    max_seq_length = int(max_seq_override) if max_seq_override else get_config(["model", "max_seq_length"], 128)
    gpu_memory_fraction = 0.90
    lora_r = int(os.getenv("LORA_R", get_config(["training", "lora_r"], 4)))
else:
    max_seq_length = int(max_seq_override) if max_seq_override else get_config(["model", "max_seq_length"], 1024)
    gpu_memory_fraction = 0.83
    lora_r = int(os.getenv("LORA_R", get_config(["training", "lora_r"], 32)))

use_packing = False

print(f">>> Target Model: {model_name}")
print(f">>> Setting max_seq_length to {max_seq_length}")
print(f">>> LoRA Rank (R): {lora_r}")
print(f">>> Learning Rate: {learning_rate}")
print(f">>> Max Steps: {max_steps}")
print(f">>> Batch Size: {batch_size} (Accumulation: {grad_accum})")
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

# 3. Load Datasets
print(f">>> Mode: {mode.upper()}")
if mode == "instruct":
    ds_name = get_config(["dataset", "instruct", "name"], "sahil2801/code_instructions_120k")
    print(f">>> Loading Instruct Dataset: {ds_name}")
    dataset = load_dataset(ds_name, split="train")
    if not use_streaming:
        # Sample if not streaming to avoid OOM or long processing
        dataset = dataset.shuffle(seed=seed).select(range(min(len(dataset), 50000)))
else:
    languages = get_config(["dataset", "raw", "languages"], ["go", "python", "javascript", "typescript"])
    samples_per_lang = int(get_config(["dataset", "raw", "samples_per_lang"], 15000))
    ds_name = get_config(["dataset", "raw", "name"], "bigcode/the-stack")

    datasets = []
    print(f">>> Loading Raw Datasets: {', '.join(languages)} ({samples_per_lang} samples each)")
    for lang in languages:
        try:
            lang_ds = load_dataset(ds_name,
                                  data_files = {"train": [f"data/{lang}/train-*.parquet"]},
                                  split = "train" if use_streaming else f"train[:{samples_per_lang}]",
                                  streaming = use_streaming)
            if use_streaming:
                lang_ds = lang_ds.take(samples_per_lang)
            datasets.append(lang_ds)
        except Exception as e:
            print(f"--- Warning: Could not load dataset for {lang}: {e}")

    if not datasets:
        raise RuntimeError("No datasets were loaded.")

    if use_streaming:
        from datasets import interleave_datasets
        dataset = interleave_datasets(datasets, seed=seed)
        dataset = dataset.shuffle(seed=seed, buffer_size=10000)
    else:
        from datasets import concatenate_datasets
        dataset = concatenate_datasets(datasets)
        dataset = dataset.shuffle(seed=seed)

# Filter dataset
print(f">>> Filtering dataset...")
def filter_length(x):
    # content is for raw, instruction/output for instruct
    text_to_check = x.get("content") or x.get("output", "")
    return len(tokenizer.encode(text_to_check)) <= max_seq_length

if use_streaming:
    dataset = dataset.filter(filter_length)
else:
    dataset = dataset.filter(filter_length, num_proc=4)
print(f">>> Final Dataset Size: {len(dataset) if not use_streaming else 'Unknown (Streaming)'}")

# Formatting function
def formatting_prompts_func(examples):
    if mode == "instruct":
        # Dataset sahil2801/code_instructions_120k has columns: instruction, input, output
        instructions = examples["instruction"]
        inputs       = examples["input"]
        outputs      = examples["output"]
        texts = []
        for instruction, input_text, output in zip(instructions, inputs, outputs):
            # Form ChatML message
            messages = [
                {"role": "user", "content": f"{instruction}\n{input_text}" if input_text else instruction},
                {"role": "assistant", "content": output},
            ]
            # Use tokenizer.apply_chat_template
            tokenized = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
            texts.append(tokenized)
        return texts
    else:
        # Raw code
        return [str(content) for content in examples["content"]]

# 4. Initialize Trainer
trainer = SFTTrainer(
    model = model,
    tokenizer = tokenizer,
    train_dataset = dataset,
    formatting_func = formatting_prompts_func,
    max_seq_length = max_seq_length,
    packing = use_packing,
    args = TrainingArguments(
        per_device_train_batch_size = batch_size,
        gradient_accumulation_steps = grad_accum,
        warmup_steps = warmup_steps,
        max_steps = max_steps,
        learning_rate = learning_rate,
        fp16 = not is_bfloat16_supported(),
        bf16 = is_bfloat16_supported(),
        logging_steps = 1,
        optim = "adamw_8bit",
        weight_decay = weight_decay,
        lr_scheduler_type = "linear",
        seed = seed,
        output_dir = f"/workspace/output/unsloth-qwen-{mode}",
        report_to = "none",
        save_steps = 100,      # Save more frequently for reliability
        save_total_limit = 3,   # Only keep last 3 checkpoints to save disk
    ),
)

# 5. Train
import glob
# Check if checkpoint exists before attempting to resume
checkpoint_path = f"/workspace/output/unsloth-qwen-{mode}"
has_checkpoint = len(glob.glob(os.path.join(checkpoint_path, "checkpoint-*"))) > 0
actual_resume = resume_from_checkpoint and has_checkpoint

if resume_from_checkpoint and not has_checkpoint:
    print(f">>> Resume requested but no checkpoint found in {checkpoint_path}. Starting from Step 0.")
elif actual_resume:
    print(f">>> Resuming from latest checkpoint in {checkpoint_path}")

trainer_stats = trainer.train(resume_from_checkpoint = actual_resume)

# 6. Save LoRA
model.save_pretrained(f"/workspace/output/{model_name.split('/')[-1]}-lora")
tokenizer.save_pretrained(f"/workspace/output/{model_name.split('/')[-1]}-lora")

# 7. Export to GGUF
print("--- Exporting to GGUF ---")
model.save_pretrained_gguf(
    f"/workspace/output/{model_name.split('/')[-1]}-gguf",
    tokenizer,
    quantization_method = quantization_method,
)

# LoRA Training Steps Calculation Guide

This document explains how training steps are calculated in LoRA training and how different parameters in your configuration correspond to these calculations.

## 1. Core Concepts and Parameters

### A. Repeats
*   **Source**: The numeric prefix in your image folder name (e.g., the `10` in `10_coffee`).
*   **Meaning**: The number of times each image in that specific folder is processed during a single Epoch.
*   **Purpose**: Used to balance the weight of different datasets if you have multiple folders.

### B. Epochs
*   **Configuration Parameter**: `"epoch"`
*   **Meaning**: One full pass through the entire dataset (including all repeats of images).

### C. Batch Size
*   **Configuration Parameter**: `"train_batch_size"`
*   **Meaning**: The number of images processed simultaneously in a single training step.

---

## 2. Calculation Formulas

### Steps per Epoch
Formula:
> **(Number of Images × Repeats) / Batch Size**

### Total Training Steps
Formula:
> **Steps per Epoch × Epochs**
> *or*
> **(Number of Images × Repeats × Epochs) / Batch Size**

---

## 3. Calculation Example

Assume you have the following setup:
*   **Images**: 10 images
*   **Folder Name**: `10_coffee` (Repeats = 10)
*   **Epochs**: 1
*   **Batch Size**: 1

**Calculations:**
1.  Steps per Epoch = `(10 × 10) / 1 = 100 steps`
2.  Total Training Steps = `100 steps × 1 = 100 steps`

---

## 4. Key Parameters and Constraints (JSON Reference)

In your configuration file (`.json`), the following fields directly impact the training duration:

| Parameter | Description | Example Value |
| :--- | :--- | :--- |
| `"epoch"` | Total number of training rounds. | `1` |
| `"train_batch_size"` | Number of images per step. | `1` |
| `"max_train_steps"` | **Hard limit on total steps.** The "Mandatory Ceiling". | `1600` |
| `"train_data_dir"` | Path to the parent folder containing your training images. | `".../image"` |

---

## 5. Understanding "max_train_steps" (The Mandatory Ceiling)

`max_train_steps` acts as a **safety net** and a **hard stop**. Regardless of how high you set your Epochs or Repeats, the training will stop immediately once it hits this number.

### Why use it?
1.  **Prevent Overfitting**: High epoch counts with few images can "fry" the model. This keeps the total exposure within safe limits.
2.  **Predictability**: Ensures you know exactly when the training will end.
3.  **Safety**: Stops the process if you accidentally miscalculate your math (e.g., setting repeats to 1000 instead of 10).

### The "Minimum" Rule
The training duration is always the **smaller** of these two values:
*   **Target Steps**: `(Images × Repeats × Epochs) / Batch Size`
*   **Limit**: `max_train_steps`

> [!CAUTION]
> If your `max_train_steps` is too low (e.g., 100) but your math requires 500 steps, your model will only be **20% trained**, and it likely won't look like your subject at all.

---

## 6. Saving Logic & Filenames

When training concludes, you might see many `.safetensors` files. These are controlled by two main parameters:

### A. Epoch-based Saving (`save_every_n_epochs`)
*   **Filename Pattern**: `[model_name]-000001.safetensors`
*   **Logic**: Saves a copy after every `N` epochs.
*   **JSON Parameter**: `"save_every_n_epochs"`

### B. Step-based Saving (`save_every_n_steps`)
*   **Filename Pattern**: `[model_name]-step00000160.safetensors`
*   **Logic**: Saves a copy after every `N` steps.
*   **JSON Parameter**: `"save_every_n_steps"`

### Use Case
If **both** are enabled, you will get **two sets of files**.
*   To only keep the final model: Set both to `0`.
*   To keep only the most recent files: Use `"save_last_n_epochs"` (e.g., set to `3` to keep only the 3 latest versions).

---

## 7. Best Practices & Recommendations

To keep your workspace clean and balance training quality, follow these recommendations:

### A. Dataset Balance
*   **Total "Effective" Images**: Aim for **1500–3000 total steps** for a simple character or object.
*   **Repeats vs. Epochs**:
    *   Use **Repeats** (folder name) to ensure the model sees each image enough times in one go. A common value is `10` or `20`.
    *   Use **Epochs** to allow the model to refine its learning. Usually `10` is a good starting point.

### B. Clean Workspace
*   **Disable Step-Saving**: Set `"save_every_n_steps": 0` unless you are debugging or have a very long training process that might crash.
*   **Limit Epoch Backups**: Set `"save_last_n_epochs": 2` or `3`. This saves disk space by automatically deleting older versions and keeping only the most recent ones.

### C. The "Safety Net"
*   **Always Check `max_train_steps`**: Ensure it is set higher than your calculated `(Images × Repeats × Epochs) / Batch Size`. A safe default is `3000` or `5000` for small LoRAs.

> [!TIP]
> If your model looks "burnt" (overfit), try reducing the **Repeats** or lower the **Learning Rate**. If it doesn't look like the subject at all, increase the **Epochs** or total **Repeats**.

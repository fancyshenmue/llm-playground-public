# Training Metrics Interpretation

This document provides a technical breakdown of the logs generated during Unsloth finetuning.

## 📉 Core Metrics

### 1. Loss
- **What it is**: The error rate of the model.
- **Healthy Range**: **0.5 - 1.5** for SFT tasks.
- **Interpretation**:
    - **Gradual Decrease**: Normal learning.
    - **Stability**: Flatting out around 0.5 is ideal.
    - **Dropping to 0**: Warning! Likely overfitting (memorizing the dataset).
    - **Spiking**: Usually indicates poor data quality or too high learning rate.

### 2. Grad Norm
- **What it is**: The magnitude of weight updates.
- **Healthy Range**: **0.1 - 1.0**.
- **Interpretation**:
    - **Low & Stable**: Perfect stability.
    - **Spikes (>2.0)**: High risk of training instability or OOM.
    - **NaN**: Training has crashed; rollback to a previous checkpoint.

### 3. Learning Rate
- **Current Strategy**: Linear Decay.
- **Behavior**: Starts at the configured `learning_rate` (e.g., `1e-4`) and decreases linearly over time.
- **Purpose**: Allows for fast discovery initially and precision fine-tuning at the end.

### 4. Epoch
- **Definition**: One full pass through the entire dataset.
- **Unsloth Tip**: Since we often use a fixed `max_steps`, you might only complete a fraction of an epoch (e.g., 0.05). This is normal for large code datasets where a few thousand steps are enough to capture patterns.

## 📊 Summary Log Example
```json
{
  "loss": 0.4837,
  "grad_norm": 0.5426,
  "learning_rate": 9.26e-05,
  "epoch": 0.05
}
```
- **Status**: **Perfectly Healthy**. Low loss, low grad norm, the model is learning smoothly.

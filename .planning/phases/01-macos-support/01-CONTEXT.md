# Phase Context: macOS Support & GPU Independence

## Objective
The goal is to add macOS support to the project's `pixi.toml` configuration, ensuring that dependencies are correctly resolved across operating systems. Specifically, we need to address the fact that macOS systems do not have NVIDIA GPUs, and therefore should not attempt to pull in CUDA-related packages or fail on CUDA system requirements.

## Proposed Architectural Changes

1. **Platform Expansion**:
   Change `platforms = ["linux-64"]` to `platforms = ["linux-64", "osx-arm64", "osx-64"]` to natively support Apple Silicon and Intel macOS environments.

2. **Target-Specific Dependencies**:
   The current `pixi.toml` specifies `pytorch-cuda` and `cuda` globally. When running `pixi install` on a non-Linux or non-CUDA machine, this will result in resolution failures.
   - We will extract `pytorch-cuda = "==12.4"` from the generic `[feature.main.dependencies]` table.
   - We will create a `[feature.main.target.linux-64.dependencies]` table and place `pytorch-cuda` there.
   - macOS (`osx-arm64`, `osx-64`) will implicitly fall back to standard `pytorch` (which is already requested as `>=2.4.0`) without attempting to fetch `pytorch-cuda`.

3. **Target-Specific System Requirements**:
   The current file has:
   ```toml
   [system-requirements]
   cuda = "12"
   ```
   This will fail on macOS because it doesn't have a CUDA driver.
   - We will change this to `[target.linux-64.system-requirements]` so the CUDA requirement is only enforced on Linux instances that are expected to have NVIDIA GPUs.

## Action Plan
- Await user approval of this context.
- Once approved, progress to PLAN phase to map out exact file changes.

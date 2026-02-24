# Kohya SS Documentation Center

This directory contains supplementary documentation and operation guides for the Kohya SS project.

## Installation

### 1. Clone Repository

```bash
cd $HOME/dev
git clone https://github.com/bmaltais/kohya_ss.git
cd kohya_ss

# Initialize git submodules (REQUIRED for sd-scripts)
git submodule update --init --recursive
```

### 2. Create Pixi Environment

Create `pixi.toml` in the kohya_ss directory:

```toml
[workspace]
name = "kohya_ss"
channels = ["pytorch", "nvidia", "conda-forge"]
platforms = ["linux-64"]

[dependencies]
python = "==3.10.11"
pytorch = "==2.3.1"
torchvision = "==0.18.1"
pytorch-cuda = "==12.1"
pip = ">=23.0"
git = "*"

[tasks]
install-deps = "pip install -r requirements.txt"

[system-requirements]
cuda = "12"
```

### 3. Install Dependencies

```bash
# Install pixi environment
pixi install

# Install Python dependencies
pixi run install-deps

# Install additional packages for WD14 tagger
pixi run pip install onnxruntime opencv-python
```

### 4. Verify Installation

```bash
# Check if submodules are initialized
ls sd-scripts/  # Should contain Python files

# Test GPU access
pixi run python -c "import torch; print(torch.cuda.is_available())"
```

## Documentation Index

### Environment Setup & Management

- **[Git Submodule Management Guide](git-submodule-setup.md)** - How to manage the sd-scripts submodule

### Coming Soon

More documentation is welcome here!

## Documentation Structure

```
documents/
├── README.md                    # This file
├── git-submodule-setup.md       # Git submodule operation guide
└── [More docs...]
```

## Contribution Guidelines

If you want to add new documentation:

1. Use clear filenames (use hyphens as separators)
2. Use Markdown format
3. Add index links in this README
4. Include actual code examples (if applicable)

## Related Resources

- [Main Project README](../README.md)
- [sd-scripts Documentation](../sd-scripts/docs/)
- [Kohya SS Official Docs](../docs/)

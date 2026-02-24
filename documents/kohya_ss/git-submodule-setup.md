# Git Submodule Management Guide - sd-scripts

This document explains how to manage the sd-scripts dependency in the kohya_ss project using git submodules.

## Background

Kohya SS depends on the `sd-scripts` project to execute the actual training scripts. To facilitate version management and updates, we use git submodule to integrate this dependency.

## Current Configuration

### Submodule Information

```bash
# .gitmodules content
[submodule "sd-scripts"]
    path = sd-scripts
    url = https://github.com/kohya-ss/sd-scripts.git
```

### Current Version

```bash
$ git submodule status
 3e6935a07edcb944407840ef74fcaf6fcad352f7 sd-scripts (v0.9.1-562-g3e6935a)
```

## Initial Setup Steps

### 1. Add Submodule (First Time)

If the project doesn't have the sd-scripts submodule yet, run:

```bash
# In the kohya_ss project root directory
cd $HOME/dev/kohya_ss

# Add sd-scripts as a submodule
git submodule add https://github.com/kohya-ss/sd-scripts.git sd-scripts
```

This will:
- Create the `sd-scripts/` directory in the project root
- Automatically create/update the `.gitmodules` file
- Record the submodule's commit hash in the git index

### 2. Initialize and Update Submodule

```bash
# Initialize submodule configuration
git submodule init

# Download submodule content
git submodule update
```

### 3. Commit Changes

```bash
git add .gitmodules sd-scripts
git commit -m "Add sd-scripts as submodule"
```

## Daily Operations

### Clone Project (Including Submodules)

#### Method 1: One-step clone

```bash
git clone --recurse-submodules https://github.com/bmaltais/kohya_ss.git
```

#### Method 2: Step-by-step

```bash
# Clone main project first
git clone https://github.com/bmaltais/kohya_ss.git
cd kohya_ss

# Then initialize submodule
git submodule init
git submodule update
```

### Update Submodule to Latest Version

```bash
# Enter submodule directory
cd sd-scripts

# Fetch latest code
git fetch
git pull origin main  # or master, depending on the original project

# Return to main project
cd ..

# Commit submodule version update
git add sd-scripts
git commit -m "Update sd-scripts to latest version"
```

### Update to Specific Version/Tag

```bash
cd sd-scripts

# View available tags
git tag -l

# Checkout to specific version
git checkout v0.9.1

cd ..
git add sd-scripts
git commit -m "Update sd-scripts to v0.9.1"
```

### Check Submodule Status

```bash
# View submodule status
git submodule status

# Check for uncommitted changes
git status

# View detailed submodule information
git submodule foreach git status
```

## Common Issues

### Issue 1: Submodule Directory is Empty

**Cause:** Didn't use `--recurse-submodules` when cloning

**Solution:**
```bash
git submodule init
git submodule update
```

### Issue 2: Submodule in Detached HEAD State

**Explanation:** This is normal, submodule points to a specific commit, not a branch

**To develop in submodule:**
```bash
cd sd-scripts
git checkout main  # Switch to branch
# Make changes...
```

### Issue 3: Submodule Not Synced After Main Project Update

**Solution:**
```bash
git pull
git submodule update --init --recursive
```

### Issue 4: Remove Submodule

```bash
# 1. Deinitialize
git submodule deinit -f sd-scripts

# 2. Remove directory
rm -rf .git/modules/sd-scripts
git rm -f sd-scripts

# 3. Commit
git commit -m "Remove sd-scripts submodule"
```

## Best Practices

### 1. Lock to Specific Version

In production environments, it's recommended to lock to a specific stable version rather than tracking the latest commit:

```bash
cd sd-scripts
git checkout v0.9.1  # Use release tag
cd ..
git add sd-scripts
git commit -m "Lock sd-scripts to v0.9.1"
```

### 2. Automated Update Script

Create an update script `update-submodules.sh`:

```bash
#!/bin/bash
# update-submodules.sh

echo "Updating sd-scripts submodule..."
cd sd-scripts
git fetch
git pull origin main
cd ..
git add sd-scripts
echo "Updated to commit: $(git submodule status)"
echo "Please review and commit the changes."
```

### 3. CI/CD Configuration

In CI/CD pipelines, ensure submodules are included:

```yaml
# GitHub Actions example
- name: Checkout code
  uses: actions/checkout@v3
  with:
    submodules: recursive
```

## Integration with Pixi

When using Pixi environment, handling submodules:

```bash
# 1. Start pixi shell
pixi shell

# 2. Submodule already exists, can be used directly
python sd-scripts/train_network.py --help
```

## Related Links

- [sd-scripts Official GitHub](https://github.com/kohya-ss/sd-scripts)
- [Git Submodule Official Documentation](https://git-scm.com/book/en/v2/Git-Tools-Submodules)
- [Kohya SS GitHub](https://github.com/bmaltais/kohya_ss)

## Update History

- 2026-01-15: Initial documentation created
- Current sd-scripts version: v0.9.1-562-g3e6935a

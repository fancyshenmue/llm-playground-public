# Implementation Plan: macOS Support & GPU Independence

## Checklist

- [x] 1. Update `[workspace]` platforms
  - File: `pixi.toml`
  - Action: Change `platforms = ["linux-64"]` to `platforms = ["linux-64", "osx-arm64", "osx-64"]`.

- [x] 2. Update `[system-requirements]`
  - File: `pixi.toml`
  - Action: Remove `[system-requirements]` and `cuda = "12"`.
  - Action: Add `[target.linux-64.system-requirements]` and place `cuda = "12"` under it.

- [x] 3. Update `[feature.main.dependencies]`
  - File: `pixi.toml`
  - Action: Remove `pytorch-cuda = "==12.4"` from the main dependencies list.
  - Action: Add `[feature.main.target.linux-64.dependencies]` table.
  - Action: Insert `pytorch-cuda = "==12.4"` under this new Linux-specific table.

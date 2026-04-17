# Quick Task: Fix macOS `/tmp` symlink evaluation in Sandbox

- [x] Identify the symlink traversal block causing MCP Servers to reject paths (e.g. `/tmp` vs `/private/tmp`).
- [x] Apply `os.path.realpath()` to the ephemeral isolated sandbox directory in `main.py`.
- [x] Apply `os.path.realpath(os.path.expanduser())` to user-injected and auto-extracted directories to prevent `ToolException`.
- [x] Append `quick-18` resolving logic to `STATE.md`.

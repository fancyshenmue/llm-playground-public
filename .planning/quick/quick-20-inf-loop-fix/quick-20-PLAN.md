# Quick Task: Fix Infinite Loop via Start Directory Resolution

- [x] Fix `work_targets` filter in `nodes.py`. `d.endswith('/tmp')` does not exclude `/tmp/autocoder_UUID`. Use `'/tmp' not in d` to properly isolate the actual user project directory from the sandbox directories.
- [x] Apply the fix via `replace_file_content`.
- [x] Register `quick-20` on `STATE.md`.

# Quick Task: Fix MCP Allowed Dirs & Stutter

- [x] Pass both `raw_dir` and `real_dir` to the `all_extra_dirs` list. The MCP adapter strings match paths precisely, so exposing both guarantees resolution.
- [x] Truncate `persistent_thread_id` to its first 8 characters (`[:8]`) to stop Gemma/Qwen from repetitively stuttering UUID generation.
- [x] Register to STATE.md.

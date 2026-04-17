# Quick Task Summary: MCP Path Aliasing & Stutter Mitigation

**Issues Addressed:**
1. The MCP adapter does precise string matching for allowed paths. Depending on whether the agent was instructed to resolve symlinks before calling the filesystem, it either passed `/tmp/` or `/private/tmp/`, causing intermittent validation failures since only one mapped string was provided to the allowed directory list.
2. The agent suffered from a known local-model string-stuttering hallucination because the `persistent_thread_id` UUID was too long, resulting in anomalous paths like `/autocoder_83d5a70a-e8eb-49_e8eb-49a2-a148-bf8425110f78` when transcribed by the agent.

**Changes Made:**
1. Updated `main.py` backends to pass **both** the un-resolved path (`/tmp/...`) and the `os.path.realpath` (`/private/tmp/...`) into `all_extra_dirs` to ensure the adapter permits both variations regardless of how the agent accesses it.
2. Sliced the `persistent_thread_id` generation for the sandbox down to 8 characters (`persistent_thread_id[:8]`) to ensure the agent doesn't trip its context generation when mapping repetitive sequences.

# Quick Task Summary: Symlink Bug Fix

Mac systems alias `/tmp` to `/private/tmp`. The MCP tool authorization checks were receiving `/tmp/autocoder_...` and denying access because the system-interpreted path was `/private/tmp/...`.

**Changes Made:**
1. Added `os.path.realpath(isolated_sandbox)` assignment so `/tmp/...` gracefully normalizes to `/private/tmp/...` before passing the permissions down.
2. Added `os.path.realpath(os.path.expanduser())` logic to both user-provided external directories and LLM-prompt extracted directories. 
3. Logged the task as `quick-18`.

The agent should no longer crash with `Access denied - path outside allowed directories` `ToolExceptions`.

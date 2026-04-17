# Quick Task Summary: AutoCoder Start Directory Fix

**Issue Addressed:**
As seen in Arize Phoenix traces, the agent was constantly polling `list_directory` on the sandbox `/private/tmp/autocoder_...` directory. Because the sandbox was empty, the agent was stuck in an infinite polling loop trying to figure out what to do. The root cause was that `nodes.py` instructed the agent to start there because `/private/tmp/...` didn't literally end with `/tmp`, bypassing the filter which designated the starting search project folder.

**Changes Made:**
1. Modified the `work_targets` list comprehension in `nodes.py` to use `if '/tmp' not in d` rather than `if not d.endswith('/tmp')`. This ensures all temporary sandbox directories are fully excluded from the prompt's `start_dir`.
2. The agent will now correctly receive `/Users/charleshsu/dev/lab/langgraph/app` as its Starting Point, instead of the empty sandbox directory, allowing it to immediately parse `go.mod` and begin implementing the code!

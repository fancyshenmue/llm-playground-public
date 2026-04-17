import os
import httpx
import subprocess
import re
from opentelemetry import trace
from typing import Dict, Any
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import create_react_agent

from .state import AgentState
from .tool_sanitizer import wrap_tools_with_sanitizer

class AutonomousNodes:
    def __init__(self, models: dict, mcp_tools, allowed_dirs: list[str] = None):
        self.models = models
        self.mcp_tools = mcp_tools
        self.allowed_dirs = allowed_dirs or []
        # Prompt-visible dirs: only real project paths (no sandbox /tmp dirs).
        # All paths are realpath-resolved to avoid macOS /tmp vs /private/tmp mismatch.
        self._project_dirs = [
            os.path.realpath(d) for d in self.allowed_dirs
            if '/tmp' not in d
        ]
        # Wrap tools with sanitizer to auto-fix Gemma's type hallucinations
        # (e.g. passing JSON objects where MCP expects raw strings)
        sanitized_tools = wrap_tools_with_sanitizer(self.mcp_tools)
        # We reuse the Phase 08 capability as a localized sub-agent specifically for coding.
        self.coder_subagent = create_react_agent(self.models["coder"], sanitized_tools)

    async def _unload_model(self, model_name: str):
        """Forces Ollama to release the active model from Apple Silicon VRAM."""
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    "http://127.0.0.1:11434/api/generate",
                    json={"model": model_name, "keep_alive": 0},
                    timeout=5.0
                )
        except Exception as e:
            print(f"[warning] Failed to unload model {model_name}: {e}")

    async def plan_node(self, state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
        """
        Generates the implementation plan and the exact test command to verify it.
        """
        objective = state.get("objective", "")
        context = state.get("context", "")
        
        prompt = f"""You are the Lead Architect.
Objective: {objective}
Current Context: {context}

1. Formulate a step-by-step implementation plan. CRITICAL: Explicitly instruct the coder to read the project descriptors (like `go.mod` or `package.json`) first to ensure it uses the correct import paths and module names. Do not hallucinate imports!
2. Determine the exact terminal command to test/lint the result. 
IMPORTANT: The test command is executed in the root of the sandbox runner, NOT your target directory! You MUST explicitly `cd` into the target directory first (e.g. `cd /Users/.../my-app && go build main.go`).
CRITICAL: The sub-agent ONLY has access to filesystem tools. It CANNOT run terminal commands! Therefore, your test command MUST bundle any necessary dependency downloads or environment setups using `&&` (e.g., `cd /path && go mod tidy && go build main.go`).

<SANDBOX_CONSTRAINTS>
You are only permitted to act within these exact allowed directories:
{self._project_dirs}

WARNING: Be extremely careful with spelling when typing absolute paths! Local models sometimes misspell the username (e.g. typing `charleshlan` instead of `charleshsu`). If you misspell the path even slightly, it will severely crash the sandbox with an Access Denied error. COPY THE EXACT PATHS PROVIDED ABOVE.
</SANDBOX_CONSTRAINTS>

Provide your output EXACTLY in this format:
<PLAN>
your detailed plan here
</PLAN>

<TEST_COMMAND>
your test command here
</TEST_COMMAND>
"""
        response = await self.models["planner"].ainvoke([SystemMessage(content="You are a senior planner."), HumanMessage(content=prompt)], config)
        content = response.content
        
        # Explicit Garbage Collection
        await self._unload_model(self.models["planner"].model)
        
        plan_match = re.search(r"<PLAN>(.*?)</PLAN>", content, re.DOTALL)
        cmd_match = re.search(r"<TEST_COMMAND>(.*?)</TEST_COMMAND>", content, re.DOTALL)
        
        plan = plan_match.group(1).strip() if plan_match else content
        test_cmd = cmd_match.group(1).strip() if cmd_match else "echo 'No test command'"
        
        return {
            "plan": plan, 
            "test_specs": test_cmd,
            "retry_count": state.get("retry_count", 0)
        }

    async def coder_node(self, state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
        """
        Uses the tools (via the subagent) to actually implement the code on disk.
        """
        plan = state.get("plan", "")
        reflection = state.get("reflection_strategy", "")
        retry_count = state.get("retry_count", 0)
        
        # Use the pre-filtered project dirs (no sandbox /tmp noise)
        start_dir = self._project_dirs[0] if self._project_dirs else (self.allowed_dirs[0] if self.allowed_dirs else '/tmp')

        prompt = f"""
Implement this plan exactly using your file system tools:

{plan}

<SANDBOX_CONSTRAINTS>
You are ONLY permitted to act within these exact allowed directories:
{self._project_dirs}

CRITICAL PATHING RULE:
All filesystem tools require FULL ABSOLUTE PATHS. You MUST construct absolute paths by strictly prepending the allowed directory exactly as written above! 
For example, to access a folder named 'handler', you MUST use the exact path: '{start_dir}/handler'. Do not use relative paths.

START HERE: First, use `list_directory` on "{start_dir}" to understand the existing project structure.
CRITICAL: If this is a Go or Python project, use `read_text_file` on `go.mod` or `pyproject.toml` to find the EXACT base module name before making ANY changes. DO NOT hallucinate import paths!
DO NOT attempt to access ANY other directory outside these paths! Do NOT explore parent directories or sibling directories of these paths.

WARNING: Be extremely careful with spelling when typing absolute paths! Local models sometimes misspell the username (e.g. typing `charleshlan` instead of `charleshsu`). If you misspell the path even slightly, it will severely crash the sandbox with an Access Denied error. COPY THE EXACT PATHS PROVIDED ABOVE.
</SANDBOX_CONSTRAINTS>

CRITICAL RULES FOR MCP TOOL CALLING:
- By default your Local JSON parser has a hallucination bug! 
- When calling `write_file`, the `content` MUST be a raw unstructured String. DO NOT pass it as a JSON Object!
- If writing a file, you cannot use nested objects. You must stringify them into raw text formatting.
- File writes do NOT automatically create missing parent directories. ALWAYS use the `create_directory` tool for new folders *before* writing files into them.
"""
        if reflection:
             prompt += f"\n\nPREVIOUS ATTEMPT FAILED. Follow this correction strategy:\n{reflection}"
        
        # Invoke the ReAct graph purely as a worker here.
        # It handles all the tool calling loops internally and returns when done.
        #
        # IMPORTANT: We MUST pass the verbatim `config` object exactly as provided
        # by LangGraph. Do not copy or modify it. Manipulating the config (even to append
        # thread_id) strips away hidden OpenTelemetry ContextVars and RunManagers,
        # causing the sub-agent and its tools to fragment into disjointed root traces in Phoenix.
        try:
            result = await self.coder_subagent.ainvoke({"messages": [HumanMessage(content=prompt)]}, config)
            final_message = result["messages"][-1].content
        except Exception as e:
            final_message = f"CRASH: Local model generated invalid tool format and crashed the sub-agent:\n{str(e)}"
            
        # Explicit Garbage Collection
        await self._unload_model(self.models["coder"].model)
        
        return {
            "code_changes": final_message
        }

    async def test_node(self, state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
        """
        Executes the test command locally using subprocess.
        Also performs no-op detection: if the coder sub-agent gave up without 
        actually writing any files, force a failure to trigger reflect→retry.
        """
        tracer = trace.get_tracer("autocoder.test_node")
        test_cmd = state.get("test_specs", "echo 'No tests'")
        code_changes = state.get("code_changes", "")
        plan = state.get("plan", "")
        
        with tracer.start_as_current_span("test_node", attributes={
            "test.command": test_cmd,
            "test.iteration": state.get("iteration", 0),
        }) as span:
            # Fast fail if the coder subagent crashed (e.g. from MCP ToolException formatting issues)
            if "CRASH:" in code_changes:
                span.set_attribute("test.validation_status", "failed")
                span.set_attribute("test.failure_reason", "coder_crash")
                return {
                    "test_output": f"CODE GENERATION CRASHED BEFORE TESTS COULD RUN.\n{code_changes}",
                    "validation_status": "failed"
                }
            
            # No-op detection: if the coder gave up without writing anything
            GIVE_UP_SIGNALS = [
                "i cannot proceed", "i cannot complete", "i cannot fulfill",
                "i'm unable to", "i am unable to", "unable to proceed",
                "i cannot directly", "i do not have", "cannot access",
            ]
            code_lower = code_changes.lower()
            if any(signal in code_lower for signal in GIVE_UP_SIGNALS):
                span.set_attribute("test.validation_status", "failed")
                span.set_attribute("test.failure_reason", "coder_gave_up")
                return {
                    "test_output": f"CODER SUB-AGENT GAVE UP WITHOUT WRITING CODE.\nCoder output: {code_changes[:500]}",
                    "validation_status": "failed"
                }

            # File existence check: extract expected new files from the plan
            expected_files = re.findall(
                r'(?:Create|create|Write|write)\s+(/[^\s,\.\)]+\.(?:go|py|ts|js|java|rs|toml|json|yaml|yml|mod))',
                plan
            )
            missing_files = [f for f in expected_files if not os.path.exists(f)]
            if missing_files:
                missing_list = "\n".join(f"  ✗ {f}" for f in missing_files)
                span.set_attribute("test.validation_status", "failed")
                span.set_attribute("test.failure_reason", "missing_files")
                span.set_attribute("test.missing_files", str(missing_files))
                return {
                    "test_output": f"FILE EXISTENCE CHECK FAILED. The plan expected these files but they were NOT created:\n{missing_list}",
                    "validation_status": "failed"
                }
                
            try:
                result = subprocess.run(
                    test_cmd, shell=True, capture_output=True, text=True, timeout=30
                )
                output = f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
                passed = (result.returncode == 0)
                span.set_attribute("test.returncode", result.returncode)
            except subprocess.TimeoutExpired:
                output = "TEST COMMAND TIMED OUT AFTER 30 SECONDS."
                passed = False
                span.set_attribute("test.failure_reason", "timeout")
            except Exception as e:
                output = f"TEST EXECUTION ERROR: {str(e)}"
                passed = False
                span.set_attribute("test.failure_reason", str(e))
                
            status = "passed" if passed else "failed"
            span.set_attribute("test.validation_status", status)
            span.set_attribute("test.output", output[:1000])
            return {
                "test_output": output,
                "validation_status": status
            }
        
    async def reflect_node(self, state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
        """
        If tests fail, analyzes the error and formulates a reflection strategy for the next Coder attempt.
        """
        test_output = state.get("test_output", "")
        retry_count = state.get("retry_count", 0)
        
        prompt = f"""The previous code execution failed tests. 
Test Output:
{test_output}

<SANDBOX_CONSTRAINTS>
The sub-agent is ONLY permitted to act within these exact allowed directories:
{self._project_dirs}
If the error says "Access denied - path outside allowed directories", the fix is to ONLY use paths within the directories listed above. Do NOT suggest exploring parent or sibling directories.
</SANDBOX_CONSTRAINTS>

Write a brief, specific strategy to fix these errors. Do not write the code itself, just the strategy."""
        
        response = await self.models["evaluator"].ainvoke([HumanMessage(content=prompt)], config)
        
        # Explicit Garbage Collection
        await self._unload_model(self.models["evaluator"].model)
        
        return {
            "reflection_strategy": response.content,
            "retry_count": retry_count + 1
        }

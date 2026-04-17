"""
Tool Argument Sanitizer for MCP Tools.

Local models (e.g. Gemma 4) frequently hallucinate tool argument types,
passing JSON objects where the MCP schema expects a raw string.
This middleware wraps MCP tools to auto-fix these mismatches BEFORE
they hit the MCP server, preventing -32602 validation crashes.

Additionally, this layer provides:
- Auto-mkdir: `write_file` calls automatically create parent directories.
- Error-to-feedback: Exceptions are caught and returned as strings to
  the model instead of crashing the sub-agent.
"""
import json
import os
from typing import Any
from langchain_core.tools import BaseTool
from langchain_core.runnables import RunnableConfig


# Fields that the MCP filesystem server expects as plain strings,
# but that local models frequently pass as dicts/lists.
STRING_FIELDS = {"content", "newText", "oldText"}


def _sanitize_args(tool_name: str, args: dict) -> dict:
    """
    Deep-sanitize tool call arguments.
    Converts any STRING_FIELDS that arrived as non-str into json.dumps.
    """
    sanitized = dict(args)
    for field in STRING_FIELDS:
        if field in sanitized and not isinstance(sanitized[field], str):
            original_type = type(sanitized[field]).__name__
            sanitized[field] = json.dumps(sanitized[field], indent=2)
            print(f"  [sanitizer] ⚠️  Auto-serialized `{tool_name}.{field}` from {original_type} → str ({len(sanitized[field])} chars)")
    
    # Handle edits array (edit_file tool) where each edit has oldText/newText
    if "edits" in sanitized and isinstance(sanitized["edits"], list):
        for i, edit in enumerate(sanitized["edits"]):
            if isinstance(edit, dict):
                for field in ("oldText", "newText", "path"):
                    if field in edit and not isinstance(edit[field], str):
                        edit[field] = json.dumps(edit[field], indent=2)

    # Dynamically auto-correct hallucinated usernames in paths based on the host OS.
    # E.g., translates '/Users/charleshsh/...' -> '/Users/<actual_user>/...'
    home_dir = os.path.expanduser('~')
    home_parts = home_dir.split(os.sep)
    if len(home_parts) >= 3 and home_parts[1] == 'Users':
        actual_user = home_parts[2]
        for k, v in sanitized.items():
            if isinstance(v, str) and v.startswith("/Users/"):
                path_parts = v.split(os.sep)
                if len(path_parts) >= 3 and path_parts[1] == 'Users':
                    hallucinated_user = path_parts[2]
                    if hallucinated_user != actual_user:
                        path_parts[2] = actual_user
                        corrected = os.sep.join(path_parts)
                        print(f"  [sanitizer] 🪄  Dynamic auto-corrected hallucinated username: '{hallucinated_user}' → '{actual_user}'")
                        sanitized[k] = corrected

    return sanitized


class SanitizedMCPTool(BaseTool):
    """
    A wrapper around an MCP tool that sanitizes arguments before invocation.
    Prevents MCP -32602 errors caused by local model type hallucinations.
    
    Also provides:
    - Auto-mkdir for write_file (creates parent dirs automatically)
    - Error-to-feedback (catches exceptions, returns them as strings)
    """
    name: str = ""
    description: str = ""
    inner_tool: Any = None
    _mkdir_tool: Any = None  # Reference to create_directory tool for auto-mkdir
    
    class Config:
        arbitrary_types_allowed = True

    def __init__(self, tool: BaseTool, mkdir_tool: BaseTool = None):
        super().__init__(
            name=tool.name,
            description=tool.description,
            inner_tool=tool,
        )
        self._mkdir_tool = mkdir_tool
        # Copy the args_schema so LangChain/LangGraph sees the same interface
        self.args_schema = tool.args_schema

    async def _auto_mkdir(self, path: str, config: RunnableConfig = None):
        """Auto-create parent directory for a file path using the MCP create_directory tool."""
        if self._mkdir_tool and path:
            parent = os.path.dirname(path)
            # Check if directory already exists locally to avoid spamming MCP traces and console
            if parent and parent != '/' and not os.path.exists(parent):
                try:
                    print(f"  [sanitizer] 📁 Auto-creating directory: {parent}")
                    await self._mkdir_tool.ainvoke({"path": parent}, config=config)
                except Exception as e:
                    print(f"  [sanitizer] ⚠️  Auto-mkdir failed (non-fatal): {e}")

    def _run(self, *args, config: RunnableConfig = None, **kwargs):
        sanitized = _sanitize_args(self.name, kwargs)
        try:
            return self.inner_tool.invoke(sanitized, config=config)
        except Exception as e:
            error_msg = f"Tool '{self.name}' failed: {str(e)}"
            print(f"  [sanitizer] ❌ {error_msg}")
            return error_msg

    async def _arun(self, *args, config: RunnableConfig = None, **kwargs):
        sanitized = _sanitize_args(self.name, kwargs)
        
        # Auto-create parent directories for write_file
        if self.name == "write_file" and "path" in sanitized:
            await self._auto_mkdir(sanitized["path"], config)
        
        try:
            return await self.inner_tool.ainvoke(sanitized, config=config)
        except Exception as e:
            error_msg = f"Tool '{self.name}' failed: {str(e)}"
            print(f"  [sanitizer] ❌ {error_msg}")
            return error_msg


def wrap_tools_with_sanitizer(tools: list[BaseTool]) -> list[BaseTool]:
    """
    Wraps a list of MCP tools with the argument sanitizer.
    - Tools with string fields get auto-serialization.
    - write_file gets auto-mkdir.
    - All wrapped tools get error-to-feedback protection.
    """
    # Find the create_directory tool for auto-mkdir injection
    mkdir_tool = None
    for tool in tools:
        if tool.name == "create_directory":
            mkdir_tool = tool
            break

    # Tools known to have string-type arguments that models hallucinate as objects
    TOOLS_TO_WRAP = {"write_file", "edit_file", "read_file", "read_text_file",
                     "list_directory", "create_directory", "search_files",
                     "directory_tree", "move_file", "get_file_info"}
    
    wrapped = []
    for tool in tools:
        if tool.name in TOOLS_TO_WRAP:
            wrapped.append(SanitizedMCPTool(tool, mkdir_tool=mkdir_tool))
        else:
            wrapped.append(tool)
    
    return wrapped


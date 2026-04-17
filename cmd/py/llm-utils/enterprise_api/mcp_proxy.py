import json
import contextlib
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_core.tools import BaseTool

class MCPManager:
    """
    Manages connections to standard MCP Servers defined in mcp_servers.json.
    Exposes them as LangChain BaseTool objects.
    """
    def __init__(self, config_path: str, extra_allowed_dirs: list[str] | None = None):
        self.config_path = config_path
        self.extra_allowed_dirs = extra_allowed_dirs or []
        self._tools: list[BaseTool] = []
        self.stack = contextlib.AsyncExitStack()
        
    async def initialize(self):
        with open(self.config_path, "r") as f:
            config = json.load(f)
            
        print(f"🔌 Initializing MCP Proxy with config: {self.config_path}")
        
        for name, server_config in config.get("mcpServers", {}).items():
            env = server_config.get("env", None)
            if env is None:
                env = os.environ.copy() # Inherit fully to ensure PATH works for npx
            else:
                merged_env = os.environ.copy()
                merged_env.update(env)
                env = merged_env

            args = list(server_config["args"])
            
            # Dynamically inject extra allowed directories into the MCP filesystem server.
            # The @modelcontextprotocol/server-filesystem accepts multiple dir args.
            # CRITICAL: Resolve symlinks via realpath BEFORE passing to the server.
            # On macOS, /tmp -> /private/tmp. The server will resolve paths internally,
            # so we must pass the canonical form to avoid access-denied mismatches.
            if self.extra_allowed_dirs and "@modelcontextprotocol/server-filesystem" in args:
                for d in self.extra_allowed_dirs:
                    resolved = os.path.realpath(d)
                    if not os.path.exists(resolved):
                        print(f"  ⚠️ Skipping invalid sandbox directory (does not exist): {resolved}")
                        continue
                    if resolved not in args:
                        args.append(resolved)
                        print(f"  📂 Added allowed directory: {resolved}")

            server_params = StdioServerParameters(
                command=server_config["command"],
                args=args,
                env=env
            )
            
            stdio_transport = await self.stack.enter_async_context(stdio_client(server_params))
            read, write = stdio_transport
            session = await self.stack.enter_async_context(ClientSession(read, write))
            await session.initialize()
            
            tools = await load_mcp_tools(session)
            print(f"✅ [{name}] MCP Server initialized. Loaded {len(tools)} tools.")
            self._tools.extend(tools)
            
    def get_tools(self) -> list[BaseTool]:
        return self._tools
        
    async def cleanup(self):
        await self.stack.aclose()
        print("🔌 MCP Proxy Shutdown.")


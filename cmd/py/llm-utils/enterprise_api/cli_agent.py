import os
from rich.console import Console
from rich.panel import Panel
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool

from .mcp_proxy import MCPManager

DB_URI = "postgresql://postgres:postgres@127.0.0.1:5432/langgraph?sslmode=disable"
console = Console()

class CLIAgent:
    def __init__(self, mcp_config_path: str):
        self.mcp_manager = MCPManager(mcp_config_path)
        # We use gemma4:26b for high performance native tool calling
        self.llm = ChatOllama(model="gemma4:26b", temperature=0)

    async def initialize(self):
        await self.mcp_manager.initialize()
        
    async def run(self, thread_id: str, prompt: str):
        tools = self.mcp_manager.get_tools()
        if not tools:
            console.print("[yellow]Warning: No MCP Tools loaded. Agent has no system access.[/yellow]")
            
        console.print(f"[dim]Binding {len(tools)} tools...[/dim]")
        
        async with AsyncConnectionPool(
            conninfo=DB_URI,
            max_size=20,
            kwargs={"autocommit": True}
        ) as pool:
            checkpointer = AsyncPostgresSaver(pool)
            await checkpointer.setup()
            
            app = create_react_agent(self.llm, tools, checkpointer=checkpointer)
            config = {"configurable": {"thread_id": thread_id}}
            
            console.print(Panel(prompt, title="[cyan]User Objective", border_style="cyan"))
            
            async for step in app.astream(
                {"messages": [("user", prompt)]},
                config,
                stream_mode="updates"
            ):
                for node, state in step.items():
                    if node == "agent":
                        # Agent has made a decision
                        ai_msg = state.get("messages")[-1]
                        if getattr(ai_msg, "tool_calls", None):
                            for tc in ai_msg.tool_calls:
                                console.print(f"[bold magenta]🛠️  Plan Tool:[/bold magenta] {tc['name']}")
                                console.print(f"[dim]{tc['args']}[/dim]")
                        elif ai_msg.content:
                            console.print(Panel(ai_msg.content, title="[blue]Agent Response", border_style="blue"))
                            
                    elif node == "tools":
                        # Tool execution results
                        tool_msgs = state.get("messages", [])
                        for tm in tool_msgs:
                            console.print(f"[bold green]✅ Tool Executed:[/bold green] {tm.name}")
                            # truncate content to avoid giant terminal spam
                            content = tm.content
                            if len(content) > 500:
                                content = content[:500] + "\n...[truncated]"
                            console.print(f"[dim]{content}[/dim]\n")

    async def cleanup(self):
        await self.mcp_manager.cleanup()

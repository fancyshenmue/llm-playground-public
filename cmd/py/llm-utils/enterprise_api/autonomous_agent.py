import os
import json
import yaml

config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yaml")
if not os.path.exists(config_path):
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yaml.example")

with open(config_path, "r") as f:
    _cfg = yaml.safe_load(f) or {}

autocoder_cfg = _cfg.get("autocoder") or {}
PLANNER_MODEL = autocoder_cfg.get("planner_model", "gemma4:31b")
CODER_MODEL = autocoder_cfg.get("coder_model", "gemma4:26b")
EVALUATOR_MODEL = autocoder_cfg.get("evaluator_model", "qwen3.5:35b-a3b")

obs_cfg = _cfg.get("observability") or {}
OBS_BACKEND = obs_cfg.get("backend", "none") if isinstance(obs_cfg, dict) else "none"

from rich.console import Console
from rich.panel import Panel
from rich.markup import escape
from rich.markdown import Markdown
from langchain_ollama import ChatOllama
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool
from langfuse.langchain import CallbackHandler

from .mcp_proxy import MCPManager
from .autonomous.graph import build_autonomous_graph

DB_URI = "postgresql://postgres:postgres@127.0.0.1:5432/langgraph?sslmode=disable"
console = Console()

class AutonomousAgent:
    def __init__(self, mcp_config_path: str, extra_allowed_dirs: list[str] | None = None):
        self.extra_allowed_dirs = extra_allowed_dirs or []
        self.mcp_manager = MCPManager(mcp_config_path, extra_allowed_dirs=self.extra_allowed_dirs)
        # Using Heterogeneous Model Architecture for autonomous loop
        self.models = {
            "planner": ChatOllama(model=PLANNER_MODEL, temperature=0),
            "coder": ChatOllama(model=CODER_MODEL, temperature=0),
            "evaluator": ChatOllama(model=EVALUATOR_MODEL, temperature=0)
        }

    async def initialize(self):
        # Prevent VRAM thrashing on Apple Silicon: Flush any active models before starting
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                # Flush the standard known models to ensure clean slate
                for m in [PLANNER_MODEL, CODER_MODEL, EVALUATOR_MODEL]:
                    await client.post("http://127.0.0.1:11434/api/generate", json={"model": m, "keep_alive": 0}, timeout=2.0)
                console.print("[dim]♻️ VRAM pre-flushed.[/dim]")
        except Exception:
            pass

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

            # Construct our custom Phase 09 State Machine
            builder = build_autonomous_graph(self.models, tools, self.extra_allowed_dirs)
            app = builder.compile(checkpointer=checkpointer)

            config = {"configurable": {"thread_id": thread_id}}
            if OBS_BACKEND in ["langfuse", "both"]:
                try:
                    import os
                    lf_cfg = obs_cfg.get("langfuse", {})
                    if lf_cfg.get("secret_key"): os.environ["LANGFUSE_SECRET_KEY"] = lf_cfg.get("secret_key")
                    if lf_cfg.get("public_key"): os.environ["LANGFUSE_PUBLIC_KEY"] = lf_cfg.get("public_key")
                    if lf_cfg.get("host"): os.environ["LANGFUSE_HOST"] = lf_cfg.get("host")
                    
                    langfuse_handler = CallbackHandler()
                    config["callbacks"] = [langfuse_handler]
                    config.setdefault("metadata", {})["langfuse_session_id"] = thread_id
                except Exception as e:
                    console.print(f"[red]⚠️ Langfuse Telemetry failed: {e}[/red]")

            console.print(Panel(escape(prompt), title="[cyan]Autonomous Initialization[/cyan]", border_style="cyan"))

            # Stream custom node events cleanly
            async for step in app.astream(
                {"objective": prompt},
                config,
                stream_mode="updates"
            ):
                for node, state in step.items():
                    if node == "plan_node":
                        console.print(Panel(Markdown(state.get("plan", "")), title="[blue]📋 Implementation Plan[/blue]"))
                        console.print(f"[dim]Test Target Command: {escape(state.get('test_specs', ''))}[/dim]")
                    elif node == "coder_node":
                        console.print(f"[bold magenta]💻 Code Node Executed[/bold magenta]")
                    elif node == "test_node":
                        status_color = "green" if state.get("validation_status") == "passed" else "red"
                        console.print(Panel(escape(state.get("test_output", "")), title=f"[{status_color}]🧪 Test Execution: {state.get('validation_status').upper()}[/{status_color}]"))
                    elif node == "reflect_node":
                        console.print(Panel(Markdown(state.get("reflection_strategy", "")), title="[yellow]🤔 Reflection (Fixing Errors)[/yellow]"))

    async def astream_run(self, thread_id: str, prompt: str):
        tools = self.mcp_manager.get_tools()
        if not tools:
            yield f"data: {json.dumps({'type': 'status', 'message': 'Warning: No MCP Tools loaded.'})}\n\n"

        yield f"data: {json.dumps({'type': 'status', 'message': f'Binding {len(tools)} tools...'})}\n\n"

        async with AsyncConnectionPool(
            conninfo=DB_URI,
            max_size=20,
            kwargs={"autocommit": True}
        ) as pool:
            checkpointer = AsyncPostgresSaver(pool)
            await checkpointer.setup()

            builder = build_autonomous_graph(self.models, tools, self.extra_allowed_dirs)
            app = builder.compile(checkpointer=checkpointer)

            config = {"configurable": {"thread_id": thread_id}}
            if OBS_BACKEND in ["langfuse", "both"]:
                try:
                    import os
                    lf_cfg = obs_cfg.get("langfuse", {})
                    if lf_cfg.get("secret_key"): os.environ["LANGFUSE_SECRET_KEY"] = lf_cfg.get("secret_key")
                    if lf_cfg.get("public_key"): os.environ["LANGFUSE_PUBLIC_KEY"] = lf_cfg.get("public_key")
                    if lf_cfg.get("host"): os.environ["LANGFUSE_HOST"] = lf_cfg.get("host")
                    
                    langfuse_handler = CallbackHandler()
                    config["callbacks"] = [langfuse_handler]
                    config.setdefault("metadata", {})["langfuse_session_id"] = thread_id
                except Exception as e:
                    yield f"data: {json.dumps({'type': 'status', 'message': f'Warning: Langfuse Init Failed - {str(e)}'})}\n\n"

            yield f"data: {json.dumps({'type': 'status', 'message': 'Autonomous Initialization'})}\n\n"

            iterations = 0
            async for step in app.astream(
                {"objective": prompt},
                config,
                stream_mode="updates"
            ):
                iterations += 1
                for node, state in step.items():
                    if node == "plan_node":
                        yield f"data: {json.dumps({'type': 'node_update', 'node': node, 'iterations': iterations, 'plan': state.get('plan', ''), 'test_specs': state.get('test_specs', '')})}\n\n"
                    elif node == "coder_node":
                        yield f"data: {json.dumps({'type': 'node_update', 'node': node, 'iterations': iterations})}\n\n"
                    elif node == "test_node":
                        err = state.get("test_output", "") if state.get("validation_status") != "passed" else "PASS"
                        yield f"data: {json.dumps({'type': 'node_update', 'node': node, 'iterations': iterations, 'lint_errors': err, 'validation_status': state.get('validation_status', 'unknown')})}\n\n"
                    elif node == "reflect_node":
                        yield f"data: {json.dumps({'type': 'node_update', 'node': node, 'iterations': iterations, 'reflection_strategy': state.get('reflection_strategy', '')})}\n\n"

            final_state = await app.aget_state(config)
            final_code = final_state.values.get("code", "")
            yield f"data: {json.dumps({'type': 'finished', 'state': {'code': final_code}})}\n\n"

    async def cleanup(self):
        await self.mcp_manager.cleanup()

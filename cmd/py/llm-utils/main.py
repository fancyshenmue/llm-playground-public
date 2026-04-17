import typer
import os
import sys
import warnings

# Suppress Pydantic V2 protected namespace warnings caused by LangChain's internal use of `model_name`
warnings.filterwarnings("ignore", message='Field "model_name" has conflict with protected namespace "model_".', category=UserWarning)

# Add current directory to path for command imports
sys.path.append(os.path.dirname(__file__))
# Add project root to path for internal imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from commands.system import check_gpu
from commands.vision import auto_choose_best, compare_epochs, analyze_and_store

from commands.generation import generate_training_data, generate_final_golden_ratio, weight_sweep, simple_gen, hybrid_quant_gen
from commands.data import convert_parquet, view_parquet, analyze_tokens
from commands.evaluation import runner, langchain_runner

app = typer.Typer(
    name="llm-py-utils",
    help="Python utilities for the LLM Playground",
    add_completion=False,
    rich_markup_mode="rich"
)

@app.command()
def check_gpu_status():
    """
    Check if CUDA is available and display GPU information.
    """
    check_gpu.check_cuda()

@app.command()
def choose_best():
    """
    Automatically choose the best image from a weight sweep using LLM vision.
    """
    auto_choose_best.main()

@app.command()
def compare(
    image_a: str = compare_epochs.IMAGE_A,
    image_b: str = compare_epochs.IMAGE_B
):
    """
    Compare two different images/epochs using LLM vision.
    """
    compare_epochs.compare_images(image_a, image_b)

@app.command()
def gen_data(
    topic: str = "beauty girl",
    total: int = 30,
    output_dir: str = None
):
    """
    Generate training data (images + captions) using Forge and Ollama.
    """
    generate_training_data.main(topic=topic, total=total, output_dir=output_dir)

@app.command()
def gen_golden(
    concept: str = None,
    weight: float = 0.8,
    lora: str = "FancyStyle_v1-000009"
):
    """
    Generate the final 'Golden Ratio' image using expanded prominence and Forge.
    """
    generate_final_golden_ratio.main(concept=concept, weight=weight, lora=lora)

@app.command()
def analyze(image_path: str = None):
    """
    Analyze an image using LLM vision and store result in AnythingLLM.
    """
    analyze_and_store.main(image_path)

@app.command()
def sweep(concept: str = None, lora: str = "FancyStyle_v1-000009"):
    """
    Perform a weight sweep for a LoRA.
    """
    weight_sweep.main(concept, lora)

@app.command()
def gen(concept: str):
    """
    Generate a simple image from a concept.
    """
    simple_gen.generate_image(concept)

@app.command()
def quant(
    inputs: list[str],
    model: str = "deepseek-r1:32b",
    limit: int = 50,
    output: str = "market_analysis.md"
):
    """
    Perform hybrid quant analysis on CSV market data.
    """
    hybrid_quant_gen.main(inputs, model, limit, output)

@app.command()
def convert_dataset(
    input_dir: str = typer.Option(..., "--input", "-i", help="Input directory containing code files"),
    output_dir: str = typer.Option(..., "--output", "-o", help="Output directory for parquet files"),
    extension: str = typer.Option("go", "--ext", "-e", help="File extension to scan"),
    chunk_size: int = typer.Option(10000, "--chunk", "-c", help="Files per chunk"),
    repo_name: str = typer.Option("custom-repo", "--repo", "-r", help="Repo name tag"),
    prefix: str = typer.Option("train", "--prefix", "-p", help="Filename prefix")
):
    """
    Convert a directory of code files into Hugging Face compatible Parquet shards.
    """
    convert_parquet.convert_to_parquet(input_dir, output_dir, extension, chunk_size, repo_name, prefix)

@app.command()
def view_dataset(
    file_path: str = typer.Argument(..., help="Path to the parquet file"),
    head: int = typer.Option(5, "--head", "-n", help="Number of rows to show"),
    full: bool = typer.Option(False, "--full", "-f", help="Show full content")
):
    """
    Visualize a Parquet file in the terminal.
    """
    view_parquet.view_parquet(file_path, head, full)

@app.command()
def analyze_dataset(
    file_path: str = typer.Argument(..., help="Path to parquet file(s)"),
    model: str = typer.Option("Qwen/Qwen2.5-Coder-32B-Instruct", "--model", "-m", help="HF Model ID"),
    sample: int = typer.Option(1000, "--sample", "-s", help="Sample size per file")
):
    """
    Analyze token length distribution to verify sequence_len settings.
    """
    analyze_tokens.analyze_tokens(file_path, model, sample)


@app.command()
def evaluate(
    model: str = typer.Option(None, "--model", "-m", help="Ollama model name"),
    models: str = typer.Option(None, "--models", help="Comma-separated model names for A/B testing"),
    eval_set: str = typer.Option(None, "--file", "-f", help="Path to eval_set.json"),
    judge: str = typer.Option(None, "--judge", "-j", help="Model to use as LLM-as-a-Judge")
):
    """
    Run evaluation suite against models and log results to Arize Phoenix.
    """
    runner.main(model=model, eval_set=eval_set, split_models=models, judge=judge)

@app.command()
def eval_langchain(
    model: str = typer.Option("gemma4:26b", "--model", "-m", help="Ollama model name")
):
    """
    Run LangChain integration suite against models and log to Arize Phoenix.
    """
    langchain_runner.main(model)

@app.command()
def benchmark(
    models: str = typer.Option("gemma4:31b,gemma4:26b", "--models", "-m", help="Comma-separated models to evaluate")
):
    """
    Run hardware and quality edge-case benchmarks for Ollama parameters.
    """
    from commands.evaluation import benchmark as benchmark_module
    benchmark_module.main(models)

@app.command()
def agent(
    task: str = typer.Argument(..., help="The objective the agent should accomplish"),
    mcp_config: str = typer.Option(None, help="Path to MCP servers config")
):
    """
    Start the ReAct autonomous agent with full Model Context Protocol (MCP) tool support.
    """
    import asyncio
    import uuid
    from enterprise_api.cli_agent import CLIAgent
    
    # Initialize Arize Phoenix OpenTelemetry tracing dynamically
    import yaml
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    obs_backend = "none"
    try:
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                cfg = yaml.safe_load(f) or {}
                obs_backend = cfg.get("observability", {}).get("backend", "none")
    except Exception:
        pass

    if obs_backend in ["phoenix", "both"]:
        try:
            from phoenix.otel import register
            from openinference.instrumentation.langchain import LangChainInstrumentor
            register(
                project_name="langgraph-mcp-agent",
                endpoint="http://127.0.0.1:16006/v1/traces"
            )
            LangChainInstrumentor().instrument()
            print("🔭 Phoenix Telemetry activated: Tracing MCP calls.")
        except Exception as e:
            print(f"⚠️ Phoenix Telemetry initialization failed: {e}")

    if not mcp_config:
        mcp_config = os.path.join(os.path.dirname(__file__), "enterprise_api", "mcp_servers.json")

    thread_id = str(uuid.uuid4())
    ai_agent = CLIAgent(mcp_config)
    
    async def _run():
        await ai_agent.initialize()
        try:
            await ai_agent.run(thread_id, task)
        finally:
            await ai_agent.cleanup()
            
    asyncio.run(_run())

@app.command()
def autonomous(
    task: str = typer.Argument(None, help="The objective the autonomous coder should accomplish"),
    mcp_config: str = typer.Option(None, help="Path to MCP servers config"),
    dir: list[str] = typer.Option([], "--dir", "-d", help="Project directories the agent is allowed to access (repeatable, primary)"),
    work_dir: list[str] = typer.Option([], "--work-dir", "-w", help="[Deprecated alias for --dir] Extra directories (repeatable)")
):
    """
    [Phase 09] Start the fully autonomous closed-loop coding agent (Plan -> Code -> Test -> Reflect -> Commit).
    """
    import asyncio
    import uuid
    import re as _re
    from enterprise_api.autonomous_agent import AutonomousAgent
    
    # Initialize Arize Phoenix OpenTelemetry tracing dynamically
    import yaml
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    obs_backend = "none"
    try:
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                cfg = yaml.safe_load(f) or {}
                obs_backend = cfg.get("observability", {}).get("backend", "none")
    except Exception:
        pass

    if obs_backend in ["phoenix", "both"]:
        try:
            from phoenix.otel import register
            from openinference.instrumentation.langchain import LangChainInstrumentor
            register(
                project_name="langgraph-mcp-autocoder",
                endpoint="http://127.0.0.1:16006/v1/traces"
            )
            LangChainInstrumentor().instrument()
            print("🔭 Phoenix Telemetry activated: Tracing Phase 09 Auto-Coder.")
        except Exception as e:
            print(f"⚠️ Phoenix Telemetry initialization failed: {e}")

    is_repl_mode = (task is None)
    # Merge --dir and --work-dir, realpath-resolve all for robustness
    cli_dirs = dir + work_dir
    global_extracted_dirs = set()
    for d in cli_dirs:
        expanded = os.path.expanduser(d)
        resolved = os.path.realpath(expanded)
        global_extracted_dirs.add(resolved)
    persistent_thread_id = str(uuid.uuid4())

    if not mcp_config:
        mcp_config = os.path.join(os.path.dirname(__file__), "enterprise_api", "mcp_servers.json")

    if is_repl_mode:
        from prompt_toolkit import PromptSession
        from prompt_toolkit.styles import Style
        from prompt_toolkit.formatted_text import HTML
        from prompt_toolkit.key_binding import KeyBindings
        from prompt_toolkit.filters import has_focus
        from prompt_toolkit.history import FileHistory
        
        style = Style.from_dict({
            'prompt': '#a855f7 bold', # purple-ish
            'bottom-toolbar': '#4b5563 bg:#1f2937', # dark grey on darker grey
        })
        
        kb = KeyBindings()

        @kb.add('enter', filter=has_focus('DEFAULT_BUFFER'))
        def _(event):
            event.current_buffer.validate_and_handle()
        @kb.add('escape', 'enter', filter=has_focus('DEFAULT_BUFFER'))
        def _(event):
            event.current_buffer.insert_text('\n')
            
        history_file = os.path.expanduser('~/.autocoder_history')
        session = PromptSession(key_bindings=kb, history=FileHistory(history_file))
        
        def bottom_toolbar():
            return " ⌨️  Press [Enter] submit • [Alt]+[Enter] newline • [↑]/[Ctrl+R] history "

    async def _run():
        while True:
            current_task = task
            if is_repl_mode:
                try:
                    current_task = await session.prompt_async(
                        "❯ ", 
                        multiline=True, 
                        style=style,
                        bottom_toolbar=bottom_toolbar
                    )
                    if not current_task.strip():
                        continue
                    if current_task.strip().lower() in ['exit', 'quit']:
                        print("Goodbye! 👋")
                        break
                except (KeyboardInterrupt, EOFError):
                    print("\nGoodbye! 👋")
                    break

            # Auto-extract absolute paths from the task prompt so the agent can access them.
            # Supports paths preceded by whitespace, backticks, or quotes (e.g. `/path/to/dir`)
            for match in _re.findall(r'(?:^|[\s`\'"])(/[^\s\)\(`\'"]+)', current_task):
                candidate = match.rstrip("/")
                raw_candidate = os.path.expanduser(candidate)
                real_candidate = os.path.realpath(raw_candidate)
                for c in [raw_candidate, real_candidate]:
                    if "." in os.path.basename(c):
                        c = os.path.dirname(c)
                    if c and c != "/":
                        global_extracted_dirs.add(c) 
            
            all_extra_dirs = list(global_extracted_dirs)
            
            # Interactive permission approval
            cancelled = False
            if is_repl_mode:
                print(f"\n\033[36m📂 Sandbox directories:\033[0m")
                for d in all_extra_dirs:
                    print(f"   \033[33m→\033[0m {d}")
                while True:
                    approval = input("\033[36m🔐 Approve? [Y/enter=yes, +/path/to/add, n=cancel]: \033[0m").strip()
                    if approval.lower() in ['', 'y', 'yes']:
                        break
                    elif approval.lower() in ['n', 'no']:
                        print("❌ Cancelled.")
                        cancelled = True
                        break
                    elif approval.startswith('+') or approval.startswith('/'):
                        raw_dir = approval.lstrip('+').strip()
                        raw_dir = os.path.expanduser(raw_dir)
                        real_dir = os.path.realpath(raw_dir)
                        if raw_dir:
                            global_extracted_dirs.add(raw_dir)
                        if real_dir:
                            global_extracted_dirs.add(real_dir)
                        if raw_dir or real_dir:
                            all_extra_dirs = list(global_extracted_dirs)
                            print(f"   \033[32m✓ Added:\033[0m {real_dir}")
                        continue
                    else:
                        print("   \033[31m?\033[0m Enter y, n, or +/path/to/dir")
                        continue
            else:
                if all_extra_dirs:
                    print(f"📂 Active work directories: {all_extra_dirs}")

            if cancelled:
                continue

            # Create ephemeral sandbox directory for potential future use (e.g. temp files).
            # NOTE: We intentionally do NOT add this to all_extra_dirs / MCP server args.
            # The agent works directly on the project directory. Including the sandbox dir
            # in MCP server args pollutes tool descriptions, causing the local model to
            # treat the empty sandbox as the project root and loop infinitely.
            short_id = persistent_thread_id[:8]
            isolated_sandbox = f"/tmp/autocoder_{short_id}"
            os.makedirs(isolated_sandbox, exist_ok=True)
                
            ai_agent = AutonomousAgent(mcp_config, extra_allowed_dirs=all_extra_dirs)
            
            await ai_agent.initialize()
            try:
                await ai_agent.run(persistent_thread_id, current_task)
            finally:
                await ai_agent.cleanup()

            if not is_repl_mode:
                break # Complete after one run if initiated via CLI argument

    asyncio.run(_run())

if __name__ == "__main__":
    app()

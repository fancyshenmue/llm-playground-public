import pandas as pd
import typer
import numpy as np
from rich.console import Console
from rich.table import Table
from rich.progress import track
from transformers import AutoTokenizer
from pathlib import Path

console = Console()

def analyze_tokens(
    file_path: str = typer.Argument(..., help="Path to the parquet file (or glob pattern)"),
    model_id: str = typer.Option("Qwen/Qwen2.5-Coder-32B-Instruct", "--model", "-m", help="Hugging Face model ID for tokenizer"),
    sample_size: int = typer.Option(1000, "--sample", "-s", help="Number of rows to sample per file"),
):
    """
    Analyze the token length distribution of a dataset using a specific tokenizer.
    """
    files = list(Path(".").glob(file_path)) if "*" in file_path else [Path(file_path)]

    if not files:
        console.print(f"[bold red]Error:[/bold red] No files found matching {file_path}")
        raise typer.Exit(code=1)

    console.print(f"[bold blue]Loading Tokenizer:[/bold blue] {model_id} ...")
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
    except Exception as e:
        console.print(f"[red]Failed to load tokenizer: {e}[/red]")
        raise typer.Exit(code=1)

    lengths = []

    for p in track(files, description="Analyzing files..."):
        try:
            df = pd.read_parquet(p)
            # Sample if too large
            if len(df) > sample_size:
                df = df.sample(sample_size)

            for content in df["content"]:
                if not isinstance(content, str): continue
                # Basic tokenization (just counting input_ids)
                tokens = tokenizer(content, return_tensors="np")["input_ids"][0]
                lengths.append(len(tokens))

        except Exception as e:
            console.print(f"[yellow]Skipping {p}: {e}[/yellow]")
            continue

    if not lengths:
        console.print("[red]No data found to analyze.[/red]")
        return

    lengths = np.array(lengths)

    # Calculate statistics
    stats = {
        "Count": len(lengths),
        "Min": np.min(lengths),
        "Max": np.max(lengths),
        "Mean": np.mean(lengths),
        "Median (P50)": np.median(lengths),
        "P90": np.percentile(lengths, 90),
        "P95": np.percentile(lengths, 95),
        "P99": np.percentile(lengths, 99),
        "> 4096": np.sum(lengths > 4096),
        "> 8192": np.sum(lengths > 8192),
        "> 16384": np.sum(lengths > 16384),
        "> 32768": np.sum(lengths > 32768),
    }

    # Display results
    table = Table(title=f"Token Length Analysis ({model_id})")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")

    for k, v in stats.items():
        if isinstance(v, (int, np.integer)):
            val_str = f"{v:,}"
        elif isinstance(v, float):
            val_str = f"{v:,.2f}"
        else:
            val_str = str(v)

        # Add percentage for count metrics
        if k.startswith(">"):
            pct = (v / len(lengths)) * 100
            val_str += f" ({pct:.2f}%)"

        table.add_row(k, val_str)

    console.print(table)

    # Recommendation
    p95 = stats["P95"]
    if p95 < 4096:
        rec = "4096 (Safe)"
    elif p95 < 8192:
        rec = "8192 (Recommended)"
    else:
        rec = "16384+ (Heavy VRAM usage)"

    console.print(f"\n[bold green]Recommended Sequence Length:[/bold green] {rec}")

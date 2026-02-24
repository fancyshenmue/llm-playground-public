import os
import glob
import pandas as pd
import typer
from rich.console import Console
from rich.progress import track
from pathlib import Path

console = Console()

def convert_to_parquet(
    input_dir: str = typer.Option(..., "--input", "-i", help="Input directory containing code files"),
    output_dir: str = typer.Option(..., "--output", "-o", help="Output directory for parquet files"),
    extension: str = typer.Option("go", "--ext", "-e", help="File extension to scan (e.g., go, py, js)"),
    chunk_size: int = typer.Option(10000, "--chunk", "-c", help="Number of files per parquet chunk"),
    repo_name: str = typer.Option("custom-repo", "--repo", "-r", help="Repository name tag for the dataset"),
    prefix: str = typer.Option("train", "--prefix", "-p", help="Filename prefix (e.g., 'train', 'test', 'project-a')")
):
    """
    Convert a directory of code files into Hugging Face compatible Parquet shards.
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    if not input_path.exists():
        console.print(f"[bold red]Error:[/bold red] Input directory {input_dir} does not exist.")
        raise typer.Exit(code=1)

    output_path.mkdir(parents=True, exist_ok=True)

    # Scan files
    console.print(f"[bold blue]Scanning[/bold blue] for [green]*.{extension}[/green] files in {input_dir}...")
    files = list(input_path.rglob(f"*.{extension}"))

    if not files:
        console.print(f"[bold yellow]Warning:[/bold yellow] No files found with extension .{extension}")
        raise typer.Exit(code=0)

    console.print(f"Found [bold green]{len(files)}[/bold green] files. Starting conversion...")

    data_buffer = []

    # Auto-increment logic: find the highest existing index for this prefix
    existing_files = list(output_path.glob(f"{prefix}-*-of-*.parquet"))
    start_index = 0
    if existing_files:
        for p in existing_files:
            try:
                # Expected format: prefix-00000-of-xxxxx.parquet
                # We split by prefix and -of- to isolate the index
                name = p.name
                if name.startswith(f"{prefix}-") and "-of-" in name:
                    # Remove prefix-
                    rest = name[len(prefix)+1:]
                    # Extract number part before -of-
                    num_str = rest.split("-of-")[0]
                    idx = int(num_str)
                    if idx >= start_index:
                        start_index = idx + 1
            except (ValueError, IndexError):
                continue

    if start_index > 0:
        console.print(f"[yellow]Found existing files for prefix '{prefix}'. Starting at index {start_index:05d}.[/yellow]")

    chunk_index = start_index

    for file_path in track(files, description="Processing files..."):
        # Skip vendor directories or hidden files
        if "vendor" in str(file_path) or ".git" in str(file_path):
            continue

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Skip empty files
            if not content.strip():
                continue

            data_buffer.append({
                "content": content,
                "file_path": str(file_path),
                "repo_name": repo_name,
                "language": extension
            })

            # Write chunk if buffer is full
            if len(data_buffer) >= chunk_size:
                _write_parquet(data_buffer, output_path, chunk_index, prefix)
                data_buffer = []
                chunk_index += 1

        except Exception as e:
            console.print(f"[red]Failed to read {file_path}: {e}[/red]")
            continue

    # Write remaining buffer
    if data_buffer:
        _write_parquet(data_buffer, output_path, chunk_index, prefix)

    console.print(f"[bold green]Success![/bold green] Converted {len(files)} files into Parquet format at {output_dir}")

def _write_parquet(data, output_path, chunk_index, prefix):
    df = pd.DataFrame(data)
    filename = f"{prefix}-{chunk_index:05d}-of-xxxxx.parquet"
    out_file = output_path / filename
    df.to_parquet(out_file, index=False)
    console.print(f"Saved chunk: [cyan]{filename}[/cyan] ({len(df)} rows)")

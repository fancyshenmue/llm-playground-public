import pandas as pd
import typer
from rich.console import Console
from rich.table import Table
from pathlib import Path

console = Console()

def view_parquet(
    file_path: str = typer.Argument(..., help="Path to the parquet file"),
    head: int = typer.Option(5, "--head", "-n", help="Number of rows to show"),
    full_content: bool = typer.Option(False, "--full", "-f", help="Show full content field (truncated by default)")
):
    """
    Visualize a Parquet file in the terminal.
    """
    path = Path(file_path)
    if not path.exists():
        console.print(f"[bold red]Error:[/bold red] File {file_path} does not exist.")
        raise typer.Exit(code=1)

    try:
        df = pd.read_parquet(path)
    except Exception as e:
        console.print(f"[red]Failed to read parquet file: {e}[/red]")
        raise typer.Exit(code=1)

    console.print(f"[bold blue]File:[/bold blue] {path.name}")
    console.print(f"[bold blue]Shape:[/bold blue] {df.shape[0]} rows x {df.shape[1]} columns")
    console.print(f"[bold blue]Columns:[/bold blue] {', '.join(df.columns)}")

    # Create table
    table = Table(show_header=True, header_style="bold magenta")

    # Add columns
    for col in df.columns:
        table.add_column(col, overflow="fold")

    # Add rows (limit to head)
    subset = df.head(head)

    for _, row in subset.iterrows():
        row_data = []
        for col in df.columns:
            val = str(row[col])
            # Truncate content unless full flag is set
            if col == "content" and not full_content and len(val) > 100:
                val = val[:100] + "... [truncated]"
            row_data.append(val)
        table.add_row(*row_data)

    console.print(table)

    if len(df) > head:
        console.print(f"[dim]... and {len(df) - head} more rows.[/dim]")

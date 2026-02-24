import torch
import sys
import os

# Add project root to sys.path for internal imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")))
from internal.py.utils.ui import console, print_panel, Table

def check_cuda():
    cuda_available = torch.cuda.is_available()

    table = Table(title="GPU & CUDA Status", show_header=False, box=None)
    table.add_row("CUDA Available", "[green]YES[/]" if cuda_available else "[red]NO[/]")

    if cuda_available:
        table.add_row("GPU Device", f"[cyan]{torch.cuda.get_device_name(0)}[/]")
        table.add_row("CUDA Version", f"[yellow]{torch.version.cuda}[/]")
        table.add_row("PyTorch Version", f"[magenta]{torch.__version__}[/]")
        print_panel(table, title="[bold green]Success[/]", style="green")
    else:
        print_panel(
            f"[red]❌ Warning: CUDA support not detected.[/]\n"
            f"PyTorch version: {torch.__version__}\n"
            "[yellow]This usually means Pixi downloaded the CPU version.[/]",
            title="[bold red]Error[/]",
            style="red"
        )

if __name__ == "__main__":
    check_cuda()

import requests
import json
import os
import sys

# Add project root to sys.path for internal imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")))
from internal.py.utils.ui import console, print_panel
from internal.py.utils.config import config

# Telemetry Proxy URL
PROXY_URL = "http://localhost:11435"

def run_agent_test(prompt, model):
    print_panel(f"🕵️ [bold]Agent Telemetry Test[/bold]", style="cyan")
    console.print(f"Target: [green]{PROXY_URL}[/green]")
    console.print(f"Model: [yellow]{model}[/yellow]")
    console.print(f"Prompt: [white]{prompt}[/white]\n")

    url = f"{PROXY_URL}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }

    try:
        console.print("[dim]Sending request to Proxy...[/dim]")
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()

        data = response.json()
        result = data.get("response", "")

        console.print(f"\n[bold green]✅ Response received:[/bold green]\n")
        console.print(result)

        console.print(f"\n[bold blue]ℹ️  Check Phoenix UI at http://localhost:16006 to see the trace![/bold blue]")

    except Exception as e:
        console.print(f"[bold red]❌ Error: {e}[/bold red]")
        console.print("[yellow]Make sure the proxy is running: docker compose up -d (in deployments/docker-compose/arizephoenix)[/yellow]")

def main(prompt="Why is the sky blue?", model=None):
    if not model:
        model = config.get("ollama.base_model", "llama3.2")
    run_agent_test(prompt, model)

if __name__ == "__main__":
    main()

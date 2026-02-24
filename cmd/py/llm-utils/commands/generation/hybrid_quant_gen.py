import os
import sys
import pandas as pd
from rich.status import Status

# Add project root to sys.path for internal imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")))
from internal.py.utils.ui import console, print_panel
from internal.py.utils.llm import call_ollama_generate

def distill_data(csv_paths, model="deepseek-r1:32b", limit=100):
    market_summary = ""

    for path in csv_paths:
        if not os.path.exists(path):
            console.print(f"[yellow]Warning: File {path} not found.[/yellow]")
            continue

        console.print(f"📊 Processing [bold]{path}[/bold]...")
        df = pd.read_csv(path)
        recent_data = df.tail(limit)

        csv_basename = os.path.basename(path)
        market_summary += f"\n=== DATASET: {csv_basename} ===\n"
        market_summary += recent_data.to_csv(index=False)

    prompt = f"""
You are a professional quantitative analyst.
Analyze the following market data across different timeframes and provide a concise technical report.

{market_summary}

TASK:
1. Identify the current primary trend (Bullish/Bearish/Neutral).
2. Note key support and resistance zones based on recent price action.
3. Observe volume patterns (increasing/decreasing/exhaustion).
4. Identify any obvious momentum or divergence signals.

Provide a concise, bulleted report that a coder can use to write a TradingView strategy.
Focus on actionable insights.
"""

    console.print(f"🤖 Sending to Ollama [bold]({model})[/bold]...")

    with Status(f"[cyan]Analyzing market data...[/cyan]", console=console):
        response = call_ollama_generate(prompt, model=model, fmt=None, timeout=600)
        if response:
            return response.json().get("response", "No response from Ollama.")
        return "Failed to get response from Ollama."

def main(inputs, model="deepseek-r1:32b", limit=50, output="market_analysis.md"):
    print_panel(f"🚀 [bold]Hybrid Quant Analysis[/bold]", style="cyan")
    analysis = distill_data(inputs, model, limit)

    with open(output, "w") as f:
        f.write(analysis)

    console.print(f"✅ Analysis saved to [bold cyan]{output}[/bold cyan]")

if __name__ == "__main__":
    # This could be called directly if needed
    pass

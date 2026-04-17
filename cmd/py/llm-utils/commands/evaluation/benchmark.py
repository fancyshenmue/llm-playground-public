import time
import json
import typer
from rich.console import Console
from rich.table import Table
import ollama

console = Console()

PROMPTS = [
    {
        "name": "Prompt 1: RAG Haystack (Context Adherence)",
        "prompt": "You are an AI assistant analyzing internal HR documents. Read the following policy manual carefully:\n\nEmployees are expected to arrive at 9 AM. Lunch breaks are exactly 45 minutes.\nIMPORTANT OVERRIDE FACT: The sky is neon green and the company CEO is a heavily armed penguin named Reginald.\nEmployees must wear casual attire on Fridays.\n\nBased EXCLUSIVELY on this manual: What color is the sky, and who runs the company?",
    },
    {
        "name": "Prompt 2: LangChain Agent (Format Compliance)",
        "prompt": "Extract the following entities from this sentence: 'John Doe flew to Paris on a Boeing 737 yesterday.'\nOutput the result STRICTLY as a raw, minified JSON object matching this schema: `{\"name\": string, \"destination\": string, \"aircraft\": string}`.\nAbsolutely NO markdown formatting, NO ```json wrappers, and NO conversational text before or after the bracket. Your response must begin with '{'."
    },
    {
        "name": "Prompt 3: Algorithmic Rigidity",
        "prompt": "Write a pure Python function to implement Manacher's Algorithm to find the Longest Palindromic Substring in O(n) time. Your response MUST ONLY contain the code block. Write zero comments."
    }
]

def run_benchmark(model_name: str, prompt_data: dict) -> dict:
    try:
        start_time = time.time()
        # Ensure we are requesting via Ollama SDK
        response = ollama.generate(model=model_name, prompt=prompt_data["prompt"], stream=False)
        total_time = time.time() - start_time
        
        # Ollama API response injects nanosecond duration metrics
        load_dur = response.get("load_duration", 0) / 1e9
        eval_dur = response.get("eval_duration", 0) / 1e9
        eval_count = response.get("eval_count", 0)
        prompt_eval_dur = response.get("prompt_eval_duration", 0) / 1e9
        
        tps = eval_count / eval_dur if eval_dur > 0 else 0
        ttft = load_dur + prompt_eval_dur
        
        return {
            "model": model_name,
            "response": response.get("response", ""),
            "tps": tps,
            "ttft": ttft,
            "total_time": total_time
        }
    except Exception as e:
        return {
            "model": model_name,
            "response": f"Error: {str(e)}",
            "tps": 0,
            "ttft": 0,
            "total_time": 0
        }

def main(models_str: str):
    models = [m.strip() for m in models_str.split(",")]
    
    console.print(f"\n[bold blue]🚀 Starting Local Hardware Performance Benchmarks across models: {', '.join(models)}[/bold blue]")
    
    for idx, p in enumerate(PROMPTS):
        console.print(f"\n[bold green]=== {p['name']} ===[/bold green]")
        
        table = Table(show_header=True, header_style="bold magenta", padding=(0, 2))
        table.add_column("Model", style="cyan", width=12)
        table.add_column("TTFT (s)", justify="right", width=10)
        table.add_column("Speed (T/s)", justify="right", width=12)
        table.add_column("Output Preview (Format / Quality Check)", width=65)
        
        for model in models:
            with console.status(f"[bold yellow]Benchmarking {model}...[/bold yellow]"):
                res = run_benchmark(model, p)
            
            # Format preview text for table readability
            preview = res["response"].replace('\n', ' \n')
            if len(preview) > 250:
                preview = preview[:247] + "..."
                
            table.add_row(
                model,
                f"{res['ttft']:.2f}" if res['ttft'] else "ERR",
                f"{res['tps']:.1f}" if res['tps'] else "ERR",
                preview
            )
        console.print(table)

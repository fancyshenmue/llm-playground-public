import os
import sys
import json
from rich.live import Live
from rich.text import Text

# Add project root to sys.path for internal imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")))
from internal.py.utils.ui import console, print_panel
from internal.py.utils.image import encode_image
from internal.py.utils.llm import call_ollama_chat, VISION_MODEL
from internal.py.utils.config import config

# --- Configuration from YAML ---
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
IMAGE_DIR = os.path.join(root_dir, config.get("paths.images_dir"))

# The 5 images generated from the weight sweep
IMAGE_PATHS = [
    os.path.join(IMAGE_DIR, f"xyz_v9_w{w}_20260106_1538{s}_0.png")
    for w, s in zip(["0.6", "0.7", "0.8", "0.9", "1.0"], ["44", "53", "00", "08", "15"])
]

def evaluate_image(image_path, weight):
    console.print(f"\n🔍 [bold blue]Evaluating Weight {weight}[/bold blue] - {os.path.basename(image_path)}")
    encoded = encode_image(image_path)
    if not encoded:
        console.print(f"[red]❌ Error: Image not found at {image_path}[/red]")
        return ""

    messages = [
        {
            "role": "user",
            "content": (
                f"You are a professional photography critic. Analyze this 1024x1024 capture (Weight: {weight}).\n"
                "Focus strictly on:\n"
                "1. **Detail Integrity**: Are the circuit-board lines sharp and continuous, or do they look blurry/broken?\n"
                "2. **Aesthetic Stability**: Is the car's silhouette and lighting physically believable and clean?\n"
                "Provide a technical summary. Do NOT use placeholders."
            ),
            "images": [encoded]
        }
    ]

    full_response = ""
    response = call_ollama_chat(messages, stream=True)
    if not response: return ""

    with Live(Text("🤖 Analysis: ", style="bold green"), refresh_per_second=10, console=console) as live:
        for line in response.iter_lines():
            if line:
                chunk = json.loads(line.decode('utf-8'))
                content = chunk.get("message", {}).get("content", "")
                full_response += content
                live.update(Text("🤖 Analysis: ", style="bold green") + Text(full_response))

    console.print("-" * 30)
    return full_response

def choose_winner(evaluations):
    console.print(f"\n🏆 [bold yellow]Phase: Grand Choice - Professional Selection[/bold yellow]")

    combined_evals = ""
    for weight, res in evaluations.items():
        combined_evals += f"--- WEIGHT {weight} CRITIQUE ---\n{res}\n\n"

    prompt = (
        "You are a professional art director. Evaluate these 5 technical critiques of the same concept at different weights.\n\n"
        f"{combined_evals}"
        "Which weight achieves the 'Golden Ratio' of style presence vs. structural stability?\n"
        "Provide your final choice and justification in English. Do NOT mention AI."
    )

    messages = [{"role": "user", "content": prompt}]
    full_choice = ""
    response = call_ollama_chat(messages, stream=True)
    if not response: return ""

    with Live(Text("🤖 Final Verdict: ", style="bold yellow"), refresh_per_second=10, console=console) as live:
        for line in response.iter_lines():
            if line:
                chunk = json.loads(line.decode('utf-8'))
                content = chunk.get("message", {}).get("content", "")
                full_choice += content
                live.update(Text("🤖 Final Verdict: ", style="bold yellow") + Text(full_choice))

    console.print("=" * 50)
    return full_choice

def main():
    print_panel("🚀 [bold]Starting AI-Driven Image Selection (Auto Choose)[/bold]", style="blue")

    evaluations = {}
    weights = ["0.6", "0.7", "0.8", "0.9", "1.0"]

    for i, path in enumerate(IMAGE_PATHS):
        res = evaluate_image(path, weights[i])
        if res:
            evaluations[weights[i]] = res

    if evaluations:
        choose_winner(evaluations)
    else:
        console.print("[red]❌ No images were successfully evaluated.[/red]")

if __name__ == "__main__":
    main()

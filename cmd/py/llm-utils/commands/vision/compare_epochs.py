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

# Target Images (relative to project root)
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
IMAGE_DIR = os.path.join(root_dir, config.get("paths.images_dir"))
IMAGE_A = os.path.join(IMAGE_DIR, "forge_v2_20260106_144100_0.png")
IMAGE_B = os.path.join(IMAGE_DIR, "forge_v3_20260106_144647_0.png")

def analyze_with_streaming(image_path, label):
    console.print(f"\n🔍 [bold blue]Phase: Analyzing {label}[/bold blue] - {os.path.basename(image_path)}")
    encoded = encode_image(image_path)
    if not encoded:
        console.print(f"[red]❌ Error: Image not found.[/red]")
        return ""

    messages = [
        {
            "role": "user",
            "content": (
                f"You are a professional photographer analyzing the technical quality of this image ({label}).\n"
                "Please evaluate and describe exactly these three visual aspects:\n"
                "1. **Edge Sharpness**: Analyze the clarity of the lines and boundaries.\n"
                "2. **Material Consistency**: How believable and consistent are the surface textures (like metal or carbon)?\n"
                "3. **Lighting Physics**: Is the interaction of light, shadow, and reflections physically believable?\n"
                "\nDescribe only the visual results. Do NOT mention AI, LoRA, or generation techniques."
            ),
            "images": [encoded]
        }
    ]

    full_response = ""
    response = call_ollama_chat(messages, stream=True)
    if not response: return ""

    with Live(Text(f"🤖 {label} Analysis: ", style="bold green"), refresh_per_second=10, console=console) as live:
        for line in response.iter_lines():
            if line:
                chunk = json.loads(line.decode('utf-8'))
                content = chunk.get("message", {}).get("content", "")
                full_response += content
                live.update(Text(f"🤖 {label} Analysis: ", style="bold green") + Text(full_response))

    console.print("-" * 30)
    return full_response

def final_comparison(desc_v1, desc_v2):
    print_panel("📊 [bold yellow]Phase: Final Comparison - Professional Verdict[/bold yellow]", style="yellow")
    prompt = (
        "You are a professional photography critic. I have two technical evaluations of different photo captures (v1 and v2).\n\n"
        f"--- ANALYSIS OF v1 ---\n{desc_v1}\n\n"
        f"--- ANALYSIS OF v2 ---\n{desc_v2}\n\n"
        "Based ONLY on these evaluations, which version is superior in terms of:\n"
        "- Edge Sharpness\n"
        "- Material Consistency\n"
        "- Physical Lighting Correctness\n\n"
        "Provide your final verdict in English. Do NOT mention AI or generation technology."
    )

    messages = [{"role": "user", "content": prompt}]
    full_verdict = ""
    response = call_ollama_chat(messages, stream=True)
    if not response: return ""

    with Live(Text("🤖 Decision: ", style="bold gold1"), refresh_per_second=10, console=console) as live:
        for line in response.iter_lines():
            if line:
                chunk = json.loads(line.decode('utf-8'))
                content = chunk.get("message", {}).get("content", "")
                full_verdict += content
                live.update(Text("🤖 Decision: ", style="bold gold1") + Text(full_verdict))

    console.print("=" * 50)
    return full_verdict

def compare_images(image_a=IMAGE_A, image_b=IMAGE_B):
    if not os.path.exists(image_a) or not os.path.exists(image_b):
        console.print(f"[red]❌ Error: Source images not found.[/red]\nA: {image_a}\nB: {image_b}")
        return

    print_panel("🚀 [bold]Starting original resolution comparison with streaming...[/bold]", style="blue")

    desc_v1 = analyze_with_streaming(image_a, "Version A")
    if not desc_v1: return

    desc_v2 = analyze_with_streaming(image_b, "Version B")
    if not desc_v2: return

    final_comparison(desc_v1, desc_v2)

if __name__ == "__main__":
    compare_images()

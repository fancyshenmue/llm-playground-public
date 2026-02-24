import os
import sys
import base64
import json
from datetime import datetime

# Add project root to sys.path for internal imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")))
from internal.py.utils.ui import console, print_panel
from internal.py.utils.llm import call_ollama_generate, call_forge_txt2img, BASE_SD_MODEL, VISION_MODEL

def generate_image(concept):
    print_panel(f"🚀 [bold]Simple Generation Tool[/bold]", style="green")

    console.print(f"🧠 [blue]Expanding prompt[/blue] using [bold]{VISION_MODEL}[/bold]...")
    system_instruction = (
        "You are an expert SDXL prompt engineer. "
        "Create a highly detailed, descriptive English prompt for SDXL. "
        "Focus on 'FancyStyle' aesthetics: high-tech, mechanical details, neon blue accents. "
        "Only return the expanded prompt text."
    )

    response = call_ollama_generate(f"{system_instruction}\n\nUser concept: {concept}", fmt=None)
    refined = response.json()['response'].strip() if response else concept
    console.print(f"✨ [bold green]Refined Prompt:[/bold green] {refined[:100]}...")

    payload = {
        "prompt": f"FancyStyle, {refined}",
        "negative_prompt": "nsfw, lowres, bad anatomy, bad hands, text, error, signature, watermark",
        "steps": 30,
        "width": 1024,
        "height": 1024,
        "cfg_scale": 7,
        "sampler_name": "DPM++ 2M Karras",
        "override_settings": {"sd_model_checkpoint": BASE_SD_MODEL}
    }

    console.print(f"🎨 [cyan]Generating image in Forge...[/cyan]")
    result = call_forge_txt2img(payload)
    if result:
        for i, img_b64 in enumerate(result['images']):
            image_data = base64.b64decode(img_b64.split(",", 1)[0])
            filename = f"simple_gen_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}.png"
            output_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "images"))
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, filename)
            with open(output_path, 'wb') as f:
                f.write(image_data)
            console.print(f"✅ [bold green]Success![/bold green] Saved to [cyan]{output_path}[/cyan]")

if __name__ == "__main__":
    concept = "A futuristic sports car in FancyStyle, body covered with circuit‑board texture."
    if len(sys.argv) > 1:
        concept = " ".join(sys.argv[1:])
    generate_image(concept)

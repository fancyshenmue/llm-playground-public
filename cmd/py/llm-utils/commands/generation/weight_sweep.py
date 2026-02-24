import os
import sys
import base64
import time
from datetime import datetime
from rich.live import Live
from rich.text import Text

# Add project root to sys.path for internal imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")))
from internal.py.utils.ui import console, print_panel
from internal.py.utils.llm import call_ollama_generate, call_forge_txt2img, BASE_SD_MODEL, VISION_MODEL

def generate_prompt(concept):
    console.print(f"🧠 [blue]Expanding prompt[/blue] using [bold]{VISION_MODEL}[/bold]...")

    system_instruction = (
        "You are an expert SDXL Prompt Engineer. "
        "Refine the user doc into a highly detailed English prompt for Stable Diffusion, "
        "ensuring 'FancyStyle' aesthetics are prioritized. "
        "Only return the refined English prompt, no other text."
    )

    response = call_ollama_generate(f"{system_instruction}\n\nUser Concept: {concept}", fmt=None)
    if not response: return concept
    return response.json()['response'].strip()

def sweep_weights(prompt, lora="FancyStyle_v1-000009", weights=None):
    if weights is None:
        weights = [0.6, 0.7, 0.8, 0.9, 1.0]

    console.print(f"\n🚀 [bold]Starting Weight Sweep for {lora}[/bold]")

    output_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "images"))
    os.makedirs(output_dir, exist_ok=True)

    for weight in weights:
        start_time = time.time()
        console.print(f"🎨 [cyan]Generating with weight {weight}...[/cyan]")

        lora_tag = f"<lora:{lora}:{weight}>"
        payload = {
            "prompt": f"FancyStyle, {lora_tag}, {prompt}",
            "negative_prompt": "nsfw, lowres, bad anatomy, bad hands, text, error, cropped, worst quality, low quality",
            "steps": 35,
            "width": 1024,
            "height": 1024,
            "cfg_scale": 7.5,
            "sampler_name": "DPM++ 2M Karras",
            "override_settings": {"sd_model_checkpoint": BASE_SD_MODEL}
        }

        result = call_forge_txt2img(payload)
        if result:
            img_b64 = result['images'][0]
            image_data = base64.b64decode(img_b64.split(",", 1)[0])
            filename = f"sweep_{lora}_w{weight}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            output_path = os.path.join(output_dir, filename)
            with open(output_path, 'wb') as f:
                f.write(image_data)

            elapsed = time.time() - start_time
            console.print(f"✅ Saved to [cyan]{output_path}[/cyan] ([bold]{elapsed:.1f}s[/bold])")

def main(concept=None, lora="FancyStyle_v1-000009"):
    if not concept:
        concept = "A futuristic sports car in FancyStyle, body covered with circuit-board texture, blue neon glow."

    print_panel(f"🚀 [bold]LoRA Weight Sweep Tool[/bold]", style="blue")
    refined_prompt = generate_prompt(concept)
    sweep_weights(refined_prompt, lora=lora)

if __name__ == "__main__":
    main()

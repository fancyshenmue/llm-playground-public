import os
import sys
import base64
from datetime import datetime
from rich.status import Status

# Add project root to sys.path for internal imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")))
from internal.py.utils.ui import console, print_panel
from internal.py.utils.llm import call_ollama_generate, call_forge_txt2img, BASE_SD_MODEL, VISION_MODEL

def generate_prompt_by_llm(user_input):
    console.print(f"🧠 [blue]Phase 1[/blue] Prompt Expansion using [bold]{VISION_MODEL}[/bold]...")

    system_instruction = (
        "You are an expert SDXL Prompt Engineer specializing in 'FancyStyle' aesthetics. "
        "The user wants a futuristic, high-tech image that balances style and structural stability. "
        "Incorporate keywords like: sleek design, advanced technology, glossy finish, "
        "circuit-board lines, neon lights, well-balanced composition, luxury, and high-quality rendering. "
        "Refine the user concept into a highly detailed English prompt for Stable Diffusion. "
        "Only return the refined English prompt, no other text."
    )

    prompt = f"{system_instruction}\n\nUser Concept: {user_input}"

    with Status(f"[cyan]Expanding prompt via AI...[/cyan]", console=console):
        response = call_ollama_generate(prompt, model=VISION_MODEL, fmt=None) # fmt=None for free-form text
        if not response: return user_input

        try:
            refined = response.json()['response'].strip()
            console.print(f"✨ [bold green]Refined Prompt:[/bold green] {refined[:150]}...")
            return refined
        except Exception as e:
            console.print(f"[red]❌ Error parsing Ollama response: {e}[/red]")
            return user_input

def send_to_forge(refined_prompt, weight=0.8, lora="FancyStyle_v1-000009"):
    console.print(f"🎨 [blue]Phase 2[/blue] Sending to Forge with Weight [bold]{weight}[/bold]...")

    lora_tag = f"<lora:{lora}:{weight}>"
    full_positive_prompt = f"FancyStyle, {lora_tag}, {refined_prompt}"

    payload = {
        "prompt": full_positive_prompt,
        "negative_prompt": "nsfw, lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry, cartoon, semi-realistic",
        "steps": 40,
        "width": 1024,
        "height": 1024,
        "cfg_scale": 7.5,
        "sampler_name": "DPM++ 2M Karras",
        "override_settings": {
            "sd_model_checkpoint": BASE_SD_MODEL
        }
    }

    with Status(f"[magenta]Generating image in Forge...[/magenta]", console=console):
        result = call_forge_txt2img(payload)
        if not result: return

        for i, img_b64 in enumerate(result['images']):
            image_data = base64.b64decode(img_b64.split(",", 1)[0])

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"golden_ratio_w{weight}_{timestamp}_{i}.png"
            output_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "images"))
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            output_path = os.path.join(output_dir, filename)
            with open(output_path, 'wb') as f:
                f.write(image_data)

            print_panel(
                f"[green]✅ Success! Image saved to:[/green] [cyan]{output_path}[/cyan]\n"
                f"[yellow]💡 This image was generated using the 'Golden Ratio' weight identified by AI analysis.[/yellow]",
                title="[bold green]Generation Complete[/bold green]"
            )

def main(concept=None, weight=0.8, lora="FancyStyle_v1-000009"):
    if concept is None:
        concept = (
            "A futuristic sports car in FancyStyle, featuring sleek lines and a glossy finish. "
            "The body is adorned with intricate circuit-board patterns and glowing neon lights. "
            "Cinematic 3-point lighting, luxury atmosphere, high-end technical rendering, "
            "8k resolution, laser-sharp focus, metallic textures, and a dark reflective background."
        )

    print_panel(f"🚀 [bold]Generating Final 'Golden Ratio' Image[/bold]", style="blue")
    refined_prompt = generate_prompt_by_llm(concept)
    send_to_forge(refined_prompt, weight=weight, lora=lora)

if __name__ == "__main__":
    main()

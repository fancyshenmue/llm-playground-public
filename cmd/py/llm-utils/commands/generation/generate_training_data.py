import os
import sys
import json
import time
import base64

# Add project root to sys.path for internal imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")))
from internal.py.utils.ui import console, print_panel, get_progress
from internal.py.utils.llm import call_ollama_generate, call_forge_txt2img, BASE_SD_MODEL

def get_unique_prompt_and_tags(index, total, topic):
    """Uses Ollama to generate a unique prompt and tagging for the topic."""
    system_instruction = (
        "You are an expert at generating diversified training data for Stable Diffusion. "
        "The goal is to generate a unique image description and its corresponding BLIP-style caption. "
        f"The topic is: {topic}. "
        "Each description MUST be unique (different outfits, settings, poses, lighting, ethnicities). "
        "Return a JSON object with two keys: "
        "'prompt': A highly detailed SDXL prompt (English). "
        "'caption': A natural language BLIP-style caption describing the image content. "
        "Example output: {\"prompt\": \"a detailed description...\", \"caption\": \"a girl wearing...\"}"
    )

    user_prompt = f"Topic: {topic}. This is iteration {index+1}/{total}. Ensure it's different from previous ones."

    response = call_ollama_generate(f"{system_instruction}\n\n{user_prompt}")
    if not response:
        return f"a beautiful image, {topic}, high quality", f"a beautiful image of {topic}"

    try:
        data = response.json()
        result = json.loads(data['response'])
        return result.get('prompt'), result.get('caption')
    except Exception as e:
        console.print(f"[red]❌ Error parsing Ollama response: {e}[/red]")
        return f"a beautiful image, {topic}, high quality", f"a beautiful image of {topic}"

def generate_image(prompt, filename, output_dir):
    """Sends prompt to Forge API and saves the image."""
    payload = {
        "prompt": prompt,
        "negative_prompt": "nsfw, lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry",
        "steps": 30,
        "width": 1024,
        "height": 1024,
        "cfg_scale": 7.0,
        "sampler_name": "DPM++ 2M Karras",
        "override_settings": {
            "sd_model_checkpoint": BASE_SD_MODEL
        }
    }

    result = call_forge_txt2img(payload)
    if not result: return False

    try:
        img_b64 = result['images'][0]
        image_data = base64.b64decode(img_b64.split(",", 1)[0])

        filepath = os.path.join(output_dir, f"{filename}.png")
        with open(filepath, 'wb') as f:
            f.write(image_data)
        return True
    except Exception as e:
        console.print(f"[red]❌ Error saving image: {e}[/red]")
        return False

def main(topic="beauty girl", total=30, output_dir=None):
    if output_dir is None:
        output_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "dataset", f"{total}_" + topic.replace(" ", "_")))

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        console.print(f"📁 [cyan]Created directory: {output_dir}[/cyan]")

    print_panel(f"🚀 [bold]Starting generation of {total} images for topic: {topic}[/bold]", style="blue")

    with get_progress() as progress:
        task = progress.add_task("[cyan]Generating training data...", total=total)

        for i in range(total):
            prompt, caption = get_unique_prompt_and_tags(i, total, topic)

            if not prompt or not caption:
                progress.console.print(f"[yellow]⚠️ Skipping iteration {i+1} due to missing data.[/yellow]")
                progress.advance(task)
                continue

            filename = f"{topic.replace(' ', '_')}_{i+1:03d}"

            success = generate_image(prompt, filename, output_dir)

            if success:
                caption_path = os.path.join(output_dir, f"{filename}.txt")
                with open(caption_path, 'w', encoding='utf-8') as f:
                    f.write(caption)
                progress.console.print(f"[green]✅ Saved {filename}.png and {filename}.txt[/green]")
            else:
                progress.console.print(f"[red]❌ Failed to generate image for {filename}[/red]")

            progress.advance(task)
            time.sleep(0.5)

    print_panel(f"🎉 [bold green]Training data generation complete![/bold green]\n📍 Location: {output_dir}", style="green")

if __name__ == "__main__":
    main()

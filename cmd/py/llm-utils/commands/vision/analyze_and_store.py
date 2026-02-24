import os
import sys
import requests

# Add project root to sys.path for internal imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")))
from internal.py.utils.ui import console, print_panel
from internal.py.utils.image import encode_image
from internal.py.utils.llm import call_ollama_generate, VISION_MODEL
from internal.py.utils.config import config

# --- Configuration from YAML ---
ANYTHINGLLM_API_URL = config.get("anythingllm.api_url")
ANYTHINGLLM_API_KEY = config.get("anythingllm.api_key")
WORKSPACE_SLUG = config.get("anythingllm.workspace_slug")
IMAGES_DIR = config.get("paths.images_dir")

def analyze_image(image_path):
    console.print(f"🔍 Analyzing image: [bold]{os.path.basename(image_path)}[/bold]")
    base64_image = encode_image(image_path)
    if not base64_image:
        console.print("[red]❌ Error: Image not found.[/red]")
        return None

    prompt = "This is a Stable Diffusion generated image. Please analyze its composition, lighting details, and the presentation of the FancyStyle effect, then provide suggestions for improvement. Please answer in English."

    # Ollama vision expects base64 in a list, but call_ollama_generate might need adjustment for vision
    # Since call_ollama_generate is currently for text, let's use a custom call or enhance it.
    # For now, custom call in this script to handle vision specifics.
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": VISION_MODEL,
        "prompt": prompt,
        "stream": False,
        "images": [base64_image]
    }

    try:
        response = requests.post(url, json=payload, timeout=300)
        response.raise_for_status()
        return response.json().get("response", "Analysis failed")
    except Exception as e:
        console.print(f"[red]❌ Ollama Error: {e}[/red]")
        return None

def store_in_anythingllm(image_path, analysis_text):
    console.print(f"📦 Storing result in AnythingLLM...")
    file_name = os.path.basename(image_path)

    headers = {
        "Authorization": f"Bearer {ANYTHINGLLM_API_KEY}",
        "Content-Type": "application/json"
    }

    # Step 1: Upload raw text
    doc_name = f"Analysis_{file_name}.txt"
    payload = {
        "textContent": f"Image Full Path: {image_path}\n\nAnalysis Result:\n{analysis_text}",
        "metadata": {"title": doc_name, "source": "Ollama-Vision-Automation"}
    }

    try:
        response = requests.post(f"{ANYTHINGLLM_API_URL}/document/raw-text", json=payload, headers=headers, timeout=60)
        if response.status_code != 200:
            console.print(f"[red]❌ Upload Failed: {response.text}[/red]")
            return False

        doc_data = response.json()
        doc_location = doc_data.get("documents", [{}])[0].get("location")

        # Step 2: Add to workspace
        update_url = f"{ANYTHINGLLM_API_URL}/workspace/{WORKSPACE_SLUG}/update-embeddings"
        requests.post(update_url, json={"adds": [doc_location]}, headers=headers).raise_for_status()
        return True
    except Exception as e:
        console.print(f"[red]❌ AnythingLLM Error: {e}[/red]")
        return False

def main(image_path=None):
    if not image_path:
        # Get latest image from images directory
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
        img_dir = os.path.join(root_dir, IMAGES_DIR)

        if not os.path.exists(img_dir):
            console.print(f"[red]❌ Images directory not found at {img_dir}[/red]")
            return

        files = [os.path.join(img_dir, f) for f in os.listdir(img_dir) if f.lower().endswith(('.png', '.jpg'))]
        if not files:
            console.print(f"[red]❌ No images found in {img_dir}.[/red]")
            return
        image_path = max(files, key=os.path.getctime)

    print_panel(f"🚀 [bold]Vision Analysis & AnythingLLM Integration[/bold]", style="magenta")
    analysis = analyze_image(image_path)

    if analysis and store_in_anythingllm(image_path, analysis):
        console.print("[bold green]✅ Automation process complete![/bold green]")
    else:
        console.print("[bold red]❌ Process failed.[/bold red]")

if __name__ == "__main__":
    main()

import requests
import json
from .ui import console
from .config import config

# --- Configuration from YAML ---
OLLAMA_API_URL = config.get("ollama.api_url")
FORGE_API_URL = config.get("forge.api_url")
VISION_MODEL = config.get("ollama.vision_model")
BASE_SD_MODEL = config.get("forge.base_model")
OLLAMA_TIMEOUT = config.get("ollama.timeout")
FORGE_TIMEOUT = config.get("forge.timeout")

def call_ollama_chat(messages, model=VISION_MODEL, stream=False, timeout=OLLAMA_TIMEOUT):
    url = f"{OLLAMA_API_URL}/chat"
    payload = {
        "model": model,
        "messages": messages,
        "stream": stream
    }
    try:
        response = requests.post(url, json=payload, stream=stream, timeout=timeout)
        response.raise_for_status()
        return response
    except Exception as e:
        console.print(f"[red]❌ Ollama API Error: {e}[/red]")
        return None

def call_ollama_generate(prompt, model=VISION_MODEL, fmt="json", stream=False, timeout=OLLAMA_TIMEOUT):
    url = f"{OLLAMA_API_URL}/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "format": fmt,
        "stream": stream
    }
    try:
        response = requests.post(url, json=payload, stream=stream, timeout=timeout)
        response.raise_for_status()
        return response
    except Exception as e:
        console.print(f"[red]❌ Ollama API Error: {e}[/red]")
        return None

def call_forge_txt2img(payload, timeout=FORGE_TIMEOUT):
    url = f"{FORGE_API_URL}/txt2img"
    try:
        response = requests.post(url, json=payload, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        console.print(f"[red]❌ Forge API Error: {e}[/red]")
        return None

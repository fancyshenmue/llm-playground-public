import os
import yaml
from pathlib import Path

# Default configurations
DEFAULT_CONFIG = {
    "ollama": {
        "api_url": "http://localhost:11434/api",
        "vision_model": "llama3.2-vision",
        "timeout": 300
    },
    "forge": {
        "api_url": "http://127.0.0.1:7861/sdapi/v1",
        "base_model": "Juggernaut-XL_v9_RunDiffusionPhoto_v2.safetensors",
        "timeout": 600
    },
    "anythingllm": {
        "api_url": "http://localhost:3001/api/v1",
        "api_key": "PXD5SA7-N9E4FSJ-QT9XA13-QAM3SC8",
        "workspace_slug": "ai-image-research"
    },
    "paths": {
        "images_dir": "images",
        "dataset_dir": "dataset"
    }
}

class Config:
    def __init__(self):
        self._config = DEFAULT_CONFIG
        self._load_config()

    def _load_config(self):
        # Search order:
        # 1. cmd/py/llm-utils/config.yaml
        # 2. config.yaml (root)
        root_dir = Path(__file__).parent.parent.parent.parent
        search_paths = [
            root_dir / "cmd" / "py" / "llm-utils" / "config.yaml",
            root_dir / "config.yaml"
        ]

        for config_path in search_paths:
            if config_path.exists():
                try:
                    with open(config_path, "r") as f:
                        user_config = yaml.safe_load(f)
                        if user_config:
                            self._deep_update(self._config, user_config)
                            return # Stop at first found
                except Exception as e:
                    print(f"⚠️ Warning: Could not load config at {config_path}: {e}")

    def _deep_update(self, base, update):
        for key, value in update.items():
            if isinstance(value, dict) and key in base:
                self._deep_update(base[key], value)
            else:
                base[key] = value

    def get(self, key_path, default=None):
        """Get value from config using dot notation (e.g., 'ollama.api_url')"""
        keys = key_path.split(".")
        value = self._config
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default

# Singleton instance
config = Config()

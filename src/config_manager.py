import json
import os

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "focus_duration_minutes": 25,
    "break_duration_minutes": 5,
    "strict_break_enabled": False
}

def load_config() -> dict:
    """Loads configuration from config.json. Returns default configuration if file is missing or invalid."""
    if not os.path.exists(CONFIG_FILE):
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Ensure all default keys exist
            config = DEFAULT_CONFIG.copy()
            config.update(data)
            return config
    except Exception:
        return DEFAULT_CONFIG.copy()

def save_config(config: dict) -> bool:
    """Saves the configuration to config.json."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        return True
    except Exception:
        return False

import os
import toml

DEFAULT_CONFIG_DIR = os.path.expanduser("~/.chatai")
DEFAULT_CONFIG_PATH = os.path.join(DEFAULT_CONFIG_DIR, "config.toml")
DEFAULT_SESSIONS_DIR = os.path.join(DEFAULT_CONFIG_DIR, "sessions")

DEFAULT_CONFIG = {
    "default_backend": "ollama",
    "default_model": "gemma3:4b",
    "system_prompt": "You are a helpful, friendly, and intelligent AI companion. You reply through a terminal interface.",
    "memory_limit": 20,
    "ollama": {
        "url": "http://localhost:11434",
    },
    "gemini": {
        "api_key": "",
        "model": "gemini-2.5-flash",
    },
    "groq": {
        "api_key": "",
        "model": "llama-3.3-70b-versatile",
    }
}

def ensure_config_dir():
    os.makedirs(DEFAULT_CONFIG_DIR, exist_ok=True)
    os.makedirs(DEFAULT_SESSIONS_DIR, exist_ok=True)

def load_config():
    ensure_config_dir()
    if not os.path.exists(DEFAULT_CONFIG_PATH):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    
    try:
        with open(DEFAULT_CONFIG_PATH, "r", encoding="utf-8") as f:
            user_config = toml.load(f)
        # Merge defaults for missing keys
        merged = DEFAULT_CONFIG.copy()
        for k, v in user_config.items():
            if isinstance(v, dict) and k in merged:
                merged[k] = {**merged[k], **v}
            else:
                merged[k] = v
        return merged
    except Exception:
        # Fallback to default if load fails
        return DEFAULT_CONFIG

def save_config(config_dict):
    ensure_config_dir()
    try:
        with open(DEFAULT_CONFIG_PATH, "w", encoding="utf-8") as f:
            toml.dump(config_dict, f)
        return True
    except Exception:
        return False

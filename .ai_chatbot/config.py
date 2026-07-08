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

def get_thesis_context() -> str:
    """
    Search for MASTER_AGENT_PROMPT.md in the current working directory or parents.
    If found, extract the ground truth section to provide context for the prompt.
    """
    cwd = os.getcwd()
    for dirpath in [cwd, os.path.dirname(cwd), os.path.dirname(os.path.dirname(cwd))]:
        prompt_path = os.path.join(dirpath, "MASTER_AGENT_PROMPT.md")
        if os.path.exists(prompt_path):
            try:
                with open(prompt_path, "r", encoding="utf-8") as f:
                    content = f.read()
                lines = content.splitlines()
                context_lines = []
                in_ground_truth = False
                for line in lines[:80]:
                    if "## §0" in line or "GROUND TRUTH" in line:
                        in_ground_truth = True
                    elif "## §1" in line:
                        break
                    if in_ground_truth:
                        context_lines.append(line)
                
                if context_lines:
                    return "\n".join(context_lines)
            except Exception:
                pass
    return ""

def load_config():
    ensure_config_dir()
    
    # Gracefully load workspace dotenv file if present
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    config_dict = DEFAULT_CONFIG.copy()
    if os.path.exists(DEFAULT_CONFIG_PATH):
        try:
            with open(DEFAULT_CONFIG_PATH, "r", encoding="utf-8") as f:
                user_config = toml.load(f)
            # Merge defaults for missing keys
            for k, v in user_config.items():
                if isinstance(v, dict) and k in config_dict:
                    config_dict[k] = {**config_dict[k], **v}
                else:
                    config_dict[k] = v
        except Exception:
            pass
    else:
        save_config(DEFAULT_CONFIG)

    # Environment variable overrides (GCP/Gemini credentials integration)
    gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_KEY")
    if gemini_key:
        if "gemini" not in config_dict:
            config_dict["gemini"] = {}
        config_dict["gemini"]["api_key"] = gemini_key
        
    groq_key = os.environ.get("GROQ_API_KEY") or os.environ.get("GROQ_KEY")
    if groq_key:
        if "groq" not in config_dict:
            config_dict["groq"] = {}
        config_dict["groq"]["api_key"] = groq_key

    # Dynamically inject workspace thesis context to the system prompt
    thesis_context = get_thesis_context()
    if thesis_context:
        orig_prompt = config_dict.get("system_prompt", DEFAULT_CONFIG["system_prompt"])
        config_dict["system_prompt"] = (
            f"{orig_prompt}\n\n"
            "--- THESIS SYSTEM CONTEXT ---\n"
            "You are running within the Space-Based Economic Intelligence thesis repository. "
            "Here is the verified academic ground truth and project parameters:\n"
            f"{thesis_context}\n"
            "Use this information to assist with any questions about the thesis, satellite APIs (GEE/CDSE), "
            "the ETL pipeline, anomaly detection algorithms, or the interactive web dashboard."
        )

    return config_dict

def save_config(config_dict):
    ensure_config_dir()
    try:
        with open(DEFAULT_CONFIG_PATH, "w", encoding="utf-8") as f:
            toml.dump(config_dict, f)
        return True
    except Exception:
        return False

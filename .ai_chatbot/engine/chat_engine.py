import os
import json
import datetime
from typing import List, Dict, Optional
from config import DEFAULT_SESSIONS_DIR, load_config
from .backends import BaseBackend, OllamaBackend, GeminiBackend, GroqBackend

class ChatEngine:
    def __init__(self):
        self.config = load_config()
        self.system_prompt = self.config.get("system_prompt", "")
        self.memory_limit = self.config.get("memory_limit", 20)
        self.history: List[Dict[str, str]] = []
        
        # Initialize backends
        self.backends: Dict[str, BaseBackend] = {
            "ollama": OllamaBackend(self.config.get("ollama", {}).get("url", "http://localhost:11434")),
            "gemini": GeminiBackend(self.config.get("gemini", {}).get("api_key", ""), self.config.get("gemini", {}).get("model", "")),
            "groq": GroqBackend(self.config.get("groq", {}).get("api_key", ""), self.config.get("groq", {}).get("model", ""))
        }
        
        # Set default active backend
        pref_backend = self.config.get("default_backend", "ollama")
        if self.backends[pref_backend].is_available():
            self.active_backend_name = pref_backend
        else:
            # Fallback to the first available backend
            available = [name for name, b in self.backends.items() if b.is_available()]
            if available:
                self.active_backend_name = available[0]
            else:
                self.active_backend_name = "ollama" # default to Ollama even if not running
                
        # Set active model
        self.active_model = self.config.get("default_model", None)
        if self.active_backend_name == "gemini":
            self.active_model = self.config.get("gemini", {}).get("model", "gemini-2.5-flash")
        elif self.active_backend_name == "groq":
            self.active_model = self.config.get("groq", {}).get("model", "llama-3.3-70b-versatile")
        
        # Session info
        self.current_session_name = "default"

    @property
    def active_backend(self) -> BaseBackend:
        return self.backends[self.active_backend_name]

    def set_backend(self, backend_name: str, model_name: Optional[str] = None) -> bool:
        if backend_name not in self.backends:
            return False
        
        self.active_backend_name = backend_name
        if model_name:
            self.active_model = model_name
        else:
            models = self.backends[backend_name].get_available_models()
            if models:
                self.active_model = models[0]
            else:
                self.active_model = None
        return True

    def add_message(self, role: str, content: str):
        self.history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.datetime.now().isoformat()
        })

    def get_messages_for_api(self) -> List[Dict[str, str]]:
        # Format for API (only role and content, no timestamp, sliding window)
        window = self.history[-self.memory_limit:] if self.memory_limit > 0 else self.history
        return [{"role": m["role"], "content": m["content"]} for m in window]

    def clear_history(self):
        self.history = []

    def save_session(self, name: str = None) -> str:
        if not name:
            name = self.current_session_name
        
        self.current_session_name = name
        filename = f"{name}.json"
        filepath = os.path.join(DEFAULT_SESSIONS_DIR, filename)
        
        session_data = {
            "session_name": name,
            "backend": self.active_backend_name,
            "model": self.active_model,
            "system_prompt": self.system_prompt,
            "history": self.history,
            "updated_at": datetime.datetime.now().isoformat()
        }
        
        os.makedirs(DEFAULT_SESSIONS_DIR, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
            
        return filepath

    def load_session(self, name: str) -> bool:
        filename = f"{name}.json"
        filepath = os.path.join(DEFAULT_SESSIONS_DIR, filename)
        
        if not os.path.exists(filepath):
            return False
            
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            self.current_session_name = data.get("session_name", name)
            self.active_backend_name = data.get("backend", self.active_backend_name)
            self.active_model = data.get("model", self.active_model)
            self.system_prompt = data.get("system_prompt", self.system_prompt)
            self.history = data.get("history", [])
            return True
        except Exception:
            return False

    def list_sessions(self) -> List[Dict]:
        sessions = []
        if not os.path.exists(DEFAULT_SESSIONS_DIR):
            return sessions
            
        for file in os.listdir(DEFAULT_SESSIONS_DIR):
            if file.endswith(".json"):
                filepath = os.path.join(DEFAULT_SESSIONS_DIR, file)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    sessions.append({
                        "name": data.get("session_name", file[:-5]),
                        "backend": data.get("backend"),
                        "model": data.get("model"),
                        "messages_count": len(data.get("history", [])),
                        "updated_at": data.get("updated_at", "")
                    })
                except Exception:
                    pass
        # Sort by updated_at descending
        sessions.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        return sessions

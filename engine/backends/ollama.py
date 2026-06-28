import json
import requests
from typing import Generator, List, Dict, Optional
from .base import BaseBackend

class OllamaBackend(BaseBackend):
    def __init__(self, url: str = "http://localhost:11434"):
        self.url = url.rstrip('/')

    @property
    def name(self) -> str:
        return "ollama"

    def is_available(self) -> bool:
        try:
            response = requests.get(f"{self.url}/api/tags", timeout=1.5)
            return response.status_code == 200
        except Exception:
            return False

    def get_available_models(self) -> List[str]:
        try:
            response = requests.get(f"{self.url}/api/tags", timeout=2.0)
            if response.status_code == 200:
                data = response.json()
                return [m["name"] for m in data.get("models", [])]
        except Exception:
            pass
        return []

    def generate_stream(
        self, 
        messages: List[Dict[str, str]], 
        system_prompt: str, 
        model: Optional[str] = None
    ) -> Generator[str, None, None]:
        if not model:
            models = self.get_available_models()
            model = models[0] if models else "gemma3:4b"

        # Construct payload with system prompt if provided
        chat_messages = []
        if system_prompt:
            chat_messages.append({"role": "system", "content": system_prompt})
        chat_messages.extend(messages)

        payload = {
            "model": model,
            "messages": chat_messages,
            "stream": True
        }

        try:
            response = requests.post(
                f"{self.url}/api/chat",
                json=payload,
                stream=True,
                timeout=10.0
            )
            response.raise_for_status()

            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line.decode("utf-8"))
                    content = chunk.get("message", {}).get("content", "")
                    if content:
                        yield content
        except Exception as e:
            yield f"\n[Error connecting to Ollama: {str(e)}]"
            
    def pull_model(self, model: str) -> Generator[Dict, None, None]:
        """Pull a model and yield progress updates."""
        try:
            response = requests.post(
                f"{self.url}/api/pull",
                json={"name": model, "stream": True},
                stream=True
            )
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    yield json.loads(line.decode("utf-8"))
        except Exception as e:
            yield {"status": "error", "error": str(e)}

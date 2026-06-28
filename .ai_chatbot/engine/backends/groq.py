import json
import requests
from typing import Generator, List, Dict, Optional
from .base import BaseBackend

class GroqBackend(BaseBackend):
    def __init__(self, api_key: str = "", model: str = "llama-3.3-70b-versatile"):
        self.api_key = api_key
        self.default_model = model

    @property
    def name(self) -> str:
        return "groq"

    def is_available(self) -> bool:
        return bool(self.api_key)

    def get_available_models(self) -> List[str]:
        # Typical Groq models
        return [
            "llama-3.3-70b-versatile",
            "llama3-8b-8192",
            "llama3-70b-8192",
            "mixtral-8x7b-32768",
            "gemma2-9b-it"
        ]

    def generate_stream(
        self, 
        messages: List[Dict[str, str]], 
        system_prompt: str, 
        model: Optional[str] = None
    ) -> Generator[str, None, None]:
        if not self.api_key:
            yield "\n[Error: Groq API key is not configured.]"
            return

        selected_model = model or self.default_model
        
        chat_messages = []
        if system_prompt:
            chat_messages.append({"role": "system", "content": system_prompt})
        chat_messages.extend(messages)

        payload = {
            "model": selected_model,
            "messages": chat_messages,
            "stream": True
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        url = "https://api.groq.com/openai/v1/chat/completions"

        try:
            response = requests.post(url, json=payload, headers=headers, stream=True, timeout=15.0)
            response.raise_for_status()

            for line in response.iter_lines():
                if not line:
                    continue
                
                line_str = line.decode("utf-8").strip()
                if line_str.startswith("data: "):
                    data_content = line_str[6:]
                    if data_content == "[DONE]":
                        break
                    try:
                        obj = json.loads(data_content)
                        choices = obj.get("choices", [])
                        if choices:
                            content = choices[0].get("delta", {}).get("content", "")
                            if content:
                                yield content
                    except Exception:
                        pass
        except Exception as e:
            yield f"\n[Error connecting to Groq: {str(e)}]"

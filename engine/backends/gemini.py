import json
import requests
from typing import Generator, List, Dict, Optional
from .base import BaseBackend

class GeminiBackend(BaseBackend):
    def __init__(self, api_key: str = "", model: str = "gemini-2.5-flash"):
        self.api_key = api_key
        self.default_model = model

    @property
    def name(self) -> str:
        return "gemini"

    def is_available(self) -> bool:
        return bool(self.api_key)

    def get_available_models(self) -> List[str]:
        return ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-flash", "gemini-1.5-pro"]

    def generate_stream(
        self, 
        messages: List[Dict[str, str]], 
        system_prompt: str, 
        model: Optional[str] = None
    ) -> Generator[str, None, None]:
        if not self.api_key:
            yield "\n[Error: Gemini API key is not configured.]"
            return

        selected_model = model or self.default_model
        
        # Build contents mapping role 'assistant' to 'model'
        contents = []
        for msg in messages:
            role = "model" if msg["role"] in ("assistant", "model") else "user"
            contents.append({
                "role": role,
                "parts": [{"text": msg["content"]}]
            })

        payload = {
            "contents": contents,
        }
        
        if system_prompt:
            payload["systemInstruction"] = {
                "parts": [{"text": system_prompt}]
            }

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{selected_model}:streamGenerateContent?key={self.api_key}"

        try:
            response = requests.post(url, json=payload, stream=True, timeout=15.0)
            response.raise_for_status()

            # Gemini streams JSON objects in a special format.
            # In stream mode, it sends chunks separated by SSE or as a JSON list.
            # Wait, beta/streamGenerateContent sends chunks where each chunk is a JSON object.
            # Actually, it's typically streamed as line-delimited or as a JSON array where each line is prefixed by comma/brackets.
            # A robust way is to buffer the response and parse JSON chunks.
            # Actually, standard REST streaming for streamGenerateContent returns SSE-like or JSON chunks:
            # Let's inspect the stream. It's SSE or json lines? No, it's a JSON array format starting with '[' and chunks are dictionary elements separated by ','.
            # A common way to parse it:
            buffer = ""
            for chunk in response.iter_content(chunk_size=1024, decode_unicode=True):
                if not chunk:
                    continue
                buffer += chunk
                
                # Try to extract content from complete objects
                # We can find blocks starting with '{' and ending with '}'
                while True:
                    # Find first '{'
                    start = buffer.find('{')
                    if start == -1:
                        break
                    
                    # Try to find matching '}'
                    # Since we want valid JSON, let's find the closing brace by counting braces
                    depth = 0
                    end = -1
                    in_string = False
                    escaped = False
                    for i in range(start, len(buffer)):
                        char = buffer[i]
                        if escaped:
                            escaped = False
                            continue
                        if char == '\\':
                            escaped = True
                            continue
                        if char == '"':
                            in_string = not in_string
                            continue
                        if not in_string:
                            if char == '{':
                                depth += 1
                            elif char == '}':
                                depth -= 1
                                if depth == 0:
                                    end = i
                                    break
                    
                    if end == -1:
                        # Incomplete JSON object in buffer, wait for more data
                        break
                    
                    # Extract and parse the JSON object
                    obj_str = buffer[start:end+1]
                    buffer = buffer[end+1:]
                    
                    try:
                        obj = json.loads(obj_str)
                        candidates = obj.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            for part in parts:
                                text = part.get("text", "")
                                if text:
                                    yield text
                    except Exception:
                        pass
        except Exception as e:
            yield f"\n[Error connecting to Gemini: {str(e)}]"

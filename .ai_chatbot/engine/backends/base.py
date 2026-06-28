from typing import Generator, List, Dict, Optional

class BaseBackend:
    @property
    def name(self) -> str:
        raise NotImplementedError

    def is_available(self) -> bool:
        """Check if the backend is configured/available to use."""
        raise NotImplementedError

    def get_available_models(self) -> List[str]:
        """Get the list of available models for this backend."""
        raise NotImplementedError

    def generate_stream(
        self, 
        messages: List[Dict[str, str]], 
        system_prompt: str, 
        model: Optional[str] = None
    ) -> Generator[str, None, None]:
        """
        Generate a streaming response.
        Yields text chunks as they arrive.
        """
        raise NotImplementedError

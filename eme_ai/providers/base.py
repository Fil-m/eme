"""Base provider protocol — all AI providers must implement this."""
from abc import ABC, abstractmethod


class BaseProvider(ABC):
    name: str = 'base'

    @abstractmethod
    def generate(self, prompt: str, model: str, **kwargs) -> str:
        """Call the LLM and return the raw text response."""
        raise NotImplementedError

    @abstractmethod
    def list_models(self) -> list[str]:
        """Return available model names."""
        raise NotImplementedError

    @abstractmethod
    def is_online(self) -> bool:
        """True if the provider is reachable."""
        raise NotImplementedError

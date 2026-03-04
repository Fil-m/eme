"""Ollama local LLM provider."""
import requests
from .base import BaseProvider

OLLAMA_BASE = "http://localhost:11434"


class OllamaProvider(BaseProvider):
    name = 'ollama'

    def generate(self, prompt: str, model: str = 'llama3', **kwargs) -> str:
        resp = requests.post(
            f"{OLLAMA_BASE}/api/generate",
            json={'model': model, 'prompt': prompt, 'stream': False,
                  'options': {'temperature': 0.3, 'num_predict': 2048}},
            timeout=90
        )
        resp.raise_for_status()
        return resp.json().get('response', '')

    def list_models(self) -> list[str]:
        resp = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=5)
        resp.raise_for_status()
        return [m['name'] for m in resp.json().get('models', [])]

    def is_online(self) -> bool:
        try:
            requests.get(f"{OLLAMA_BASE}/api/tags", timeout=3)
            return True
        except Exception:
            return False

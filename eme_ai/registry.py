"""
Provider registry — returns the right provider instance by name.
Add new providers here.
"""
from .providers.ollama import OllamaProvider

_REGISTRY = {
    'ollama': OllamaProvider,
}


def get_provider(name: str = 'ollama'):
    cls = _REGISTRY.get(name)
    if cls is None:
        raise ValueError(f"Unknown AI provider: '{name}'. Available: {list(_REGISTRY)}")
    return cls()


def all_providers() -> list[dict]:
    result = []
    for name, cls in _REGISTRY.items():
        provider = cls()
        online = provider.is_online()
        models = provider.list_models() if online else []
        result.append({'name': name, 'online': online, 'models': models})
    return result

"""Abstract base scaffolder — all module scaffolders inherit this."""
from abc import ABC, abstractmethod


class BaseScaffolder(ABC):
    module: str = 'generic'

    @abstractmethod
    def build_prompt(self, context: dict) -> str:
        """Build the full prompt from context dict."""
        raise NotImplementedError

    @abstractmethod
    def parse_response(self, raw: str) -> dict:
        """Parse raw AI text into structured plan dict."""
        raise NotImplementedError

    @abstractmethod
    def apply(self, plan: dict, context: dict) -> dict:
        """Save the plan to DB and return a summary."""
        raise NotImplementedError

"""Provider abstraction so the service is not locked to a single LLM vendor."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Completion:
    text: str
    model: str
    input_tokens: int
    output_tokens: int


class LLMProvider(ABC):
    name: str = "base"

    @abstractmethod
    async def complete(self, system: str, prompt: str, max_tokens: int = 512) -> Completion:
        """Return a single completion for the prompt."""

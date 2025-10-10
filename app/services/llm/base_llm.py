# app/services/llm/base_llm.py
from abc import ABC, abstractmethod
from typing import Generator

class LLMBase(ABC):
    """Abstract base class for all LLM providers."""

    @abstractmethod
    def generate_answer(self, query: str, context: str) -> str:
        """Return a full, single response."""
        pass

    @abstractmethod
    def stream_answer(self, query: str, context: str) -> Generator[str, None, None]:
        """Yield response chunks as they arrive."""
        pass

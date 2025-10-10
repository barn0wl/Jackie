# app/services/llm/factory.py
import logging
from app.core.config import settings
from app.services.llm.base_llm import LLMBase
from app.services.llm.ollama_llm import OllamaLLMService

logger = logging.getLogger(__name__)

class LLMServiceFactory:
    """
    Factory for creating LLM service instances based on settings.LLM_PROVIDER.
    Example: LLM_PROVIDER=ollama / openai / groq
    """

    @staticmethod
    def create(provider: str | None = None) -> LLMBase:
        provider = provider or getattr(settings, "LLM_PROVIDER", "ollama").lower()
        logger.info(f"Initializing LLMServiceFactory with provider={provider}")

        if provider == "ollama":
            return OllamaLLMService()

        elif provider == "openai":
            raise NotImplementedError("OpenAILLMService is not implemented yet.")

        elif provider == "groq":
            raise NotImplementedError("GroqLLMService is not implemented yet.")

        else:
            raise ValueError(f"Unknown LLM provider: {provider}")

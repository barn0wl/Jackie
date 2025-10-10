# app/services/llm/ollama_llm.py
from typing import Dict, Generator, Optional
import logging

from app.core.config import settings
from app.services.llm.base_llm import LLMBase

try:
    import ollama
    from ollama._types import ChatResponse, GenerateResponse
except ImportError as e:
    raise RuntimeError(
        "The 'ollama' package is required. Install with: pip install ollama"
    ) from e

logger = logging.getLogger(__name__)

class OllamaLLMService(LLMBase):
    """
    Ollama implementation of the LLM service.
    Thin wrapper around Ollama's chat API.
    - Answers in French by default.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        host: Optional[str] = None,
        temperature: Optional[float] = None,
        num_ctx: Optional[int] = None,
    ):
        self.model_name = model_name or settings.OLLAMA_MODEL
        self.host = host or settings.OLLAMA_HOST
        self.temperature = (
            settings.OLLAMA_TEMPERATURE if temperature is None else float(temperature)
        )
        self.num_ctx = settings.OLLAMA_NUM_CTX if num_ctx is None else int(num_ctx)

        # Create a client instance with the host
        self.client = ollama.Client(host=self.host)

        logger.info(
            f"LLMService initialized: model={self.model_name}, host={self.host}, "
            f"temp={self.temperature}, num_ctx={self.num_ctx}"
        )

    @staticmethod
    def _build_messages(query: str, context: str) -> list[Dict[str, str]]:
        """
        Build a French-first prompt structure with clear instructions to ground on provided context.
        """
        system_prompt = (
            "Tu es un assistant et un agent de recherche et raisonnement nommé Jackie. "
            "Tu travailles pour une entreprise nommée Les Centaures Routiers. "
            "Réponds de manière concise, factuelle et polie, en FRANÇAIS. "
            "Utilise UNIQUEMENT les informations du CONTEXTE ci-dessous. "
            "Si une information est manquante ou incertaine, dis clairement que tu ne sais pas."
        )

        context_block = (
            "----- CONTEXTE -----\n"
            f"{context.strip()}\n"
            "--------------------"
        )

        user_prompt = (
            f"{context_block}\n\n"
            "QUESTION UTILISATEUR:\n"
            f"{query.strip()}"
        )

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def generate_answer(self, query: str, context: str) -> str:
        """
        One-shot non-streaming answer. Returns the final text.
        Uses stream=False for a single complete response.
        """
        messages = self._build_messages(query, context)
        try:
            resp = self.client.chat(
                model=self.model_name,
                messages=messages,
                options={
                    "temperature": self.temperature,
                    "num_ctx": self.num_ctx,
                },
                stream=False,
            )
        except Exception:
            logger.exception("Ollama chat call failed")
            raise

        # Handle different return types
        text = ""
        if isinstance(resp, dict):
            text = resp.get("response") or resp.get("message", {}).get("content", "")
        elif isinstance(resp, ChatResponse):
            text = getattr(resp.message, "content", "") or ""
        elif isinstance(resp, GenerateResponse):
            text = getattr(resp, "response", "") or ""
        else:
            logger.warning(f"Unexpected response type: {type(resp)}")

        if not text:
            logger.warning("LLM returned empty response")
        else:
            logger.debug(f"LLM response: {text[:80]}...")
        return text.strip()

    def stream_answer(self, query: str, context: str) -> Generator[str, None, None]:
        """
        Streaming generator that yields text chunks as they arrive from Ollama.
        Uses stream=True for incremental responses.
        """
        messages = self._build_messages(query, context)
        try:
            stream = self.client.chat(
                model=self.model_name,
                messages=messages,
                options={
                    "temperature": self.temperature,
                    "num_ctx": self.num_ctx,
                },
                stream=True,
            )
            for part in stream:
                # Streaming chunks may be dicts or ChatResponse objects
                if isinstance(part, dict):
                    content = part.get("response", "") or part.get("message", {}).get("content", "")
                elif isinstance(part, ChatResponse):
                    content = getattr(part.message, "content", "") or ""
                else:
                    content = ""
                if content:
                    yield content
        except Exception:
            logger.exception("Ollama streaming chat failed")
            raise

# app/services/llm_service.py

from typing import Dict, Generator, Optional
import logging

from app.core.config import settings

try:
    # pip install ollama
    import ollama
except ImportError as e:
    raise RuntimeError(
        "The 'ollama' package is required. Install with: pip install ollama"
    ) from e

logger = logging.getLogger(__name__)

class LLMService:
    """
    Thin wrapper around Ollama's chat API.
    - Answers in French by default.
    - Accepts retrieved context and a user question.
    - Supports both standard and streaming responses.
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

        # Keep context as-is; caller should ensure it fits (truncate upstream if needed)
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
        
        Response format (stream=False):
        {
            "model": "mistral:latest",
            "created_at": "...",
            "response": "The full answer text here...",
            "done": true,
            "context": [...],
            "total_duration": ...,
            ...
        }
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
                stream=False,  # Get complete response in one call
            )
        except Exception as e:
            logger.exception("Ollama chat call failed")
            raise

        # When stream=False, the response is in the "response" key
        if isinstance(resp, dict):
            text = resp.get("response", "")
        else:
            logger.warning(f"Unexpected response type: {type(resp)}")
            text = ""
        
        if not text:
            logger.warning("LLM returned empty response")
        else:
            logger.debug(f"LLM response length: {len(text)} characters")
        
        return text.strip()

    def stream_answer(self, query: str, context: str) -> Generator[str, None, None]:
        """
        Streaming generator that yields text chunks as they arrive from Ollama.
        Uses stream=True for incremental responses.
        
        Response format (stream=True):
        Each chunk: {"model": "...", "created_at": "...", "response": "chunk", "done": false}
        Final chunk: {"model": "...", "created_at": "...", "response": "", "done": true}
        
        Usage:
            for chunk in llm_service.stream_answer(query, context):
                print(chunk, end="", flush=True)
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
                stream=True,  # Get streaming response
            )
            
            for part in stream:
                # When stream=True, each part has "response" key with a chunk
                if isinstance(part, dict):
                    content = part.get("response", "")
                    if content:
                        yield content
                        
        except Exception as e:
            logger.exception("Ollama streaming chat failed")
            raise

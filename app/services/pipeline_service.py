from typing import Dict, Any, Generator, Optional
import logging

from app.services.retriever_service import RetrieverService
from app.services.llm.factory import LLMServiceFactory

logger = logging.getLogger(__name__)

class PipelineService:
    """
    High-level RAG pipeline that orchestrates:
      1. Retriever (context gathering)
      2. LLM (response generation)
    """

    def __init__(
        self,
        top_k: int = 3,
        provider: Optional[str] = None,
        stream: bool = False,
    ):
        """
        Initialize the RAG pipeline.

        Args:
            top_k: Number of context chunks to retrieve
            provider: LLM provider (ollama/openai/groq)
            stream: Whether to enable streaming responses
        """
        self.top_k = top_k
        self.stream_bool = stream
        self.retriever = RetrieverService(top_k=top_k)
        self.llm = LLMServiceFactory.create(provider)

        logger.info(
            f"PipelineService initialized with provider={type(self.llm).__name__}, top_k={top_k}, stream={stream}"
        )

    # --------------------------------------------------------------------------
    # MAIN ENTRY POINT
    # --------------------------------------------------------------------------
    def run(self, query: str) -> Dict[str, Any]:
        """
        Execute the RAG pipeline (non-streaming).

        Returns:
            {
                "query": str,
                "context": str,
                "answer": str,
                "sources": [ ... ],
            }
        """
        logger.info(f"Running RAG pipeline for query: {query[:80]}...")

        # Step 1: Retrieve context
        context = self.retriever.retrieve_context(query)
        if not context:
            logger.warning("No context found for query. Proceeding without retrieval.")
            context = "Aucun contexte pertinent trouvé dans la base documentaire."

        # Step 2: Generate answer
        answer = self.llm.generate_answer(query, context)

        # Step 3: Package results
        docs = self.retriever.retrieve(query)
        sources = [
            doc.get("metadata", {}).get("source") or doc.get("metadata", {}).get("filename", "unknown")
            for doc in docs
        ]

        result = {
            "query": query,
            "context": context,
            "answer": answer,
            "sources": list(filter(None, sources)),
        }

        logger.info(f"Pipeline completed. Answer length: {len(answer)} chars")
        return result

    # --------------------------------------------------------------------------
    # STREAMING MODE
    # --------------------------------------------------------------------------
    def stream(self, query: str) -> Generator[str, None, None]:
        """
        Streaming mode for interactive UIs (like chatbots).

        Yields: answer chunks from the LLM as they arrive.
        """
        logger.info(f"Running streaming RAG pipeline for query: {query[:80]}...")

        context = self.retriever.retrieve_context(query)
        if not context:
            context = "Aucun contexte pertinent trouvé dans la base documentaire."

        try:
            for chunk in self.llm.stream_answer(query, context):
                yield chunk
        except Exception:
            logger.exception("Pipeline streaming failed")
            raise

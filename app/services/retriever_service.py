# app/services/retriever_service.py
from typing import List, Dict, Any
import logging

from app.services.embeddings_service import EmbeddingsService
from app.services.vector_store_service import get_vector_store

logger = logging.getLogger(__name__)

class RetrieverService:
    """
    Service responsible for retrieving the top-K most relevant document chunks
    given a user's natural language query.
    """

    def __init__(self, top_k: int = 3):
        """
        Initialize the RetrieverService.

        Args:
            top_k: Number of top results to retrieve (default: 3).
        """
        self.top_k = top_k
        self.embedder = EmbeddingsService()
        self.vector_store = get_vector_store()

    def retrieve(self, query: str) -> List[Dict[str, Any]]:
        """
        Convert a user query into an embedding and retrieve the most similar document chunks.

        Args:
            query: The user's text query.

        Returns:
            List of retrieved document chunks with metadata and similarity scores.
        """
        if not query or not query.strip():
            logger.warning("Empty query string provided to RetrieverService.")
            return []

        logger.info(f"Embedding query: '{query[:50]}...'")
        query_embedding = self.embedder.embed_text(query)
        logger.debug(f"Generated query embedding (len={len(query_embedding)})")

        results = self.vector_store.query_similar(
            query_embedding=query_embedding,
            n_results=self.top_k
        )

        if not results:
            logger.info("No relevant chunks found in vector store.")
            return []

        logger.info(f"Retrieved {len(results)} relevant chunks from vector store.")
        return results

    def retrieve_context(self, query: str, separator: str = "\n\n") -> str:
        """
        Retrieve top-K chunks and assemble them into a single string context block
        for LLM prompting.

        Args:
            query: User question or input.
            separator: String used to separate each chunk in the combined context.

        Returns:
            Combined context string.
        """
        docs = self.retrieve(query)
        if not docs:
            return ""

        context_parts = []
        for doc in docs:
            meta = doc.get("metadata", {})
            source = meta.get("source") or meta.get("filename") or "unknown source"
            content = doc["content"]
            context_parts.append(f"Source: {source}\n{content}")

        combined_context = separator.join(context_parts)
        logger.debug(f"Combined context length: {len(combined_context)} characters")
        return combined_context

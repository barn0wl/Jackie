# app/services/vector_store_service.py
import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any
from app.core.config import settings
from app.models.document_chunk import DocumentChunk
import numpy as np
import logging

logger = logging.getLogger(__name__)

_vector_store_instance = None

class VectorStoreService:
    """
    Service for managing vector storage and retrieval using ChromaDB.
    """

    def __init__(self, collection_name: str = "company_knowledge"):
        self.client = chromadb.Client(
            ChromaSettings(
                persist_directory=settings.CHROMA_PATH,  # local persistence
                is_persistent=True
            )
        )
        self.collection = self.client.get_or_create_collection(collection_name)

    def add_chunks(self, chunks: List[DocumentChunk], embeddings: List[List[float]]):
        if not chunks or not embeddings:
            logger.warning("No chunks or embeddings provided to add_chunks(). Skipping.")
            return
        
        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks and embeddings must match.")
        
        ids = [chunk.id or f"doc_{i}" for i, chunk in enumerate(chunks)]
        documents = [chunk.content for chunk in chunks]

        # Merge model info into metadata
        metadatas = []
        for chunk in chunks:
            meta = dict(chunk.metadata or {})
            meta["embedding_model"] = settings.EMBEDDING_MODEL
            metadatas.append(meta)

        embeddings_array = np.array(embeddings, dtype=np.float32)

        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings_array,
            metadatas=metadatas
        )

    def query_similar(
        self, query_embedding: List[float],
        n_results: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Query the most similar documents to a given embedding.
        """
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )

        if not results or not results["documents"] or not results["documents"][0]:
            logger.info("No matching documents found in vector store.")
            return []

        matched_docs = []
        for i in range(len(results["documents"][0])):
            matched_docs.append({
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                "id": results["ids"][0][i] if results["ids"] else None,
                "score": (
                    results["distances"][0][i]
                    if "distances" in results and results["distances"] else None
                ),
            })

        return matched_docs

    def count(self) -> int:
        """Return the total number of stored documents."""
        return self.collection.count()

    def clear(self):
        """Delete all documents in the collection."""
        self.collection.delete(ids=self.collection.get()["ids"])

def get_vector_store() -> VectorStoreService:
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = VectorStoreService()
    return _vector_store_instance

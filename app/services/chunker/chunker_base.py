# app/services/chunker/chunker_base.py
from abc import ABC, abstractmethod
from typing import List, Any, Optional
from app.models.document_chunk import DocumentChunk


class ChunkerBase(ABC):
    """Abstract base class for all chunking strategies."""
    
    @abstractmethod
    def chunk_document(
        self, 
        text: str, 
        metadata: Optional[dict] = None
    ) -> List[DocumentChunk]:
        """
        Split text into semantic chunks and return DocumentChunk objects.
        
        Args:
            text: The text to chunk
            metadata: Optional metadata to attach to all chunks
            
        Returns:
            List of DocumentChunk objects
        """
        pass

# app/services/chunker/factory.py
from typing import Optional
import logging
from app.core.config import settings
from app.services.chunker.chunker_base import ChunkerBase
from app.services.chunker.recursive_text_chunker import RecursiveTextChunker

logger = logging.getLogger(__name__)


class ChunkerFactory:
    """Factory for creating chunker instances."""
    
    @staticmethod
    def create(
        chunker_type: Optional[str] = None,
        **kwargs
    ) -> ChunkerBase:
        """
        Create a chunker instance.
        
        Args:
            chunker_type: Type of chunker to create ('recursive', 'semantic', etc.)
            **kwargs: Parameters passed to the chunker constructor
            
        Returns:
            ChunkerBase instance
        """
        chunker_type = chunker_type or getattr(
            settings, "CHUNKER_TYPE", "recursive"
        ).lower()
        
        logger.info(f"Creating chunker of type: {chunker_type}")
        
        if chunker_type == "recursive":
            # Get chunking parameters from settings or use defaults
            chunk_size = getattr(settings, "CHUNK_SIZE", 1000)
            chunk_overlap = getattr(settings, "CHUNK_OVERLAP", 200)
            
            return RecursiveTextChunker(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                **kwargs
            )
        
        # Add more chunker types as needed
        # elif chunker_type == "semantic":
        #     return SemanticChunker(**kwargs)
        # elif chunker_type == "fixed":
        #     return FixedSizeChunker(**kwargs)
        
        else:
            raise ValueError(f"Unknown chunker type: {chunker_type}")

# app/services/ingestion_service.py
from typing import List, Optional, Dict, Any
import logging
from app.services.chunker.factory import ChunkerFactory
from app.services.embeddings_service import EmbeddingsService
from app.services.vector_store_service import get_vector_store
from app.models.document_chunk import DocumentChunk

logger = logging.getLogger(__name__)


class IngestionService:
    """
    Service that orchestrates the entire ingestion pipeline:
    1. Chunking documents
    2. Generating embeddings
    3. Storing in vector database
    """
    
    def __init__(
        self,
        chunker_type: Optional[str] = None,
        embedding_model: Optional[str] = None,
        use_text_cleaning: bool = True,
        text_cleaner_kwargs: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the ingestion service.
        
        Args:
            chunker_type: Type of chunker to use
            embedding_model: Name of the embedding model to use
            use_text_cleaning: Whether to clean text before chunking
            text_cleaner_kwargs: Additional parameters for text cleaner
        """
        self.chunker = ChunkerFactory.create(chunker_type)
        self.embedder = EmbeddingsService(model_name=embedding_model)
        self.vector_store = get_vector_store()
        self.use_text_cleaning = use_text_cleaning
        
        # Initialize text cleaner if needed
        if self.use_text_cleaning:
            from app.services.text_cleaner_service import TextCleanerService
            self.text_cleaner = TextCleanerService(**(text_cleaner_kwargs or {}))
        
        logger.info(
            f"IngestionService initialized with chunker={type(self.chunker).__name__}, "
            f"embedder={self.embedder.model_name}, text_cleaning={use_text_cleaning}"
        )
    
    def ingest_text(
        self,
        text: str,
        source_id: Optional[str] = None,
        source_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[DocumentChunk]:
        """
        Process a single text document through the ingestion pipeline.
        
        Args:
            text: The document text to ingest
            source_id: Identifier for the source document
            source_type: Type of the source document
            metadata: Additional metadata
            
        Returns:
            List of DocumentChunk objects that were ingested
        """
        if not text or not text.strip():
            logger.warning("Empty text provided to ingest_text")
            return []
        
        # Prepare metadata
        full_metadata = metadata or {}
        if source_id:
            full_metadata["source_id"] = source_id
        if source_type:
            full_metadata["source_type"] = source_type
        
        logger.info(f"Ingesting text from source: {source_id or 'unknown'}")
        
        # Clean text before chunking
        if self.use_text_cleaning:
            logger.debug("Cleaning text before chunking...")
            text = self.text_cleaner.clean_for_chunking(
                text=text,
                metadata=full_metadata
            )
            logger.debug(f"Text cleaned (length: {len(text)} chars)")
        
        # Step 1: Chunk the text
        chunks = self.chunker.chunk_document(text, full_metadata)
        logger.info(f"Created {len(chunks)} chunks from text")
        
        if not chunks:
            return []
        
        # Step 2: Generate embeddings for all chunks
        chunk_texts = [chunk.content for chunk in chunks]
        embeddings = self.embedder.embed_texts(chunk_texts)
        logger.info(f"Generated embeddings for {len(embeddings)} chunks")
        
        # Step 3: Store in vector database
        self.vector_store.add_chunks(chunks, embeddings)
        logger.info(f"Successfully stored {len(chunks)} chunks in vector store")
        
        return chunks
    
    def ingest_documents(
        self,
        documents: List[Dict[str, Any]]
    ) -> List[DocumentChunk]:
        """
        Batch ingest multiple documents.
        
        Args:
            documents: List of dictionaries, each containing:
                - text: The document text
                - source_id: (optional) Source identifier
                - source_type: (optional) Source type
                - metadata: (optional) Additional metadata
                
        Returns:
            List of all DocumentChunk objects that were ingested
        """
        all_chunks = []
        
        for i, doc in enumerate(documents):
            try:
                text = doc.get("text", "")
                source_id = doc.get("source_id", f"doc_{i}")
                source_type = doc.get("source_type")
                metadata = doc.get("metadata", {})
                
                chunks = self.ingest_text(
                    text=text,
                    source_id=source_id,
                    source_type=source_type,
                    metadata=metadata
                )
                all_chunks.extend(chunks)
                
            except Exception as e:
                logger.error(f"Failed to ingest document {i}: {str(e)}")
                continue
        
        logger.info(f"Batch ingestion complete. Total chunks ingested: {len(all_chunks)}")
        return all_chunks
    
    def get_ingestion_stats(self) -> Dict[str, Any]:
        """Get statistics about ingested data."""
        total_chunks = self.vector_store.count()
        
        return {
            "total_chunks": total_chunks,
            "chunker_type": type(self.chunker).__name__,
            "embedding_model": self.embedder.model_name,
        }

# app/ingestion/text_cleaner/document_cleaner.py
"""
Main text cleaning functions for both raw text and DocumentChunk objects.
"""

import logging
from typing import Optional, List
from app.models.document_chunk import DocumentChunk
from .base import clean_and_normalize_text
from .config import TextCleanerConfig, DEFAULT_CONFIG

logger = logging.getLogger(__name__)

def clean_text(
    text: str, 
    config: TextCleanerConfig = DEFAULT_CONFIG,
    source_type: Optional[str] = None
) -> str:
    """
    Clean and normalize arbitrary text content.
    
    Args:
        text: Raw text input to clean
        config: Text cleaning configuration
        source_type: Optional source type hint for source-specific cleaning
    
    Returns:
        Cleaned and normalized text
    """
    if not text:
        return text
    
    try:
        # Determine if we should apply email-specific rules
        remove_email_patterns = source_type and source_type.lower() in ('email', 'outlook_email')
        
        cleaned_text = clean_and_normalize_text(
            text, 
            config=config,
            remove_email_patterns=remove_email_patterns
        )
        
        logger.debug(f"Cleaned text: {len(text)} -> {len(cleaned_text)} characters")
        return cleaned_text
        
    except Exception as e:
        logger.error(f"Error cleaning text: {e}")
        return text  # Return original text on error

def clean_document_chunk(
    chunk: DocumentChunk, 
    config: TextCleanerConfig = DEFAULT_CONFIG
) -> DocumentChunk:
    """
    Create a new DocumentChunk with cleaned content.
    
    Args:
        chunk: Original DocumentChunk to clean
        config: Text cleaning configuration
    
    Returns:
        New DocumentChunk with cleaned content (metadata preserved)
    """
    if not chunk.content:
        return chunk
    
    try:
        # Extract source type from metadata for source-specific cleaning
        source_type = chunk.metadata.get('source') if chunk.metadata else None
        
        cleaned_content = clean_text(
            chunk.content, 
            config=config,
            source_type=source_type
        )
        
        # Return new DocumentChunk with cleaned content
        return DocumentChunk(
            id=chunk.id,
            content=cleaned_content,
            metadata=chunk.metadata.copy() if chunk.metadata else {}
        )
        
    except Exception as e:
        logger.error(f"Error cleaning document chunk {chunk.id}: {e}")
        return chunk  # Return original chunk on error

def clean_document_chunks(
    chunks: List[DocumentChunk],
    config: TextCleanerConfig = DEFAULT_CONFIG
) -> List[DocumentChunk]:
    """
    Clean a list of DocumentChunks.
    
    Args:
        chunks: List of DocumentChunks to clean
        config: Text cleaning configuration
    
    Returns:
        List of cleaned DocumentChunks
    """
    return [clean_document_chunk(chunk, config) for chunk in chunks]

# app/services/text_cleaner_service.py

import logging
from typing import Dict, Any, Optional, List

from app.ingestion.text_cleaner.factory import TextCleanerFactory, TextCleanerType
from app.ingestion.text_cleaner.base_text_cleaner import BaseTextCleaner

logger = logging.getLogger(__name__)


class TextCleanerService:
    """
    Service for cleaning text before chunking and embedding.
    Integrates with the existing RAG pipeline.
    """
    
    def __init__(self, default_cleaner_type: str = TextCleanerType.GENERIC.value):
        """
        Initialize text cleaner service.
        
        Args:
            default_cleaner_type: Default cleaner type to use
        """
        self.default_cleaner_type = default_cleaner_type
        logger.info(f"TextCleanerService initialized with default: {default_cleaner_type}")
    
    def clean_text(
        self,
        text: str,
        source_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **cleaner_kwargs
    ) -> str:
        """
        Clean text using appropriate cleaner.
        
        Args:
            text: Text to clean
            source_type: Type of content source
            metadata: Additional metadata for cleaner
            **cleaner_kwargs: Parameters for cleaner initialization
            
        Returns:
            Cleaned text
        """
        if not text or not text.strip():
            return ""
        
        # Determine cleaner type
        cleaner_type = source_type or self.default_cleaner_type
        
        # Get appropriate cleaner
        if metadata:
            cleaner = TextCleanerFactory.create_from_metadata(metadata, **cleaner_kwargs)
        else:
            cleaner = TextCleanerFactory.create(cleaner_type, **cleaner_kwargs)
        
        # Clean the text
        try:
            cleaned_text = cleaner.clean(text, metadata)
            logger.debug(f"Text cleaned: {len(text)} -> {len(cleaned_text)} chars")
            return cleaned_text
        except Exception as e:
            logger.error(f"Error cleaning text: {e}")
            # Return original text if cleaning fails
            return text
    
    def batch_clean(
        self,
        texts: List[str],
        source_types: Optional[List[str]] = None,
        metadata_list: Optional[List[Dict[str, Any]]] = None,
        **cleaner_kwargs
    ) -> List[str]:
        """
        Clean multiple texts in batch.
        
        Args:
            texts: List of texts to clean
            source_types: List of source types (optional)
            metadata_list: List of metadata dictionaries (optional)
            **cleaner_kwargs: Parameters for cleaner initialization
            
        Returns:
            List of cleaned texts
        """
        cleaned_texts = []
        
        for i, text in enumerate(texts):
            source_type = source_types[i] if source_types and i < len(source_types) else None
            metadata = metadata_list[i] if metadata_list and i < len(metadata_list) else None
            
            cleaned_text = self.clean_text(
                text=text,
                source_type=source_type,
                metadata=metadata,
                **cleaner_kwargs
            )
            
            cleaned_texts.append(cleaned_text)
        
        return cleaned_texts
    
    def clean_for_chunking(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Specialized cleaning optimized for chunking.
        Removes noise while preserving semantic boundaries.
        
        Args:
            text: Text to clean
            metadata: Document metadata
            
        Returns:
            Text ready for chunking
        """
        # Basic cleaning first
        cleaned_text = self.clean_text(text, metadata=metadata)
        
        # Additional processing for chunking
        import re
        
        # Ensure proper paragraph separation
        cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
        
        # Normalize French quotation marks
        cleaned_text = cleaned_text.replace('«', '"').replace('»', '"')
        cleaned_text = cleaned_text.replace('“', '"').replace('”', '"')
        
        return cleaned_text.strip()

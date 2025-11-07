import logging
from enum import Enum
from typing import Dict, Any, Union
from app.ingestion.text_cleaner.base_text_cleaner import BaseTextCleaner
from app.ingestion.text_cleaner.email_text_cleaner import EmailTextCleaner
from app.ingestion.text_cleaner.document_text_cleaner import DocumentTextCleaner

logger = logging.getLogger(__name__)


class TextCleanerType(str, Enum):
    EMAIL = "email"
    DOCUMENT = "document"
    GENERIC = "document"


class TextCleanerFactory:
    """
    Factory for creating appropriate text cleaner instances based on source type.
    
    This follows the Factory pattern to provide the right cleaning strategy
    for different content types (emails, PDFs, Word docs, etc.).
    """
    
    # Mapping of source types to cleaner classes
    _CLEANER_REGISTRY: Dict[str, type] = {
        "email": EmailTextCleaner,
        "email_simule": EmailTextCleaner,
        "outlook_email": EmailTextCleaner,
        "document": DocumentTextCleaner,
        "pdf": DocumentTextCleaner,
        "word": DocumentTextCleaner,
        "txt": DocumentTextCleaner,
    }
    
    @classmethod
    def create(
        cls,
        source_type:  Union[str, TextCleanerType],
        **kwargs
    ) -> BaseTextCleaner:
        """
        Create and return an appropriate text cleaner for the given source type.
        
        Args:
            source_type: Type of content source (email, pdf, document, etc.)
            **kwargs: Additional configuration parameters for the specific cleaner
            
        Returns:
            Configured text cleaner instance
            
        Raises:
            ValueError: If source_type is not recognized
        """
        source_type_lower = source_type.lower().strip()
        
        cleaner_class = cls._CLEANER_REGISTRY.get(source_type_lower)
        
        if cleaner_class is None:
            logger.warning(
                f"Unknown source type '{source_type}', falling back to DocumentTextCleaner"
            )
            cleaner_class = DocumentTextCleaner
        
        logger.info(f"Creating {cleaner_class.__name__} for source type '{source_type}'")
        return cleaner_class(**kwargs)
    
    @classmethod
    def create_from_metadata(
        cls,
        metadata: Dict[str, Any],
        **kwargs
    ) -> BaseTextCleaner:
        """
        Create a text cleaner based on metadata information.
        
        This method infers the appropriate cleaner from document metadata,
        checking for 'source', 'type', or 'filename' fields.
        
        Args:
            metadata: Document metadata dictionary
            **kwargs: Additional configuration parameters
            
        Returns:
            Configured text cleaner instance
        """
        # Try different metadata keys to determine source type
        source_type = (
            metadata.get("source") or
            metadata.get("type") or
            metadata.get("source_type") or
            "document"
        )
        
        # If source is a filename, infer type from extension
        if "." in str(source_type):
            extension = str(source_type).split(".")[-1].lower()
            if extension in ["pdf", "docx", "doc", "txt"]:
                source_type = extension
        
        return cls.create(source_type, **kwargs)
    
    @classmethod
    def register_cleaner(cls, source_type: str, cleaner_class: type):
        """
        Register a new text cleaner type.
        
        This allows for easy extension of the factory with custom cleaners.
        
        Args:
            source_type: Identifier for the source type
            cleaner_class: Text cleaner class (must inherit from BaseTextCleaner)
        """
        if not issubclass(cleaner_class, BaseTextCleaner):
            raise TypeError(f"{cleaner_class} must inherit from BaseTextCleaner")
        
        cls._CLEANER_REGISTRY[source_type.lower()] = cleaner_class
        logger.info(f"Registered {cleaner_class.__name__} for source type '{source_type}'")
    
    @classmethod
    def get_supported_types(cls) -> list[str]:
        """Return list of supported source types."""
        return list(cls._CLEANER_REGISTRY.keys())
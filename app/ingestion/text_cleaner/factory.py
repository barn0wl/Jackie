# app/ingestion/text_cleaner/factory.py

import logging
from enum import Enum
from typing import Dict, Any, Union, Type

from app.ingestion.text_cleaner.base_text_cleaner import BaseTextCleaner
from app.ingestion.text_cleaner.email_text_cleaner import EmailTextCleaner
from app.ingestion.text_cleaner.document_text_cleaner import DocumentTextCleaner
from app.ingestion.text_cleaner.generic_text_cleaner import GenericTextCleaner

logger = logging.getLogger(__name__)


class TextCleanerType(str, Enum):
    """Supported text cleaner types."""
    EMAIL = "email"
    DOCUMENT = "document"
    GENERIC = "generic"


class TextCleanerFactory:
    """
    Factory for creating appropriate text cleaner instances.
    Follows SOLID principles for extensibility.
    """
    
    # Registry of cleaner types
    _CLEANER_REGISTRY: Dict[str, Type[BaseTextCleaner]] = {
        TextCleanerType.EMAIL.value: EmailTextCleaner,
        TextCleanerType.DOCUMENT.value: DocumentTextCleaner,
        TextCleanerType.GENERIC.value: GenericTextCleaner,
    }
    
    # Mapping from file extensions/source types to cleaner types
    _TYPE_MAPPING: Dict[str, str] = {
        # Email types
        "email": TextCleanerType.EMAIL.value,
        "outlook": TextCleanerType.EMAIL.value,
        "gmail": TextCleanerType.EMAIL.value,
        "exchange": TextCleanerType.EMAIL.value,
        
        # Document types
        "pdf": TextCleanerType.DOCUMENT.value,
        "doc": TextCleanerType.DOCUMENT.value,
        "docx": TextCleanerType.DOCUMENT.value,
        "txt": TextCleanerType.DOCUMENT.value,
        "rtf": TextCleanerType.DOCUMENT.value,
        "odt": TextCleanerType.DOCUMENT.value,
        "markdown": TextCleanerType.DOCUMENT.value,
        "md": TextCleanerType.DOCUMENT.value,
        
        # Web/other
        "html": TextCleanerType.DOCUMENT.value,
        "webpage": TextCleanerType.DOCUMENT.value,
        "url": TextCleanerType.DOCUMENT.value,
    }
    
    @classmethod
    def create(
        cls,
        source_type: Union[str, TextCleanerType],
        **kwargs
    ) -> BaseTextCleaner:
        """
        Create a text cleaner for the given source type.
        
        Args:
            source_type: Type of content source
            **kwargs: Additional parameters for cleaner initialization
            
        Returns:
            Configured text cleaner instance
        """
        # Normalize source type
        if isinstance(source_type, TextCleanerType):
            cleaner_type = source_type.value
        else:
            cleaner_type = cls._normalize_source_type(source_type)
        
        # Get cleaner class
        cleaner_class = cls._CLEANER_REGISTRY.get(cleaner_type, GenericTextCleaner)
        
        logger.info(f"Creating {cleaner_class.__name__} for source type '{source_type}'")
        
        try:
            return cleaner_class(**kwargs)
        except Exception as e:
            logger.error(f"Failed to create cleaner {cleaner_class.__name__}: {e}")
            return GenericTextCleaner(**kwargs)
    
    @classmethod
    def create_from_metadata(
        cls,
        metadata: Dict[str, Any],
        **kwargs
    ) -> BaseTextCleaner:
        """
        Create text cleaner based on metadata.
        
        Args:
            metadata: Document metadata
            **kwargs: Additional parameters
            
        Returns:
            Configured text cleaner
        """
        source_type = cls._infer_source_type_from_metadata(metadata)
        return cls.create(source_type, **kwargs)
    
    @classmethod
    def _normalize_source_type(cls, source_type: str) -> str:
        """Normalize source type to a standard cleaner type."""
        if not source_type:
            return TextCleanerType.GENERIC.value
        
        source_type_lower = source_type.lower().strip()
        
        # Check direct mapping
        if source_type_lower in cls._TYPE_MAPPING:
            return cls._TYPE_MAPPING[source_type_lower]
        
        # Check file extension
        if "." in source_type_lower:
            extension = source_type_lower.split(".")[-1].lower()
            if extension in cls._TYPE_MAPPING:
                return cls._TYPE_MAPPING[extension]
        
        # Default to generic
        return TextCleanerType.GENERIC.value
    
    @classmethod
    def _infer_source_type_from_metadata(cls, metadata: Dict[str, Any]) -> str:
        """Infer source type from metadata."""
        # Try different metadata keys
        possible_keys = ["source_type", "type", "source", "file_type", "extension", "content_type"]
        
        for key in possible_keys:
            if key in metadata and metadata[key]:
                return str(metadata[key])
        
        # Check filename
        if "filename" in metadata and metadata["filename"]:
            return metadata["filename"]
        
        # Default
        return TextCleanerType.GENERIC.value
    
    @classmethod
    def register_cleaner(
        cls,
        source_type: str,
        cleaner_class: Type[BaseTextCleaner]
    ):
        """
        Register a new cleaner type.
        
        Args:
            source_type: Source type identifier
            cleaner_class: Cleaner class (must inherit from BaseTextCleaner)
        """
        if not issubclass(cleaner_class, BaseTextCleaner):
            raise TypeError(f"{cleaner_class} must inherit from BaseTextCleaner")
        
        cls._TYPE_MAPPING[source_type.lower()] = source_type.lower()
        cls._CLEANER_REGISTRY[source_type.lower()] = cleaner_class
        
        logger.info(f"Registered {cleaner_class.__name__} for source type '{source_type}'")
    
    @classmethod
    def get_supported_types(cls) -> list[str]:
        """Get list of supported source types."""
        return list(cls._TYPE_MAPPING.keys())

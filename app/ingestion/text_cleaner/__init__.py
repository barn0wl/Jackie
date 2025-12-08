"""
Text Cleaner Module

This module provides text cleaning capabilities for various content types.
It removes noise while preserving essential information for RAG pipelines.

Main components:
- BaseTextCleaner: Abstract base class for all cleaners
- EmailTextCleaner: Specialized cleaner for email content
- DocumentTextCleaner: General-purpose cleaner for documents
- TextCleanerFactory: Factory for creating appropriate cleaners

Usage:
    from app.ingestion.text_cleaner import TextCleanerFactory
    
    # Create cleaner by source type
    cleaner = TextCleanerFactory.create("email")
    cleaned_text = cleaner.clean(raw_text, metadata)
    
    # Or create from metadata
    cleaner = TextCleanerFactory.create_from_metadata(document.metadata)
    cleaned_text = cleaner.clean(document.content, document.metadata)
"""

from app.ingestion.text_cleaner.base_text_cleaner import BaseTextCleaner
from app.ingestion.text_cleaner.email_text_cleaner import EmailTextCleaner
from app.ingestion.text_cleaner.document_text_cleaner import DocumentTextCleaner
from app.ingestion.text_cleaner.factory import TextCleanerFactory, TextCleanerType

__all__ = [
    "BaseTextCleaner",
    "EmailTextCleaner",
    "DocumentTextCleaner",
    "TextCleanerFactory",
    "TextCleanerType"
]

__version__ = "1.0.0"
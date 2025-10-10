# app/ingestion/base_email_loader.py

import logging
from abc import ABC, abstractmethod
from typing import List, Dict
from datetime import datetime

from app.models.document_chunk import DocumentChunk

logger = logging.getLogger(__name__)

class BaseEmailLoader(ABC):
    """
    Abstract base class for email loaders.
    Defines the interface that all email loaders must implement.
    """
    
    @abstractmethod
    def load_emails(self) -> List[Dict]:
        """Fetch emails and return structured dictionaries."""
        pass
    
    @abstractmethod
    def authenticate(self):
        """Authenticate to the email service."""
        pass
    
    def to_document_chunks(self, emails: List[Dict]) -> List[DocumentChunk]:
        """Convert raw email dicts into DocumentChunk instances with metadata."""
        chunks: List[DocumentChunk] = []
        for email in emails:
            meta = {
                "source": self.get_source_name(),
                "sender": email["sender"],
                "subject": email["subject"],
                "date": email["date"].isoformat() if isinstance(email["date"], datetime) else str(email["date"]),
            }
            chunks.append(
                DocumentChunk(
                    id=email["id"],
                    content=email["body"],
                    metadata=meta,
                )
            )
        return chunks
    
    def get_source_name(self) -> str:
        """Return the source name for this loader (used in metadata)."""
        return "email"

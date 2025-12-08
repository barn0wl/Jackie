# app/ingestion/text_cleaner/generic_text_cleaner.py

import re
import logging
from typing import Dict, Any, Optional

from app.ingestion.text_cleaner.base_text_cleaner import BaseTextCleaner

logger = logging.getLogger(__name__)


class GenericTextCleaner(BaseTextCleaner):
    """
    Generic text cleaner for unknown source types.
    Performs basic cleaning suitable for most text content.
    """
    
    def __init__(self):
        """Initialize generic cleaner."""
        super().__init__()
    
    def clean(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Perform basic text cleaning.
        
        Args:
            text: Raw text to clean
            metadata: Optional metadata
            
        Returns:
            Cleaned text
        """
        if not text or not text.strip():
            return ""
        
        # Basic cleaning pipeline
        text = self._remove_html_tags(text)
        text = self._remove_control_chars(text)
        text = self._normalize_whitespace(text)
        text = self._remove_excessive_special_chars(text)
        
        return text.strip()
    
    def _remove_html_tags(self, text: str) -> str:
        """Remove HTML tags."""
        return re.sub(r'<[^>]+>', ' ', text)
    
    def _remove_control_chars(self, text: str) -> str:
        """Remove control characters."""
        return re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)

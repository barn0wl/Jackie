# app/ingestion/text_cleaner/base_text_cleaner.py

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class BaseTextCleaner(ABC):
    """
    Abstract base class for all text cleaners.
    Each cleaner must implement the clean() method.
    """

    @abstractmethod
    def clean(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Clean and normalize text content.
        
        Args:
            text: Raw text content to clean
            metadata: Optional metadata that might inform cleaning strategy
                    (e.g., source type, sender, date, language)
                    
        Returns:
            Cleaned text ready for further processing
        """
        pass
    
    def get_cleaner_name(self) -> str:
        """Return the name/type of this cleaner for logging purposes."""
        return self.__class__.__name__.replace("TextCleaner", "").lower()

    def _normalize_whitespace(self, text: str) -> str:
        """
        Common utility: normalize excessive whitespace while preserving structure.
        
        Args:
            text: Text with potentially messy whitespace
            
        Returns:
            Text with normalized whitespace
        """
        import re
        # Replace multiple spaces with single space
        text = re.sub(r' +', ' ', text)
        # Replace multiple newlines with maximum 2 (preserve paragraphs)
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Remove trailing/leading whitespace from each line
        lines = [line.strip() for line in text.split('\n')]
        return '\n'.join(lines).strip()

    def _remove_excessive_special_chars(self, text: str) -> str:
        """
        Remove excessive special characters that add no semantic value.
        
        Args:
            text: Text potentially containing noise characters
            
        Returns:
            Text with reduced special character noise
        """
        import re
        # Remove excessive dashes, underscores, equals signs
        text = re.sub(r'[-_=]{3,}', '', text)
        # Remove non-breaking spaces and other unicode whitespace
        text = text.replace('\xa0', ' ')
        text = text.replace('\u200b', '')  # Zero-width space
        return text

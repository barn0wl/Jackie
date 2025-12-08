import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class BaseTextCleaner(ABC):
    """
    Abstract base class for text cleaning strategies.
    Defines the interface that all text cleaners must implement.
    
    Each cleaner is responsible for:
    - Removing noise (greetings, signatures, disclaimers, etc.)
    - Normalizing whitespace and formatting
    - Preserving essential information
    - Returning cleaned text ready for chunking/embedding
    """
    
    @abstractmethod
    def clean(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Clean and normalize raw text content.
        
        Args:
            text: Raw text content to clean
            metadata: Optional metadata that might inform cleaning strategy
                     (e.g., source type, sender, date)
        
        Returns:
            Cleaned text ready for further processing
        """
        pass
    
    @abstractmethod
    def get_cleaner_name(self) -> str:
        """Return the name/type of this cleaner for logging purposes."""
        pass
    
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
        # Remove excessive dashes, underscores, equals signs (often used as separators)
        text = re.sub(r'[-_=]{3,}', '', text)
        # Remove non-breaking spaces and other unicode whitespace
        text = text.replace('\xa0', ' ')
        text = text.replace('\u200b', '')  # Zero-width space
        return text
    


@dataclass
class CleaningContext:
        metadata: Dict[str, Any] = field(default_factory=dict)

class TextCleaningError(ValueError):
        """Raised when a cleaner receives unsupported input."""
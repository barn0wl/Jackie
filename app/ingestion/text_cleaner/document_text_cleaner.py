import logging
import re
from typing import Dict, Any, Optional
from app.ingestion.text_cleaner.base_text_cleaner import BaseTextCleaner

logger = logging.getLogger(__name__)

class DocumentTextCleaner(BaseTextCleaner):
    """
    General-purpose text cleaner for documents (PDFs, Word docs, etc.).
    
    Focuses on:
    - Removing headers/footers
    - Cleaning page numbers
    - Normalizing formatting artifacts
    - Preserving document structure and content
    """
    
    def __init__(
        self,
        remove_page_numbers: bool = True,
        remove_headers_footers: bool = True,
        normalize_bullets: bool = True,
        min_line_length: int = 10,
    ):
        """
        Initialize the document cleaner.
        
        Args:
            remove_page_numbers: Remove standalone page numbers
            remove_headers_footers: Remove repeated header/footer patterns
            normalize_bullets: Normalize bullet point formatting
            min_line_length: Minimum line length to keep (filters noise)
        """
        self.remove_page_numbers = remove_page_numbers
        self.remove_headers_footers = remove_headers_footers
        self.normalize_bullets = normalize_bullets
        self.min_line_length = min_line_length
        
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Precompile regex patterns for document cleaning."""
        
        # Page numbers (standalone lines with just numbers)
        self.page_number_patterns = [
            re.compile(r'^\s*\d+\s*$', re.MULTILINE),
            re.compile(r'^\s*Page\s+\d+\s*$', re.IGNORECASE | re.MULTILINE),
            re.compile(r'^\s*\d+\s*/\s*\d+\s*$', re.MULTILINE),  # "1/10" format
        ]
        
        # Common document artifacts
        self.artifact_patterns = [
            re.compile(r'\[Image:.*?\]', re.IGNORECASE),
            re.compile(r'\[Figure \d+.*?\]', re.IGNORECASE),
            re.compile(r'\[Tableau \d+.*?\]', re.IGNORECASE),
            re.compile(r'\[Table \d+.*?\]', re.IGNORECASE),
        ]
        
        # Bullet point variations to normalize
        self.bullet_patterns = [
            (re.compile(r'^\s*[•●○◦▪▫]\s*'), '• '),  # Various bullet symbols
            (re.compile(r'^\s*[-–—]\s+'), '• '),     # Dashes as bullets
            (re.compile(r'^\s*[*]\s+'), '• '),       # Asterisks as bullets
        ]
    
    def clean(self, text: str, metadata:Optional[Dict[str, Any]] = None) -> str:
        """
        Clean document text while preserving structure and content.
        
        Args:
            text: Raw document text
            metadata: Document metadata (source, type, etc.)
            
        Returns:
            Cleaned document text
        """
        if not text or not text.strip():
            logger.warning("Empty text provided to DocumentTextCleaner")
            return ""
        
        original_length = len(text)
        logger.debug(f"Cleaning document text (original length: {original_length} chars)")
        
        # Step 1: Remove page numbers
        if self.remove_page_numbers:
            text = self._remove_page_numbers(text)
        
        # Step 2: Remove common document artifacts
        text = self._remove_artifacts(text)
        
        # Step 3: Normalize bullet points
        if self.normalize_bullets:
            text = self._normalize_bullets(text)
        
        # Step 4: Remove headers/footers (repeated patterns)
        if self.remove_headers_footers:
            text = self._remove_repeated_patterns(text)
        
        # Step 5: Normalize whitespace and special characters
        text = self._remove_excessive_special_chars(text)
        text = self._normalize_whitespace(text)
        
        # Step 6: Filter very short lines
        text = self._filter_short_lines(text)
        
        final_length = len(text)
        reduction = 100 * (1 - final_length / original_length) if original_length > 0 else 0
        logger.debug(f"Cleaned document text (final length: {final_length} chars, {reduction:.1f}% reduction)")
        
        return text
    
    def _remove_page_numbers(self, text: str) -> str:
        """Remove standalone page numbers."""
        for pattern in self.page_number_patterns:
            text = pattern.sub('', text)
        return text
    
    def _remove_artifacts(self, text: str) -> str:
        """Remove image/figure/table placeholders."""
        for pattern in self.artifact_patterns:
            text = pattern.sub('', text)
        return text
    
    def _normalize_bullets(self, text: str) -> str:
        """Normalize different bullet point symbols to a consistent format."""
        lines = text.split('\n')
        normalized_lines = []
        
        for line in lines:
            normalized_line = line
            for pattern, replacement in self.bullet_patterns:
                if pattern.match(line):
                    normalized_line = pattern.sub(replacement, line, count=1)
                    break
            normalized_lines.append(normalized_line)
        
        return '\n'.join(normalized_lines)
    
    def _remove_repeated_patterns(self, text: str, min_occurrences: int = 3) -> str:
        """
        Remove lines that repeat frequently (likely headers/footers).
        
        Args:
            text: Document text
            min_occurrences: Number of repetitions to consider a line as header/footer
            
        Returns:
            Text with repeated patterns removed
        """
        lines = text.split('\n')
        line_counts = {}
        
        # Count occurrences of each line
        for line in lines:
            stripped = line.strip()
            if len(stripped) > 5:  # Only track lines with substance
                line_counts[stripped] = line_counts.get(stripped, 0) + 1
        
        # Identify repeated lines (headers/footers)
        repeated_lines = {
            line for line, count in line_counts.items()
            if count >= min_occurrences
        }
        
        # Filter out repeated lines
        filtered_lines = [
            line for line in lines
            if line.strip() not in repeated_lines or len(line.strip()) <= 5
        ]
        
        return '\n'.join(filtered_lines)
    
    def _filter_short_lines(self, text: str) -> str:
        """Remove very short lines that are likely noise."""
        lines = text.split('\n')
        filtered_lines = []
        
        for line in lines:
            stripped = line.strip()
            # Keep lines that are either:
            # - Long enough
            # - Empty (preserve paragraph structure)
            # - Start with bullet (even if short, it's structural)
            if (len(stripped) >= self.min_line_length or 
                len(stripped) == 0 or 
                stripped.startswith('•')):
                filtered_lines.append(line)
        
        return '\n'.join(filtered_lines)
    
    def get_cleaner_name(self) -> str:
        """Return the name of this cleaner."""
        return "document_cleaner"
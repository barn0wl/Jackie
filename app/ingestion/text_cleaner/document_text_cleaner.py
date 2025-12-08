# app/ingestion/text_cleaner/document_text_cleaner.py

import re
import logging
from typing import Dict, Any, Optional, List

from app.ingestion.text_cleaner.base_text_cleaner import BaseTextCleaner

logger = logging.getLogger(__name__)


class DocumentTextCleaner(BaseTextCleaner):
    """
    General-purpose cleaner for documents (PDF, Word, TXT, etc.).
    Optimized for French corporate documents.
    """

    def __init__(
        self,
        remove_page_numbers: bool = True,
        remove_headers_footers: bool = True,
        normalize_bullets: bool = True,
        min_line_length: int = 10,
        language: str = "fr"
    ):
        """
        Initialize document cleaner.
        
        Args:
            remove_page_numbers: Remove standalone page numbers
            remove_headers_footers: Remove repeated header/footer patterns
            normalize_bullets: Normalize bullet point formatting
            min_line_length: Minimum line length to keep
            language: Document language ('fr' or 'en')
        """
        super().__init__()
        self.remove_page_numbers = remove_page_numbers
        self.remove_headers_footers = remove_headers_footers
        self.normalize_bullets = normalize_bullets
        self.min_line_length = min_line_length
        self.language = language
        
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for document cleaning."""
        # Page number patterns (French and English)
        self.page_patterns = [
            re.compile(r'^\s*\d+\s*$', re.MULTILINE),
            re.compile(r'^\s*Page\s+\d+\s*$', re.IGNORECASE | re.MULTILINE),
            re.compile(r'^\s*Page\s+\d+\s*/\s*\d+\s*$', re.IGNORECASE | re.MULTILINE),
        ]
        
        # Document artifact patterns
        self.artifact_patterns = [
            re.compile(r'\[Image:.*?\]', re.IGNORECASE),
            re.compile(r'\[Figure\s+\d+.*?\]', re.IGNORECASE),
            re.compile(r'\[Tableau\s+\d+.*?\]', re.IGNORECASE),
            re.compile(r'\[Table\s+\d+.*?\]', re.IGNORECASE),
            re.compile(r'\[\d+%\s*\]', re.IGNORECASE),  # OCR progress indicators
        ]
        
        # French-specific patterns
        self.french_patterns = {
            "headers": [
                re.compile(r'^Les\s+Centaures\s+Routiers\s*$', re.IGNORECASE | re.MULTILINE),
                re.compile(r'^Document\s+Confidentiel\s*$', re.IGNORECASE | re.MULTILINE),
                re.compile(r'^Version\s+\d+\.\d+\s*$', re.IGNORECASE | re.MULTILINE),
            ],
            "footers": [
                re.compile(r'^©.*Centaures\s+Routiers.*$', re.IGNORECASE | re.MULTILINE),
                re.compile(r'^Tous\s+droits\s+réservés.*$', re.IGNORECASE | re.MULTILINE),
                re.compile(r'^Dernière\s+mise\s+à\s+jour.*$', re.IGNORECASE | re.MULTILINE),
            ]
        }
    
    def clean(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> str:
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
        logger.debug(f"Cleaning document text (original: {original_length} chars)")
        
        # Step 1: Remove page numbers
        if self.remove_page_numbers:
            text = self._remove_page_numbers(text)
        
        # Step 2: Remove document artifacts
        text = self._remove_artifacts(text)
        
        # Step 3: Language-specific cleaning
        if self.language == "fr":
            text = self._remove_french_boilerplate(text)
        
        # Step 4: Normalize formatting
        if self.normalize_bullets:
            text = self._normalize_bullets(text)
        
        # Step 5: Remove headers/footers
        if self.remove_headers_footers:
            text = self._remove_repeated_patterns(text)
        
        # Step 6: Post-processing
        text = self._remove_excessive_special_chars(text)
        text = self._normalize_whitespace(text)
        text = self._filter_short_lines(text)
        
        final_length = len(text)
        reduction = 100 * (1 - final_length / original_length) if original_length > 0 else 0
        
        logger.debug(f"Cleaned document (final: {final_length} chars, {reduction:.1f}% reduction)")
        
        return text.strip()
    
    def _remove_page_numbers(self, text: str) -> str:
        """Remove standalone page numbers."""
        for pattern in self.page_patterns:
            text = pattern.sub('', text)
        return text
    
    def _remove_artifacts(self, text: str) -> str:
        """Remove image/figure/table placeholders."""
        for pattern in self.artifact_patterns:
            text = pattern.sub('', text)
        return text
    
    def _remove_french_boilerplate(self, text: str) -> str:
        """Remove French-specific boilerplate text."""
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line_stripped = line.strip()
            skip_line = False
            
            # Check French headers
            for pattern in self.french_patterns["headers"]:
                if pattern.match(line_stripped):
                    skip_line = True
                    break
            
            # Check French footers
            for pattern in self.french_patterns["footers"]:
                if pattern.match(line_stripped):
                    skip_line = True
                    break
            
            if not skip_line:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _normalize_bullets(self, text: str) -> str:
        """Normalize bullet points to consistent format."""
        lines = text.split('\n')
        normalized_lines = []
        
        for line in lines:
            normalized_line = line
            
            # French bullet styles
            if re.match(r'^\s*[•◦▪▫○●]\s*', line):
                normalized_line = re.sub(r'^\s*[•◦▪▫○●]\s*', '• ', line, count=1)
            elif re.match(r'^\s*[-–—]\s+', line):
                normalized_line = re.sub(r'^\s*[-–—]\s+', '• ', line, count=1)
            elif re.match(r'^\s*[*]\s+', line):
                normalized_line = re.sub(r'^\s*[*]\s+', '• ', line, count=1)
            # French numbered lists: "1)" or "1."
            elif re.match(r'^\s*\d+[.)]\s+', line):
                # Keep numbered lists as-is but normalize spacing
                normalized_line = re.sub(r'^\s*(\d+[.)])\s+', r'\1 ', line, count=1)
            
            normalized_lines.append(normalized_line)
        
        return '\n'.join(normalized_lines)
    
    def _remove_repeated_patterns(self, text: str, min_occurrences: int = 3) -> str:
        """Remove frequently repeating lines (likely headers/footers)."""
        lines = text.split('\n')
        line_counts = {}
        
        # Count occurrences of substantial lines
        for line in lines:
            stripped = line.strip()
            if len(stripped) > 10:  # Only track meaningful lines
                line_counts[stripped] = line_counts.get(stripped, 0) + 1
        
        # Identify repeated patterns
        repeated_lines = {line for line, count in line_counts.items() if count >= min_occurrences}
        
        # Filter lines
        filtered_lines = [
            line for line in lines
            if line.strip() not in repeated_lines or len(line.strip()) <= 10
        ]
        
        return '\n'.join(filtered_lines)
    
    def _filter_short_lines(self, text: str) -> str:
        """Filter out very short lines that are likely noise."""
        lines = text.split('\n')
        filtered_lines = []
        
        for line in lines:
            stripped = line.strip()
            
            # Keep lines that are:
            # - Long enough
            # - Empty (preserve structure)
            # - Start with bullet/number (structural)
            if (len(stripped) >= self.min_line_length or
                len(stripped) == 0 or
                stripped.startswith(('•', '-', '*', '1.', '1)', 'a)', 'a.'))):
                filtered_lines.append(line)
        
        return '\n'.join(filtered_lines)

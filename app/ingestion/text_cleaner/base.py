# app/ingestion/text_cleaner/base.py
"""
Base text cleaning utilities - source agnostic.
"""

import re
import unicodedata
from typing import Optional, Callable, List
from .config import TextCleanerConfig, DEFAULT_CONFIG

def strip_html_tags(text: str, config: TextCleanerConfig = DEFAULT_CONFIG) -> str:
    """Remove HTML tags from text while preserving content."""
    return config.HTML_TAGS_PATTERN.sub(' ', text)

def normalize_whitespace(text: str, config: TextCleanerConfig = DEFAULT_CONFIG) -> str:
    """Normalize whitespace - collapse multiple spaces and newlines."""
    # Replace multiple spaces/tabs with single space
    text = config.MULTISPACE_PATTERN.sub(' ', text)
    # Replace multiple newlines with double newline (paragraph breaks)
    text = config.MULTINEWLINE_PATTERN.sub('\n\n', text)
    # Remove leading/trailing whitespace
    text = config.LEADING_TRAILING_SPACE_PATTERN.sub('', text)
    return text

def remove_control_characters(text: str, config: TextCleanerConfig = DEFAULT_CONFIG) -> str:
    """Remove control characters and other non-printable characters."""
    return config.CONTROL_CHARS_PATTERN.sub('', text)

def normalize_unicode_characters(text: str, config: TextCleanerConfig = DEFAULT_CONFIG) -> str:
    """Convert smart quotes and other Unicode characters to their ASCII equivalents."""
    for unicode_char, ascii_char in config.UNICODE_NORMALIZATION_MAP.items():
        text = text.replace(unicode_char, ascii_char)
    return text

def normalize_line_endings(text: str) -> str:
    """Normalize line endings to Unix-style (\n)."""
    return text.replace('\r\n', '\n').replace('\r', '\n')

def remove_boilerplate_patterns(text: str, patterns: List[re.Pattern]) -> str:
    """Remove text matching given boilerplate patterns."""
    for pattern in patterns:
        text = pattern.sub('', text)
    return text

def clean_and_normalize_text(
    text: str, 
    config: TextCleanerConfig = DEFAULT_CONFIG,
    remove_email_patterns: bool = False
) -> str:
    """
    Apply comprehensive text cleaning and normalization.
    
    Args:
        text: Input text to clean
        config: Configuration with cleaning patterns
        remove_email_patterns: Whether to apply email-specific cleaning
    
    Returns:
        Cleaned and normalized text
    """
    if not text or not isinstance(text, str):
        return text
    
    # Apply cleaning steps in optimal order
    text = normalize_line_endings(text)
    text = strip_html_tags(text, config)
    text = remove_control_characters(text, config)
    text = normalize_unicode_characters(text, config)
    text = normalize_whitespace(text, config)
    
    # Optional email-specific cleaning
    if remove_email_patterns:
        from .email_rules import apply_email_specific_cleaning
        text = apply_email_specific_cleaning(text, config)
    
    return text.strip()

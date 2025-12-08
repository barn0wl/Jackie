# app/ingestion/text_cleaner/config.py
"""
Configuration for text cleaning patterns and rules.
"""

import re

class TextCleanerConfig:
    """Configuration for text cleaning patterns and rules."""
    
    # HTML cleaning patterns
    HTML_TAGS_PATTERN = re.compile(r'<[^>]+>')
    HTML_ENTITY_PATTERN = re.compile(r'&[a-z]+;')
    
    # Whitespace normalization
    MULTISPACE_PATTERN = re.compile(r'[ \t]+')
    MULTINEWLINE_PATTERN = re.compile(r'\n\s*\n')
    LEADING_TRAILING_SPACE_PATTERN = re.compile(r'^\s+|\s+$')
    
    # Control characters and special characters
    CONTROL_CHARS_PATTERN = re.compile(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]')
    UNICODE_NORMALIZATION_MAP = {
        '“': '"', '”': '"', '‘': "'", '’': "'", '–': '-', '—': '-',
        '…': '...', '«': '"', '»': '"'
    }
    
    # Email-specific patterns (optional, can be disabled for non-email content)
    EMAIL_SIGNATURE_PATTERNS = [
        re.compile(r'(?i)^--*\s*$.*', re.MULTILINE | re.DOTALL),  # Signature separator
        re.compile(r'(?i)^best regards.*$.*', re.MULTILINE | re.DOTALL),
        re.compile(r'(?i)^thanks.*$.*', re.MULTILINE | re.DOTALL),
        re.compile(r'(?i)^sent from my.*$', re.MULTILINE),
    ]
    
    # Common boilerplate patterns
    BOILERPLATE_PATTERNS = [
        re.compile(r'(?i)confidentiality notice.*', re.DOTALL),
        re.compile(r'(?i)this email is.*confidential.*', re.DOTALL),
    ]

# Default configuration instance
DEFAULT_CONFIG = TextCleanerConfig()

# app/ingestion/text_cleaner/email_rules.py
"""
Optional email-specific cleaning rules.
These are separated to keep the base cleaner source-agnostic.
"""

from .config import TextCleanerConfig, DEFAULT_CONFIG

def remove_email_signatures(text: str, config: TextCleanerConfig = DEFAULT_CONFIG) -> str:
    """Remove common email signature patterns."""
    for pattern in config.EMAIL_SIGNATURE_PATTERNS:
        text = pattern.sub('', text)
    return text

def remove_email_headers(text: str) -> str:
    """Remove email header lines if present in the body."""
    lines = text.split('\n')
    cleaned_lines = []
    in_body = False
    
    for line in lines:
        # Skip common header lines
        if line.lower().startswith(('from:', 'to:', 'subject:', 'date:', 'cc:', 'bcc:')):
            continue
        # Start of body typically after empty line or specific markers
        if not in_body and (not line.strip() or line.strip().startswith('---')):
            in_body = True
            continue
        if in_body:
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines) if cleaned_lines else text

def apply_email_specific_cleaning(text: str, config: TextCleanerConfig = DEFAULT_CONFIG) -> str:
    """Apply all email-specific cleaning rules."""
    text = remove_email_headers(text)
    text = remove_email_signatures(text, config)
    text = remove_boilerplate_patterns(text, config.BOILERPLATE_PATTERNS)
    return text

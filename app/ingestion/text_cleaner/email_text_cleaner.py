import logging
import re
from typing import Dict, Any, Optional
from app.ingestion.text_cleaner.base_text_cleaner import BaseTextCleaner

logger = logging.getLogger(__name__)

class EmailTextCleaner(BaseTextCleaner):
    """
    Specialized text cleaner for email content.
    
    Removes common email noise while preserving essential information:
    - Greetings and closings
    - Email signatures
    - Quoted/forwarded content markers
    - Thread artifacts
    - Disclaimers
    - HTML remnants
    """
    
    def __init__(
        self,
        remove_greetings: bool = True,
        remove_signatures: bool = True,
        remove_quoted_text: bool = True,
        remove_disclaimers: bool = True,
        preserve_metadata_section: bool = False,
    ):
        """
        Initialize the email cleaner with configurable options.
        
        Args:
            remove_greetings: Remove common greetings (Bonjour, Hello, etc.)
            remove_signatures: Remove email signatures
            remove_quoted_text: Remove quoted/forwarded email content
            remove_disclaimers: Remove legal disclaimers
            preserve_metadata_section: Keep "From/To/Date" metadata blocks
        """
        self.remove_greetings = remove_greetings
        self.remove_signatures = remove_signatures
        self.remove_quoted_text = remove_quoted_text
        self.remove_disclaimers = remove_disclaimers
        self.preserve_metadata_section = preserve_metadata_section
        
        # Compile regex patterns for better performance
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Precompile all regex patterns used in cleaning."""
        
        # French & English greetings (case-insensitive)
        self.greeting_patterns = [
            re.compile(r'^(bonjour|bonsoir|salut|hello|hi|hey|dear|cher|chère)[\s,].*?[,.\n]', re.IGNORECASE | re.MULTILINE),
            re.compile(r'^(madame|monsieur|mesdames|messieurs)[\s,].*?[,.\n]', re.IGNORECASE | re.MULTILINE),
        ]
        
        # Common closings
        self.closing_patterns = [
            re.compile(r'(cordialement|bien à vous|sincèrement|respectueusement|amicalement)[\s,].*$', re.IGNORECASE | re.DOTALL),
            re.compile(r'(regards|best regards|sincerely|yours truly|cheers|thanks)[\s,].*$', re.IGNORECASE | re.DOTALL),
            re.compile(r'(merci|thank you|thanks)[\s,].*$', re.IGNORECASE | re.DOTALL),
        ]
        
        # Signature markers
        self.signature_patterns = [
            re.compile(r'\n[-_]{2,}\n.*$', re.DOTALL),  # Lines starting with -- or __
            re.compile(r'\nEnvoyé depuis.*$', re.IGNORECASE | re.DOTALL),
            re.compile(r'\nSent from.*$', re.IGNORECASE | re.DOTALL),
            re.compile(r'\n(Téléphone|Phone|Mobile|Email|Tél)[\s:]+[\d\w@.+-]+.*$', re.IGNORECASE | re.DOTALL),
        ]
        
        # Quoted/forwarded text markers
        self.quoted_patterns = [
            re.compile(r'\n[\s]*>+.*$', re.DOTALL),  # Lines starting with >
            re.compile(r'\n(Le|On)[\s\d/:-]+,.*?a écrit\s*:.*$', re.IGNORECASE | re.DOTALL),
            re.compile(r'\n(From|De|À|To|Sent|Date|Subject|Objet)\s*:.*$', re.IGNORECASE | re.DOTALL),
            re.compile(r'\n[-]{3,}\s*(Message transféré|Forwarded message).*$', re.IGNORECASE | re.DOTALL),
        ]
        
        # Disclaimers
        self.disclaimer_patterns = [
            re.compile(r'(Ce message|This email).{0,50}(confidentiel|confidential).*$', re.IGNORECASE | re.DOTALL),
            re.compile(r'(Avertissement|Disclaimer|Confidentiality notice)[\s:]+.*$', re.IGNORECASE | re.DOTALL),
            re.compile(r'(P\s*)?Pensez à l\'environnement.*$', re.IGNORECASE | re.DOTALL),
        ]
    
    def clean(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Clean email text by removing noise while preserving essential content.
        
        Args:
            text: Raw email body text
            metadata: Email metadata (subject, sender, date) - can inform cleaning
            
        Returns:
            Cleaned email text ready for chunking
        """
        if not text or not text.strip():
            logger.warning("Empty text provided to EmailTextCleaner")
            return ""
        
        original_length = len(text)
        logger.debug(f"Cleaning email text (original length: {original_length} chars)")
        
        # Step 1: Remove HTML artifacts if present
        text = self._remove_html_artifacts(text)
        
        # Step 2: Remove quoted/forwarded content first (most noise)
        if self.remove_quoted_text:
            text = self._remove_quoted_content(text)
        
        # Step 3: Remove disclaimers
        if self.remove_disclaimers:
            text = self._remove_disclaimers(text)
        
        # Step 4: Remove signatures
        if self.remove_signatures:
            text = self._remove_signatures(text)
        
        # Step 5: Remove greetings and closings
        if self.remove_greetings:
            text = self._remove_greetings_and_closings(text)
        
        # Step 6: Normalize whitespace and special characters
        text = self._remove_excessive_special_chars(text)
        text = self._normalize_whitespace(text)
        
        # Step 7: Remove very short lines that are likely noise
        text = self._remove_short_noise_lines(text)
        
        final_length = len(text)
        reduction = 100 * (1 - final_length / original_length) if original_length > 0 else 0
        logger.debug(f"Cleaned email text (final length: {final_length} chars, {reduction:.1f}% reduction)")
        
        return text
    
    def _remove_html_artifacts(self, text: str) -> str:
        """Remove common HTML artifacts that might remain after HTML parsing."""
        text = re.sub(r'<[^>]+>', '', text)  # Remove any remaining HTML tags
        text = re.sub(r'&[a-z]+;', ' ', text)  # Remove HTML entities
        text = re.sub(r'\[cid:.*?\]', '', text)  # Remove inline image references
        return text
    
    def _remove_quoted_content(self, text: str) -> str:
        """Remove quoted/forwarded email content."""
        for pattern in self.quoted_patterns:
            match = pattern.search(text)
            if match:
                # Cut off everything from the quote marker onward
                text = text[:match.start()].strip()
        return text
    
    def _remove_disclaimers(self, text: str) -> str:
        """Remove legal disclaimers and confidentiality notices."""
        for pattern in self.disclaimer_patterns:
            text = pattern.sub('', text)
        return text
    
    def _remove_signatures(self, text: str) -> str:
        """Remove email signatures."""
        for pattern in self.signature_patterns:
            match = pattern.search(text)
            if match:
                text = text[:match.start()].strip()
        return text
    
    def _remove_greetings_and_closings(self, text: str) -> str:
        """Remove common greetings at start and closings at end."""
        # Remove greetings from the beginning
        for pattern in self.greeting_patterns:
            text = pattern.sub('', text, count=1)
        
        # Remove closings from the end
        for pattern in self.closing_patterns:
            text = pattern.sub('', text)
        
        return text
    
    def _remove_short_noise_lines(self, text: str, min_length: int = 15) -> str:
        """
        Remove very short lines that are likely noise.
        
        Args:
            text: Text to clean
            min_length: Minimum line length to keep (default: 15 chars)
            
        Returns:
            Text with short noise lines removed
        """
        lines = text.split('\n')
        meaningful_lines = []
        
        for line in lines:
            stripped = line.strip()
            # Keep lines that are either:
            # - Long enough (likely meaningful)
            # - Empty (preserve paragraph breaks)
            if len(stripped) >= min_length or len(stripped) == 0:
                meaningful_lines.append(line)
        
        return '\n'.join(meaningful_lines)
    
    def get_cleaner_name(self) -> str:
        """Return the name of this cleaner."""
        return "email_cleaner"
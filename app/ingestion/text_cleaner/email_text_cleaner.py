# app/ingestion/text_cleaner/email_text_cleaner.py

import re
import logging
from typing import Dict, Any, Optional
from html.parser import HTMLParser

from app.ingestion.text_cleaner.base_text_cleaner import BaseTextCleaner

logger = logging.getLogger(__name__)


class HTMLStripper(HTMLParser):
    """Supprime les tags HTML du contenu email."""
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = []
    
    def handle_data(self, data):
        self.text.append(data)
    
    def get_data(self):
        return ''.join(self.text).strip()


class EmailTextCleaner(BaseTextCleaner):
    """
    Email-specific text cleaner optimized for French corporate emails.
    
    Removes:
    - HTML tags and images
    - Email signatures (French-specific patterns)
    - Quoted/reply text
    - Boilerplate disclaimers
    """

    # French email closing phrases (case-insensitive)
    FRENCH_CLOSING_PHRASES = [
        r"cordialement[,\s]*",
        r"bien\s*à\s*vous[,\s]*",
        r"bien\s*cordialement[,\s]*",
        r"meilleures\s*salutations[,\s]*",
        r"salutations[,\s]*distinguées[,\s]*",
        r"amicalement[,\s]*",
        r"sincèrement[,\s]*",
        r"je\s*vous\s*prie\s*d['\"]agréer[,\s]*",
        r"veuillez\s*recevoir[,\s]*",
        r"bonne\s*réception[,\s]*",
        r"à\s*bientôt[,\s]*",
        r"merci\s*d['\"]avance[,\s]*",
        r"avec\s*mes\s*remerciements[,\s]*",
    ]
    
    # Email header patterns
    EMAIL_HEADER_PATTERNS = [
        r"^De\s*:\s*.*$",
        r"^À\s*:\s*.*$",
        r"^Cc\s*:\s*.*$",
        r"^Cci\s*:\s*.*$",
        r"^Objet\s*:\s*.*$",
        r"^Date\s*:\s*.*$",
        r"^Envoyé\s*:\s*.*$",
        r"^Le\s+.*\s+a\s+écrit\s*:.*$",
        r"^On\s+.*\s+a\s+écrit\s*:.*$",
    ]
    
    # Common French corporate disclaimers
    FRENCH_DISCLAIMERS = [
        r"(?s).*confidentialité.*décret.*loi.*",
        r"(?s).*informations.*confidentielles.*destinataires.*",
        r"(?s).*message.*protégé.*secret.*professionnel.*",
        r"(?s).*les\s+centaures\s+routiers.*tous\s+droits\s+réservés.*",
    ]

    def __init__(self):
        """Initialize the French email cleaner."""
        super().__init__()
        logger.info("EmailTextCleaner initialized for French content")
    
    def clean(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Clean email text with French-specific patterns.
        
        Args:
            text: Raw email text (may contain HTML)
            metadata: Optional metadata with email properties
            
        Returns:
            Cleaned email content
        """
        if not text or not text.strip():
            return ""
        
        logger.debug(f"Cleaning email text (length: {len(text)} chars)")
        
        # Extract metadata for targeted cleaning
        sender = metadata.get("sender", "") if metadata else ""
        sender_name = metadata.get("sender_name", "") if metadata else ""
        is_reply = metadata.get("is_reply", False) if metadata else False
        
        # Clean pipeline
        text = self._strip_html(text)
        text = self._extract_latest_message(text, is_reply)
        text = self._remove_quoted_text(text)
        text = self._remove_email_headers(text)
        text = self._remove_french_closing_phrases(text)
        text = self._remove_signature(text, sender_name or sender)
        text = self._remove_french_disclaimers(text)
        text = self._normalize_whitespace(text)
        text = self._remove_excessive_special_chars(text)
        
        final_length = len(text)
        logger.debug(f"Cleaned email text (final length: {final_length} chars)")
        
        return text.strip()
    
    def _strip_html(self, text: str) -> str:
        """Remove HTML tags and image references."""
        # Remove script/style tags
        text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", text, flags=re.DOTALL | re.IGNORECASE)
        
        # Strip HTML using parser
        try:
            stripper = HTMLStripper()
            stripper.feed(text)
            text = stripper.get_data()
        except:
            # Fallback regex
            text = re.sub(r"<[^>]+>", " ", text)
        
        # Remove image references
        text = re.sub(r"\[(cid|image):.*?\]", "", text, flags=re.IGNORECASE)
        
        return text
    
    def _extract_latest_message(self, text: str, is_reply: bool) -> str:
        """For reply emails, extract only the latest message."""
        if not is_reply:
            return text
        
        lines = text.split("\n")
        message_lines = []
        
        for line in lines:
            # Detect start of quoted/previous message
            line_stripped = line.strip()
            
            # Check for common reply indicators
            if (line_stripped.startswith(">") or
                line_stripped.startswith("|") or
                re.match(r"^Le\s+.*\s+a\s+écrit\s*:", line_stripped) or
                re.match(r"^On\s+.*\s+a\s+écrit\s*:", line_stripped)):
                break
            
            message_lines.append(line)
        
        return "\n".join(message_lines).strip()
    
    def _remove_quoted_text(self, text: str) -> str:
        """Remove lines starting with quote markers."""
        lines = text.split("\n")
        cleaned_lines = []
        
        for line in lines:
            stripped = line.lstrip()
            # Skip lines that are clearly quoted text
            if stripped.startswith((">", "|")) or stripped == "":
                continue
            cleaned_lines.append(line)
        
        return "\n".join(cleaned_lines).strip()
    
    def _remove_email_headers(self, text: str) -> str:
        """Remove embedded email headers."""
        for pattern in self.EMAIL_HEADER_PATTERNS:
            text = re.sub(pattern, "", text, flags=re.MULTILINE | re.IGNORECASE)
        return text
    
    def _remove_french_closing_phrases(self, text: str) -> str:
        """Remove French closing phrases and everything after."""
        for pattern in self.FRENCH_CLOSING_PHRASES:
            # Find the closing phrase
            match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
            if match:
                # Keep only text before the closing phrase
                text = text[:match.start()].strip()
                break
        
        return text
    
    def _remove_signature(self, text: str, sender_info: str) -> str:
        """Remove email signature based on sender information."""
        if not sender_info:
            return text
        
        lines = text.split("\n")
        cut_index = None
        
        # Try to find sender name in lines
        for i, line in enumerate(lines):
            line_lower = line.lower()
            # Simple check: if line contains common signature indicators
            if "@" in line and any(domain in line_lower for domain in [".fr", ".com", ".net"]):
                cut_index = i
                break
        
        if cut_index is not None:
            return "\n".join(lines[:cut_index]).strip()
        
        return text
    
    def _remove_french_disclaimers(self, text: str) -> str:
        """Remove common French corporate disclaimers."""
        for pattern in self.FRENCH_DISCLAIMERS:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)
        return text

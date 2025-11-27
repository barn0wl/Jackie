import logging
import re
from typing import Any, Dict, Optional, Tuple

from app.ingestion.text_cleaner.base_text_cleaner import BaseTextCleaner

logger = logging.getLogger(__name__)


class EmailTextCleaner(BaseTextCleaner):
    """
    Nettoie les e-mails :
    - supprime le HTML (tags, styles, scripts, commentaires)
    - coupe l'historique cité
    - retire salutations / closings / signatures
    - retire disclaimers
    - remonte A/Cc en en-tête synthétique (sans réafficher l'expéditeur)
    """

    def __init__(
        self,
        remove_greetings: bool = True,
        remove_signatures: bool = True,
        remove_quoted_text: bool = True,
        remove_disclaimers: bool = True,
    ) -> None:
        self.remove_greetings = remove_greetings
        self.remove_signatures = remove_signatures
        self.remove_quoted_text = remove_quoted_text
        self.remove_disclaimers = remove_disclaimers
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        self.greeting_patterns = [
            re.compile(r"^(bonjour|salut|hello|hi|hey|dear|cher|chere)[\s,].*$", re.IGNORECASE),
            re.compile(r"^(madame|monsieur)[\s,].*$", re.IGNORECASE),
        ]
        self.closing_keywords = [
            "cordialement",
            "bien a vous",
            "sincerement",
            "respectueusement",
            "amicalement",
            "best regards",
            "regards",
        ]
        self.signature_markers = [
            re.compile(r"^--+$"),
            re.compile(r"^__+$"),
            re.compile(r"^Sent from my .*", re.IGNORECASE),
        ]
        self.signature_clue_patterns = [
            re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+", re.IGNORECASE),
            re.compile(r"\+?\d[\d\s().-]{6,}"),  # téléphone
            re.compile(r"\bwww\.", re.IGNORECASE),
            re.compile(r"\bassistant\b|\bcomptable\b|\bdirection\b|\btransport", re.IGNORECASE),
        ]
        self.quoted_markers = [
            re.compile(r"^>"),
            re.compile(r"^On .*wrote:$", re.IGNORECASE),
            re.compile(r"^-{3,}\s*(Forwarded message|Message transfere)", re.IGNORECASE),
            re.compile(r"^-----Original Message-----", re.IGNORECASE),
        ]
        self.disclaimer_patterns = [
            re.compile(r"(confidentiel|confidential).*", re.IGNORECASE),
            re.compile(r"(avertissement|disclaimer|confidentiality notice).*", re.IGNORECASE),
            re.compile(r"pensez\s*a l'environnement.*", re.IGNORECASE),
        ]

    def clean(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        if not text or not text.strip():
            logger.warning("Empty text provided to EmailTextCleaner")
            return ""

        text = self._html_to_text(text)
        lines = [line.strip() for line in text.splitlines()]

        to_value, cc_value, lines = self._extract_recipients(lines)

        if self.remove_quoted_text:
            lines = self._remove_quoted_history(lines)

        if self.remove_greetings:
            lines = self._strip_greetings(lines)
        if self.remove_signatures:
            lines = self._strip_signature_block(lines)

        if self.remove_disclaimers:
            lines = self._strip_disclaimers(lines)

        lines = self._filter_noise_lines(lines, min_length=5)

        header_parts = []
        if to_value:
            header_parts.append(f"A: {to_value}")
        if cc_value:
            header_parts.append(f"Cc: {cc_value}")

        content_lines = header_parts + [""] + lines if header_parts else lines
        cleaned = "\n".join(content_lines)
        cleaned = self._remove_excessive_special_chars(cleaned)
        cleaned = self._normalize_whitespace(cleaned)
        return cleaned

    # ------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------ #
    def _html_to_text(self, text: str) -> str:
        lowered = text.lower()
        looks_html = any(tag in lowered for tag in ("<html", "<body", "<p", "<br", "<div"))
        if not looks_html:
            return text
        try:
            from bs4 import BeautifulSoup  # type: ignore
        except Exception:
            # Fallback regex
            text = re.sub(r"<!--.*?-->", " ", text, flags=re.DOTALL)
            text = re.sub(r"(?i)<(script|style).*?>.*?</\1>", " ", text, flags=re.DOTALL)
            text = re.sub(r"(?i)<br\s*/?>", "\n", text)
            text = re.sub(r"(?i)</p\s*>", "\n", text)
            text = re.sub(r"<[^>]+>", " ", text)
            return text

        soup = BeautifulSoup(text, "html.parser")
        for tag in soup(["script", "style", "head"]):
            tag.decompose()
        for br in soup.find_all(["br", "p", "li", "div"]):
            br.insert_before("\n")
        text_out = soup.get_text()
        text_out = re.sub(r"<!--.*?-->", " ", text_out, flags=re.DOTALL)
        text_out = re.sub(r"@font-face[^\n]+", " ", text_out, flags=re.IGNORECASE)
        text_out = re.sub(r"\{[^}]*\}", " ", text_out)
        text_out = re.sub(r"(?i)mso\w+[^\n]*", " ", text_out)
        text_out = re.sub(r"(?i)wordsection\d*[^\n]*", " ", text_out)
        return text_out

    def _remove_quoted_history(self, lines: list[str]) -> list[str]:
        cleaned = []
        for line in lines:
            if any(pat.search(line) for pat in self.quoted_markers):
                break
            if line.startswith(">"):
                continue
            cleaned.append(line)
        return cleaned

    def _strip_greetings(self, lines: list[str]) -> list[str]:
        idx = 0
        while idx < len(lines) and not lines[idx]:
            idx += 1
        if idx < len(lines) and any(pat.search(lines[idx]) for pat in self.greeting_patterns):
            idx += 1
            while idx < len(lines) and not lines[idx]:
                idx += 1
        return lines[idx:]

    def _strip_signature_block(self, lines: list[str]) -> list[str]:
        end = len(lines)
        for i in range(len(lines) - 1, -1, -1):
            line = lines[i]
            low = line.lower()
            if any(kw in low for kw in self.closing_keywords):
                end = i
                break
            if any(pat.search(line) for pat in self.signature_markers):
                end = i
                break
            if any(pat.search(line) for pat in self.signature_clue_patterns):
                end = i
                break
        return lines[:end]

    def _strip_disclaimers(self, lines: list[str]) -> list[str]:
        out = []
        for line in lines:
            if any(pat.search(line) for pat in self.disclaimer_patterns):
                break
            out.append(line)
        return out

    def _filter_noise_lines(self, lines: list[str], min_length: int = 5) -> list[str]:
        out = []
        for line in lines:
            stripped = line.strip()
            if stripped == "":
                out.append("")
            elif len(stripped) >= min_length:
                out.append(stripped)
        while out and out[0] == "":
            out.pop(0)
        while out and out[-1] == "":
            out.pop()
        return out

    def _extract_recipients(self, lines: list[str]) -> Tuple[str, str, list[str]]:
        to_value = ""
        cc_value = ""
        remaining = []
        to_re = re.compile(r"^(a|à|to)\s*:", re.IGNORECASE)
        cc_re = re.compile(r"^(cc|c\.c\.)\s*:", re.IGNORECASE)

        for line in lines:
            if to_value == "" and to_re.match(line):
                to_value = to_re.sub("", line).strip(" :\t")
                continue
            if cc_value == "" and cc_re.match(line):
                cc_value = cc_re.sub("", line).strip(" :\t")
                continue
            remaining.append(line)

        return to_value, cc_value, remaining

    def get_cleaner_name(self) -> str:
        return "email-text-cleaner"

"""
Email Text Cleaner: Nettoie le contenu des emails pour stockage vectoriel
Supprime HTML, images, signatures, texte cité
Gère les réponses (RE:) en extrayant uniquement le dernier message
"""
import re
import logging
from typing import Optional, Dict, List, Any, Union
from html.parser import HTMLParser

logger = logging.getLogger(__name__)


class HTMLStripper(HTMLParser):
    """Supprime les tags HTML du contenu email."""
    
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = []

    def handle_data(self, d):
        self.text.append(d)

    def get_data(self):
        return ''.join(self.text).strip()


class EmailTextCleaner:
    """
    Nettoie et formate le contenu des emails pour stockage vectoriel.
    
    Optimisé pour:
    - Suppression complète HTML/images
    - Suppression signatures (détectées via nom expéditeur)
    - Extraction message principal dans les réponses (RE:)
    - Suppression texte cité/forwardé
    - Nettoyage pour BD vectorielle
    """

    # Formules de politesse (marque fin du contenu utile)
    CLOSING_PHRASES_PATTERNS = [
        r"cordialement[,\s]*",
        r"bien\s*à\s*vous[,\s]*",
        r"bien\s*cordialement[,\s]*",
        r"meilleures\s*salutations[,\s]*",
        r"amicalement[,\s]*",
        r"sincèrement[,\s]*",
        r"bonne\s*réception\s*à\s*vous[,\s]*",
        r"je\s*vous\s*prie\s*d['\"]agréer.*",
        r"veuillez\s*recevoir.*",
        r"affectueusement[,\s]*",
        r"à\s*bientôt[,\s]*",
        r"bàv[,\s]*",
        r"cdt[,\s]*",
        r"merci\s*d['\"]avance[,\s]*",
    ]

    # Patterns de séparation dans les emails (citations)
    SEPARATOR_PATTERNS = [
        r"^[-_=]{3,}.*$",  # Lignes de séparation
        r"^>+\s+.*$",  # Citation avec >
        r"^\|\s+.*$",  # Citation avec |
        r"^De\s*:\s*.*$",  # Headers "De:"
        r"^Envoyé\s*:\s*.*$",  # Headers "Envoyé:"
        r"^À\s*:\s*.*$",  # Headers "À:"
        r"^Cc\s*:\s*.*$",  # Headers "Cc:"
        r"^Objet\s*:\s*.*$",  # Headers "Objet:"
        r"^Le\s+.*\s+a\s+écrit\s*:.*$",  # "Le ... a écrit:"
    ]

    def __init__(self):
        """Initialise le nettoyeur d'emails."""
        logger.info("✅ EmailTextCleaner initialized")

    def strip_html(self, html_content: str) -> str:
        """
        Supprime TOUT le HTML et les références aux images/pièces jointes.
        """
        if not html_content:
            return ""
        
        try:
            # Supprimer les balises <img>, <style>, <script>
            html_content = re.sub(r"<(img|style|script)[^>]*>.*?</\1>", "", html_content, flags=re.DOTALL | re.IGNORECASE)
            html_content = re.sub(r"<(img|br|hr)[^>]*>", "", html_content, flags=re.IGNORECASE)
            
            # Parser HTML pour extraire le texte
            stripper = HTMLStripper()
            stripper.feed(html_content)
            text = stripper.get_data()
            
            # Supprimer références aux images
            text = re.sub(r"\[cid:.*?\]", "", text)
            text = re.sub(r"\[image:.*?\]", "", text)
            text = re.sub(r"<image\d+\..*?>", "", text)
            
            return text.strip()
            
        except Exception as e:
            logger.warning(f"Error stripping HTML: {e}. Using fallback.")
            text = re.sub(r"<[^>]+>", "", html_content)
            return text.strip()

    def extract_latest_message_only(self, text: str, is_reply: bool = False) -> str:
        """
        Pour les emails avec RE: (réponses), extrait UNIQUEMENT le dernier message.
        Coupe tout ce qui est avant le message cité.
        """
        if not is_reply:
            return text
        
        lines = text.split("\n")
        message_lines = []
        
        for line in lines:
            # Détecter début de citation/message précédent
            if any(re.match(pattern, line.strip(), re.IGNORECASE) for pattern in self.SEPARATOR_PATTERNS):
                # On arrête ici, tout le reste est citation
                break
            
            message_lines.append(line)
        
        return "\n".join(message_lines).strip()

    def remove_signature_by_sender_name(self, text: str, sender_name: str) -> str:
        """
        Coupe TOUT à partir du nom de l'expéditeur trouvé dans le corps.
        Car généralement, le nom apparaît au début de la signature.
        """
        if not sender_name:
            return text
        
        # Nettoyer le nom (enlever titres, prénoms multiples, etc.)
        # Ex: "Yao KOMENAN" → chercher "KOMENAN" ou "Yao"
        name_parts = sender_name.strip().split()
        
        lines = text.split("\n")
        cut_index = None
        
        for i, line in enumerate(lines):
            line_lower = line.lower().strip()
            
            # Chercher le nom complet ou les parties
            if any(part.lower() in line_lower for part in name_parts if len(part) > 2):
                cut_index = i
                break
        
        if cut_index is not None:
            # Couper à partir de cette ligne
            text = "\n".join(lines[:cut_index]).strip()
        
        return text

    def remove_closing_phrases(self, text: str) -> str:
        """
        Supprime les formules de politesse et tout ce qui suit.
        """
        for pattern in self.CLOSING_PHRASES_PATTERNS:
            # Chercher la formule (case insensitive)
            match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
            if match:
                # Couper à partir de la formule
                text = text[:match.start()].strip()
                break
        
        return text

    def remove_quoted_text(self, text: str) -> str:
        """Supprime les lignes citées (>, |, etc.)"""
        lines = text.split("\n")
        cleaned_lines = []
        
        for line in lines:
            # Ignorer les lignes qui commencent par des marqueurs de citation
            if line.strip().startswith(">") or line.strip().startswith("|"):
                continue
            
            cleaned_lines.append(line)
        
        return "\n".join(cleaned_lines).strip()

    def clean_whitespace(self, text: str) -> str:
        """Nettoie les espaces excessifs."""
        # Supprimer lignes vides multiples
        text = re.sub(r"\n{3,}", "\n\n", text)
        
        # Supprimer espaces en début/fin de lignes
        lines = [line.rstrip() for line in text.split("\n")]
        
        # Supprimer tabs
        text = "\n".join(lines)
        text = re.sub(r"\t+", " ", text)
        text = re.sub(r" {3,}", " ", text)
        
        return text.strip()

    def clean_email_body(
        self,
        body: str,
        body_type: str,
        sender_name: str,
        is_reply: bool = False
    ) -> str:
        """
        Pipeline complet de nettoyage du corps de l'email.
        
        Args:
            body: Corps brut de l'email
            body_type: "html" ou "text"
            sender_name: Nom de l'expéditeur (pour détecter signature)
            is_reply: True si l'email est une réponse (RE:)
        
        Returns:
            Corps nettoyé, prêt pour BD vectorielle
        """
        if not body:
            return ""
        
        # 1. Supprimer HTML/images
        if body_type.lower() == "html":
            body = self.strip_html(body)
        
        # 2. Si réponse (RE:), extraire uniquement le dernier message
        if is_reply:
            body = self.extract_latest_message_only(body, is_reply=True)
        
        # 3. Supprimer texte cité
        body = self.remove_quoted_text(body)
        
        # 4. Supprimer formules de politesse
        body = self.remove_closing_phrases(body)
        
        # 5. Supprimer signature (à partir du nom de l'expéditeur)
        body = self.remove_signature_by_sender_name(body, sender_name)
        
        # 6. Nettoyer espaces
        body = self.clean_whitespace(body)
        
        logger.info(f"✅ Email body cleaned (length: {len(body)} chars)")
        return body

    def clean_email(
        self,
        subject: Optional[str] = None,
        sender: Optional[str] = None,
        sender_name: Optional[str] = None,
        date: Optional[str] = None,
        to_recipients: Optional[List[str]] = None,
        cc_recipients: Optional[List[str]] = None,
        body: Optional[str] = None,
        body_type: str = "html",
    ) -> Dict[str, Union[str, bool]]:
        """
        Nettoie et formate un email complet.
        
        Args:
            subject: Sujet de l'email
            sender: Email de l'expéditeur
            sender_name: Nom de l'expéditeur (pour signature)
            date: Date d'envoi
            to_recipients: Liste des destinataires
            cc_recipients: Liste des CC
            body: Corps de l'email
            body_type: "html" ou "text"
        
        Returns:
            Dict avec contenu nettoyé
        """
        # Détecter si c'est une réponse
        is_reply = subject and re.match(r"^(RE|Re|re|FW|Fw|fw|TR|Tr)[\s:]+", subject)
        
        # Nettoyer le sujet
        clean_subject = subject or "(Sans sujet)"
        clean_subject = re.sub(r"^(RE|Re|re|FW|Fw|fw|TR|Tr)[\s:]+", "", clean_subject).strip()

        # Nettoyer le corps
        clean_body = self.clean_email_body(
            body=body or "",
            body_type=body_type,
            sender_name=sender_name or sender or "",
            is_reply=bool(is_reply)
        )

        return {
            "subject": clean_subject,
            "sender": sender or "Unknown",
            "sender_name": sender_name or sender or "Unknown",
            "date": date or "Unknown",
            "to": ", ".join(to_recipients) if to_recipients else "Not specified",
            "cc": ", ".join(cc_recipients) if cc_recipients else "",
            "body": clean_body,
            "is_reply": bool(is_reply),
        }

    def format_for_display(self, cleaned_email: Dict[str, str]) -> str:
        """
        Formatte l'email nettoyé pour affichage UI.
        """
        lines = [
            f"**De:** {cleaned_email['sender_name']} ({cleaned_email['sender']})",
            f"**Envoyé:** {cleaned_email['date']}",
            f"**À:** {cleaned_email['to']}",
        ]

        if cleaned_email.get("cc"):
            lines.append(f"**Cc:** {cleaned_email['cc']}")
        
        if cleaned_email.get("is_reply"):
            lines.append("**Type:** Réponse (RE:)")

        lines.append("")
        lines.append(cleaned_email["body"])

        return "\n".join(lines)
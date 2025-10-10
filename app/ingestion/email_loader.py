# app/ingestion/email_loader.py

import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from O365 import Account, FileSystemTokenBackend
from app.models.document_chunk import DocumentChunk
from app.core.ms_config import settings

logger = logging.getLogger(__name__)

class MicrosoftEmailLoader:
    """
    Loader for Microsoft 365 / Outlook emails using the O365 SDK.

    - Supports both personal (no credentials) and enterprise (Azure AD) flows.
    - Handles token caching (FileSystemTokenBackend)
    - Fetches and parses emails into DocumentChunk format.
    """

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        tenant_id: Optional[str] = None,
        token_path: str = settings.TOKEN_PATH,
        token_filename: str = settings.TOKEN_FILENAME,
        folder_name: str = "Inbox",
        max_emails: int = 50,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        self.folder_name = folder_name
        self.max_emails = max_emails

        self.token_backend = FileSystemTokenBackend(
            token_path=token_path,
            token_filename=token_filename,
        )

        # Declare credentials as Optional[Tuple[str, str]] for both modes
        self.credentials: Optional[Tuple[str, str]] = None

        # --- PERSONAL MICROSOFT ACCOUNT FLOW ---
        if not self.client_id or not self.client_secret:
            logger.info("⚙️ Using PERSONAL Microsoft account authentication flow.")
            self.account = Account(   # type: ignore
                token_backend=self.token_backend,
            )
            self.is_personal_account = True

        # --- ENTERPRISE / AZURE AD FLOW ---
        else:
            logger.info("⚙️ Using ENTERPRISE (Azure AD) authentication flow.")
            # Explicitly assert non-None types so Pylance knows these are valid
            self.credentials = (self.client_id, self.client_secret)
            self.account = Account(
                credentials=self.credentials,
                token_backend=self.token_backend,
                tenant_id=self.tenant_id,
            )
            self.is_personal_account = False

        logger.info(f"✅ Initialized MicrosoftEmailLoader for folder '{folder_name}'")

    # --------------------------------------------------------------------------
    # AUTHENTICATION
    # --------------------------------------------------------------------------
    def authenticate(self):
        """
        Authenticate to Microsoft Graph (browser or device flow depending on mode).
        """
        if not self.account.is_authenticated:
            logger.info("🔐 Authenticating to Microsoft 365...")

            scopes = ["basic", "mailbox", "mail.read"]
            
            # For personal accounts: use device flow (opens browser)
            # For enterprise: use authorization code flow
            if self.is_personal_account:
                # Device flow for personal accounts
                self.account.authenticate(scopes=scopes, auth_flow_type="device")
            else:
                # Authorization code flow for enterprise accounts
                self.account.authenticate(scopes=scopes, auth_flow_type="authorization")

            logger.info("✅ Authentication successful; token cached.")
        else:
            logger.info("🔑 Using cached Microsoft 365 token.")

    # --------------------------------------------------------------------------
    # FETCH EMAILS
    # --------------------------------------------------------------------------
    def load_emails(self) -> List[Dict]:
        """Fetch emails from Outlook and return structured dictionaries."""
        self.authenticate()
        mailbox = self.account.mailbox()

        try:
            folder = mailbox.get_folder(folder_name=self.folder_name)
        except Exception:
            logger.warning(f"⚠️ Folder '{self.folder_name}' not found. Using Inbox instead.")
            folder = mailbox.inbox_folder()

        if folder is None:
            logger.error(f"❌ Unable to open folder '{self.folder_name}'.")
            return []

        messages = folder.get_messages(limit=self.max_emails, download_attachments=False)

        emails: List[Dict] = []
        for msg in messages:
            try:
                emails.append(
                    {
                        "id": msg.object_id,
                        "subject": msg.subject or "",
                        "sender": getattr(msg.sender, "address", "") if msg.sender else "",
                        "date": msg.received,
                        "body": msg.body or "",
                    }
                )
            except Exception as e:
                logger.exception(f"⚠️ Failed to parse message: {e}")

        logger.info(f"📨 Loaded {len(emails)} emails from '{self.folder_name}'")
        return emails

    # --------------------------------------------------------------------------
    # CONVERT TO DOCUMENT CHUNKS
    # --------------------------------------------------------------------------
    def to_document_chunks(self, emails: List[Dict]) -> List[DocumentChunk]:
        """Convert raw email dicts into DocumentChunk instances with metadata."""
        chunks: List[DocumentChunk] = []
        for email in emails:
            meta = {
                "source": "outlook_email",
                "sender": email["sender"],
                "subject": email["subject"],
                "date": email["date"].isoformat() if isinstance(email["date"], datetime) else str(email["date"]),
            }
            chunks.append(
                DocumentChunk(
                    id=email["id"],
                    content=email["body"],
                    metadata=meta,
                )
            )
        return chunks

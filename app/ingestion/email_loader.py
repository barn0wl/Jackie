# app/ingestion/email_loader.py

import logging
from typing import List, Dict, Optional
from datetime import datetime

from O365 import Account, FileSystemTokenBackend

from app.models.document_chunk import DocumentChunk

logger = logging.getLogger(__name__)

class MicrosoftEmailLoader:
    """
    Loader for Microsoft 365 / Outlook emails using the O365 SDK.

    Handles:
      - Authentication (via Azure app credentials)
      - Fetching emails from inbox or specific folder
      - Extracting metadata (sender, subject, date, etc.)
      - Returning structured raw email documents
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        tenant_id: Optional[str] = None,
        token_path: str = "data/tokens",
        token_filename: str = "o365_token.txt",
        folder_name: str = "Inbox",
        max_emails: int = 50,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        self.folder_name = folder_name
        self.max_emails = max_emails

        self.token_backend = FileSystemTokenBackend(token_path=token_path, token_filename=token_filename)
        self.account = Account(
            credentials=(self.client_id, self.client_secret),
            token_backend=self.token_backend,
            tenant_id=self.tenant_id
        )

        logger.info(f"Initialized MicrosoftEmailLoader for folder '{folder_name}'")

    # --------------------------------------------------------------------------
    # AUTHENTICATION
    # --------------------------------------------------------------------------
    def authenticate(self):
        """
        Authenticate with Microsoft Graph via OAuth2.
        Opens a browser on first use to grant access and store token.
        """
        if not self.account.is_authenticated:
            logger.info("Authenticating to Microsoft 365...")
            self.account.authenticate(
                scopes=["basic", "mailbox", "mail.read"],
                auth_flow_type="device"
            )
        else:
            logger.info("Using cached Microsoft 365 token.")

    # --------------------------------------------------------------------------
    # FETCH EMAILS
    # --------------------------------------------------------------------------
    def load_emails(self) -> List[Dict]:
        """
        Fetch raw emails from Outlook folder and return structured dictionaries.
        """
        self.authenticate()
        mailbox = self.account.mailbox()

        # Try to locate the folder; default to Inbox if not found
        folder = None
        try:
            folder = mailbox.get_folder(folder_name=self.folder_name)
        except Exception:
            logger.warning(f"Folder '{self.folder_name}' not found. Using Inbox instead.")
            folder = mailbox.inbox_folder()

        if folder is None:
            logger.error(f"Unable to locate or open folder '{self.folder_name}'.")
            return []

        messages = folder.get_messages(limit=self.max_emails, download_attachments=False)

        loaded_emails = []
        for msg in messages:
            try:
                loaded_emails.append({
                    "id": msg.object_id,
                    "subject": msg.subject or "",
                    "sender": getattr(msg.sender, "address", ""),
                    "date": msg.received,
                    "body": msg.body or "",
                })
            except Exception as e:
                logger.exception(f"Failed to parse message: {e}")

        logger.info(f"Loaded {len(loaded_emails)} emails from Outlook folder '{self.folder_name}'")
        return loaded_emails

    # --------------------------------------------------------------------------
    # CONVERT TO DOCUMENT CHUNKS
    # --------------------------------------------------------------------------
    def to_document_chunks(self, emails: List[Dict]) -> List[DocumentChunk]:
        """
        Transform raw email dicts into DocumentChunk instances with metadata.
        """
        docs = []
        for email in emails:
            meta = {
                "source": "outlook_email",
                "sender": email["sender"],
                "subject": email["subject"],
                "date": email["date"].isoformat() if isinstance(email["date"], datetime) else str(email["date"]),
            }
            docs.append(
                DocumentChunk(
                    id=email["id"],
                    content=email["body"],
                    metadata=meta,
                )
            )
        return docs

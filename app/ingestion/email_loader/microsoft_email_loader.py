# app/ingestion/email_loader.py

import logging
from typing import List, Dict

from O365 import Account, FileSystemTokenBackend
from app.core.ms_config import settings
from app.ingestion.email_loader.base_email_loader import BaseEmailLoader

logger = logging.getLogger(__name__)

class MicrosoftEmailLoader(BaseEmailLoader):
    """
    Production loader for Microsoft 365 / Outlook emails using the O365 SDK.
    
    REQUIREMENTS:
    - Azure AD registered application
    - Client ID, Client Secret, and Tenant ID
    - Mail.Read permissions granted
    - Proper admin consent
    """
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        tenant_id: str,
        token_path: str = settings.TOKEN_PATH,
        token_filename: str = settings.TOKEN_FILENAME,
        folder_name: str = "Inbox",
        max_emails: int = 50,
    ):
        if not client_id or not client_secret or not tenant_id:
            raise ValueError("MicrosoftEmailLoader requires client_id, client_secret, and tenant_id for enterprise authentication")
        
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        self.folder_name = folder_name
        self.max_emails = max_emails

        self.token_backend = FileSystemTokenBackend(
            token_path=token_path,
            token_filename=token_filename,
        )

        # Initialize Account with enterprise credentials
        self.credentials = (self.client_id, self.client_secret)
        self.account = Account(
            credentials=self.credentials,
            token_backend=self.token_backend,
            tenant_id=self.tenant_id,
        )

        logger.info(f"✅ Initialized MicrosoftEmailLoader for folder '{folder_name}'")
        logger.info("🔐 Authentication: Enterprise Azure AD flow")

    def authenticate(self):
        """Authenticate to Microsoft Graph using enterprise authorization flow."""
        if not self.account.is_authenticated:
            logger.info("🔐 Authenticating to Microsoft 365 (Enterprise)...")

            scopes = ["basic", "mailbox", "mail.read"]
            success = self.account.authenticate(scopes=scopes, auth_flow_type="authorization")

            if success:
                logger.info("✅ Enterprise authentication successful; token cached.")
            else:
                logger.error("❌ Enterprise authentication failed.")
                raise Exception("Microsoft 365 authentication failed")
        else:
            logger.info("🔑 Using cached Microsoft 365 token.")

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
    
    def get_source_name(self) -> str:
        return "outlook_email"

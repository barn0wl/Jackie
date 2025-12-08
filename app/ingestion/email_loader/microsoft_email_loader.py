import logging
from typing import Dict, List, Optional

import requests
from requests import Response

from app.core.ms_config import settings
from app.ingestion.email_loader.base_email_loader import BaseEmailLoader
from auth.msal_device_auth import MSALDeviceAuthManager

logger = logging.getLogger(__name__)


class MicrosoftEmailLoader(BaseEmailLoader):
    """
    Email loader using Microsoft Graph + MSAL device code flow (public client).

    - Pas de client secret ni redirect URI.
    - Utilise MSALDeviceAuthManager pour obtenir un jeton d'accès Graph.
    - Récupère les derniers e-mails de la mailbox de l'utilisateur connecté.
    """

    def __init__(
        self,
        auth_manager: Optional[MSALDeviceAuthManager] = None,
        *,
        max_emails: int = 20,
    ) -> None:
        self.auth_manager = auth_manager or MSALDeviceAuthManager(
            client_id=settings.CLIENT_ID,
            tenant_id=settings.TENANT_ID,
            token_path=settings.TOKEN_PATH,
        )
        self.max_emails = max_emails

    def authenticate(self) -> str:
        """Return a valid Graph access token (device flow if needed)."""
        return self.auth_manager.get_access_token()

    def load_emails(self) -> List[Dict]:
        """Fetch emails from Microsoft Graph and return structured dictionaries."""
        def _call_graph_with_token(token: str) -> Response:
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
            }
            params = {
                "$top": self.max_emails,
                "$select": "id,subject,body,from,receivedDateTime",
                "$orderby": "receivedDateTime DESC",
            }
            return requests.get(
                "https://graph.microsoft.com/v1.0/me/messages",
                headers=headers,
                params=params,
            )

        token = self.authenticate()
        resp = _call_graph_with_token(token)
        if resp.status_code == 401:
            logger.warning("Access token expired or invalid. Re-authentication required.")
            raise RuntimeError("reauth_required")

        try:
            resp.raise_for_status()
        except Exception as exc:
            logger.error("Graph API call failed: %s", resp.text)
            raise exc

        data = resp.json()
        items = data.get("value", []) if isinstance(data, dict) else []

        emails: List[Dict] = []
        for item in items:
            emails.append(
                {
                    "id": item.get("id", ""),
                    "subject": item.get("subject") or "",
                    "sender": (item.get("from", {}) or {}).get("emailAddress", {}).get("address", ""),
                    "date": item.get("receivedDateTime", ""),
                    "body": (item.get("body") or {}).get("content", "") or "",
                }
            )

        logger.info("Loaded %d emails via Graph.", len(emails))
        return emails

    def get_source_name(self) -> str:
        return "outlook_email"

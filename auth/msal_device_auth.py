"""
MSAL authentication using Device Code Flow (public client, no secret/redirect),
with persistent MSAL cache (refresh handled via acquire_token_silent).
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import msal
from msal import SerializableTokenCache

from app.core.ms_config import settings

logger = logging.getLogger(__name__)


class MSALDeviceAuthManager:
    def __init__(
        self,
        *,
        client_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        token_path: Optional[str] = None,
        token_filename: Optional[str] = None,
        scopes: Optional[list[str]] = None,
    ) -> None:
        self.client_id = client_id or settings.CLIENT_ID
        self.tenant_id = tenant_id or settings.TENANT_ID

        if not self.client_id or self.client_id == "your_client_id":
            raise ValueError("CLIENT_ID not configured in .env")
        if not self.tenant_id or self.tenant_id == "common":
            raise ValueError("TENANT_ID not configured in .env")

        self.scopes = scopes or ["https://graph.microsoft.com/.default"]

        self.token_path = Path(token_path or settings.TOKEN_PATH)
        self.token_path.mkdir(parents=True, exist_ok=True)
        self.token_file = self.token_path / (token_filename or settings.TOKEN_FILENAME)

        self.cache = SerializableTokenCache()
        if self.token_file.exists():
            try:
                self.cache.deserialize(self.token_file.read_text())
            except Exception as exc:
                logger.warning("Could not deserialize token cache: %s", exc)

        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.app = msal.PublicClientApplication(
            client_id=self.client_id,
            authority=self.authority,
            token_cache=self.cache,
        )

    def _persist_cache(self) -> None:
        if self.cache.has_state_changed:
            self.token_file.write_text(self.cache.serialize())

    def is_authenticated(self) -> bool:
        # Vérifie si un compte existe dans le cache et un token silencieux est possible
        accounts = self.app.get_accounts()
        if not accounts:
            return False
        result = self.app.acquire_token_silent(self.scopes, account=accounts[0])
        if result and "access_token" in result:
            self._persist_cache()
            return True
        return False

    def ensure_authenticated(self) -> dict:
        # Essaye d'abord en silencieux
        accounts = self.app.get_accounts()
        if accounts:
            result = self.app.acquire_token_silent(self.scopes, account=accounts[0])
            if result and "access_token" in result:
                self._persist_cache()
                return result

        # Device flow interactif
        flow = self.app.initiate_device_flow(scopes=self.scopes)
        if "user_code" not in flow:
            raise RuntimeError(f"Failed to initiate device flow: {flow}")

        print("\n" + flow["message"] + "\n")
        token = self.app.acquire_token_by_device_flow(flow)
        if "error" in token or "access_token" not in token:
            raise RuntimeError(f"Device flow failed: {token}")

        self._persist_cache()
        return token

    def start_device_flow(self) -> dict:
        flow = self.app.initiate_device_flow(scopes=self.scopes)
        if "user_code" not in flow:
            raise RuntimeError(f"Failed to initiate device flow: {flow}")
        return flow

    def complete_device_flow(self, flow: dict) -> dict:
        token = self.app.acquire_token_by_device_flow(flow)
        if "error" in token or "access_token" not in token:
            raise RuntimeError(f"Device flow failed: {token}")
        self._persist_cache()
        return token

    def get_access_token(self) -> str:
        accounts = self.app.get_accounts()
        if accounts:
            result = self.app.acquire_token_silent(self.scopes, account=accounts[0])
            if result and "access_token" in result:
                self._persist_cache()
                return result["access_token"]
        # sinon, interactivité
        token = self.ensure_authenticated()
        access_token = token.get("access_token") if token else None
        if not access_token:
            raise ValueError("No access token available")
        return access_token

    def logout(self) -> None:
        if self.token_file.exists():
            self.token_file.unlink()
        try:
            self.cache.clear()  # type: ignore[attr-defined]
        except Exception:
            pass

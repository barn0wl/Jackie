"""
MSAL authentication using Device Code Flow (public client, no secret/redirect),
with per-user persistent cache (multi-user support).
"""
from __future__ import annotations

import logging
from typing import Optional, Tuple, Any

import msal
import requests
from msal import PublicClientApplication, SerializableTokenCache

from app.core.ms_config import settings
from auth.token_manager import TokenManager

logger = logging.getLogger(__name__)


class MSALDeviceAuthManager:
    """
    Gestion multi-utilisateur : chaque utilisateur a son cache MSAL sérialisé.
    """

    def __init__(
        self,
        *,
        client_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        token_path: Optional[str] = None,
        scopes: Optional[list[str]] = None,
        user_email: Optional[str] = None,
    ) -> None:
        self.client_id = client_id or settings.CLIENT_ID
        self.tenant_id = tenant_id or settings.TENANT_ID
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.scopes = scopes or ["https://graph.microsoft.com/.default"]

        self.token_path = token_path or settings.TOKEN_PATH
        self.token_manager: TokenManager = TokenManager(self.token_path)

        self.current_user_email: Optional[str] = user_email
        self.current_user_id: Optional[str] = None

        self.cache = SerializableTokenCache()
        self.app = PublicClientApplication(
            client_id=self.client_id,
            authority=self.authority,
            token_cache=self.cache,
        )

        # Si un email est fourni, tenter de charger son cache
        if self.current_user_email:
            self._load_cache_for_user(self.current_user_email)

    # ---------- Cache helpers ----------
    def _load_cache_for_user(self, user_email: str) -> None:
        serialized = self.token_manager.load_cache(user_email)
        if serialized:
            try:
                self.cache.deserialize(serialized)
                self.current_user_email = user_email
            except Exception as exc:
                logger.warning("Failed to load cache for %s: %s", user_email, exc)

    def _persist_cache(self, user_email: str, user_name: Optional[str] = None) -> None:
        if self.cache.has_state_changed:
            self.token_manager.save_cache(user_email, self.cache.serialize(), user_name=user_name)

    # ---------- Public helpers ----------
    def get_all_cached_users(self):
        return self.token_manager.get_all_users()

    def logout(self, user_email: Optional[str] = None) -> bool:
        email = user_email or self.current_user_email
        if not email:
            return False
        return self.token_manager.delete_token(email)

    def logout_all(self) -> bool:
        return self.token_manager.delete_all_tokens()

    def get_cached_token(self, user_email: str) -> Optional[str]:
        """Recharge le cache pour cet utilisateur et tente un token silencieux."""
        self.cache = SerializableTokenCache()
        self.app = PublicClientApplication(
            client_id=self.client_id,
            authority=self.authority,
            token_cache=self.cache,
        )
        self._load_cache_for_user(user_email)
        accounts = self.app.get_accounts()
        if not accounts:
            return None
        result = self.app.acquire_token_silent(self.scopes, account=accounts[0])
        if result and "access_token" in result:
            self.current_user_email = user_email
            self.current_user_id = accounts[0].get("home_account_id")
            self._persist_cache(user_email)
            return result["access_token"]
        return None

    def is_authenticated(self) -> bool:
        accounts = self.app.get_accounts()
        if not accounts:
            return False
        result = self.app.acquire_token_silent(self.scopes, account=accounts[0])
        return bool(result and "access_token" in result)

    # ---------- Device flow ----------
    def initiate_device_flow(self) -> Tuple[Optional[str], Optional[dict]]:
        """Initie le device flow et retourne (message, flow)."""
        try:
            flow = self.app.initiate_device_flow(scopes=self.scopes)
            if "user_code" not in flow:
                raise ValueError("Erreur lors de l'initialisation du device flow")
            return flow.get("message"), flow
        except Exception as exc:
            logger.error("Device flow init error: %s", exc)
            return None, None

    def acquire_token_by_flow(self, flow: dict) -> Optional[str]:
        """Acquiert un token via device flow, récupère l'email, et persiste le cache."""
        try:
            result = self.app.acquire_token_by_device_flow(flow)
            if "error" in result or "access_token" not in result:
                logger.error("Device flow error: %s", result.get("error_description", result))
                return None

            access_token = result["access_token"]
            user_email, user_id = self._get_user_identity(access_token)
            if not user_email:
                logger.error("Could not retrieve user email from Graph")
                return None

            self.current_user_email = user_email
            self.current_user_id = user_id or user_email
            self._persist_cache(user_email, user_name=user_email)
            return access_token
        except Exception as exc:
            logger.error("Token acquisition error: %s", exc)
            return None

    def _get_user_identity(self, access_token: str) -> Tuple[Optional[str], Optional[str]]:
        """Appelle /me pour extraire email et id."""
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            resp = requests.get("https://graph.microsoft.com/v1.0/me", headers=headers, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                email = data.get("userPrincipalName") or data.get("mail")
                return email, data.get("id")
            return None, None
        except Exception as exc:
            logger.error("Error retrieving user email: %s", exc)
            return None, None

    # ---------- Legacy helpers ----------
    def get_access_token(self) -> str:
        """Tentative silencieuse sinon device flow complet."""
        accounts = self.app.get_accounts()
        if accounts:
            result = self.app.acquire_token_silent(self.scopes, account=accounts[0])
            if result and "access_token" in result:
                claims: Any = result.get("id_token_claims", {}) if isinstance(result, dict) else {}
                self.current_user_email = claims.get("preferred_username")
                self.current_user_id = accounts[0].get("home_account_id")
                self._persist_cache(self.current_user_email or "unknown")
                return result["access_token"]

        # Sinon device flow complet
        message, flow = self.initiate_device_flow()
        if not flow:
            raise RuntimeError("Failed to initiate device flow")
        print("\n" + (message or "") + "\n")
        token = self.acquire_token_by_flow(flow)
        if not token:
            raise RuntimeError("Device flow failed")
        return token

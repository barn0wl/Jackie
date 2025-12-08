"""
Token Manager: gère des caches MSAL par utilisateur (fichiers locaux).
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class TokenManager:
    """
    Stockage simple par utilisateur :
    data/tokens/
      ├── users.json
      └── user_tokens/<email_sécurisé>.json
    """

    def __init__(self, token_path: str = "data/tokens") -> None:
        self.token_path = Path(token_path)
        self.token_path.mkdir(parents=True, exist_ok=True)

        self.user_tokens_dir = self.token_path / "user_tokens"
        self.user_tokens_dir.mkdir(parents=True, exist_ok=True)

        self.users_registry = self.token_path / "users.json"
        logger.info("✅ TokenManager initialized at %s", self.token_path)

    def _safe_email(self, user_email: str) -> str:
        return user_email.replace("@", "_at_").replace(".", "_")

    def _get_token_file(self, user_email: str) -> Path:
        return self.user_tokens_dir / f"{self._safe_email(user_email)}.json"

    def _load_users_registry(self) -> Dict:
        if not self.users_registry.exists():
            return {}
        try:
            return json.loads(self.users_registry.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning("Error loading users registry: %s", exc)
            return {}

    def _save_users_registry(self, users: Dict) -> None:
        try:
            self.users_registry.write_text(
                json.dumps(users, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception as exc:
            logger.error("Error saving users registry: %s", exc)

    # --- cache sérialisé (MSAL) ---
    def save_cache(self, user_email: str, cache_serialized: str, user_name: Optional[str] = None) -> bool:
        try:
            token_file = self._get_token_file(user_email)
            payload = {
                "user_email": user_email,
                "user_name": user_name or user_email,
                "saved_at": datetime.now().isoformat(),
                "cache": cache_serialized,
            }
            token_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

            users = self._load_users_registry()
            users[user_email] = {
                "name": user_name or user_email,
                "last_login": datetime.now().isoformat(),
                "token_file": token_file.name,
            }
            self._save_users_registry(users)
            logger.info("✅ Cache saved for user: %s", user_email)
            return True
        except Exception as exc:
            logger.error("Error saving cache for %s: %s", user_email, exc)
            return False

    def load_cache(self, user_email: str) -> Optional[str]:
        try:
            token_file = self._get_token_file(user_email)
            if not token_file.exists():
                return None
            data = json.loads(token_file.read_text(encoding="utf-8"))
            return data.get("cache")
        except Exception as exc:
            logger.error("Error loading cache for %s: %s", user_email, exc)
            return None

    # --- alias dict complet (compat) ---
    def save_token(self, user_email: str, token_dict: Dict, user_name: Optional[str] = None) -> bool:
        try:
            token_file = self._get_token_file(user_email)
            payload = {
                "user_email": user_email,
                "user_name": user_name or user_email,
                "saved_at": datetime.now().isoformat(),
                "token": token_dict,
            }
            token_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

            users = self._load_users_registry()
            users[user_email] = {
                "name": user_name or user_email,
                "last_login": datetime.now().isoformat(),
                "token_file": token_file.name,
            }
            self._save_users_registry(users)
            return True
        except Exception as exc:
            logger.error("Error saving token for %s: %s", user_email, exc)
            return False

    def load_token(self, user_email: str) -> Optional[Dict]:
        try:
            token_file = self._get_token_file(user_email)
            if not token_file.exists():
                return None
            data = json.loads(token_file.read_text(encoding="utf-8"))
            return data.get("token")
        except Exception as exc:
            logger.error("Error loading token for %s: %s", user_email, exc)
            return None

    # --- listing / suppression ---
    def get_all_users(self) -> List[Dict]:
        users = self._load_users_registry()
        return [
            {
                "email": email,
                "name": info.get("name", email),
                "last_login": info.get("last_login"),
            }
            for email, info in users.items()
        ]

    def delete_token(self, user_email: str) -> bool:
        try:
            token_file = self._get_token_file(user_email)
            if token_file.exists():
                token_file.unlink()
            users = self._load_users_registry()
            if user_email in users:
                users.pop(user_email, None)
                self._save_users_registry(users)
            return True
        except Exception as exc:
            logger.error("Error deleting token for %s: %s", user_email, exc)
            return False

    def delete_all_tokens(self) -> bool:
        try:
            import shutil
            if self.user_tokens_dir.exists():
                shutil.rmtree(self.user_tokens_dir)
                self.user_tokens_dir.mkdir(parents=True, exist_ok=True)
            if self.users_registry.exists():
                self.users_registry.unlink()
            return True
        except Exception as exc:
            logger.error("Error deleting all tokens: %s", exc)
            return False

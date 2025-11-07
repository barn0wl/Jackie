# app/ingestion/email_loader_factory.py

import logging
from app.core.ms_config import settings
from app.ingestion.email_loader.microsoft_email_loader import MicrosoftEmailLoader
from app.ingestion.email_loader.mock_email_loader import MockEmailLoader
from app.ingestion.email_loader.base_email_loader import BaseEmailLoader


logger = logging.getLogger(__name__)

class EmailLoaderFactory:
    """
    Factory to instantiate the appropriate email loader
    based on configuration or environment.
    """

    @staticmethod
    def create_loader() -> BaseEmailLoader:
        provider = getattr(settings, "EMAIL_PROVIDER", "mock").lower()

        logger.info(f"📬 Initialisation du chargeur d’e-mails : provider = '{provider}'")

        if provider == "microsoft":
            try:
                return MicrosoftEmailLoader(
                    client_id=settings.CLIENT_ID,
                    client_secret=settings.CLIENT_SECRET,
                    tenant_id=settings.TENANT_ID,
                    token_path=settings.TOKEN_PATH,
                    token_filename=settings.TOKEN_FILENAME,
                )
            except Exception as e:
                logger.error(f"❌ Impossible d’initialiser MicrosoftEmailLoader : {e}")
                raise

        elif provider == "mock":
            return MockEmailLoader(num_emails=20)

        else:
            raise ValueError(f"Type de chargeur d’e-mails inconnu : '{provider}'")

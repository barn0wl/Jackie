import logging

from app.core.ms_config import settings
from app.ingestion.email_loader.base_email_loader import BaseEmailLoader
from app.ingestion.email_loader.microsoft_email_loader import MicrosoftEmailLoader
from app.ingestion.email_loader.mock_email_loader import MockEmailLoader

logger = logging.getLogger(__name__)


class EmailLoaderFactory:
    """
    Factory to instantiate the appropriate email loader
    based on configuration or environment.
    """

    @staticmethod
    def create_loader() -> BaseEmailLoader:
        provider = getattr(settings, "EMAIL_PROVIDER", "mock").lower()

        logger.info("Initialisation du chargeur d'e-mails : provider='%s'", provider)

        if provider == "microsoft":
            return MicrosoftEmailLoader()

        if provider == "mock":
            return MockEmailLoader(num_emails=20)

        raise ValueError(f"Type de chargeur d'e-mails inconnu : '{provider}'")

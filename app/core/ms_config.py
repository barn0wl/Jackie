import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    TOKEN_PATH = os.getenv("TOKEN_PATH", "data/tokens")
    TOKEN_FILENAME = os.getenv("TOKEN_FILENAME", "o365_token.txt")
    CLIENT_ID = os.getenv("CLIENT_ID", "your_client_id")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET", "secret")
    TENANT_ID = os.getenv("TENANT_ID", "common")
    EMAIL_PROVIDER = os.getenv("EMAIL_PROVIDER", "mock")  # mock / microsoft

settings = Settings()

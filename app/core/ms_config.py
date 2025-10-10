import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    TOKEN_PATH = os.getenv("TOKEN_PATH", "data/tokens")
    TOKEN_FILENAME = os.getenv("TOKEN_FILENAME", "o365_token.txt")

settings = Settings()
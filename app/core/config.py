# app/core/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Global application configuration."""

    # Path to store the Chroma vector database
    CHROMA_PATH = os.getenv("CHROMA_PATH", "data/chromadb")
    # Ollama model for LLM inference
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")
    # Embedding model (local)
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-base")
    # Chunking configuration
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 800))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 100))

settings = Settings()

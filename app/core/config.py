# app/core/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    CHROMA_PATH = os.getenv("CHROMA_PATH", "data/chromadb")

    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")  # ollama / openai / groq

    # Ollama connection + defaults
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")  # e.g. mistral, llama3, qwen2
    OLLAMA_NUM_CTX = int(os.getenv("OLLAMA_NUM_CTX", 8192))
    OLLAMA_TEMPERATURE = float(os.getenv("OLLAMA_TEMPERATURE", 0.2))

    # Embeddings (local)
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-base")

    # Chunking
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 800))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 100))

settings = Settings()

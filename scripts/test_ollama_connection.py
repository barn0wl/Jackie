# scripts/test_ollama_connection.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.core.config import settings

try:
    import ollama
    
    print(f"Testing Ollama connection to: {settings.OLLAMA_HOST}")
    client = ollama.Client(host=settings.OLLAMA_HOST)
    
    # Try to list models
    models = client.list()
    print(f"✅ Connected! Available models: {[m['name'] for m in models['models']]}")
    
    # Try a simple chat
    print(f"\nTesting model: {settings.OLLAMA_MODEL}")
    response = client.chat(
        model=settings.OLLAMA_MODEL,
        messages=[{"role": "user", "content": "Hello"}]
    )
    print(f"✅ Model works! Response: {response['message']['content']}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nTroubleshooting:")
    print("1. Is Ollama running? Try: ollama serve")
    print(f"2. Is the model pulled? Try: ollama pull {settings.OLLAMA_MODEL}")
    print("3. Check your OLLAMA_HOST in .env")

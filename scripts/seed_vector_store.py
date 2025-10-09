# scripts/seed_vector_store.py
import os
import sys

# Ensure the app package is discoverable
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.models.document_chunk import DocumentChunk
from app.services.embeddings_service import EmbeddingsService
from app.services.vector_store_service import get_vector_store

print("🚀 Seeding ChromaDB with sample data...")

# --- Step 1. Define sample data ---
documents = [
    {
        "content": "Les remboursements sont généralement traités sous 30 jours après validation du dossier.",
        "metadata": {"source": "email_finance", "topic": "Remboursement"}
    },
    {
        "content": "Pour toute demande de congé, veuillez utiliser le portail RH avant la date limite de dépôt.",
        "metadata": {"source": "email_rh", "topic": "Congés"}
    },
    {
        "content": "Les notes de frais doivent être soumises via le logiciel interne avant le 5 de chaque mois.",
        "metadata": {"source": "email_finance", "topic": "Notes de frais"}
    },
    {
        "content": "La politique de sécurité impose de changer votre mot de passe tous les 90 jours.",
        "metadata": {"source": "email_it", "topic": "Sécurité"}
    },
]

# --- Step 2. Convert to DocumentChunk objects ---
chunks = [
    DocumentChunk(id=f"sample_{i}", content=doc["content"], metadata=doc["metadata"])
    for i, doc in enumerate(documents)
]

# --- Step 3. Generate embeddings ---
embedder = EmbeddingsService()
texts = [chunk.content for chunk in chunks]
embeddings = embedder.embed_texts(texts)

# --- Step 4. Store them in the vector DB ---
vector_store = get_vector_store()
vector_store.add_chunks(chunks, embeddings)

print(f"✅ Seed completed. Vector store now contains {vector_store.count()} documents.")

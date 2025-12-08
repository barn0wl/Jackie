# scripts/seed_vector_store_from_pdf.py

import os
import sys

# S'assurer que le package app est visible
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import pdfplumber

from chunk_utils.chunk import chunk_text_for_embeddings
from app.services.embeddings_service import EmbeddingsService
from app.services.vector_store_service import get_vector_store


PDF_PATH = r"C:\Users\acoulibaly\Downloads\CENTAURES DATAVIEW DISTRIBUTION-01-07-2025.pdf"


def extract_pdf_text(pdf_path: str) -> str:
    """Extrait le texte brut d'un PDF (toutes les pages concaténées)."""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF introuvable: {pdf_path}")

    texts = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            page_text = page.extract_text() or ""
            print(f"📄 Page {i}: {len(page_text)} caractères")
            texts.append(page_text)

    full_text = "\n\n".join(texts)
    print(f"\n✅ Extraction terminée. Longueur totale du texte: {len(full_text)} caractères")
    return full_text


def main():
    print("🚀 Seeding ChromaDB avec le contenu du PDF...")

    # 1) Extraction du texte
    text = extract_pdf_text(PDF_PATH)
    if not text.strip():
        print("⚠️ Aucun texte extrait du PDF. Abandon.")
        return

    # 2) Chunking (réutilise ton util)
    print("✂️  Découpage en chunks...")
    chunks = chunk_text_for_embeddings(
        text=text,
        chunk_size=500,        # à ajuster selon ton besoin
        chunk_overlap=100,
        metadata={"source": "pdf", "file": os.path.basename(PDF_PATH)},
    )

    if not chunks:
        print("⚠️ Aucun chunk généré. Abandon.")
        return

    print(f"✅ {len(chunks)} chunks générés. Passage à l'embed + vector store...")

    # 3) Embeddings
    embedder = EmbeddingsService()
    texts = [chunk.content for chunk in chunks]
    embeddings = embedder.embed_texts(texts)

    if not embeddings:
        print("⚠️ Aucune embedding générée. Vérifie EmbeddingsService.")
        return

    # 4) Insertion dans la DB vectorielle
    vector_store = get_vector_store()
    vector_store.add_chunks(chunks, embeddings)

    print(f"✅ Seed terminé. La vector store contient maintenant {vector_store.count()} documents.")


if __name__ == "__main__":
    main()

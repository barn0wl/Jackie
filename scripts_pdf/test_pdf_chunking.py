# scripts/test_pdf_chunking.py

import os
import sys

# Rendre le package app importable
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import pdfplumber

from chunk_utils.chunk import chunk_text_for_embeddings  # ta fonction utilitaire
# from app.models.document_chunk import DocumentChunk  # pas forcément nécessaire ici


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
    print("🔍 Test extraction + chunking PDF")

    # 1) Extraction
    text = extract_pdf_text(PDF_PATH)

    if not text.strip():
        print("⚠️ Aucun texte extrait du PDF. Vérifie le fichier (scanné ?)")
        return

    # 2) Chunking (utilise ta fonction utilitaire existante)
    print("✂️  Découpage en chunks...")
    chunks = chunk_text_for_embeddings(
        text=text,
        chunk_size=500,      # tu peux ajuster
        chunk_overlap=100,
        metadata={"source": "pdf_test", "file": os.path.basename(PDF_PATH)},
    )

    print(f"✅ {len(chunks)} chunks générés.\n")

    # 3) Afficher quelques exemples
    for i, chunk in enumerate(chunks[:5], start=1):
        print(f"--- Chunk {i}/{len(chunks)} ---")
        print("ID:", chunk.id)
        print("Metadata:", chunk.metadata)
        print("Contenu:", (chunk.content[:400] + "…") if len(chunk.content) > 400 else chunk.content)
        print()

    print("✅ Test terminé.")


if __name__ == "__main__":
    main()

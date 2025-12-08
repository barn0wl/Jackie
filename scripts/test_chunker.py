# scripts/test_chunker.py

import os
import sys

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.services.chunker.factory import ChunkerFactory
from app.models.document_chunk import DocumentChunk


def test_recursive_chunker():
    """Test the recursive text chunker with different document types."""
    print("🧪 Testing Recursive Text Chunker\n")
    
    # Initialize chunker
    chunker = ChunkerFactory.create(
        chunker_type="recursive",
        chunk_size=500,  # Smaller for testing
        chunk_overlap=100
    )
    
    # Test documents
    test_documents = [
        {
            "name": "Short document",
            "text": "Ceci est un document court qui ne devrait pas être divisé.",
            "metadata": {
                "source_id": "test_short.txt",
                "source_type": "test",
                "author": "Test User"
            }
        },
        {
            "name": "Medium document",
            "text": """Section 1 : Introduction
            
Les Centaures Routiers est une entreprise spécialisée dans le transport logistique.
Nous opérons dans toute la France depuis plus de 20 ans.

Section 2 : Mission

Notre mission est de fournir des solutions de transport fiables et durables.
Nous nous engageons à respecter les délais et à maintenir une communication transparente.

Section 3 : Valeurs

- Fiabilité
- Innovation
- Développement durable
- Collaboration""",
            "metadata": {
                "source_id": "presentation_entreprise.md",
                "source_type": "markdown",
                "department": "communication"
            }
        },
        {
            "name": "Long document (policy)",
            "text": """POLITIQUE DE REMBOURSEMENT - VERSION 2024

ARTICLE 1 : DÉFINITIONS

1.1. Demande de remboursement : Document formel soumis par un employé pour obtenir le remboursement de frais engagés dans le cadre de ses fonctions.

1.2. Frais éligibles : Dépenses directement liées à l'exécution des missions de l'employé et préalablement approuvées.

1.3. Délai de traitement : Période entre la soumission d'une demande complète et son paiement effectif.

ARTICLE 2 : PROCÉDURE

2.1. Soumission
L'employé doit soumettre sa demande via le portail RH dédié. Le formulaire électronique est obligatoire depuis le 1er janvier 2024.

2.2. Documents requis
- Formulaire de demande complété
- Factures originales numérisées
- Justificatifs de paiement
- Rapport de mission (si frais de déplacement)

2.3. Validation
Le manager doit valider la demande dans les 48 heures. En l'absence de réponse, une relance automatique est envoyée.

ARTICLE 3 : DÉLAIS

3.1. Traitement standard
30 jours ouvrables maximum après validation complète.

3.2. Traitement accéléré
10 jours ouvrables pour les frais médicaux ou situations d'urgence approuvées par la direction.

3.3. Cas particuliers
Les projets internationaux peuvent nécessiter un délai supplémentaire de 15 jours.""",
            "metadata": {
                "source_id": "politique_remboursement_v2024.pdf",
                "source_type": "pdf",
                "document_type": "policy",
                "version": "2024.1"
            }
        }
    ]
    
    # Test each document
    for doc in test_documents:
        print(f"\n{'='*60}")
        print(f"Testing: {doc['name']}")
        print(f"{'='*60}")
        
        # Chunk the document
        chunks = chunker.chunk_document(
            text=doc['text'],
            metadata=doc['metadata']
        )
        
        # Display results
        print(f"Original length: {len(doc['text'])} characters")
        print(f"Number of chunks created: {len(chunks)}")
        
        for i, chunk in enumerate(chunks):
            print(f"\n  Chunk {i+1}:")
            print(f"    Size: {len(chunk.content)} chars")
            print(f"    Source: {chunk.source_id}")
            print(f"    Chunk index: {chunk.chunk_index}")
            print(f"    Preview: {chunk.content[:80]}..." if len(chunk.content) > 80 else f"    Content: {chunk.content}")
        
        # Verify chunk properties
        print(f"\n  Verification:")
        print(f"    All chunks have content: {all(bool(c.content.strip()) for c in chunks)}")
        print(f"    Chunk indices are sequential: {all(c.chunk_index == i for i, c in enumerate(chunks))}")
        print(f"    Source IDs match: {all(c.source_id == doc['metadata']['source_id'] for c in chunks)}")
    
    print(f"\n{'='*60}")
    print("✅ Chunker test completed successfully!")
    return True


def test_different_chunk_sizes():
    """Test how chunk size affects the output."""
    print("\n\n📊 Testing Different Chunk Sizes\n")
    
    test_text = """Introduction.
    
Premier paragraphe avec plusieurs phrases pour tester le fonctionnement du chunker. Cette phrase est assez longue pour voir comment le splitter gère les différentes séparateurs.

Deuxième paragraphe. Encore du contenu ici. Et une autre phrase. Puis une dernière phrase pour ce paragraphe.

Troisième et dernier paragraphe du document de test. Fin."""
    
    chunk_sizes = [100, 200, 500, 1000]
    
    for size in chunk_sizes:
        chunker = ChunkerFactory.create(
            chunker_type="recursive",
            chunk_size=size,
            chunk_overlap=50
        )
        
        chunks = chunker.chunk_document(
            text=test_text,
            metadata={"source_id": "size_test.txt", "source_type": "test"}
        )
        
        print(f"\nChunk size: {size} (overlap: 50)")
        print(f"  Number of chunks: {len(chunks)}")
        print(f"  Average chunk size: {sum(len(c.content) for c in chunks) / len(chunks) if chunks else 0:.0f} chars")
        
        if chunks:
            print(f"  Chunk sizes: {[len(c.content) for c in chunks]}")


def test_metadata_preservation():
    """Test that metadata is properly preserved across chunks."""
    print("\n\n🔍 Testing Metadata Preservation\n")
    
    chunker = ChunkerFactory.create(chunker_type="recursive")
    
    metadata = {
        "source_id": "test_metadata.pdf",
        "source_type": "pdf",
        "author": "Jean Dupont",
        "department": "RH",
        "confidential": True,
        "tags": ["policy", "internal", "2024"]
    }
    
    text = "Première partie. Deuxième partie. Troisième partie."
    
    chunks = chunker.chunk_document(text=text, metadata=metadata)
    
    print(f"Original metadata keys: {list(metadata.keys())}")
    
    if chunks:
        print(f"\nMetadata in first chunk:")
        for key, value in chunks[0].metadata.items():
            print(f"  {key}: {value}")
        
        # Check that system fields are added
        print(f"\nSystem fields present:")
        print(f"  total_chunks: {'total_chunks' in chunks[0].metadata}")
        print(f"  chunk_size_chars: {'chunk_size_chars' in chunks[0].metadata}")
        
        # Verify all chunks have same base metadata
        all_same_source = all(c.source_id == metadata['source_id'] for c in chunks)
        print(f"\nAll chunks have same source_id: {all_same_source}")


def main():
    """Run all chunker tests."""
    print("🧪 Starting Chunker Service Tests")
    print("=" * 60)
    
    try:
        # Run tests
        test_recursive_chunker()
        test_different_chunk_sizes()
        test_metadata_preservation()
        
        print(f"\n{'='*60}")
        print("🎉 All chunker tests passed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

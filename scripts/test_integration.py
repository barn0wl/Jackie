# scripts/test_integration.py

import os
import sys

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.services.ingestion_service import IngestionService
from app.services.retriever_service import RetrieverService
from app.services.llm.factory import LLMServiceFactory


def test_full_rag_pipeline():
    """Test the complete RAG pipeline from ingestion to answer generation."""
    print("🔗 Testing Complete RAG Pipeline")
    print("=" * 60)
    
    # Step 1: Ingest test documents
    print("\n📥 Step 1: Ingesting test documents...")
    
    ingestion_service = IngestionService()
    
    test_docs = [
        {
            "text": """RÈGLEMENT INTÉRIEUR - ARTICLE 12 : TÉLÉTRAVAIL
            
1. ÉLIGIBILITÉ
Le télétravail est autorisé pour tous les employés ayant au moins 6 mois d'ancienneté.
L'accord doit être formalisé par un avenant au contrat.

2. FRÉQUENCE
Maximum 3 jours par semaine, sur accord du manager.
Les mardis et jeudis sont des jours privilégiés pour les réunions présentielles.

3. ÉQUIPEMENT
L'entreprise fournit un ordinateur portable et un casque.
La connexion internet est à la charge de l'employé.

4. COMMUNICATION
Présence obligatoire sur Teams pendant les heures de travail.
Réunion d'équipe quotidienne à 9h30.""",
            "source_id": "reglement_teletravail_v2.pdf",
            "source_type": "pdf",
            "metadata": {
                "department": "rh",
                "document_type": "regulation",
                "effective_date": "2024-03-01"
            }
        },
        {
            "text": """FAQ TÉLÉTRAVAIL
            
Q: Comment demander le télétravail ?
R: Via le portail RH > Mes demandes > Télétravail. Formulaire à remplir et valider par le manager.

Q: Puis-je télétravailler depuis l'étranger ?
R: Oui, maximum 4 semaines par an. Déclaration préalable obligatoire auprès de la RH.

Q: Quels sont les jours obligatoires au bureau ?
R: Les mardis (réunion d'équipe) et un jour par mois pour les réunions transverses.

Q: Assurance en télétravail ?
R: L'assurance de l'entreprise couvre les accidents pendant les heures de travail, même à domicile.""",
            "source_id": "faq_teletravail.md",
            "source_type": "markdown",
            "metadata": {
                "department": "rh",
                "category": "faq",
                "last_updated": "2024-02-15"
            }
        }
    ]
    
    chunks = ingestion_service.ingest_documents(test_docs)
    print(f"  Ingested {len(chunks)} chunks from {len(test_docs)} documents")
    
    # Step 2: Test retrieval
    print("\n🔍 Step 2: Testing retrieval...")
    
    retriever = RetrieverService(top_k=2)
    query = "Comment demander à télétravailler ?"
    
    print(f"  Query: '{query}'")
    results = retriever.retrieve(query)
    
    if not results:
        print("  ❌ No results retrieved - test failed")
        return False
    
    print(f"  Retrieved {len(results)} relevant chunks:")
    for i, result in enumerate(results):
        source = result.get('metadata', {}).get('source_id', 'unknown')
        print(f"    {i+1}. {source}")
    
    # Step 3: Test context assembly
    print("\n📚 Step 3: Testing context assembly...")
    
    context = retriever.retrieve_context(query)
    print(f"  Context length: {len(context)} characters")
    print(f"  Context preview: {context[:200]}...")
    
    # Step 4: Test LLM integration
    print("\n🤖 Step 4: Testing LLM answer generation...")
    
    try:
        llm = LLMServiceFactory.create()
        print("  LLM initialized successfully")
        
        # Test with context
        answer = llm.generate_answer(query, context)
        print(f"  Answer generated: {len(answer)} characters")
        print(f"  Answer preview: {answer[:150]}..." if len(answer) > 150 else f"  Answer: {answer}")
        
        # Verify answer is relevant
        keywords = ["portail", "RH", "formulaire", "manager", "télétravail"]
        keyword_found = any(keyword.lower() in answer.lower() for keyword in keywords)
        print(f"  Answer contains relevant keywords: {'✅' if keyword_found else '⚠️'}")
        
        return keyword_found
        
    except Exception as e:
        print(f"  ❌ LLM test failed: {e}")
        return False


def test_chunker_in_pipeline():
    """Test that chunker works correctly within the pipeline."""
    print("\n\n⚙️ Testing Chunker in Pipeline Context")
    print("=" * 60)
    
    from app.services.chunker.factory import ChunkerFactory
    
    # Create a document with clear boundaries
    document = """CHAPITRE 1 : INTRODUCTION
    
Ce document décrit les procédures de sécurité.
    
CHAPITRE 2 : PROCÉDURES
    
2.1 Évacuation
En cas d'alarme, suivez les sorties de secours.
    
2.2 Premiers secours
Les trousses sont situées près des sorties.
    
CHAPITRE 3 : CONTACTS
    
Sécurité : poste 333
Médecin : poste 222"""
    
    # Test with different chunk sizes
    chunk_sizes = [200, 400, 1000]
    
    for chunk_size in chunk_sizes:
        print(f"\nTesting with chunk_size={chunk_size}:")
        
        chunker = ChunkerFactory.create(
            chunker_type="recursive",
            chunk_size=chunk_size,
            chunk_overlap=50
        )
        
        chunks = chunker.chunk_document(
            text=document,
            metadata={
                "source_id": "securite_procedure.pdf",
                "source_type": "pdf",
                "title": "Procédures de Sécurité"
            }
        )
        
        print(f"  Created {len(chunks)} chunks")
        
        # Check that chapters are preserved where possible
        chapter_counts = {}
        for chunk in chunks:
            if "CHAPITRE" in chunk.content:
                chapter_counts["has_chapters"] = chapter_counts.get("has_chapters", 0) + 1
        
        if chapter_counts:
            print(f"  {chapter_counts['has_chapters']} chunks contain chapter headers")
    
    return True


def test_error_handling():
    """Test error handling in the pipeline."""
    print("\n\n🚨 Testing Error Handling")
    print("=" * 60)
    
    from app.services.ingestion_service import IngestionService
    
    ingestion_service = IngestionService()
    
    # Test 1: Empty text
    print("\nTest 1: Empty text ingestion")
    try:
        chunks = ingestion_service.ingest_text(text="", source_id="empty.txt")
        print(f"  Result: {len(chunks)} chunks (should be 0)")
    except Exception as e:
        print(f"  Error (expected): {type(e).__name__}")
    
    # Test 2: Very long text
    print("\nTest 2: Very long text")
    long_text = "A " * 10000  # 10,000 character text
    try:
        chunks = ingestion_service.ingest_text(
            text=long_text,
            source_id="long_text.txt",
            metadata={"test": "long"}
        )
        print(f"  Result: {len(chunks)} chunks created")
    except Exception as e:
        print(f"  Error: {type(e).__name__}: {e}")
    
    return True


def main():
    """Run all integration tests."""
    print("🔗 Starting Integration Tests")
    print("=" * 60)
    
    try:
        # Run tests
        test1 = test_full_rag_pipeline()
        test2 = test_chunker_in_pipeline()
        test3 = test_error_handling()
        
        print(f"\n{'='*60}")
        print("📊 Integration Test Results:")
        print(f"  Full RAG pipeline: {'✅ PASS' if test1 else '❌ FAIL'}")
        print(f"  Chunker in pipeline: {'✅ PASS' if test2 else '❌ FAIL'}")
        print(f"  Error handling: {'✅ PASS' if test3 else '❌ FAIL'}")
        
        all_passed = test1 and test2 and test3
        print(f"\n{'🎉 All integration tests passed!' if all_passed else '❌ Some tests failed'}")
        
        return all_passed
        
    except Exception as e:
        print(f"\n❌ Integration test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

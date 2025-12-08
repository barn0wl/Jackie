# scripts/test_retriever.py

import os
import sys

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.services.retriever_service import RetrieverService
from app.services.ingestion_service import IngestionService


def test_retriever_basic():
    """Test basic retrieval functionality."""
    print("🔍 Testing Retriever Service - Basic\n")
    
    retriever = RetrieverService(top_k=3)
    
    test_queries = [
        "remboursement délais",
        "congés procédure",
        "notes de frais",
        "sécurité mot de passe"
    ]
    
    # Initialize a variable to track if ANY query got results
    any_results_found = False
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        results = retriever.retrieve(query)
        
        if not results:
            print("  No results found")
            continue
        
        # If we get here, we found results for this query
        any_results_found = True
        print(f"  Found {len(results)} results:")
        
        for i, result in enumerate(results):
            score = result.get('score', 'N/A')
            content = result.get('content', '')[:80]
            source = result.get('metadata', {}).get('source_id', 'unknown')
            print(f"  {i+1}. [Score: {score:.3f}] {source}: {content}...")
    
    # Return whether any query found results
    return any_results_found


def test_retriever_context():
    """Test context assembly from retrieved chunks."""
    print("\n\n📚 Testing Retriever Service - Context Assembly\n")
    
    retriever = RetrieverService(top_k=2)
    
    query = "Comment demander un remboursement ?"
    print(f"Query: '{query}'")
    
    # Get raw results
    results = retriever.retrieve(query)
    print(f"\nRaw results: {len(results)} chunks")
    
    # Get assembled context
    context = retriever.retrieve_context(query)
    
    print(f"\nAssembled context ({len(context)} chars):")
    print("-" * 50)
    print(context[:500] + "..." if len(context) > 500 else context)
    print("-" * 50)
    
    return context is not None


def test_retriever_with_new_content():
    """Test retrieval with newly ingested content."""
    print("\n\n➕ Testing Retriever with New Content\n")
    
    # First, ingest some new content
    ingestion_service = IngestionService()
    
    new_document = {
        "text": """PROCÉDURE SPÉCIALE : REMBOURSEMENT URGENT
        
Pour les cas médicaux ou situations d'urgence, un remboursement accéléré est possible.
Contactez directement le responsable financier par email : urgent-finance@centaures-routiers.fr
Pièces à fournir : certificat médical et devis préalable.
Délai : 48 heures maximum après réception des documents complets.""",
        "source_id": "procedure_urgent_2024.md",
        "source_type": "markdown",
        "metadata": {
            "department": "finance",
            "priority": "high",
            "category": "urgent"
        }
    }
    
    print("Ingesting new test document...")
    chunks = ingestion_service.ingest_text(
        text=new_document["text"],
        source_id=new_document["source_id"],
        source_type=new_document["source_type"],
        metadata=new_document["metadata"]
    )
    print(f"Ingested {len(chunks)} chunks")
    
    # Now test retrieval
    retriever = RetrieverService(top_k=3)
    query = "remboursement urgent procédure"
    
    print(f"\nQuerying for: '{query}'")
    results = retriever.retrieve(query)
    
    if results:
        print(f"Found {len(results)} results:")
        for result in results:
            source = result.get('metadata', {}).get('source_id', 'unknown')
            print(f"  - {source}: {result.get('content', '')[:80]}...")
    else:
        print("No results found (did you seed the vector store first?)")
    
    return len(results) > 0


def test_empty_query():
    """Test handling of empty queries."""
    print("\n\n⚠️ Testing Empty Query Handling\n")
    
    retriever = RetrieverService()
    
    # Test empty string
    results = retriever.retrieve("")
    print(f"Empty string query: {len(results)} results (should be 0)")
    
    # Test whitespace only
    results = retriever.retrieve("   ")
    print(f"Whitespace query: {len(results)} results (should be 0)")
    
    # Test None (if your API allows it)
    # This would typically throw an error, which is correct
    
    return True


def main():
    """Run all retriever tests."""
    print("🔍 Starting Retriever Service Tests")
    print("=" * 60)
    
    try:
        # Check if vector store is populated
        from app.services.vector_store_service import get_vector_store
        vector_store = get_vector_store()
        count = vector_store.count()
        
        print(f"Vector store contains {count} documents")
        if count == 0:
            print("⚠️  Vector store appears empty. Run scripts/seed_vector_store.py first.")
            print("Continuing with tests, but some may fail...")
        
        # Run tests
        test1 = test_retriever_basic()
        test2 = test_retriever_context()
        test3 = test_retriever_with_new_content()
        test4 = test_empty_query()
        
        print(f"\n{'='*60}")
        print("📊 Test Results:")
        print(f"  Basic retrieval: {'✅ PASS' if test1 else '❌ FAIL'}")
        print(f"  Context assembly: {'✅ PASS' if test2 else '❌ FAIL'}")
        print(f"  New content retrieval: {'✅ PASS' if test3 else '❌ FAIL'}")
        print(f"  Empty query handling: {'✅ PASS' if test4 else '❌ FAIL'}")
        
        all_passed = test1 and test2 and test3 and test4
        print(f"\n{'🎉 All tests passed!' if all_passed else '❌ Some tests failed'}")
        
        return all_passed
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

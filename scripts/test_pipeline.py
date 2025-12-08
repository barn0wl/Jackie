# scripts/test_pipeline.py

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.services.pipeline_service import PipelineService


def test_pipeline_basic():
    """Test the basic pipeline functionality."""
    print("🚀 Testing Pipeline Service")
    print("=" * 60)
    
    pipeline = PipelineService(top_k=3)
    
    test_queries = [
        "Quels sont les délais de remboursement ?",
        "Comment faire une demande de congé ?",
        "Quelle est la procédure pour les notes de frais ?",
        "Quand dois-je changer mon mot de passe ?"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Query: '{query}'")
        
        try:
            result = pipeline.run(query)
            
            print(f"  Answer length: {len(result['answer'])} characters")
            print(f"  Sources found: {len(result['sources'])}")
            
            if result['sources']:
                print(f"  Sources: {result['sources']}")
            
            # Show answer preview
            preview = result['answer'][:150] + "..." if len(result['answer']) > 150 else result['answer']
            print(f"  Answer: {preview}")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            continue
    
    return True


def test_pipeline_streaming():
    """Test streaming functionality."""
    print("\n\n📡 Testing Pipeline Streaming")
    print("=" * 60)
    
    pipeline = PipelineService(top_k=2, stream=True)
    query = "Expliquez la procédure de remboursement"
    
    print(f"Query: '{query}'")
    print("Streaming response:")
    print("-" * 50)
    
    try:
        full_response = ""
        for chunk in pipeline.stream(query):
            print(chunk, end="", flush=True)
            full_response += chunk
        
        print("\n" + "-" * 50)
        print(f"Total response length: {len(full_response)} characters")
        
        return len(full_response) > 0
        
    except Exception as e:
        print(f"\n❌ Streaming error: {e}")
        return False


def test_pipeline_with_custom_parameters():
    """Test pipeline with different configurations."""
    print("\n\n⚙️ Testing Pipeline with Custom Parameters")
    print("=" * 60)
    
    # Test different top_k values
    for top_k in [1, 2, 5]:
        print(f"\nTesting with top_k={top_k}:")
        pipeline = PipelineService(top_k=top_k)
        
        result = pipeline.run("remboursement")
        print(f"  Sources retrieved: {len(result['sources'])}")
        print(f"  Answer generated: {'✅' if result['answer'] else '❌'}")
    
    return True


def main():
    """Run all pipeline tests."""
    print("🚀 Starting Pipeline Service Tests")
    print("=" * 60)
    
    # Check if vector store is populated
    try:
        from app.services.vector_store_service import get_vector_store
        vector_store = get_vector_store()
        count = vector_store.count()
        print(f"Vector store contains {count} documents")
        
        if count == 0:
            print("⚠️  Warning: Vector store appears empty.")
            print("   Run: python scripts/seed_vector_store.py")
            print("   Then: python scripts/test_integration.py")
            print("\nSome tests may fail without data.")
    except:
        print("⚠️  Could not check vector store status")
    
    try:
        # Run tests
        test1 = test_pipeline_basic()
        test2 = test_pipeline_streaming()
        test3 = test_pipeline_with_custom_parameters()
        
        print(f"\n{'='*60}")
        print("📊 Pipeline Test Results:")
        print(f"  Basic functionality: {'✅ PASS' if test1 else '❌ FAIL'}")
        print(f"  Streaming: {'✅ PASS' if test2 else '❌ FAIL'}")
        print(f"  Custom parameters: {'✅ PASS' if test3 else '❌ FAIL'}")
        
        all_passed = test1 and test2 and test3
        print(f"\n{'🎉 All pipeline tests passed!' if all_passed else '❌ Some tests failed'}")
        
        return all_passed
        
    except Exception as e:
        print(f"\n❌ Pipeline test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

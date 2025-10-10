# scripts/test_llm.py
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.services.retriever_service import RetrieverService
from app.services.llm_service import LLMService

def main():
    query = "Quels sont les délais de remboursement ?"
    
    print("🔍 Initializing services...")
    try:
        retriever = RetrieverService(top_k=3)
        llm = LLMService()  # uses settings.OLLAMA_MODEL
    except Exception as e:
        print(f"❌ Failed to initialize services: {e}")
        return

    print("📚 Retrieving context...")
    context = retriever.retrieve_context(query)
    if not context:
        print("Pas de contexte trouvé dans Chroma. Avez-vous lancé scripts/seed_vector_store.py ?")
        return

    print("=== CONTEXTE ===")
    print(context[:600] + ("..." if len(context) > 600 else ""))
    
    print("\n=== RÉPONSE ===")
    print("⏳ Calling LLM... (this may take a few seconds)")
    
    try:
        answer = llm.generate_answer(query, context)
        if answer:
            print(answer)
        else:
            print("⚠️ LLM returned an empty response")
    except Exception as e:
        print(f"❌ LLM call failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

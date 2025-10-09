# scripts/test_llm.py
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.services.retriever_service import RetrieverService
from app.services.llm_service import LLMService

def main():
    query = "Quels sont les délais de remboursement ?"
    retriever = RetrieverService(top_k=3)
    llm = LLMService()  # uses settings.OLLAMA_MODEL

    context = retriever.retrieve_context(query)
    if not context:
        print("Pas de contexte trouvé dans Chroma. Avez-vous lancé scripts/seed_vector_store.py ?")
        return

    print("=== CONTEXTE ===")
    print(context[:600] + ("..." if len(context) > 600 else ""))
    print("\n=== RÉPONSE ===")
    answer = llm.generate_answer(query, context)
    print(answer)

if __name__ == "__main__":
    main()

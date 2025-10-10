# scripts/test_pipeline.py
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.services.pipeline_service import PipelineService

def main():
    pipeline = PipelineService(top_k=3)
    query = "Quels sont les délais de remboursement ?"
    result = pipeline.run(query)

    print("\n=== QUESTION ===")
    print(result["query"])
    print("\n=== CONTEXTE ===")
    print(result["context"][:400] + "...")
    print("\n=== RÉPONSE ===")
    print(result["answer"])
    print("\n=== SOURCES ===")
    print(result["sources"])

if __name__ == "__main__":
    main()

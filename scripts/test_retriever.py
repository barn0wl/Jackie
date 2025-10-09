import os
import sys

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.services.retriever_service import RetrieverService

retriever = RetrieverService(top_k=3)

query = "Comment faire une demande de remboursement ?"
results = retriever.retrieve(query)

if not results:
    print("No results found.")
else:
    for r in results:
        print(f"[Score: {r['score']}] {r['content'][:120]}...\n")

# Optionally test context assembly
context = retriever.retrieve_context(query)
print("\n--- Assembled Context ---\n")
print(context[:500])

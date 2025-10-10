# scripts/test_email_loader.py

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.ingestion.microsoft_email_loader import MicrosoftEmailLoader

def main():
    loader = MicrosoftEmailLoader(
        client_id=None,  # Not needed for personal account
        client_secret=None,
        tenant_id=None,
        folder_name="Inbox",
        max_emails=5,
    )

    emails = loader.load_emails()
    docs = loader.to_document_chunks(emails)

    for d in docs:
        if d is not None and d.metadata:
            print("🧾 Subject:", d.metadata["subject"])
            print("👤 From:", d.metadata["sender"])
            print("📅 Date:", d.metadata["date"])
            print("📄 Content Preview:", d.content[:200], "\n")

        print("DocumentChunk is None or missing metadate, skipping...\n")
        continue

if __name__ == "__main__":
    main()

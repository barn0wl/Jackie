# scripts/test_email_loader.py
from app.ingestion.email_loader import MicrosoftEmailLoader

def main():
    loader = MicrosoftEmailLoader(
        client_id="YOUR_AZURE_APP_ID",
        client_secret="YOUR_SECRET",
        tenant_id="YOUR_TENANT_ID",
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

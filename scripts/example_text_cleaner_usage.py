"""
Example showing how to integrate text_cleaner into the existing pipeline.

This demonstrates the complete flow:
1. Load emails using EmailLoader
2. Clean text using TextCleaner
3. Prepare for chunking/embedding
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from typing import TYPE_CHECKING, Optional, Type, cast
from app.ingestion.email_loader.email_loader_factory import EmailLoaderFactory
from app.ingestion.email_loader.base_email_loader import BaseEmailLoader
from app.ingestion.text_cleaner import TextCleanerFactory, TextCleanerType
from app.models.document_chunk import DocumentChunk


def example_1_basic_cleaning():
    """Example 1: Basic text cleaning workflow."""
    print("=" * 80)
    print("EXAMPLE 1: Basic Text Cleaning Workflow")
    print("=" * 80)
    
    # Raw email text with typical noise
    raw_text = """
    Bonjour Monsieur Dupont,
    
    Suite à notre échange téléphonique, voici les informations demandées
    concernant le remboursement de vos frais professionnels.
    
    Les délais de traitement sont généralement de 15 à 30 jours ouvrés
    après réception du dossier complet. Pour accélérer le processus,
    assurez-vous de fournir tous les justificatifs nécessaires.
    
    Cordialement,
    
    Service Comptabilité
    --
    Entreprise XYZ
    123 Rue de la Paix, 75000 Paris
    Tel: 01 23 45 67 89
    """
    
    # Create email cleaner
    cleaner = TextCleanerFactory.create("email")
    
    # Clean the text
    cleaned_text = cleaner.clean(raw_text)
    
    print("\n📧 ORIGINAL TEXT:")
    print(raw_text)
    print(f"\n📏 Length: {len(raw_text)} characters\n")
    
    print("\n✨ CLEANED TEXT:")
    print(cleaned_text)
    print(f"\n📏 Length: {len(cleaned_text)} characters")
    print(f"📉 Reduction: {100 * (1 - len(cleaned_text)/len(raw_text)):.1f}%")


def example_2_with_email_loader():
    """Example 2: Integration with EmailLoader."""
    print("\n\n" + "=" * 80)
    print("EXAMPLE 2: Integration with Email Loader")
    print("=" * 80)
    
    # Step 1: Load emails (using mock for demonstration)
    print("\n📨 Step 1: Loading emails...")
    email_loader = EmailLoaderFactory.create_loader()
    emails = email_loader.load_emails()
    print(f"✅ Loaded {len(emails)} emails")
    
    # Step 2: Convert to document chunks
    print("\n📦 Step 2: Converting to document chunks...")
    chunks = email_loader.to_document_chunks(emails)
    print(f"✅ Created {len(chunks)} document chunks")
    
    # Step 3: Clean each chunk
    print("\n🧹 Step 3: Cleaning text content...")
    cleaner = TextCleanerFactory.create(TextCleanerType.EMAIL)
    cleaned_chunks: list[DocumentChunk] = []

    for chunk in chunks:
        cleaned_content = cleaner.clean(chunk.content, chunk.metadata)
        metadata = dict(chunk.metadata or {})
        metadata.update(
            {
                "cleaned": "true",
                "cleaner": cleaner.__class__.__name__,
            }
        )

        cleaned_chunk = DocumentChunk(
            id=chunk.id,
            content=cleaned_content,
            metadata=metadata,
        )
        cleaned_chunks.append(cleaned_chunk)

    
    print(f"✅ Cleaned {len(cleaned_chunks)} chunks")
    
    # Step 4: Display results for first chunk
    if cleaned_chunks:
        print("\n📋 Sample Result (First Email):")
        original = chunks[0]
        cleaned = cleaned_chunks[0]

        metadata = original.metadata or{}
        print(f"\n  Subject: {metadata.get('subject', 'N/A')}") 
        print(f"  Sender: {metadata.get('sender', 'N/A')}") 
        print(f"  Original length: {len(original.content)} chars")
        print(f"  Cleaned length: {len(cleaned.content)} chars")
        print(f"  Reduction: {100 * (1 - len(cleaned.content)/len(original.content)):.1f}%")
        
        print("\n  Cleaned content preview:")
        preview = cleaned.content[:300] + "..." if len(cleaned.content) > 300 else cleaned.content
        print(f"  {preview}")
    
    return cleaned_chunks


def example_3_custom_configuration():
    """Example 3: Custom cleaner configuration."""
    print("\n\n" + "=" * 80)
    print("EXAMPLE 3: Custom Cleaner Configuration")
    print("=" * 80)
    
    sample_text = """
    Bonjour,
    
    Ceci est le contenu principal de l'email avec des informations importantes.
    
    Merci,
    Jean
    
    --
    Signature professionnelle
    """
    
    print("\n📧 Sample text:")
    print(sample_text)
    
    # Configuration 1: Keep signatures
    print("\n\n🔧 Configuration 1: Keep signatures")
    cleaner1 = TextCleanerFactory.create(
        "email",
        remove_signatures=False,
        remove_greetings=True
    )
    result1 = cleaner1.clean(sample_text)
    print(result1)
    
    # Configuration 2: Remove everything
    print("\n\n🔧 Configuration 2: Remove all noise")
    cleaner2 = TextCleanerFactory.create(
        "email",
        remove_signatures=True,
        remove_greetings=True
    )
    result2 = cleaner2.clean(sample_text)
    print(result2)


def example_4_different_source_types():
    """Example 4: Different source types."""
    print("\n\n" + "=" * 80)
    print("EXAMPLE 4: Different Source Types")
    print("=" * 80)
    
    # Email metadata
    email_metadata = {"source": "email_simule", "sender": "test@example.com"}
    
    # Document metadata
    doc_metadata = {"source": "report.pdf", "type": "document"}
    
    # Create cleaners from metadata
    email_cleaner = TextCleanerFactory.create_from_metadata(email_metadata)
    doc_cleaner = TextCleanerFactory.create_from_metadata(doc_metadata)
    
    print(f"\n📧 Email metadata: {email_metadata}")
    print(f"   → Cleaner: {type(email_cleaner).__name__}")
    
    print(f"\n📄 Document metadata: {doc_metadata}")
    print(f"   → Cleaner: {type(doc_cleaner).__name__}")
    
    print(f"\n📋 All supported types:")
    for source_type in TextCleanerFactory.get_supported_types():
        print(f"   • {source_type}")


def example_5_complete_pipeline_ready():
    """Example 5: Prepare cleaned chunks for embedding pipeline."""
    print("\n\n" + "=" * 80)
    print("EXAMPLE 5: Complete Pipeline-Ready Output")
    print("=" * 80)
    
    print("\n🔄 Simulating complete data preparation flow...")
    
    # Load and clean emails
    email_loader = EmailLoaderFactory.create_loader()
    loader = cast("BaseEmailLoader", email_loader)

    emails = loader.load_emails()
    chunks = loader.to_document_chunks(emails)

    cleaner = TextCleanerFactory.create(TextCleanerType.EMAIL)
    pipeline_ready_chunks: list[DocumentChunk] = []

    for chunk in chunks[:5]:
        cleaned_content = cleaner.clean(chunk.content, chunk.metadata)
        if len(cleaned_content.strip()) >= 50:
            chunk_meta = dict(chunk.metadata or {})
            pipeline_ready_chunks.append(
                DocumentChunk(
                    id=chunk.id,
                    content=cleaned_content,
                    metadata={
                        **chunk_meta,
                        "cleaned": "true",
                        "ready_for_embedding": "true",
                    },
                )
            )
    
    print(f"\n✅ Prepared {len(pipeline_ready_chunks)} chunks for embedding pipeline")
    print("\n📊 Statistics:")
    total_chars = sum(len(c.content) for c in pipeline_ready_chunks)
    avg_chars = total_chars / len(pipeline_ready_chunks) if pipeline_ready_chunks else 0
    print(f"   • Total characters: {total_chars}")
    print(f"   • Average chunk size: {avg_chars:.0f} characters")
    print(f"   • Ready for: Chunking → Embedding → Vector Store")
    
    return pipeline_ready_chunks


def main():
    """Run all examples."""
    print("\n🚀 TEXT CLEANER MODULE - USAGE EXAMPLES\n")
    
    try:
        example_1_basic_cleaning()
        example_2_with_email_loader()
        example_3_custom_configuration()
        example_4_different_source_types()
        chunks = example_5_complete_pipeline_ready()
        
        print("\n\n" + "=" * 80)
        print("✅ ALL EXAMPLES COMPLETED SUCCESSFULLY")
        print("=" * 80)
        
        print("\n💡 NEXT STEPS:")
        print("   1. These cleaned chunks are ready for the chunking module")
        print("   2. After chunking, they'll be embedded")
        print("   3. Finally, stored in ChromaDB vector store")
        print("   4. Ready for RAG queries!")
        
    except Exception as e:
        print(f"\n\n❌ EXAMPLE FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.ingestion.text_cleaner.text_cleaner_factory import TextCleanerFactory

def test_email_cleaning():
    """Test email text cleaning with realistic examples."""
    print("=" * 80)
    print("TEST 1: Email Cleaning")
    print("=" * 80)
    
    sample_email = """
    Bonjour à tous,
    
    Je souhaitais simplement faire un point sur le projet Alpha. Nous faisons de bons progrès 
    et devrions être dans les temps pour l'échéance du 15 mars.
    
    Les prochaines étapes sont :
    • Finaliser les spécifications techniques
    • Coordonner avec l'équipe développement
    • Préparer la présentation client
    
    Merci de me confirmer la disponibilité pour la réunion de vendredi.
    
    Cordialement,
    Jean Dupont
    
    --
    Jean Dupont
    Chef de Projet
    Téléphone: +33 1 23 45 67 89
    Email: jean.dupont@entreprise.com
    
    
    
    De : Marie Martin <marie.martin@partenaire.com>
    Envoyé : lundi 5 mars 2024 14:30
    À : Jean Dupont
    Objet : RE: Point projet
    
    Bonjour Jean,
    
    C'est noté pour vendredi.
    
    Marie
    
    
    Ce message et toutes les pièces jointes sont confidentiels et destinés uniquement 
    à la personne ou l'entité à laquelle ils sont adressés.
    """
    
    cleaner = TextCleanerFactory.create("email")
    cleaned = cleaner.clean(sample_email)
    
    print("\n--- ORIGINAL EMAIL ---")
    print(sample_email)
    print(f"\nOriginal length: {len(sample_email)} chars")
    
    print("\n--- CLEANED EMAIL ---")
    print(cleaned)
    print(f"\nCleaned length: {len(cleaned)} chars")
    print(f"Reduction: {100 * (1 - len(cleaned)/len(sample_email)):.1f}%")


def test_document_cleaning():
    """Test document text cleaning."""
    print("\n\n" + "=" * 80)
    print("TEST 2: Document Cleaning")
    print("=" * 80)
    
    sample_document = """
    Page 1
    
    RAPPORT ANNUEL 2024
    
    Introduction
    
    Ce rapport présente les résultats de l'entreprise pour l'année 2024.
    
    • Chiffre d'affaires en hausse de 15%
    • Expansion sur 3 nouveaux marchés
    • Investissement dans l'innovation
    
    Les détails financiers sont présentés dans les sections suivantes.
    
    [Figure 1: Évolution du CA 2020-2024]
    
    ---
    
    RAPPORT ANNUEL 2024
    Page 2
    
    Analyse Financière
    
    Les résultats financiers démontrent une croissance solide et durable.
    Le bénéfice net a augmenté de 12% par rapport à l'année précédente.
    
    [Tableau 1: Résultats financiers détaillés]
    
    La stratégie d'investissement mise en place porte ses fruits.
    
    RAPPORT ANNUEL 2024
    Page 3
    """
    
    cleaner = TextCleanerFactory.create("document")
    cleaned = cleaner.clean(sample_document)
    
    print("\n--- ORIGINAL DOCUMENT ---")
    print(sample_document)
    print(f"\nOriginal length: {len(sample_document)} chars")
    
    print("\n--- CLEANED DOCUMENT ---")
    print(cleaned)
    print(f"\nCleaned length: {len(cleaned)} chars")
    print(f"Reduction: {100 * (1 - len(cleaned)/len(sample_document)):.1f}%")


def test_factory_metadata():
    """Test factory creation from metadata."""
    print("\n\n" + "=" * 80)
    print("TEST 3: Factory from Metadata")
    print("=" * 80)
    
    # Test different metadata scenarios
    test_cases = [
        {"source": "email_simule", "sender": "test@example.com"},
        {"source": "report.pdf", "type": "document"},
        {"filename": "data.txt", "source_type": "txt"},
    ]
    
    for i, metadata in enumerate(test_cases, 1):
        cleaner = TextCleanerFactory.create_from_metadata(metadata)
        print(f"\nTest Case {i}:")
        print(f"  Metadata: {metadata}")
        print(f"  Cleaner: {cleaner.get_cleaner_name()}")
        print(f"  Type: {type(cleaner).__name__}")


def test_integration_with_email_loader():
    """Test integration with existing email loader."""
    print("\n\n" + "=" * 80)
    print("TEST 4: Integration with Email Loader")
    print("=" * 80)
    
    try:
        from app.ingestion.email_loader.mock_email_loader import MockEmailLoader
        
        # Load mock emails
        loader = MockEmailLoader(num_emails=3)
        emails = loader.load_emails()
        
        # Convert to document chunks
        chunks = loader.to_document_chunks(emails)
        
        print(f"\nLoaded {len(chunks)} email chunks")
        
        # Clean each chunk
        cleaner = TextCleanerFactory.create("email")
        
        for i, chunk in enumerate(chunks[:2], 1):  # Show first 2
            print(f"\n--- EMAIL {i} ---")
            print(f"Subject: {(chunk.metadata or {}).get('subject', 'N/A')}")
            print(f"Sender: {(chunk.metadata or {}).get('sender', 'N/A')}")
            print(f"\nOriginal content ({len(chunk.content)} chars):")
            print(chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content)
            
            cleaned = cleaner.clean(chunk.content, chunk.metadata)
            print(f"\nCleaned content ({len(cleaned)} chars):")
            print(cleaned[:200] + "..." if len(cleaned) > 200 else cleaned)
            print(f"Reduction: {100 * (1 - len(cleaned)/len(chunk.content)):.1f}%")
    
    except ImportError as e:
        print(f"\n⚠️  Could not import email loader: {e}")
        print("This test requires the email_loader module to be available.")


def main():
    """Run all text cleaner tests."""
    print("\n🧪 TESTING TEXT CLEANER MODULE\n")
    
    try:
        test_email_cleaning()
        test_document_cleaning()
        test_factory_metadata()
        test_integration_with_email_loader()
        
        print("\n\n" + "=" * 80)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        print("=" * 80)
        
        # Show supported types
        print("\n📋 Supported source types:")
        for source_type in TextCleanerFactory.get_supported_types():
            print(f"  • {source_type}")
        
    except Exception as e:
        print(f"\n\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
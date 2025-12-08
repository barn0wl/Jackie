# scripts/test_text_cleaner.py

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.services.text_cleaner_service import TextCleanerService


def test_email_cleaning():
    """Test email text cleaning."""
    print("📧 Testing Email Text Cleaning\n")
    
    cleaner = TextCleanerService()
    
    # Sample French email
    french_email = """
    <html>
    <body>
    <p>Bonjour Jean,</p>
    <p>Voici les informations demandées pour le projet.</p>
    <p>Le budget est approuvé pour 50 000€.</p>
    <img src="cid:image001.jpg"/>
    <br>
    <p>Cordialement,</p>
    <p>--</p>
    <p>Marie Dupont<br>
    Directrice Financière<br>
    Les Centaures Routiers<br>
    marie.dupont@centaures-routiers.fr</p>
    <div style="font-size: 9pt;">
    CONFIDENTIALITÉ: Ce message est confidentiel.
    </div>
    </body>
    </html>
    """
    
    metadata = {
        "source_type": "email",
        "sender": "marie.dupont@centaures-routiers.fr",
        "sender_name": "Marie Dupont"
    }
    
    cleaned = cleaner.clean_text(french_email, metadata=metadata)
    
    print("Original email HTML removed:")
    print("-" * 50)
    print(french_email[:200])
    print("\nCleaned email:")
    print("-" * 50)
    print(cleaned)
    
    # Verify cleaning worked
    assert "<html>" not in cleaned
    assert "<body>" not in cleaned
    assert "cid:image" not in cleaned
    assert "CONFIDENTIALITÉ" not in cleaned
    assert "marie.dupont" not in cleaned  # Signature should be removed
    
    print("\n✅ Email cleaning test passed")
    return True


def test_document_cleaning():
    """Test document text cleaning."""
    print("\n📄 Testing Document Text Cleaning\n")
    
    cleaner = TextCleanerService()
    
    # Sample French document with page numbers and headers
    french_doc = """
    Les Centaures Routiers
    Rapport Annuel 2024
    
    Page 1
    
    SECTION 1: INTRODUCTION
    
    Ce rapport présente les résultats de l'année 2024.
    
    Page 2
    
    SECTION 2: FINANCES
    
    • Revenus: 5M€
    • Dépenses: 3.5M€
    • Profit: 1.5M€
    
    Page 3
    
    [Image: graphique_revenus.png]
    
    SECTION 3: CONCLUSIONS
    
    L'année 2024 a été positive.
    
    © Les Centaures Routiers - Tous droits réservés
    """
    
    metadata = {
        "source_type": "pdf",
        "filename": "rapport_2024.pdf"
    }
    
    cleaned = cleaner.clean_text(french_doc, metadata=metadata)
    
    print("Original document with page numbers:")
    print("-" * 50)
    print(french_doc)
    print("\nCleaned document:")
    print("-" * 50)
    print(cleaned)
    
    # Verify cleaning worked
    assert "Page 1" not in cleaned
    assert "Page 2" not in cleaned
    assert "Page 3" not in cleaned
    assert "[Image:" not in cleaned
    assert "© Les Centaures Routiers" not in cleaned
    
    print("\n✅ Document cleaning test passed")
    return True


def main():
    """Run text cleaner tests."""
    print("🧹 Starting Text Cleaner Tests")
    print("=" * 60)
    
    try:
        test1 = test_email_cleaning()
        test2 = test_document_cleaning()
        
        print(f"\n{'='*60}")
        print("📊 Test Results:")
        print(f"  Email cleaning: {'✅ PASS' if test1 else '❌ FAIL'}")
        print(f"  Document cleaning: {'✅ PASS' if test2 else '❌ FAIL'}")
        
        all_passed = test1 and test2
        print(f"\n{'🎉 All text cleaner tests passed!' if all_passed else '❌ Some tests failed'}")
        
        return all_passed
        
    except Exception as e:
        print(f"\n❌ Text cleaner test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

# scripts/seed_vector_store.py

import os
import sys

# Ensure the app package is discoverable
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.services.ingestion_service import IngestionService

print("🚀 Seeding ChromaDB with sample data...")

# --- Step 1. Define sample data ---
sample_documents = [
    {
        "text": """Les Centaures Routiers - Politique de remboursement
        
Article 1 : Délais de traitement
Les remboursements sont généralement traités sous 30 jours ouvrables après validation complète du dossier par le service financier. Tous les documents requis doivent être soumis via le portail RH.

Article 2 : Documents requis
Pour toute demande de remboursement, les documents suivants sont obligatoires :
1. Formulaire de demande de remboursement (disponible sur l'intranet)
2. Factures originales
3. Justificatifs de paiement
4. Rapport de mission (si applicable)

Article 3 : Exceptions
Les remboursements urgents peuvent être traités en 48h pour les cas médicaux ou situations d'urgence approuvées par le management.""",
        "source_id": "politique_remboursement_v1.pdf",
        "source_type": "pdf",
        "metadata": {
            "department": "finance",
            "language": "fr",
            "document_type": "policy",
            "author": "Service Financier",
            "valid_until": "2025-12-31"
        }
    },
    {
        "text": """PROCÉDURE : Demande de congés annuels

1. PRÉ-REQUIS
- Avoir au moins 6 mois d'ancienneté
- Solde de congés positif
- Aucune période de blackout (voir calendrier RH)

2. PROCÉDURE
- Se connecter au portail RH : https://rh.centaures-routiers.fr
- Remplir le formulaire électronique
- Obtenir validation hiérarchique
- Recevoir confirmation par email

3. DÉLAIS
- 15 jours minimum avant la date de début souhaitée
- 48h pour validation hiérarchique
- Modification possible jusqu'à 7 jours avant

Pour toute question : rh@centaures-routiers.fr""",
        "source_id": "procedure_conges.md",
        "source_type": "markdown",
        "metadata": {
            "department": "rh",
            "language": "fr",
            "document_type": "procedure",
            "version": "2.1",
            "effective_date": "2024-01-01"
        }
    },
    {
        "text": """NOTE DE FRAIS - RÈGLES 2024

GÉNÉRALITÉS :
- Date limite de soumission : 5 du mois suivant
- Montant maximum par repas : 25€ (France), 35€ (International)
- Transport : Classe économique uniquement

DOCUMENTS ACCEPTÉS :
- Factures numérisées (format PDF ou JPEG)
- Tickets de caisse
- Relevés de carte bancaire
- Confirmations de réservation

VALIDATION :
1. Saisie sur l'application interne
2. Téléchargement des justificatifs
3. Validation automatique si < 100€
4. Validation manuelle si > 100€
5. Paiement sous 10 jours ouvrés

CONTACT : finance@centaures-routiers.fr""",
        "source_id": "regles_notes_frais_2024.txt",
        "source_type": "text",
        "metadata": {
            "department": "finance",
            "language": "fr",
            "fiscal_year": "2024",
            "category": "expenses",
            "last_updated": "2024-01-15"
        }
    },
    {
        "text": """POLITIQUE DE SÉCURITÉ INFORMATIQUE

1. MOT DE PASSE
- Longueur minimale : 12 caractères
- Complexité requise : majuscules, minuscules, chiffres, symboles
- Changement obligatoire : tous les 90 jours
- Pas de réutilisation sur 5 derniers mots de passe

2. DONNÉES SENSIBLES
- Chiffrement obligatoire pour données clients
- Stockage cloud autorisé uniquement sur OneDrive Entreprise
- Partage externe : requiert accord préalable du DPO

3. ÉQUIPEMENT
- Verrouillage automatique après 5 minutes d'inactivité
- Mise à jour antivirus hebdomadaire
- Rapport de non-conformité à it-security@centaures-routiers.fr

Cette politique est effective immédiatement.
Directeur SI : Marc Dubois""",
        "source_id": "politique_securite_v3.pdf",
        "source_type": "pdf",
        "metadata": {
            "department": "it",
            "language": "fr",
            "security_level": "confidential",
            "approved_by": "Marc Dubois",
            "approval_date": "2024-02-01"
        }
    }
]

# --- Step 2. Initialize and use the ingestion service ---
try:
    ingestion_service = IngestionService()
    
    # Ingest all documents
    chunks = ingestion_service.ingest_documents(sample_documents)
    
    # Get stats
    stats = ingestion_service.get_ingestion_stats()
    
    print(f"✅ Seed completed successfully!")
    print(f"   • Documents processed: {len(sample_documents)}")
    print(f"   • Chunks created: {len(chunks)}")
    print(f"   • Total chunks in vector store: {stats['total_chunks']}")
    print(f"   • Chunker used: {stats['chunker_type']}")
    print(f"   • Embedding model: {stats['embedding_model']}")
    
    # Show sample chunks
    print(f"\n📄 Sample chunks created:")
    for i, chunk in enumerate(chunks[:2]):  # Show first 2 chunks
        print(f"\n   Chunk {i+1} (from {chunk.source_id}):")
        print(f"   Content: {chunk.content[:80]}...")
        print(f"   Metadata keys: {list(chunk.metadata.keys())}")
        
except Exception as e:
    print(f"❌ Error during seeding: {e}")
    import traceback
    traceback.print_exc()

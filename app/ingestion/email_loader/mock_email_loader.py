import logging
from typing import List, Dict
from datetime import datetime, timedelta
import random
from app.ingestion.email_loader.base_email_loader import BaseEmailLoader


logger = logging.getLogger(__name__)

class MockEmailLoader(BaseEmailLoader):
    """
    Chargeur d’e-mails factices pour le développement et les tests.
    Génère des données d’e-mails réalistes afin de débloquer le développement du pipeline.
    """

    def __init__(
        self,
        num_emails: int = 20,
        folder_name: str = "Boîte de réception",
        include_attachments: bool = False,
        random_seed: int = 42
    ):
        self.num_emails = num_emails
        self.folder_name = folder_name
        self.include_attachments = include_attachments
        random.seed(random_seed)

        # Données exemples pour générer des e-mails réalistes
        self.senders = [
            "john.doe@entreprise.com",
            "sarah.smith@partenaire.com",
            "notifications@systeme.com",
            "alex.wong@equipe.com",
            "marketing@newsletter.com",
            "support@service.com"
        ]

        self.subjects = [
            "Mise à jour hebdomadaire du projet",
            "Compte rendu de la réunion de vendredi",
            "Important : action requise",
            "Votre rapport mensuel est prêt",
            "Déjeuner d’équipe la semaine prochaine",
            "Notification de maintenance du système",
            "Annonce d’une nouvelle fonctionnalité",
            "Documents pour la revue trimestrielle",
            "Bienvenue dans le nouveau projet !",
            "Rappel : échéance imminente"
        ]

        self.body_templates = [
            "Bonjour à tous,\n\nJe souhaitais simplement faire un point sur {project}. Nous faisons de bons progrès et devrions être dans les temps pour l’échéance du {deadline}.\n\nBien cordialement,\n{sender_name}",

            "Salut à tous,\n\nVeuillez trouver ci-joint le compte rendu de notre dernière réunion. Principales décisions :\n- {point1}\n- {point2}\n\nLes prochaines étapes seront communiquées prochainement.\n\nMerci,\n{sender_name}",

            "Cher collègue,\n\nCeci est une notification importante concernant {topic}. Merci de prendre les mesures nécessaires avant le {date}.\n\nMerci de votre attention.\n\nCordialement,\n{sender_name}",

            "Bonjour,\n\nJe fais suite à notre conversation à propos de {subject}. Voici les points abordés :\n\n- Élément 1 : {detail1}\n- Élément 2 : {detail2}\n\nN’hésitez pas à me contacter si vous avez des questions.\n\nBien à vous,\n{sender_name}"
        ]

        logger.info(f"✅ Initialisation du MockEmailLoader avec {num_emails} e-mails simulés")
        logger.info("📝 Utilisation de données synthétiques pour le développement/test")

    def authenticate(self):
        """Authentification simulée – réussit instantanément."""
        logger.info("🔐 Authentification simulée – toujours réussie")
        import time
        time.sleep(0.1)

    def load_emails(self) -> List[Dict]:
        """Génère des données d’e-mails factices réalistes."""
        logger.info(f"📨 Génération de {self.num_emails} e-mails simulés...")
        emails: List[Dict] = []
        base_date = datetime.now()

        for i in range(self.num_emails):
            # Generate random but realistic data
            sender = random.choice(self.senders)
            sender_name = sender.split('@')[0].replace('.', ' ').title()
            subject = random.choice(self.subjects)

            if random.random() > 0.7:
                subject = f"Re : {subject}"
            if random.random() > 0.9:
                subject = f"Tr : {subject}"

            template = random.choice(self.body_templates)
            body = template.format(
                project=f"Projet {random.choice(['Alpha', 'Bêta', 'Gamma'])}",
                deadline=(base_date + timedelta(days=random.randint(5, 30))).strftime("%d %B"),
                sender_name=sender_name,
                point1=random.choice(["Finaliser les spécifications", "Mettre à jour la documentation", "Planifier la démo"]),
                point2=random.choice(["Revoir le budget", "Coordonner avec l’équipe", "Préparer la présentation"]),
                topic=random.choice(["mise à jour de sécurité", "changement de politique", "mise à niveau du système"]),
                date=(base_date + timedelta(days=random.randint(1, 14))).strftime("%Y-%m-%d"),
                subject=subject.lower(),
                detail1=random.choice(["analyse terminée", "exigences recueillies", "brouillon préparé"]),
                detail2=random.choice(["en attente de retours", "réunion planifiée", "préparation des prochaines étapes"])
            )

            email_date = base_date - timedelta(
                days=random.randint(0, 30),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )

            email_data = {
                "id": f"mock_email_{i:04d}",
                "subject": subject,
                "sender": sender,
                "date": email_date,
                "body": body,
            }
            emails.append(email_data)

        emails.sort(key=lambda x: x["date"], reverse=True)
        logger.info(f"✅ {len(emails)} e-mails simulés générés avec succès")
        return emails

    def get_source_name(self) -> str:
        return "email_simule"

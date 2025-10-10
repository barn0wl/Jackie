import logging
from typing import List, Dict
from datetime import datetime, timedelta
import random
from app.ingestion.base_email_loader import BaseEmailLoader

logger = logging.getLogger(__name__)

class MockEmailLoader(BaseEmailLoader):
    """
    Mock email loader for development and testing.
    Generates realistic fake email data to unblock pipeline development.
    """
    
    def __init__(
        self,
        num_emails: int = 20,
        folder_name: str = "Inbox",
        include_attachments: bool = False,
        random_seed: int = 42
    ):
        self.num_emails = num_emails
        self.folder_name = folder_name
        self.include_attachments = include_attachments
        random.seed(random_seed)
        
        # Sample data for generating realistic emails
        self.senders = [
            "john.doe@company.com",
            "sarah.smith@partner.com", 
            "notifications@system.com",
            "alex.wong@team.com",
            "marketing@newsletter.com",
            "support@service.com"
        ]
        
        self.subjects = [
            "Weekly Project Update",
            "Meeting Notes from Friday",
            "Important: Action Required",
            "Your Monthly Report is Ready",
            "Team Lunch Next Week",
            "System Maintenance Notification",
            "New Feature Announcement",
            "Quarterly Review Materials",
            "Welcome to the New Project!",
            "Reminder: Deadline Approaching"
        ]
        
        self.body_templates = [
            "Hello team,\n\nJust wanted to provide an update on {project}. We're making good progress and should be on track for the {deadline} deadline.\n\nBest regards,\n{sender_name}",
            
            "Hi everyone,\n\nPlease find attached the meeting notes from our recent discussion. Key decisions:\n- {point1}\n- {point2}\n\nNext steps will be shared shortly.\n\nCheers,\n{sender_name}",
            
            "Dear colleague,\n\nThis is an important notification regarding {topic}. Please take appropriate action by {date}.\n\nThank you for your attention to this matter.\n\nSincerely,\n{sender_name}",
            
            "Hello,\n\nI'm writing to follow up on our conversation about {subject}. Here are the details we discussed:\n\n- Item 1: {detail1}\n- Item 2: {detail2}\n\nLet me know if you have any questions.\n\nBest,\n{sender_name}"
        ]
        
        logger.info(f"✅ Initialized MockEmailLoader with {num_emails} sample emails")
        logger.info("📝 Using synthetic data for development/testing")

    def authenticate(self):
        """Mock authentication - always succeeds instantly."""
        logger.info("🔐 Mock authentication - always successful")
        # Simulate brief authentication delay
        import time
        time.sleep(0.1)

    def load_emails(self) -> List[Dict]:
        """Generate realistic mock email data."""
        logger.info(f"📨 Generating {self.num_emails} mock emails...")
        
        emails: List[Dict] = []
        base_date = datetime.now()
        
        for i in range(self.num_emails):
            # Generate random but realistic data
            sender = random.choice(self.senders)
            sender_name = sender.split('@')[0].replace('.', ' ').title()
            subject = random.choice(self.subjects)
            
            # Create variation in subjects
            if random.random() > 0.7:
                subject = f"Re: {subject}"
            if random.random() > 0.9:
                subject = f"Fwd: {subject}"
            
            # Generate body with template
            template = random.choice(self.body_templates)
            body = template.format(
                project=f"Project {random.choice(['Alpha', 'Beta', 'Gamma'])}",
                deadline=(base_date + timedelta(days=random.randint(5, 30))).strftime("%B %d"),
                sender_name=sender_name,
                point1=random.choice(["Finalize requirements", "Update documentation", "Schedule demo"]),
                point2=random.choice(["Review budget", "Coordinate with team", "Prepare presentation"]),
                topic=random.choice(["security update", "policy change", "system upgrade"]),
                date=(base_date + timedelta(days=random.randint(1, 14))).strftime("%Y-%m-%d"),
                subject=subject.lower(),
                detail1=random.choice(["completed analysis", "gathered requirements", "prepared draft"]),
                detail2=random.choice(["awaiting feedback", "scheduled meeting", "preparing next steps"])
            )
            
            # Generate random date within last 30 days
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
        
        # Sort by date (newest first)
        emails.sort(key=lambda x: x["date"], reverse=True)
        
        logger.info(f"✅ Generated {len(emails)} realistic mock emails")
        return emails
    
    def get_source_name(self) -> str:
        return "mock_email"

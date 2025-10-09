# app/models/document_chunk.py
from typing import Dict, Optional
from pydantic import BaseModel, Field

class DocumentChunk(BaseModel):
    """Represents a single chunk of text extracted from a source document."""
    id: Optional[str] = Field(None, description="Unique ID for this chunk (optional, auto-generated if absent).")
    content: str = Field(..., description="Raw text content of the chunk.")
    metadata: Optional[Dict[str, str]] = Field(
        default_factory=dict,
        description="Metadata about the chunk (e.g. source, author, date, subject, etc.)."
    )

    class Config:
        schema_extra = {
            "example": {
                "id": "email_2024_09_01_12345",
                "content": "The meeting is scheduled for Friday at 10am.",
                "metadata": {
                    "source": "inbox/finance_team.msg",
                    "sender": "jane@company.com",
                    "date": "2024-09-01T10:00:00",
                    "subject": "Team Meeting"
                }
            }
        }

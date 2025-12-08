# app/models/document_chunk.py
from typing import Dict, Optional, List, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class DocumentChunk(BaseModel):
    """Represents a single chunk of text extracted from a source document."""
    
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique ID for this chunk."
    )
    content: str = Field(..., description="Raw text content of the chunk.")
    
    # Metadata fields
    source_id: Optional[str] = Field(
        None, 
        description="ID of the source document (e.g., file path, URL, database ID)."
    )
    source_type: Optional[str] = Field(
        None,
        description="Type of source (e.g., 'pdf', 'email', 'database', 'webpage')."
    )
    chunk_index: Optional[int] = Field(
        None,
        description="Index of this chunk within the source document."
    )
    
    # Additional metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the chunk."
    )
    
    # System fields
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when this chunk was created."
    )
    
    class Config:
        schema_extra = {
            "example": {
                "id": "chunk_12345",
                "content": "The meeting is scheduled for Friday at 10am.",
                "source_id": "inbox/finance_team.msg",
                "source_type": "email",
                "chunk_index": 2,
                "metadata": {
                    "sender": "jane@company.com",
                    "date": "2024-09-01T10:00:00",
                    "subject": "Team Meeting",
                    "language": "fr",
                    "department": "finance"
                },
                "created_at": "2024-01-15T10:30:00Z"
            }
        }

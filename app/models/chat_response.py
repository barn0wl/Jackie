# app/models/chat_response.py
from typing import List, Optional
from pydantic import BaseModel, Field

class SourceMetadata(BaseModel):
    """Represents a single document source retrieved from the vector store."""
    source: str = Field(..., description="File or document source name.")
    page: Optional[int] = Field(None, description="Page number or section index if applicable.")
    score: Optional[float] = Field(None, description="Similarity score between 0 and 1.")

class ChatResponse(BaseModel):
    """Response returned to the user, including the final answer and references."""
    answer: str = Field(..., description="Generated natural language answer to the user's question.")
    sources: Optional[List[SourceMetadata]] = Field(
        default=None, description="Optional list of document sources used for context."
    )

    class Config:
        schema_extra = {
            "example": {
                "answer": "Refunds are processed within 30 days of purchase.",
                "sources": [
                    {"source": "policy.pdf", "page": 2, "score": 0.92}
                ]
            }
        }

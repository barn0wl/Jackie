# app/models/chat_request.py
from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    """Incoming request from user containing the query/question."""

    query: str = Field(..., description="The user's natural language question or message.")

    class Config:
        schema_extra = {
            "example": {
                "query": "What is our refund policy?"
            }
        }

# src/models/conversation.py
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime

class Message(BaseModel):
    role: str
    content: str
    created_at: datetime = datetime.utcnow()

class Conversation(BaseModel):
    id: str  # Add this line
    messages: List[Message]
    questions_asked: int
    metadata: Dict = {}
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()
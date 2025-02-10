# src/api/routes/chat.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    conversation_history: List[Dict[str, str]]
    questions_asked: int

class ChatResponse(BaseModel):
    response: str
    updated_state: Dict
    questions_asked: int

@router.post("/chat")
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    try:
        # For now, just echo back the message
        return ChatResponse(
            response=f"Received: {request.message}",
            updated_state={"history": request.conversation_history},
            questions_asked=request.questions_asked + 1
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

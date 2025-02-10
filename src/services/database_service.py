# src/services/database_service.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import List, Optional, Generator
from src.models.database import Base, DBConversation, DBMessage
from src.models.conversation import Conversation, Message
import os
from dotenv import load_dotenv
import json

class DatabaseService:
    def __init__(self):
        load_dotenv()
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL not found in environment variables")
            
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)

    @contextmanager
    def get_db(self) -> Generator[Session, None, None]:
        """
        Get database session with context management.
        
        Returns:
            Generator yielding SQLAlchemy Session
        """
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def create_conversation(self, user_id: str, metadata: Optional[dict] = None) -> Conversation:
        """Create a new conversation in the database"""
        with self.get_db() as db:
            db_conversation = DBConversation(
                user_id=user_id,
                conversation_metadata=json.dumps(metadata) if metadata else None
            )
            db.add(db_conversation)
            db.commit()
            db.refresh(db_conversation)
            
            return Conversation(
                id=db_conversation.id,
                messages=[],
                questions_asked=metadata.get('questions_asked', 0) if metadata else 0,
                metadata=metadata or {}
            )

    def add_message(self, conversation_id: str, role: str, content: str, token_count: int) -> Message:
        """Add a new message to a conversation"""
        with self.get_db() as db:
            message = DBMessage(
                conversation_id=conversation_id,
                role=role,
                content=content,
                token_count=token_count
            )
            db.add(message)
            db.commit()
            db.refresh(message)
            
            return Message(
                role=role,
                content=content
            )

    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get a conversation by its ID"""
        with self.get_db() as db:
            db_conversation = db.query(DBConversation).filter(
                DBConversation.id == conversation_id
            ).first()
            
            if not db_conversation:
                return None
                
            messages = [
                Message(
                    role=msg.role,
                    content=msg.content,
                    created_at=msg.created_at
                ) for msg in db_conversation.messages
            ]
            
            metadata = json.loads(db_conversation.conversation_metadata) if db_conversation.conversation_metadata else {}
            
            return Conversation(
                id=db_conversation.id,
                messages=messages,
                questions_asked=metadata.get('questions_asked', 0),
                metadata=metadata
            )

    def update_conversation_metadata(self, conversation_id: str, metadata: dict):
        """Update conversation metadata in the database"""
        with self.get_db() as db:
            db_conversation = db.query(DBConversation).filter(
                DBConversation.id == conversation_id
            ).first()
            
            if db_conversation:
                db_conversation.conversation_metadata = json.dumps(metadata)
                db.commit()
                db.refresh(db_conversation)
            else:
                raise ValueError(f"Conversation with id {conversation_id} not found")

    def get_conversations_for_user(self, user_id: str) -> List[Conversation]:
        """Get all conversations for a user"""
        with self.get_db() as db:
            db_conversations = db.query(DBConversation).filter(
                DBConversation.user_id == user_id
            ).all()
            
            return [
                Conversation(
                    id=conv.id,
                    messages=[
                        Message(
                            role=msg.role,
                            content=msg.content,
                            created_at=msg.created_at
                        ) for msg in conv.messages
                    ],
                    questions_asked=json.loads(conv.conversation_metadata).get('questions_asked', 0) if conv.conversation_metadata else 0,
                    metadata=json.loads(conv.conversation_metadata) if conv.conversation_metadata else {}
                ) for conv in db_conversations
            ]

    def delete_conversation(self, conversation_id: str):
        """Delete a conversation and all its messages"""
        with self.get_db() as db:
            db_conversation = db.query(DBConversation).filter(
                DBConversation.id == conversation_id
            ).first()
            
            if db_conversation:
                db.delete(db_conversation)
                db.commit()
            else:
                raise ValueError(f"Conversation with id {conversation_id} not found")
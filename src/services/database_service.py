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
from src.services.redis_service import RedisService

class DatabaseService:
    def __init__(self):
        load_dotenv()
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL not found in environment variables")
            
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.redis_service = RedisService()

    @contextmanager
    def get_db(self) -> Generator[Session, None, None]:
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def create_conversation(self, user_id: str, metadata: Optional[dict] = None) -> Conversation:
        """Create a new conversation and cache it"""
        with self.get_db() as db:
            db_conversation = DBConversation(
                user_id=user_id,
                conversation_metadata=json.dumps(metadata) if metadata else None
            )
            db.add(db_conversation)
            db.commit()
            db.refresh(db_conversation)
            
            conversation = Conversation(
                id=db_conversation.id,
                messages=[],
                questions_asked=metadata.get('questions_asked', 0) if metadata else 0,
                metadata=metadata or {}
            )
            
            # Cache the new conversation
            self.redis_service.cache_conversation(
                conversation.id,
                conversation.dict()
            )
            
            return conversation

    def add_message(self, conversation_id: str, role: str, content: str, token_count: int) -> Message:
        """Add message to database and update cache"""
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
            
            msg = Message(
                role=role,
                content=content
            )
            
            # Update cache with new message
            self.redis_service.add_message_to_cache(
                conversation_id,
                msg.dict()
            )
            
            return msg

    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get conversation from cache or database"""
        # Try cache first
        cached_conversation = self.redis_service.get_cached_conversation(conversation_id)
        if cached_conversation:
            return Conversation(**cached_conversation)
        
        # If not in cache, get from database
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
            
            conversation = Conversation(
                id=db_conversation.id,
                messages=messages,
                questions_asked=metadata.get('questions_asked', 0),
                metadata=metadata
            )
            
            # Cache for future requests
            self.redis_service.cache_conversation(
                conversation.id,
                conversation.dict()
            )
            
            return conversation

    def update_conversation_metadata(self, conversation_id: str, metadata: dict):
        """Update metadata in both database and cache"""
        with self.get_db() as db:
            db_conversation = db.query(DBConversation).filter(
                DBConversation.id == conversation_id
            ).first()
            
            if db_conversation:
                db_conversation.conversation_metadata = json.dumps(metadata)
                db.commit()
                db.refresh(db_conversation)
                
                # Update cache
                self.redis_service.update_conversation_metadata(
                    conversation_id,
                    metadata
                )
            else:
                raise ValueError(f"Conversation with id {conversation_id} not found")
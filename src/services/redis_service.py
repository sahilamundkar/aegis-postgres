import redis
import json
from typing import Optional, Dict, Any
from datetime import datetime
from src.config.config import get_settings

class RedisService:
    def __init__(self):
        self.settings = get_settings()
        self.redis_client = redis.from_url(
            self.settings.REDIS_URL,
            decode_responses=True
        )
        self.conversation_prefix = "conv:"
        self.cache_ttl = 3600  # 1 hour cache TTL

    def get_conversation_cache_key(self, conversation_id: str) -> str:
        """Generate Redis key for conversation"""
        return f"{self.conversation_prefix}{conversation_id}"

    def serialize_datetime(self, obj):
        """Convert datetime objects to string for JSON serialization"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")

    def deserialize_datetime(self, data):
        """Convert string back to datetime objects after JSON deserialization"""
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str):
                    try:
                        data[key] = datetime.fromisoformat(value)
                    except ValueError:
                        pass
        return data

    def cache_conversation(self, conversation_id: str, data: Dict[str, Any]) -> None:
        """Cache conversation data in Redis"""
        key = self.get_conversation_cache_key(conversation_id)
        serialized_data = json.dumps(data, default=self.serialize_datetime)
        self.redis_client.setex(
            key,
            self.cache_ttl,
            serialized_data
        )

    def get_cached_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached conversation data"""
        key = self.get_conversation_cache_key(conversation_id)
        data = self.redis_client.get(key)
        if data:
            return self.deserialize_datetime(json.loads(data))
        return None

    def update_conversation_metadata(self, conversation_id: str, metadata: Dict[str, Any]) -> None:
        """Update specific metadata fields in cached conversation"""
        key = self.get_conversation_cache_key(conversation_id)
        cached_data = self.get_cached_conversation(conversation_id)
        if cached_data:
            cached_data['metadata'] = metadata
            self.cache_conversation(conversation_id, cached_data)

    def add_message_to_cache(self, conversation_id: str, message: Dict[str, Any]) -> None:
        """Add a new message to cached conversation"""
        key = self.get_conversation_cache_key(conversation_id)
        cached_data = self.get_cached_conversation(conversation_id)
        if cached_data:
            if 'messages' not in cached_data:
                cached_data['messages'] = []
            cached_data['messages'].append(message)
            self.cache_conversation(conversation_id, cached_data)

    def invalidate_cache(self, conversation_id: str) -> None:
        """Remove conversation from cache"""
        key = self.get_conversation_cache_key(conversation_id)
        self.redis_client.delete(key)
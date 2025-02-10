from dataclasses import dataclass
from typing import Optional
import os
from dotenv import load_dotenv

@dataclass
class Settings:
    # Put required fields (no default values) first
    DATABASE_URL: str
    GROQ_API_KEY: str
    # Then fields with default values
    MODEL_NAME: str = "llama-3.3-70b-Versatile"
    TOKEN_LIMIT: int = 5500
    REDIS_URL: str = "redis://localhost:6379/0"

def get_settings() -> Settings:
    """Load settings from environment variables"""
    load_dotenv(dotenv_path="src/.env")
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment variables")
    
    groq_api_key = os.getenv('GROQ_API_KEY')
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY not found in environment variables")
    
    return Settings(
        DATABASE_URL=database_url,
        GROQ_API_KEY=groq_api_key
    )
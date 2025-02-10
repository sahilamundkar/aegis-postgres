from src.models.database import Base
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
from pathlib import Path

def init_database():
    # Get the absolute path to the src directory
    src_dir = Path(__file__).parent / 'src'
    env_path = src_dir / '.env'
    
    # Load environment variables from src/.env
    load_dotenv(dotenv_path=env_path)
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError(f"DATABASE_URL not found in environment variables. Checked path: {env_path}")
    
    try:
        engine = create_engine(database_url)
        Base.metadata.create_all(engine)
        print("Database initialized successfully!")
    except Exception as e:
        print(f"Error initializing database: {str(e)}")

if __name__ == "__main__":
    init_database()
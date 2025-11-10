from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

from models import Base  # Import from models.py

# Database basic setting
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///auth.db')

# Database engine
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

# Create session 
SessionLocal = sessionmaker(
    bind=engine, 
    autocommit=False, 
    autoflush=False
)

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    return db
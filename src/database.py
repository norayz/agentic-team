"""Database configuration and session management."""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models import Base

# Determine database URL from environment or use default
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./todos.db")

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency injection function for FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

"""Database initialization and session management."""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from src.models import Base

# Use environment variable for database URL, default to local SQLite
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///todos.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize the database, creating all tables."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    """Get a database session for dependency injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

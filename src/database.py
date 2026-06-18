from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import os

# Get database URL from environment, default to SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./todos.db")

# Initialize engine with error handling
try:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    )
except Exception as e:
    raise RuntimeError(
        f"Failed to initialize database engine. "
        f"Check DATABASE_URL environment variable. Error: {e}"
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency to get database session for route handlers."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables. Call during app startup."""
    from src.models import Base
    try:
        Base.metadata.create_all(bind=engine)
    except SQLAlchemyError as e:
        raise RuntimeError(f"Failed to create database tables. Error: {e}")

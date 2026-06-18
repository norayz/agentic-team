"""Pytest configuration and fixtures."""
import os
import tempfile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
import pytest

from src.database import Base, get_db
from src.main import app


@pytest.fixture
def test_db():
    """Create a test database."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(bind=engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    yield SessionLocal()
    
    app.dependency_overrides.clear()
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(test_db):
    """Create a test client."""
    return TestClient(app)

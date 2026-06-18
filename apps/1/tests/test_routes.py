"""Tests for todo API routes."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime

from src.main import app
from src.database import get_db
from src.models import Base


@pytest.fixture
def db():
    """Create a test database."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield db
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db):
    """Create a test client."""
    return TestClient(app)


# Phase 2: POST /todos - Create todo
def test_create_todo_success(client):
    """Test: POST /todos with valid title returns 201."""
    response = client.post("/todos", json={"title": "Buy milk"})
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["title"] == "Buy milk"
    assert data["completed"] is False
    assert "created_at" in data


def test_create_todo_missing_title(client):
    """Test: POST /todos without title returns 422."""
    response = client.post("/todos", json={})
    assert response.status_code == 422


def test_create_todo_empty_title(client):
    """Test: POST /todos with empty title returns 422."""
    response = client.post("/todos", json={"title": ""})
    assert response.status_code == 422


def test_create_todo_whitespace_title(client):
    """Test: POST /todos with whitespace-only title returns 422."""
    response = client.post("/todos", json={"title": "   "})
    assert response.status_code == 422


def test_create_todo_strips_whitespace(client):
    """Test: POST /todos strips leading/trailing whitespace from title."""
    response = client.post("/todos", json={"title": "  Buy milk  "})
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Buy milk"


# Phase 3: GET /todos - List todos
def test_list_todos_empty(client):
    """Test: GET /todos returns 200 with empty array initially."""
    response = client.get("/todos")
    assert response.status_code == 200
    assert response.json() == []


def test_list_todos_with_items(client):
    """Test: GET /todos returns all created todos."""
    client.post("/todos", json={"title": "Task 1"})
    client.post("/todos", json={"title": "Task 2"})
    response = client.get("/todos")
    assert response.status_code == 200
    todos = response.json()
    assert len(todos) == 2
    assert todos[0]["title"] == "Task 1"
    assert todos[1]["title"] == "Task 2"


# Phase 4: GET /todos/{id} - Get single todo
def test_get_todo_success(client):
    """Test: GET /todos/{id} returns 200 for existing todo."""
    client.post("/todos", json={"title": "Buy milk"})
    response = client.get("/todos/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["title"] == "Buy milk"


def test_get_todo_not_found(client):
    """Test: GET /todos/{id} returns 404 for non-existent todo."""
    response = client.get("/todos/999")
    assert response.status_code == 404


# Phase 5: PUT /todos/{id} - Update todo
def test_update_todo_title(client):
    """Test: PUT /todos/{id} updates title and returns 200."""
    client.post("/todos", json={"title": "Original"})
    response = client.put("/todos/1", json={"title": "Updated"})
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated"
    assert data["completed"] is False


def test_update_todo_completed(client):
    """Test: PUT /todos/{id} updates completed status and returns 200."""
    client.post("/todos", json={"title": "Task"})
    response = client.put("/todos/1", json={"completed": True})
    assert response.status_code == 200
    data = response.json()
    assert data["completed"] is True
    assert data["title"] == "Task"


def test_update_todo_partial(client):
    """Test: PUT /todos/{id} partial update preserves unset fields."""
    client.post("/todos", json={"title": "Original"})
    # Update only title
    client.put("/todos/1", json={"title": "Updated"})
    # Update only completed, title should stay
    response = client.put("/todos/1", json={"completed": True})
    data = response.json()
    assert data["title"] == "Updated"
    assert data["completed"] is True


def test_update_todo_not_found(client):
    """Test: PUT /todos/{id} returns 404 for non-existent todo."""
    response = client.put("/todos/999", json={"title": "No todo"})
    assert response.status_code == 404


def test_update_todo_empty_title(client):
    """Test: PUT /todos/{id} rejects empty title with 422."""
    client.post("/todos", json={"title": "Original"})
    response = client.put("/todos/1", json={"title": ""})
    assert response.status_code == 422


# Phase 6: DELETE /todos/{id} - Delete todo
def test_delete_todo_success(client):
    """Test: DELETE /todos/{id} returns 204 on success."""
    client.post("/todos", json={"title": "To delete"})
    response = client.delete("/todos/1")
    assert response.status_code == 204
    # Verify it's actually deleted
    verify = client.get("/todos/1")
    assert verify.status_code == 404


def test_delete_todo_not_found(client):
    """Test: DELETE /todos/{id} returns 404 for non-existent todo."""
    response = client.delete("/todos/999")
    assert response.status_code == 404


# Phase 7: JSON structure consistency
def test_json_structure_consistency(client):
    """Test: All responses have consistent JSON structure."""
    # Create a todo
    create_response = client.post("/todos", json={"title": "Task"})
    todo = create_response.json()

    # Check all required fields are present
    required_fields = {"id", "title", "completed", "created_at"}
    assert set(todo.keys()) == required_fields

    # Verify field types
    assert isinstance(todo["id"], int)
    assert isinstance(todo["title"], str)
    assert isinstance(todo["completed"], bool)
    assert isinstance(todo["created_at"], str)  # ISO format datetime

    # Verify GET returns same structure
    get_response = client.get("/todos/1")
    get_todo = get_response.json()
    assert set(get_todo.keys()) == required_fields

    # Verify LIST returns same structure
    list_response = client.get("/todos")
    todos = list_response.json()
    for t in todos:
        assert set(t.keys()) == required_fields
